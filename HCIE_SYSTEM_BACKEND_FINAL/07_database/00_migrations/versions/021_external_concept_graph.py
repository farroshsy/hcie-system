"""External concept graph for observational graph-aware transfer measurement.

Revision ID: 021_external_concept_graph
Revises: 020_external_kt_evaluation
Create Date: 2026-05-25 00:00:00.000000

Phase 1: Observational graph storage only.

Stores the concept-level directed graph inferred from each external KT
dataset (ASSISTments, EdNet, Junyi, CSEDM) so that:

  1. Graph topology is queryable per run for audit and future Phase 2 work.
  2. The runtime (JT computation, transfer_realized) is NOT touched yet.
  3. Replay determinism is fully preserved: the table is written once at
     ``external_run`` setup time and never mutated during the attempt loop.

Schema notes:

  - Scoped by ``experiment_run_id`` so the existing cohort-runs lineage
    is preserved end-to-end (matches ``external_log_attempts`` convention).
  - ``source_concept_id`` / ``target_concept_id`` carry the HCIE-namespaced
    concept IDs (e.g. ``assist15.skill_23``), matching the prefix scheme in
    ``external_dataset_registry``.
  - ``transfer_weight`` is the raw edge weight produced by the graph
    construction method (transition probability, co-occurrence count
    normalised, or explicit prerequisite weight). Phase 2 will read this
    column to override ``RealDAGDependencies.get_dependencies()``.
  - ``graph_method`` records the ``GraphMethod`` enum value used so audit
    queries can distinguish QMATRIX vs TRANSITION vs HYBRID edges.
  - The UNIQUE constraint on ``(experiment_run_id, source_concept_id,
    target_concept_id)`` ensures idempotent re-runs write the same graph
    without accumulating duplicate edges.
"""

from alembic import op


revision = "021_external_concept_graph"
down_revision = "020_external_kt_evaluation"


# ---------------------------------------------------------------------------
# Forward
# ---------------------------------------------------------------------------


_CREATE_GRAPH = """
CREATE TABLE IF NOT EXISTS external_concept_graph (
    id                BIGSERIAL PRIMARY KEY,
    experiment_run_id TEXT NOT NULL,
    dataset_id        TEXT NOT NULL REFERENCES external_dataset_registry(dataset_id),
    source_concept_id TEXT NOT NULL,
    target_concept_id TEXT NOT NULL,
    transfer_weight   DOUBLE PRECISION NOT NULL,
    graph_method      TEXT NOT NULL,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (experiment_run_id, source_concept_id, target_concept_id)
);

CREATE INDEX IF NOT EXISTS idx_external_concept_graph_run
    ON external_concept_graph (experiment_run_id);

CREATE INDEX IF NOT EXISTS idx_external_concept_graph_source
    ON external_concept_graph (experiment_run_id, source_concept_id);
"""


def upgrade() -> None:
    op.execute(_CREATE_GRAPH)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS external_concept_graph")
