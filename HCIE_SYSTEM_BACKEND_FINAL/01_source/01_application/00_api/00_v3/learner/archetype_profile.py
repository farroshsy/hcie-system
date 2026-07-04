"""Learner-facing archetype profile endpoints.

The archetype profile captures the learner's self-reported VARK / behavioural
/ motivational tendencies. Slice 5b design note: this profile is
**observational only** — it never feeds back into MAB scoring. It exists so
the instructor dashboard can do Archetype × Concept analysis without
contaminating HCIE/JT validation.

Endpoints:

- ``GET /v3/learner/archetype-profile/{user_id}`` — read the caller's own
  profile. Returns 404 if the learner hasn't completed onboarding.
- ``PUT /v3/learner/archetype-profile/{user_id}`` — write the caller's own
  profile (upsert). Called when the learner submits the onboarding card or
  re-takes the survey from the profile page.
"""

from __future__ import annotations

import json
import math
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator

from app.api.dependencies.rbac import require_student
from app.api.v3.dependencies_its import get_its_runtime_service


router = APIRouter(prefix="/archetype-profile", tags=["v3-learner-archetype"])


# Allowed score keys for each axis. We reject unknown keys on PUT to keep
# the dashboard groupings tidy.
VARK_KEYS = ("visual", "auditory", "reading", "kinesthetic")
BEHAV_KEYS = ("participant", "passenger", "partner", "pathfinder", "pirate", "prisoner")
MOTIV_KEYS = ("social", "solitary", "logical", "explorer")


class ArchetypeProfile(BaseModel):
    user_id: str
    vark_scores: Dict[str, float]
    behav_scores: Dict[str, float]
    motiv_scores: Dict[str, float]
    source: str = "self_report"
    confidence: float = 0.5
    raw_responses: Dict[str, Any] = Field(default_factory=dict)


class ArchetypeProfileWrite(BaseModel):
    vark_scores: Dict[str, float]
    behav_scores: Dict[str, float]
    motiv_scores: Dict[str, float]
    source: str = "self_report"
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    raw_responses: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("vark_scores")
    @classmethod
    def _check_vark(cls, v: Dict[str, float]) -> Dict[str, float]:
        return _validate_axis(v, VARK_KEYS, "vark_scores")

    @field_validator("behav_scores")
    @classmethod
    def _check_behav(cls, v: Dict[str, float]) -> Dict[str, float]:
        return _validate_axis(v, BEHAV_KEYS, "behav_scores")

    @field_validator("motiv_scores")
    @classmethod
    def _check_motiv(cls, v: Dict[str, float]) -> Dict[str, float]:
        return _validate_axis(v, MOTIV_KEYS, "motiv_scores")

    @field_validator("source")
    @classmethod
    def _check_source(cls, v: str) -> str:
        if v not in {"self_report", "inferred", "hybrid", "default"}:
            raise ValueError(
                "source must be one of self_report|inferred|hybrid|default"
            )
        return v


def _validate_axis(
    value: Dict[str, float],
    allowed: tuple,
    field_name: str,
) -> Dict[str, float]:
    extras = set(value.keys()) - set(allowed)
    if extras:
        raise ValueError(
            f"{field_name} has unknown keys: {sorted(extras)}; allowed = {list(allowed)}"
        )
    # We don't require sum=1.0 (the frontend may submit raw weights) but we
    # do require non-negative finite floats.
    out: Dict[str, float] = {}
    for k in allowed:
        raw = value.get(k, 0.0)
        try:
            f = float(raw)
        except (TypeError, ValueError):
            raise ValueError(f"{field_name}.{k} must be a number")
        if f < 0 or math.isnan(f):  # NaN check
            raise ValueError(f"{field_name}.{k} must be non-negative finite")
        out[k] = f
    # Normalize to sum=1 if total > 0, otherwise leave as uniform.
    total = sum(out.values())
    if total > 0:
        out = {k: round(v / total, 4) for k, v in out.items()}
    else:
        n = len(allowed)
        out = {k: round(1.0 / n, 4) for k in allowed}
    return out


def _auth_check(user: Dict[str, Any], target_user_id: str) -> None:
    """Learners can only read/write their own archetype profile."""
    caller_id = str(user.get("id") or user.get("user_id") or "")
    if not caller_id:
        raise HTTPException(status_code=401, detail="User identity missing")
    if caller_id != target_user_id:
        raise HTTPException(
            status_code=403,
            detail="Cannot access another learner's archetype profile",
        )


def _as_dict(value: Any) -> Dict[str, float]:
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            return {}
    if not isinstance(value, dict):
        return {}
    out: Dict[str, float] = {}
    for k, v in value.items():
        try:
            out[str(k)] = float(v)
        except (TypeError, ValueError):
            continue
    return out


def _as_raw(value: Any) -> Dict[str, Any]:
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            return {}
    if isinstance(value, dict):
        return value
    return {}


@router.get("/{user_id}", response_model=ArchetypeProfile)
async def get_profile(
    user_id: str,
    user: Dict[str, Any] = Depends(require_student),
    its=Depends(get_its_runtime_service),
):
    _auth_check(user, user_id)
    row = its.postgres_store.execute_read(
        """
        SELECT user_id, vark_scores, behav_scores, motiv_scores,
               source, confidence, raw_responses
        FROM user_archetype_profile
        WHERE user_id = %s
        """,
        (user_id,),
        fetch_one=True,
    )
    if not row:
        raise HTTPException(
            status_code=404,
            detail="No archetype profile yet — complete onboarding first",
        )
    return ArchetypeProfile(
        user_id=str(row["user_id"]),
        vark_scores=_as_dict(row.get("vark_scores")),
        behav_scores=_as_dict(row.get("behav_scores")),
        motiv_scores=_as_dict(row.get("motiv_scores")),
        source=str(row.get("source") or "self_report"),
        confidence=float(row.get("confidence") or 0.5),
        raw_responses=_as_raw(row.get("raw_responses")),
    )


@router.put("/{user_id}", response_model=ArchetypeProfile)
async def put_profile(
    user_id: str,
    body: ArchetypeProfileWrite,
    user: Dict[str, Any] = Depends(require_student),
    its=Depends(get_its_runtime_service),
):
    _auth_check(user, user_id)
    # Upsert via ON CONFLICT (user_id). The score JSONB columns are nullable
    # in the table (see migration 029 design note), so a partial insert is
    # safe even when prior rows lacked one axis.
    its.postgres_store.execute_write(
        """
        INSERT INTO user_archetype_profile (
            user_id, vark_scores, behav_scores, motiv_scores,
            source, confidence, raw_responses, updated_at
        ) VALUES (
            %s, CAST(%s AS jsonb), CAST(%s AS jsonb), CAST(%s AS jsonb),
            %s, %s, CAST(%s AS jsonb), now()
        )
        ON CONFLICT (user_id) DO UPDATE SET
            vark_scores = EXCLUDED.vark_scores,
            behav_scores = EXCLUDED.behav_scores,
            motiv_scores = EXCLUDED.motiv_scores,
            source = EXCLUDED.source,
            confidence = EXCLUDED.confidence,
            raw_responses = EXCLUDED.raw_responses,
            updated_at = now()
        """,
        (
            user_id,
            json.dumps(body.vark_scores),
            json.dumps(body.behav_scores),
            json.dumps(body.motiv_scores),
            body.source,
            body.confidence,
            json.dumps(body.raw_responses),
        ),
    )

    return ArchetypeProfile(
        user_id=user_id,
        vark_scores=body.vark_scores,
        behav_scores=body.behav_scores,
        motiv_scores=body.motiv_scores,
        source=body.source,
        confidence=body.confidence,
        raw_responses=body.raw_responses,
    )
