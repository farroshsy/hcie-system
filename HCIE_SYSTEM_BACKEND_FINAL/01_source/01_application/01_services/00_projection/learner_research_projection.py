"""
Learner research projection service.

Slice 3 authority model:
- read-only over `learner_projections`, trajectory rows, and projection events
- no UnifiedBrain calls
- no mutation/backfill
- explicit insufficient_data when evidence is missing
"""

import csv
import io
import json
import math
from collections import Counter, defaultdict
from typing import Any, Dict, Iterable, List, Optional


GOVERNANCE_COMPONENTS = (
    "delta_m",
    "transfer",
    "challenge",
    "uncertainty",
    "zpd",
)


class LearnerResearchProjection:
    """Read-only research views for one learner."""

    def __init__(self, postgres_store: Any):
        self.postgres_store = postgres_store

    def _read(self, query: str, params: tuple = (), fetch_one: bool = False):
        if not self.postgres_store:
            return None if fetch_one else []
        try:
            return self.postgres_store.execute_read(query, params, fetch_one=fetch_one)
        except Exception:
            return None if fetch_one else []

    def _table_exists(self, table_name: str) -> bool:
        row = self._read("SELECT to_regclass(%s) AS table_name", (f"public.{table_name}",), fetch_one=True)
        return bool(row and row.get("table_name"))

    @staticmethod
    def _status(rows: Iterable[Any]) -> str:
        return "ok" if list(rows) else "insufficient_data"

    @staticmethod
    def _safe_float(value: Any) -> Optional[float]:
        try:
            if value is None:
                return None
            numeric = float(value)
            if math.isnan(numeric) or math.isinf(numeric):
                return None
            return numeric
        except Exception:
            return None

    @staticmethod
    def _jsonish(value: Any) -> Any:
        if value is None:
            return {}
        if isinstance(value, (dict, list)):
            return value
        try:
            return json.loads(value)
        except Exception:
            return value

    @staticmethod
    def _entropy(values: List[str]) -> float:
        if not values:
            return 0.0
        counts = Counter(values)
        total = sum(counts.values())
        return float(
            -sum((count / total) * math.log2(count / total) for count in counts.values())
        )

    def _projection_rows(self, user_id: str) -> List[Dict[str, Any]]:
        if not self._table_exists("learner_projections"):
            return []
        rows = self._read(
            """
            SELECT user_id, concept_id, recommended_concept, projection,
                   ux_semantics, governance, cold_start, selection_metrics,
                   capability_manifest_fingerprint, source_event_id, updated_at
            FROM learner_projections
            WHERE user_id = %s
            ORDER BY updated_at DESC
            """,
            (user_id,),
        )
        return [dict(row) for row in (rows or [])]

    def _trajectory_rows(self, user_id: str, limit: int = 500) -> List[Dict[str, Any]]:
        if not self._table_exists("experiment_trajectories"):
            return []
        rows = self._read(
            """
            SELECT *
            FROM experiment_trajectories
            WHERE user_id = %s
            ORDER BY timestamp ASC, interaction_number ASC
            LIMIT %s
            """,
            (user_id, limit),
        )
        return [dict(row) for row in (rows or [])]

    def governance_state(self, user_id: str) -> Dict[str, Any]:
        rows = self._projection_rows(user_id)
        if not rows:
            return {
                "user_id": user_id,
                "status": "insufficient_data",
                "reason": "projection_missing",
                "authority": "learner_projections",
                "semantic_version": "1.0",
            }
        row = rows[0]
        return {
            "user_id": user_id,
            "status": "ok",
            "authority": "learner_projections",
            "concept_id": row.get("concept_id"),
            "recommended_concept": row.get("recommended_concept"),
            "projection": self._jsonish(row.get("projection")),
            "ux_semantics": self._jsonish(row.get("ux_semantics")),
            "governance": self._jsonish(row.get("governance")),
            "cold_start": self._jsonish(row.get("cold_start")),
            "selection_metrics": self._jsonish(row.get("selection_metrics")),
            "capability_manifest_fingerprint": row.get("capability_manifest_fingerprint"),
            "source_event_id": row.get("source_event_id"),
            "updated_at": row.get("updated_at"),
            "semantic_version": "1.0",
        }

    def governance_trajectory(self, user_id: str, limit: int = 500) -> Dict[str, Any]:
        rows = self._trajectory_rows(user_id, limit)
        trajectory = []
        for row in rows:
            mb = row.get("mastery_before")
            ma = row.get("mastery_after")
            try:
                delta_m_real = (float(ma) - float(mb)) if (mb is not None and ma is not None) else None
            except (TypeError, ValueError):
                delta_m_real = None
            trajectory.append(
                {
                    # identifiers + context
                    "timestamp": row.get("timestamp"),
                    "experiment_run_id": row.get("experiment_run_id"),
                    "interaction_number": row.get("interaction_number"),
                    "concept": row.get("concept"),
                    "policy": row.get("policy"),
                    "arm_selected": row.get("selected_arm") or row.get("arm_selected"),
                    "capability_manifest_fingerprint": row.get("capability_manifest_fingerprint"),
                    # response
                    "correctness": row.get("correctness"),
                    "response_time": row.get("response_time"),
                    "difficulty": row.get("difficulty"),
                    # JT 6D decomposition (phase-A enriched)
                    "jt_value": row.get("jt_value"),
                    "jt_volatility": row.get("jt_volatility"),
                    "jt_delta_m": row.get("jt_delta_m_contribution"),
                    "jt_transfer": row.get("jt_transfer_contribution"),
                    "jt_challenge": row.get("jt_challenge_contribution"),
                    "jt_uncertainty": row.get("jt_uncertainty_contribution"),
                    "jt_zpd": row.get("jt_zpd_contribution"),
                    "jt_unclamped": row.get("jt_unclamped"),
                    "jt_clamped": row.get("jt_clamped"),
                    # mastery transition
                    "mastery_before": mb,
                    "mastery_after": ma,
                    "mastery_delta": delta_m_real,
                    # uncertainty / confidence
                    "uncertainty_before": row.get("uncertainty_before"),
                    "uncertainty_after": row.get("uncertainty_after"),
                    # transfer
                    "transfer_amount": row.get("transfer_amount"),
                    "transfer_efficiency": row.get("transfer_efficiency"),
                    # exploration / stability
                    "stability_index": row.get("stability_index"),
                    "exploration_pressure": row.get("exploration_pressure"),
                    "exploration_regime": row.get("exploration_regime"),
                    "cv_window": row.get("cv_window"),
                    "uncertainty_weight": row.get("uncertainty_weight"),
                    "volatility_scaling_factor": row.get("volatility_scaling_factor"),
                    # ZPD
                    "zpd_score": row.get("zpd_score"),
                    "zpd_target": row.get("zpd_target"),
                    # ensemble (JSONB columns — passed through as-is)
                    "ensemble_weights": self._jsonish(row.get("ensemble_weights")),
                    "normalized_weight_vector": self._jsonish(row.get("normalized_weight_vector")),
                    "attribution_scores": self._jsonish(row.get("attribution_scores")),
                    "candidate_arm_scores": self._jsonish(row.get("candidate_arm_scores")),
                }
            )
        return {
            "user_id": user_id,
            "status": "ok" if trajectory else "insufficient_data",
            "authority": "experiment_trajectories",
            "trajectory": trajectory,
            "count": len(trajectory),
            "semantic_version": "1.0",
        }

    def ensemble_weights(self, user_id: str, limit: int = 500) -> Dict[str, Any]:
        rows = self._trajectory_rows(user_id, limit)
        series = []
        for row in rows:
            weights = self._jsonish(row.get("ensemble_weights"))
            normalized = self._jsonish(row.get("normalized_weight_vector"))
            if weights or normalized:
                series.append(
                    {
                        "timestamp": row.get("timestamp"),
                        "interaction_number": row.get("interaction_number"),
                        "concept": row.get("concept"),
                        "ensemble_weights": weights,
                        "normalized_weight_vector": normalized,
                        "attribution_scores": self._jsonish(row.get("attribution_scores")),
                    }
                )
        return {
            "user_id": user_id,
            "status": "ok" if series else "insufficient_data",
            "authority": "experiment_trajectories",
            "series": series,
            "count": len(series),
            "semantic_version": "1.0",
        }

    def adaptation_trajectory(self, user_id: str) -> Dict[str, Any]:
        rows = self._projection_rows(user_id)
        trajectory = []
        for row in rows:
            metrics = self._jsonish(row.get("selection_metrics"))
            trajectory.append(
                {
                    "updated_at": row.get("updated_at"),
                    "concept_id": row.get("concept_id"),
                    "recommended_concept": row.get("recommended_concept"),
                    "adaptation_enriched": bool(metrics.get("adaptation_enriched")),
                    "selection_metrics": metrics,
                    "source_event_id": row.get("source_event_id"),
                }
            )
        return {
            "user_id": user_id,
            "status": "ok" if trajectory else "insufficient_data",
            "authority": "learner_projections",
            "trajectory": trajectory,
            "count": len(trajectory),
            "semantic_version": "1.0",
        }

    def jt_attribution(self, user_id: str, limit: int = 500) -> Dict[str, Any]:
        rows = self._trajectory_rows(user_id, limit)
        if not rows:
            return {
                "user_id": user_id,
                "status": "insufficient_data",
                "reason": "trajectory_missing",
                "authority": "experiment_trajectories",
                "semantic_version": "1.0",
            }

        columns = {
            "delta_m": "jt_delta_m_contribution",
            "transfer": "jt_transfer_contribution",
            "challenge": "jt_challenge_contribution",
            "uncertainty": "jt_uncertainty_contribution",
            "zpd": "jt_zpd_contribution",
        }
        totals: Dict[str, float] = defaultdict(float)
        observations: Dict[str, int] = defaultdict(int)
        for row in rows:
            for component, column in columns.items():
                value = self._safe_float(row.get(column))
                if value is not None:
                    totals[component] += abs(value)
                    observations[component] += 1

        total_mass = sum(totals.values())
        components = {
            component: {
                "absolute_mass": totals.get(component, 0.0),
                "share": (totals.get(component, 0.0) / total_mass) if total_mass else 0.0,
                "observations": observations.get(component, 0),
                "active": totals.get(component, 0.0) > 0.0,
            }
            for component in GOVERNANCE_COMPONENTS
        }
        jt_values = [self._safe_float(row.get("jt_value")) for row in rows]
        jt_values = [value for value in jt_values if value is not None]
        return {
            "user_id": user_id,
            "status": "ok" if total_mass else "insufficient_data",
            "authority": "experiment_trajectories",
            "components": components,
            "summary": {
                "rows": len(rows),
                "jt_mean": sum(jt_values) / len(jt_values) if jt_values else None,
                "dominant_component": max(components, key=lambda key: components[key]["share"])
                if total_mass
                else None,
            },
            "semantic_version": "1.0",
        }

    def discriminability(self, user_id: str, limit: int = 500) -> Dict[str, Any]:
        rows = self._trajectory_rows(user_id, limit)
        if not rows:
            return {
                "user_id": user_id,
                "status": "insufficient_data",
                "reason": "trajectory_missing",
                "authority": "experiment_trajectories",
                "semantic_version": "1.0",
            }

        concepts = [str(row.get("concept")) for row in rows if row.get("concept")]
        policies = [str(row.get("policy")) for row in rows if row.get("policy")]
        arms = [
            str(row.get("selected_arm") or row.get("arm_selected"))
            for row in rows
            if row.get("selected_arm") or row.get("arm_selected")
        ]
        mastery_values = [
            self._safe_float(row.get("mastery_after")) for row in rows
        ]
        mastery_values = [value for value in mastery_values if value is not None]
        return {
            "user_id": user_id,
            "status": "ok" if len(rows) >= 2 else "insufficient_data",
            "authority": "experiment_trajectories",
            "metrics": {
                "row_count": len(rows),
                "concept_diversity": len(set(concepts)),
                "concept_entropy_bits": self._entropy(concepts),
                "policy_diversity": len(set(policies)),
                "arm_entropy_bits": self._entropy(arms),
                "mastery_span": (
                    max(mastery_values) - min(mastery_values)
                    if len(mastery_values) >= 2
                    else None
                ),
            },
            "semantic_version": "1.0",
        }

    def bandit_state(self, user_id: str, limit: int = 500) -> Dict[str, Any]:
        rows = self._trajectory_rows(user_id, limit)
        latest = rows[-1] if rows else {}
        projection = self.governance_state(user_id)
        state = {
            "selected_arm": latest.get("selected_arm") or latest.get("arm_selected"),
            "candidate_arm_scores": self._jsonish(latest.get("candidate_arm_scores")),
            "exploration_pressure": latest.get("exploration_pressure"),
            "exploration_regime": latest.get("exploration_regime"),
            "uncertainty_weight": latest.get("uncertainty_weight"),
            "volatility_scaling_factor": latest.get("volatility_scaling_factor"),
            "latest_recommended_concept": projection.get("recommended_concept"),
            "selection_metrics": projection.get("selection_metrics", {}),
        }
        has_state = any(value not in (None, {}, []) for value in state.values())
        return {
            "user_id": user_id,
            "status": "ok" if has_state else "insufficient_data",
            "authority": "experiment_trajectories + learner_projections",
            "bandit_state": state,
            "semantic_version": "1.0",
        }

    def representation_arms(
        self, user_id: str, concept_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Per-modality Beta(alpha, beta) success beliefs for one learner — the live
        data behind the representation (modality) bandit. Each modality (text / mcq /
        video_question / audio_listen / code) is an arm: alpha = 1 + successes,
        beta = 1 + failures, read from the ``interactions`` table (representation +
        correct recorded on every attempt by ItsRuntimeService.submit_attempt).
        Global across concepts by default; pass ``concept_id`` to scope to the
        per-concept arms the bandit actually samples over."""
        where = "user_id = %s"
        params: tuple = (user_id,)
        if concept_id:
            where += " AND concept_id = %s"
            params = (user_id, concept_id)
        rows = self._read(
            f"""
            SELECT representation,
                   SUM(CASE WHEN correct THEN 1 ELSE 0 END)::int AS c,
                   COUNT(*)::int AS n
            FROM interactions
            WHERE {where}
              AND representation IS NOT NULL AND representation <> 'unknown'
              AND correct IS NOT NULL
            GROUP BY representation
            ORDER BY representation
            """,
            params,
        ) or []

        arms = []
        for r in rows:
            c = int(r.get("c") or 0)
            n = int(r.get("n") or 0)
            alpha = 1.0 + c
            beta = 1.0 + max(0, n - c)
            arms.append(
                {
                    "representation": r.get("representation"),
                    "alpha": alpha,
                    "beta": beta,
                    "successes": c,
                    "attempts": n,
                    "est_success_rate": alpha / (alpha + beta),
                }
            )

        # Concepts where this learner has >1 modality recorded — i.e. where the
        # bandit actually has a choice to make. Lets the UI offer a drill-down.
        multi = self._read(
            """
            SELECT concept_id,
                   COUNT(DISTINCT representation)::int AS n_modalities,
                   COUNT(*)::int AS attempts
            FROM interactions
            WHERE user_id = %s
              AND representation IS NOT NULL AND representation <> 'unknown'
              AND correct IS NOT NULL
            GROUP BY concept_id
            HAVING COUNT(DISTINCT representation) > 1
            ORDER BY attempts DESC
            LIMIT 50
            """,
            (user_id,),
        ) or []
        multi_modal_concepts = [
            {
                "concept_id": m.get("concept_id"),
                "n_modalities": int(m.get("n_modalities") or 0),
                "attempts": int(m.get("attempts") or 0),
            }
            for m in multi
        ]

        return {
            "user_id": user_id,
            "concept_id": concept_id,
            "status": "ok" if arms else "insufficient_data",
            "authority": "interactions (representation + correct per attempt)",
            "vocabulary": ["text", "mcq", "video_question", "audio_listen", "code"],
            "arms": arms,
            "multi_modal_concepts": multi_modal_concepts,
            "semantic_version": "1.0",
        }

    def ranking(self, user_id: str, limit: int = 500) -> Dict[str, Any]:
        bandit = self.bandit_state(user_id, limit)
        scores = self._jsonish(bandit.get("bandit_state", {}).get("candidate_arm_scores"))
        ranking = []
        if isinstance(scores, dict):
            ranking = [
                {"arm": arm, "score": score}
                for arm, score in sorted(scores.items(), key=lambda item: item[1], reverse=True)
            ]
        elif isinstance(scores, list):
            ranking = scores

        if not ranking:
            state = self.governance_state(user_id)
            recommended = state.get("recommended_concept")
            if recommended:
                ranking = [{"arm": recommended, "score": None, "source": "learner_projections"}]

        return {
            "user_id": user_id,
            "status": "ok" if ranking else "insufficient_data",
            "authority": "experiment_trajectories + learner_projections",
            "ranking": ranking,
            "semantic_version": "1.0",
        }

    def trajectory_csv(self, user_id: str, limit: int = 500) -> str:
        rows = self._trajectory_rows(user_id, limit)
        fields = [
            "timestamp",
            "experiment_run_id",
            "interaction_number",
            "user_id",
            "concept",
            "policy",
            "arm_selected",
            "selected_arm",
            "correctness",
            "mastery_before",
            "mastery_after",
            "uncertainty_before",
            "uncertainty_after",
            "jt_value",
            "jt_volatility",
            "stability_index",
            "exploration_pressure",
            "zpd_score",
            "transfer_amount",
            "transfer_efficiency",
            "capability_manifest_fingerprint",
        ]
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field) for field in fields})
        return output.getvalue()
