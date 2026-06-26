"""
Recommendation Projection Service (Stateless View)

Projection service for recommendation logic from the materialized projection
store. Slice 2 rule: `learner_projections` is a derived read model fed only
from `learning_analytics`; live reads must not recompute from UnifiedBrain.
"""

import json
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class RecommendationState:
    """Recommendation state projection (stateless view)."""
    user_id: str
    recommended_concept: str
    recommendation_metadata: Dict[str, Any]
    semantic_version: str = "1.0"


class RecommendationProjection:
    """
    Projection service for recommendation logic from UnifiedBrain.
    
    CRITICAL: Stateless view - NO temporal memory ownership.
    CRITICAL: NO cached_recommendation_state - NO authority caching.
    CRITICAL: READ fresh from source every time (ephemeral response cache allowed).
    CRITICAL: NO inference, NO mutation, NO synthesis.
    """

    def __init__(
        self,
        unified_brain=None,
        postgres_store=None,
        cache_store=None,
    ):
        # `unified_brain` remains accepted for compatibility but is not read
        # here. Projection authority is `learner_projections`.
        self.unified_brain = unified_brain
        self.postgres_store = postgres_store
        self.cache_store = cache_store

    def _ensure_projection_table(self) -> None:
        if not self.postgres_store:
            return
        self.postgres_store.execute_write(
            """
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1
                    FROM information_schema.tables
                    WHERE table_name = 'learner_projections'
                )
                AND NOT EXISTS (
                    SELECT 1
                    FROM information_schema.columns
                    WHERE table_name = 'learner_projections'
                      AND column_name = 'concept_id'
                )
                THEN
                    ALTER TABLE learner_projections
                    RENAME TO learner_projections_legacy_slice2;
                END IF;
            END $$;

            CREATE TABLE IF NOT EXISTS learner_projections (
                user_id TEXT NOT NULL,
                concept_id TEXT NOT NULL,
                recommended_concept TEXT NOT NULL,
                projection JSONB NOT NULL DEFAULT '{}'::jsonb,
                ux_semantics JSONB NOT NULL DEFAULT '{}'::jsonb,
                governance JSONB NOT NULL DEFAULT '{}'::jsonb,
                cold_start JSONB NOT NULL DEFAULT '{}'::jsonb,
                selection_metrics JSONB NOT NULL DEFAULT '{}'::jsonb,
                capability_manifest_fingerprint TEXT,
                source_event_id TEXT,
                synthetic BOOLEAN NOT NULL DEFAULT FALSE,
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                PRIMARY KEY (user_id, concept_id)
            );
            ALTER TABLE learner_projections
            ADD COLUMN IF NOT EXISTS synthetic BOOLEAN NOT NULL DEFAULT FALSE;
            CREATE INDEX IF NOT EXISTS idx_learner_projections_user_updated
            ON learner_projections(user_id, updated_at DESC);
            """,
            (),
        )

    def _cache_client(self):
        if not self.cache_store:
            return None
        return getattr(self.cache_store, "redis_client", None) or getattr(self.cache_store, "client", None)

    @staticmethod
    def _cache_key(user_id: str, include_synthetic: bool) -> str:
        scope = "with_synthetic" if include_synthetic else "live_only"
        return f"learner_projection:{scope}:{user_id}:latest"

    def _get_cached_latest(self, user_id: str, *, include_synthetic: bool = False) -> Optional[Dict[str, Any]]:
        client = self._cache_client()
        if not client:
            return None
        try:
            raw = client.get(self._cache_key(user_id, include_synthetic))
            return json.loads(raw) if raw else None
        except Exception:
            return None

    def _set_cached_latest(self, user_id: str, row: Dict[str, Any], *, include_synthetic: bool = False) -> None:
        client = self._cache_client()
        if not client:
            return
        try:
            client.setex(
                self._cache_key(user_id, include_synthetic),
                30,
                json.dumps(row, default=str),
            )
        except Exception:
            return

    def latest_projection_for_user(self, user_id: str, *, include_synthetic: bool = False) -> Optional[Dict[str, Any]]:
        """Read the latest materialized projection row for a user.

        Learner-facing reads default to live human rows only. Synthetic cohort
        projections are opt-in so research/cohort flows can inspect them
        without making them visible to arbitrary live recommendation callers.
        """
        cached = self._get_cached_latest(user_id, include_synthetic=include_synthetic)
        if cached:
            return cached
        if not self.postgres_store:
            return None
        self._ensure_projection_table()
        row = self.postgres_store.execute_read(
            """
            SELECT user_id, concept_id, recommended_concept, projection,
                   ux_semantics, governance, cold_start, selection_metrics,
                   capability_manifest_fingerprint, source_event_id, updated_at
            FROM learner_projections
            WHERE user_id = %s
              AND (%s OR synthetic = FALSE)
            ORDER BY updated_at DESC
            LIMIT 1
            """,
            (user_id, include_synthetic),
            fetch_one=True,
        )
        if row:
            self._set_cached_latest(user_id, row, include_synthetic=include_synthetic)
        return row

    def progress_for_user(self, user_id: str, *, include_synthetic: bool = False) -> Dict[str, float]:
        """Read all projected concept mastery values for a user.

        Reads from `learner_projections` (eventually-consistent projection
        populated by the projection-consumer worker via Kafka).

        When that projection is empty for this user (consumer lag, cold start,
        new learner), falls back to `learning_state` — the synchronously-written
        authoritative mastery store. This makes /learner/progress robust to
        outbox/Kafka pipeline lag.
        """
        if not self.postgres_store:
            return {}
        self._ensure_projection_table()
        rows = self.postgres_store.execute_read(
            """
            SELECT concept_id, projection
            FROM learner_projections
            WHERE user_id = %s
              AND (%s OR synthetic = FALSE)
            ORDER BY updated_at DESC
            """,
            (user_id, include_synthetic),
        )
        progress: Dict[str, float] = {}
        for row in rows or []:
            projection = row.get("projection") or {}
            mastery = projection.get("projected_mastery")
            if mastery is None:
                mastery = projection.get("mastery")
            if mastery is not None:
                progress[row["concept_id"]] = float(mastery) / 100 if float(mastery) > 1 else float(mastery)

        # Fallback: read directly from learning_state when projection is empty.
        # learning_state.state_data->>'mastery' is written synchronously by the
        # ITS runtime, so this is always current. The projection-consumer
        # mirrors these values eventually, but we don't need to wait for it.
        if not progress:
            ls_rows = self.postgres_store.execute_read(
                """
                SELECT concept, state_data
                FROM learning_state
                WHERE user_id = %s
                  AND state_data ? 'mastery'
                """,
                (user_id,),
            )
            for row in ls_rows or []:
                state = row.get("state_data") or {}
                # state_data is JSONB — psycopg already deserializes; sometimes
                # it comes back as a string, so handle both forms.
                if isinstance(state, str):
                    import json as _json
                    try:
                        state = _json.loads(state)
                    except Exception:
                        continue
                mastery = state.get("mastery")
                if mastery is not None:
                    try:
                        progress[row["concept"]] = float(mastery)
                    except (TypeError, ValueError):
                        continue
        return progress

    def project_recommendation(
        self,
        user_id: str,
        mastery_data: Optional[Dict[str, Any]] = None,
        *,
        include_synthetic: bool = False,
    ) -> RecommendationState:
        """
        Project recommendation for a user.
        
        READ fresh from source every time.
        NO caching as authority.
        NO temporal memory ownership.
        """
        row = self.latest_projection_for_user(user_id, include_synthetic=include_synthetic)
        if not row:
            recommendation = {
                "recommended_concept": "unknown",
                "confidence": 0.0,
                "reason": "projection_missing",
                "authority": "learner_projections",
            }
            return RecommendationState(
                user_id=user_id,
                recommended_concept="unknown",
                recommendation_metadata=recommendation,
                semantic_version="1.0",
            )

        projection = row.get("projection") or {}
        selection_metrics = row.get("selection_metrics") or {}
        recommendation = {
            "recommended_concept": row.get("recommended_concept") or row.get("concept_id") or "unknown",
            "concept_id": row.get("concept_id"),
            "projection": projection,
            "ux_semantics": row.get("ux_semantics") or {},
            "governance": row.get("governance") or {},
            "selection_metrics": selection_metrics,
            "capability_manifest_fingerprint": row.get("capability_manifest_fingerprint"),
            "source_event_id": row.get("source_event_id"),
            "updated_at": row.get("updated_at"),
            "authority": "learner_projections",
        }
        
        return RecommendationState(
            user_id=user_id,
            recommended_concept=recommendation.get("recommended_concept", "unknown"),
            recommendation_metadata=recommendation,
            semantic_version="1.0"
        )
