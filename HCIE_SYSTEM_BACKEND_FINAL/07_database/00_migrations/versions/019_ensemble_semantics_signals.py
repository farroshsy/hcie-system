"""Persist ensemble-semantics math signals as explicit columns.

Revision ID: 019_ensemble_semantics_signals
Revises: 018_normalized_trajectory_signals
Create Date: 2026-05-22 18:00:00.000000

This migration adds first-class evidence columns for the ensemble layer
described in ``ENSEMBLE_SEMANTICS.md``. Per the user's directive, these
columns are kept **semantically distinct from the JT 6D governance
attribution columns** (migration 018):

- JT 6D attribution (`jt_*_contribution`, `jt_attribution`) describes
  governance-component shares of |J_t|.
- Ensemble attribution (`ensemble_weight_*`, `learner_jt_contribution_*`)
  describes per-learner shares of the ensemble mastery synthesis.

Mixing them would poison the math audit. The audit script consumes each
family independently.

Persisted because they are evidence (auditable per-row), not just
derivable: even when a value equals a runtime constant or a doc-claimed
formula, persisting it is what makes that equality verifiable per
interaction.
"""

from alembic import op
import sqlalchemy as sa


revision = "019_ensemble_semantics_signals"
down_revision = "018_normalized_trajectory_signals"


_NEW_COLUMNS = [
    # --- Estimator layer: m_ensemble = Σ w_i × m_i ---
    # Raw synthesis output BEFORE any governance regulation. The
    # ENSEMBLE_SEMANTICS doc distinguishes m_ensemble (estimate) from
    # m_canonical (governance-regulated). Persist both so any future
    # governance-regulation patch becomes auditable per-row.
    ("ensemble_mastery_estimate", "FLOAT"),
    ("canonical_mastery_after", "FLOAT"),

    # --- Learner disagreement (ensemble variance) ---
    # Var([lyapunov, bayesian, kalman]) — the "epistemic uncertainty
    # across the ensemble" from the doc. Already in the brain payload as
    # `ensemble_variance`; we promote it to a stable column.
    ("ensemble_variance_after", "FLOAT"),

    # --- Bayesian posterior reconstruction ---
    # Beta(alpha,beta) mastery = alpha/(alpha+beta); variance and
    # uncertainty from MasteryModel.variance / .uncertainty. These are
    # derivable but persisting them is what makes "is the live Bayesian
    # mastery exactly alpha/(alpha+beta)?" auditable directly in SQL
    # without re-running the formula in the audit harness.
    ("bayesian_mastery_after", "FLOAT"),
    ("bayesian_variance_after", "FLOAT"),

    # --- Kalman filter internals ---
    # Kalman gain K = P_pred / (P_pred + R), R=0.1 hardcoded in the
    # learner. Persist so the audit can verify Kalman update consistency
    # P_after = (1-K) × P_pred.
    ("kalman_gain_after", "FLOAT"),
    ("kalman_R_after", "FLOAT"),  # observation noise actually used

    # --- Lyapunov internals ---
    # raw_lyapunov_mastery_before/after already shipped by migration 013
    # but never populated. Populating them through the writer now makes
    # the V2 lyapunov stability audit runnable.

    # --- Per-learner ensemble weights (explicit, not JSON-only) ---
    # The existing `ensemble_weights JSONB` column ships these as a blob.
    # Promote the three canonical weights to explicit FLOAT columns for
    # SQL aggregation. The JSONB stays for forward-compat keys.
    ("ensemble_weight_lyapunov", "FLOAT"),
    ("ensemble_weight_bayesian", "FLOAT"),
    ("ensemble_weight_kalman", "FLOAT"),

    # --- Per-learner JT contributions (ensemble attribution) ---
    # contribution_i = m_i × |J_t| from JTAttributedEnsemble.record.
    # Persisting per-row instead of relying on a rolling window in Redis
    # lets us audit the EMA basis directly: weights should track these.
    ("learner_jt_contribution_lyapunov", "FLOAT"),
    ("learner_jt_contribution_bayesian", "FLOAT"),
    ("learner_jt_contribution_kalman", "FLOAT"),

    # --- Ensemble weight derivation method ---
    # Doc claims `w_i = softmax(JT_contribution_i / τ)`; live code uses
    # EMA-smoothed L1-normalized contributions. Persisting the method
    # per-row prevents future doc-vs-code drift and lets the audit flag
    # the discrepancy directly.
    ("ensemble_weight_method", "TEXT"),
    ("ensemble_ema_alpha", "FLOAT"),
    ("ensemble_softmax_temperature", "FLOAT"),

    # --- Learning dynamics: raw vs effective mastery delta ---
    # `mastery_delta` (018) is the post-policy delta. Persist the raw
    # direct-learning gain (no policy/bandit multiplier) so the audit
    # can decompose mastery_delta = direct + policy + bandit + transfer.
    ("mastery_delta_direct", "FLOAT"),
    ("transfer_amount_total", "FLOAT"),
    ("transfer_amounts_json", "JSONB"),

    # --- ZPD diagnostics (raw, pre-clamp) ---
    # `zpd_score`, `zpd_target`, `zpd_alignment_error` already shipped.
    # Persist the raw delta signal used inside J_t computation so the
    # ZPD column in audit corresponds to what governance actually saw.
    ("zpd_delta_signal", "FLOAT"),
]


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "experiment_trajectories" not in inspector.get_table_names():
        return

    for column, ctype in _NEW_COLUMNS:
        op.execute(
            f"ALTER TABLE experiment_trajectories "
            f"ADD COLUMN IF NOT EXISTS {column} {ctype}"
        )

    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_experiment_trajectories_ensemble_method "
        "ON experiment_trajectories(ensemble_weight_method)"
    )


def downgrade():
    op.execute(
        "DROP INDEX IF EXISTS idx_experiment_trajectories_ensemble_method"
    )
    for column, _ in reversed(_NEW_COLUMNS):
        op.execute(
            f"ALTER TABLE experiment_trajectories DROP COLUMN IF EXISTS {column}"
        )
