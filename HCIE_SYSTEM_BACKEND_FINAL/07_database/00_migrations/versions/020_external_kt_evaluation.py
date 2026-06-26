"""External KT-dataset evaluation surfaces.

Revision ID: 020_external_kt_evaluation
Revises: 019_ensemble_semantics_signals
Create Date: 2026-05-23 00:00:00.000000

Adds the persistence layer for Contribution C's external-baseline
prediction surface: feeding real KT logs (ASSISTments, EdNet, Junyi,
etc.) through the same Kafka outbox + audit stack as the synthetic
cohorts, and storing baseline-model predictions side-by-side with HCIE
trajectories for honest cold-start AUC comparison.

Three new tables, deliberately *separate* from `experiment_trajectories`
so the math audit, replay audit, and ranking-geometry audit stay
semantically clean:

  - ``external_dataset_registry``
      Declarative inventory of the datasets the harness knows how to
      ingest. Acts as the join key between HCIE's concept_id namespace
      and the dataset's native skill_id namespace.

  - ``external_log_attempts``
      The raw rows pulled from the external dataset (1:1 with the CSV
      row the user supplies), normalized into HCIE's runtime contract
      (user, task, concept, correct, response_time). Persisting these
      gives us an addressable "ground truth" surface for AUC
      computation — the audit can verify "did the runtime see the
      attempt we claimed it saw" per row.

  - ``kt_baseline_predictions``
      Per-attempt predictions from each baseline KT model
      (BKT, DKT, …). Stores ``predicted_correct_prob`` *before* the
      attempt is consumed by the model (i.e. the model's pre-update
      forecast of the upcoming answer). This is the canonical KT-
      evaluation metric.

  - ``kt_prediction_evaluations``
      Cached AUC / accuracy / log-loss summaries per
      (run_id, model_id, cold_start_window). Lets the figure pipeline
      pull stable numbers without recomputing from raw rows.

All four tables are partitioned by `experiment_run_id` so the existing
cohort-runs lineage is preserved end-to-end.
"""

from alembic import op


revision = "020_external_kt_evaluation"
down_revision = "019_ensemble_semantics_signals"


# ---------------------------------------------------------------------------
# Forward
# ---------------------------------------------------------------------------


_CREATE_REGISTRY = """
CREATE TABLE IF NOT EXISTS external_dataset_registry (
    dataset_id      TEXT PRIMARY KEY,
    family          TEXT NOT NULL,
    schema_version  TEXT NOT NULL DEFAULT '1.0',
    description     TEXT,
    concept_prefix  TEXT NOT NULL,
    task_prefix     TEXT NOT NULL,
    citation        TEXT,
    license         TEXT,
    metadata        JSONB,
    registered_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_external_dataset_family
    ON external_dataset_registry (family);
"""


_CREATE_ATTEMPTS = """
CREATE TABLE IF NOT EXISTS external_log_attempts (
    id                       BIGSERIAL PRIMARY KEY,
    experiment_run_id        TEXT NOT NULL,
    dataset_id               TEXT NOT NULL REFERENCES external_dataset_registry(dataset_id),
    -- Identity in the original dataset (kept for traceability/audit)
    source_user_id           TEXT NOT NULL,
    source_skill_id          TEXT NOT NULL,
    source_problem_id        TEXT,
    -- HCIE-side normalized identifiers (after prefix mapping)
    user_id                  TEXT NOT NULL,
    concept_id               TEXT NOT NULL,
    task_id                  TEXT NOT NULL,
    -- Attempt content
    attempt_index            INTEGER NOT NULL,
    correct                  BOOLEAN NOT NULL,
    response_time            DOUBLE PRECISION,
    raw_timestamp            TIMESTAMPTZ,
    -- Audit linkage
    submitted_event_id       TEXT,
    api_status               INTEGER,
    metadata                 JSONB,
    created_at               TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_external_log_attempts_run
    ON external_log_attempts (experiment_run_id);
CREATE INDEX IF NOT EXISTS idx_external_log_attempts_user
    ON external_log_attempts (experiment_run_id, user_id, attempt_index);
CREATE INDEX IF NOT EXISTS idx_external_log_attempts_concept
    ON external_log_attempts (experiment_run_id, concept_id);
"""


_CREATE_PREDICTIONS = """
CREATE TABLE IF NOT EXISTS kt_baseline_predictions (
    id                       BIGSERIAL PRIMARY KEY,
    experiment_run_id        TEXT NOT NULL,
    model_id                 TEXT NOT NULL,
    model_version            TEXT NOT NULL DEFAULT '1.0',
    user_id                  TEXT NOT NULL,
    concept_id               TEXT NOT NULL,
    attempt_index            INTEGER NOT NULL,
    -- Forecast of the upcoming attempt's correctness, BEFORE the attempt
    -- is consumed by the model. This is the standard KT eval contract
    -- (predict P(correct_t+1) given history up to t).
    predicted_correct_prob   DOUBLE PRECISION NOT NULL,
    -- Actual outcome (denormalized for fast AUC queries).
    actual_correct           BOOLEAN NOT NULL,
    -- Internal model state snapshot (small, optional, helps audit).
    model_state              JSONB,
    created_at               TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (experiment_run_id, model_id, user_id, attempt_index)
);

CREATE INDEX IF NOT EXISTS idx_kt_baseline_predictions_run_model
    ON kt_baseline_predictions (experiment_run_id, model_id);
CREATE INDEX IF NOT EXISTS idx_kt_baseline_predictions_concept
    ON kt_baseline_predictions (experiment_run_id, model_id, concept_id);
"""


_CREATE_EVALUATIONS = """
CREATE TABLE IF NOT EXISTS kt_prediction_evaluations (
    id                       BIGSERIAL PRIMARY KEY,
    experiment_run_id        TEXT NOT NULL,
    model_id                 TEXT NOT NULL,
    cold_start_window        INTEGER NOT NULL,
    n_predictions            INTEGER NOT NULL,
    n_users                  INTEGER NOT NULL,
    auc                      DOUBLE PRECISION,
    accuracy                 DOUBLE PRECISION,
    log_loss                 DOUBLE PRECISION,
    brier                    DOUBLE PRECISION,
    per_concept_summary      JSONB,
    metadata                 JSONB,
    created_at               TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (experiment_run_id, model_id, cold_start_window)
);

CREATE INDEX IF NOT EXISTS idx_kt_prediction_evaluations_run
    ON kt_prediction_evaluations (experiment_run_id);
"""


def upgrade() -> None:
    op.execute(_CREATE_REGISTRY)
    op.execute(_CREATE_ATTEMPTS)
    op.execute(_CREATE_PREDICTIONS)
    op.execute(_CREATE_EVALUATIONS)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS kt_prediction_evaluations")
    op.execute("DROP TABLE IF EXISTS kt_baseline_predictions")
    op.execute("DROP TABLE IF EXISTS external_log_attempts")
    op.execute("DROP TABLE IF EXISTS external_dataset_registry")
