"""
Trajectory Recorder for Phase 1 Experiment Infrastructure

Records interaction trajectories for analysis and visualization.
Supports Contribution A (System Design), B (Decision-Making), C (Empirical Validation).
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
import numpy as np
import json

logger = logging.getLogger(__name__)

def extract_correctness(interaction_data: Optional[Dict[str, Any]]) -> Optional[bool]:
    """
    Audit fix F-024: normalize correctness from interaction payload.

    Accepts ``correctness`` (bool/int) or ``correct`` (bool/int 0/1).
    Returns None when neither key is present.
    """
    if not interaction_data:
        return None
    if interaction_data.get("correctness") is not None:
        return bool(interaction_data.get("correctness"))
    if interaction_data.get("correct") is not None:
        return bool(interaction_data.get("correct"))
    return None


def convert_numpy_types(value):
    """Convert numpy types to Python types"""
    if isinstance(value, np.ndarray):
        return value.tolist()
    elif isinstance(value, (np.integer, np.floating)):
        return value.item()
    elif isinstance(value, dict):
        return {k: convert_numpy_types(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [convert_numpy_types(v) for v in value]
    return value


class PostgresInteractionStoreAdapter:
    """
    Adapter to make PostgresInteractionStore compatible with TrajectoryRecorder interface

    TrajectoryRecorder expects db_client with insert() and query() methods,
    but PostgresInteractionStore has different method signatures.
    """
    def __init__(self, postgres_store):
        self.postgres_store = postgres_store
        self._ensure_trajectory_table_exists()

    def _ensure_trajectory_table_exists(self):
        """Create a simple trajectory table without foreign key constraints"""
        try:
            sql = """
            CREATE TABLE IF NOT EXISTS experiment_trajectories (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                experiment_run_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                concept TEXT NOT NULL,
                interaction_id TEXT NOT NULL,
                event_id TEXT NOT NULL,
                interaction_number INTEGER NOT NULL,

                -- State before interaction
                mastery_before FLOAT,
                uncertainty_before FLOAT,
                confidence_before FLOAT,
                lyapunov_mastery_before FLOAT,
                bayesian_alpha_before FLOAT,
                bayesian_beta_before FLOAT,
                kalman_mastery_before FLOAT,
                kalman_covariance_before FLOAT,

                -- Interaction data
                correctness BOOLEAN,
                response_time FLOAT,
                difficulty FLOAT,
                policy TEXT,
                arm_selected TEXT,

                -- State after interaction
                mastery_after FLOAT,
                uncertainty_after FLOAT,
                confidence_after FLOAT,
                lyapunov_mastery_after FLOAT,
                bayesian_alpha_after FLOAT,
                bayesian_beta_after FLOAT,
                kalman_mastery_after FLOAT,
                kalman_covariance_after FLOAT,

                -- Governance signals
                jt_value FLOAT,
                jt_volatility FLOAT,
                stability_index FLOAT,
                exploration_pressure FLOAT,

                -- Transfer signals
                transfer_amount FLOAT,
                transfer_efficiency FLOAT,

                -- ZPD signals
                zpd_target FLOAT,
                zpd_alignment_error FLOAT,
                zpd_score FLOAT,

                -- 🔥 PHASE A: Ensemble attribution state (A2)
                ensemble_weights JSONB,
                attribution_scores JSONB,
                softmax_inputs JSONB,
                normalized_weight_vector JSONB,

                -- 🔥 PHASE A: JT decomposition (A3)
                jt_delta_m_contribution FLOAT,
                jt_transfer_contribution FLOAT,
                jt_challenge_contribution FLOAT,
                jt_uncertainty_contribution FLOAT,
                jt_zpd_contribution FLOAT,
                jt_unclamped FLOAT,
                jt_clamped FLOAT,
                -- Tier 2.5 V2 JT dims (nullable unless HCIE_REDESIGN_V2=1)
                jt_baseline_difficulty_contribution FLOAT,
                jt_challenge_event_contribution FLOAT,
                jt_population_prior_contribution FLOAT,
                jt_t_realized_v2_contribution FLOAT,
                jt_v2_active BOOLEAN,
                jt_v2_state_snapshot JSONB,
                jt_v2_challenge_event_fired BOOLEAN,
                jt_v2_challenge_event_reason TEXT,

                -- 🔥 PHASE A: Exploration governance state (A4)
                cv_window FLOAT,
                exploration_regime TEXT,
                uncertainty_weight FLOAT,
                volatility_scaling_factor FLOAT,
                selected_arm TEXT,
                candidate_arm_scores JSONB,

                -- 🔥 PHASE A: Raw estimator states BEFORE aggregation (A1)
                raw_lyapunov_mastery_before FLOAT,
                raw_bayesian_alpha_before FLOAT,
                raw_bayesian_beta_before FLOAT,
                raw_kalman_mastery_before FLOAT,
                raw_kalman_covariance_before FLOAT,
                raw_lyapunov_mastery_after FLOAT,
                raw_bayesian_alpha_after FLOAT,
                raw_bayesian_beta_after FLOAT,
                raw_kalman_mastery_after FLOAT,
                raw_kalman_covariance_after FLOAT,

                -- Metadata
                capability_manifest_fingerprint TEXT,
                processing_time FLOAT,
                timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );

            ALTER TABLE experiment_trajectories
            ADD COLUMN IF NOT EXISTS capability_manifest_fingerprint TEXT;
            ALTER TABLE experiment_trajectories
            ADD COLUMN IF NOT EXISTS synthetic BOOLEAN NOT NULL DEFAULT FALSE;
            ALTER TABLE experiment_trajectories
            ADD COLUMN IF NOT EXISTS jt_baseline_difficulty_contribution FLOAT;
            ALTER TABLE experiment_trajectories
            ADD COLUMN IF NOT EXISTS jt_challenge_event_contribution FLOAT;
            ALTER TABLE experiment_trajectories
            ADD COLUMN IF NOT EXISTS jt_population_prior_contribution FLOAT;
            ALTER TABLE experiment_trajectories
            ADD COLUMN IF NOT EXISTS jt_t_realized_v2_contribution FLOAT;
            ALTER TABLE experiment_trajectories
            ADD COLUMN IF NOT EXISTS jt_v2_active BOOLEAN;
            ALTER TABLE experiment_trajectories
            ADD COLUMN IF NOT EXISTS jt_v2_state_snapshot JSONB;
            ALTER TABLE experiment_trajectories
            ADD COLUMN IF NOT EXISTS jt_v2_challenge_event_fired BOOLEAN;
            ALTER TABLE experiment_trajectories
            ADD COLUMN IF NOT EXISTS jt_v2_challenge_event_reason TEXT;

            CREATE INDEX IF NOT EXISTS idx_experiment_trajectories_run ON experiment_trajectories(experiment_run_id);
            CREATE INDEX IF NOT EXISTS idx_experiment_trajectories_user ON experiment_trajectories(user_id);
            CREATE INDEX IF NOT EXISTS idx_experiment_trajectories_concept ON experiment_trajectories(concept);
            """
            self.postgres_store.execute_write(sql, ())
            logger.debug("Ensured experiment_trajectories table exists")
        except Exception as e:
            logger.warning(f"Failed to create experiment_trajectories table: {e}")

    # Cache: column set per table (computed lazily on first insert).
    _table_columns_cache: Dict[str, set] = {}

    def _get_table_columns(self, table: str) -> set:
        """Return the set of columns that actually exist in `table`.

        Cached per-instance. Used to defensively drop fields the writer wants
        to insert but that the schema doesn't have (e.g. the recorder's
        `lyapunov_mastery_before` vs the table's migration-013 `raw_*` naming).
        """
        if table not in self._table_columns_cache:
            try:
                rows = self.postgres_store.execute_read(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_schema = 'public' AND table_name = %s",
                    (table,),
                )
                self._table_columns_cache[table] = {r["column_name"] for r in (rows or [])}
            except Exception:
                self._table_columns_cache[table] = set()
        return self._table_columns_cache[table]

    def insert(self, requested_table: str, record: Dict[str, Any]) -> bool:
        """
        Insert a record into the specified table

        Args:
            requested_table: ignored — only 'experiment_trajectories' is supported
            record: Dictionary containing record data

        Returns:
            True if successful, False otherwise
        """
        # Use our simplified table instead of trajectory_records
        table = "experiment_trajectories"

        try:
            # Defensively drop keys not present in the actual table schema.
            # The recorder historically wrote columns like `lyapunov_mastery_before`
            # that exist in its internal CREATE TABLE (lines 73-90) but NOT in
            # the canonical migration-007 + migration-013 schema (which uses
            # `raw_lyapunov_mastery_before`). Filtering here lets the same
            # record dict work against both internal-bootstrap and migrated
            # schemas without losing the rest of the row's data.
            valid_columns = self._get_table_columns(table)
            if valid_columns:
                dropped = [k for k in record.keys() if k not in valid_columns]
                if dropped:
                    record = {k: v for k, v in record.items() if k in valid_columns}
                    logger.debug(
                        f"Dropped {len(dropped)} unknown columns for {table}: {dropped[:5]}"
                        + (" ..." if len(dropped) > 5 else "")
                    )

            # SECURITY (identifier safety): values are parameterized, but table/column NAMES are
            # interpolated into the SQL — validate them as plain SQL identifiers so a malformed
            # name can never inject.
            import re as _re
            _ident = _re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
            if not _ident.match(str(table)):
                raise ValueError(f"unsafe table identifier: {table!r}")
            for _c in record.keys():
                if not _ident.match(str(_c)):
                    raise ValueError(f"unsafe column identifier: {_c!r}")

            # Build dynamic INSERT statement based on (filtered) record keys
            columns = list(record.keys())
            placeholders = ", ".join(["%s"] * len(columns))
            columns_str = ", ".join(columns)

            sql = f"""
            INSERT INTO {table} ({columns_str})
            VALUES ({placeholders})
            """

            # Convert record to tuple of values in column order
            # 🔥 FIX: Convert numpy types to native Python types to prevent SQL interpolation errors
            values = tuple(convert_numpy_types(record[col]) for col in columns)

            # Use execute_write method from postgres_store
            self.postgres_store.execute_write(sql, values)
            logger.debug(f"Inserted trajectory record for {record.get('user_id')}/{record.get('concept')}")
            return True

        except Exception as e:
            # 🔥 IMPROVED: Detailed error logging to diagnose SQL issues quickly
            logger.error(f"❌ Failed to insert trajectory record: {e}")
            logger.error(f"   Table: {table}")
            logger.error(f"   Columns: {columns}")
            # Log first few values with their types to identify problematic data
            for i, (col, val) in enumerate(zip(columns[:5], values[:5])):
                logger.error(f"   {col}: {val!r} (type: {type(val).__name__})")
            if len(columns) > 5:
                logger.error(f"   ... ({len(columns) - 5} more columns)")
            return False

    def query(self, table: str, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Query records from the specified table

        Args:
            table: Table name
            filters: Optional filter dictionary

        Returns:
            List of matching records
        """
        try:
            # Build WHERE clause from filters
            where_clause = ""
            params = []
            if filters:
                conditions = [f"{k} = %s" for k in filters.keys()]
                where_clause = "WHERE " + " AND ".join(conditions)
                params = list(filters.values())
            
            sql = f"SELECT * FROM {table} {where_clause} ORDER BY timestamp DESC"
            
            results = self.postgres_store.execute_read(sql, tuple(params))
            return results
            
        except Exception as e:
            logger.error(f"Failed to query trajectory records: {e}")
            return []


class TrajectoryRecorder:
    """
    Records learning trajectories for experiment analysis

    RESPONSIBILITIES:
    - Capture state before/after each interaction
    - Store governance signals (JT, volatility, stability)
    - Track transfer and ZPD signals
    - Enable deterministic replay for experiments
    """

    def __init__(self, db_client):
        """
        Initialize trajectory recorder

        Args:
            db_client: Database client for trajectory storage
                      Can be PostgresInteractionStore or compatible client
        """
        self.db_client = db_client
        # Ensure logger is available at class level
        self.logger = logging.getLogger(__name__)
        # Check if db_client has insert/query methods (TrajectoryRecorder interface)
        # If not, wrap it to work with PostgresInteractionStore
        if not hasattr(db_client, 'insert'):
            self.db_client = PostgresInteractionStoreAdapter(db_client)
    
    def record_interaction(
        self,
        experiment_run_id: str,
        user_id: str,
        concept: str,
        interaction_id: str,
        event_id: str,
        interaction_number: int,
        state_before: Dict[str, Any],
        state_after: Dict[str, Any],
        interaction_data: Optional[Dict[str, Any]] = None,
        governance_signals: Optional[Dict[str, Any]] = None,
        ensemble_attribution: Optional[Dict[str, Any]] = None,
        jt_decomposition: Optional[Dict[str, Any]] = None,
        exploration_governance: Optional[Dict[str, Any]] = None,
        raw_estimator_states: Optional[Dict[str, Any]] = None
    ):
        """
        Record a single interaction trajectory

        Args:
            experiment_run_id: Experiment run identifier
            user_id: User identifier
            concept: Learning concept
            interaction_id: Interaction identifier
            event_id: Event identifier for idempotency
            interaction_number: Sequential interaction number
            state_before: State before interaction
            state_after: State after interaction
            interaction_data: Interaction data (correctness, response_time, etc.)
            governance_signals: Governance signals (JT, volatility, etc.)
            ensemble_attribution: Ensemble attribution state (weights, attribution_scores, etc.) - PHASE A
            jt_decomposition: JT component decomposition (ΔM, transfer, challenge, uncertainty, ZPD) - PHASE A
            exploration_governance: Exploration governance state (CV window, regime, etc.) - PHASE A
            raw_estimator_states: Raw estimator states BEFORE aggregation (lyapunov, bayesian, kalman) - PHASE A
        """
        try:
            # Prepare trajectory record
            record = {
                "experiment_run_id": experiment_run_id,
                "user_id": user_id,
                "concept": concept,
                "interaction_id": interaction_id,
                "event_id": event_id,
                "interaction_number": interaction_number,

                # State before
                "mastery_before": state_before.get("mastery"),
                "uncertainty_before": state_before.get("uncertainty"),
                "confidence_before": state_before.get("confidence"),
                "lyapunov_mastery_before": state_before.get("lyapunov_mastery"),
                "bayesian_alpha_before": state_before.get("bayesian_alpha"),
                "bayesian_beta_before": state_before.get("bayesian_beta"),
                "kalman_mastery_before": state_before.get("kalman_mastery"),
                "kalman_covariance_before": state_before.get("kalman_covariance"),

                # Interaction data (F-024: dual-key binding)
                "correctness": extract_correctness(interaction_data),
                "response_time": interaction_data.get("response_time") if interaction_data else None,
                "difficulty": interaction_data.get("difficulty") if interaction_data else None,
                "policy": interaction_data.get("policy") if interaction_data else None,
                "arm_selected": interaction_data.get("arm_selected") if interaction_data else None,

                # State after
                "mastery_after": state_after.get("mastery"),
                "uncertainty_after": state_after.get("uncertainty"),
                "confidence_after": state_after.get("confidence"),
                "lyapunov_mastery_after": state_after.get("lyapunov_mastery"),
                "bayesian_alpha_after": state_after.get("bayesian_alpha"),
                "bayesian_beta_after": state_after.get("bayesian_beta"),
                "kalman_mastery_after": state_after.get("kalman_mastery"),
                "kalman_covariance_after": state_after.get("kalman_covariance"),

                # Governance signals
                "jt_value": governance_signals.get("jt_value") if governance_signals else None,
                "jt_volatility": governance_signals.get("jt_volatility") if governance_signals else None,
                "stability_index": governance_signals.get("stability_index") if governance_signals else None,
                "exploration_pressure": governance_signals.get("exploration_pressure") if governance_signals else None,

                # Transfer signals
                "transfer_amount": governance_signals.get("transfer_amount") if governance_signals else None,
                "transfer_efficiency": governance_signals.get("transfer_efficiency") if governance_signals else None,

                # ZPD signals
                "zpd_target": governance_signals.get("zpd_target") if governance_signals else None,
                "zpd_alignment_error": governance_signals.get("zpd_alignment_error") if governance_signals else None,
                "zpd_score": governance_signals.get("zpd_score") if governance_signals else None,

                # 🔥 PHASE A: Ensemble attribution state (A2)
                "ensemble_weights": json.dumps(ensemble_attribution.get("ensemble_weights")) if ensemble_attribution and ensemble_attribution.get("ensemble_weights") else None,
                "attribution_scores": json.dumps(ensemble_attribution.get("attribution_scores")) if ensemble_attribution and ensemble_attribution.get("attribution_scores") else None,
                "softmax_inputs": json.dumps(ensemble_attribution.get("softmax_inputs")) if ensemble_attribution and ensemble_attribution.get("softmax_inputs") else None,
                "normalized_weight_vector": json.dumps(ensemble_attribution.get("normalized_weight_vector")) if ensemble_attribution and ensemble_attribution.get("normalized_weight_vector") else None,

                # 🔥 PHASE A: JT decomposition (A3)
                "jt_delta_m_contribution": jt_decomposition.get("jt_delta_m_contribution") if jt_decomposition else None,
                "jt_transfer_contribution": jt_decomposition.get("jt_transfer_contribution") if jt_decomposition else None,
                "jt_challenge_contribution": jt_decomposition.get("jt_challenge_contribution") if jt_decomposition else None,
                "jt_uncertainty_contribution": jt_decomposition.get("jt_uncertainty_contribution") if jt_decomposition else None,
                "jt_zpd_contribution": jt_decomposition.get("jt_zpd_contribution") if jt_decomposition else None,
                "jt_unclamped": jt_decomposition.get("jt_unclamped") if jt_decomposition else None,
                "jt_clamped": jt_decomposition.get("jt_clamped") if jt_decomposition else None,
                "jt_baseline_difficulty_contribution": jt_decomposition.get("jt_baseline_difficulty_contribution") if jt_decomposition else None,
                "jt_challenge_event_contribution": jt_decomposition.get("jt_challenge_event_contribution") if jt_decomposition else None,
                "jt_population_prior_contribution": jt_decomposition.get("jt_population_prior_contribution") if jt_decomposition else None,
                "jt_t_realized_v2_contribution": jt_decomposition.get("jt_t_realized_v2_contribution") if jt_decomposition else None,
                "jt_v2_active": jt_decomposition.get("jt_v2_active") if jt_decomposition else None,
                "jt_v2_state_snapshot": json.dumps(jt_decomposition.get("jt_v2_state_snapshot")) if jt_decomposition and jt_decomposition.get("jt_v2_state_snapshot") else None,
                "jt_v2_challenge_event_fired": jt_decomposition.get("jt_v2_challenge_event_fired") if jt_decomposition else None,
                "jt_v2_challenge_event_reason": jt_decomposition.get("jt_v2_challenge_event_reason") if jt_decomposition else None,

                # 🔥 PHASE A: Exploration governance state (A4)
                "cv_window": exploration_governance.get("cv_window") if exploration_governance else None,
                "exploration_regime": exploration_governance.get("exploration_regime") if exploration_governance else None,
                "uncertainty_weight": exploration_governance.get("uncertainty_weight") if exploration_governance else None,
                "volatility_scaling_factor": exploration_governance.get("volatility_scaling_factor") if exploration_governance else None,
                "selected_arm": exploration_governance.get("selected_arm") if exploration_governance else None,
                "candidate_arm_scores": json.dumps(exploration_governance.get("candidate_arm_scores")) if exploration_governance and exploration_governance.get("candidate_arm_scores") else None,

                # 🔥 PHASE A: Raw estimator states BEFORE aggregation (A1)
                "raw_lyapunov_mastery_before": raw_estimator_states.get("raw_lyapunov_mastery_before") if raw_estimator_states else None,
                "raw_bayesian_alpha_before": raw_estimator_states.get("raw_bayesian_alpha_before") if raw_estimator_states else None,
                "raw_bayesian_beta_before": raw_estimator_states.get("raw_bayesian_beta_before") if raw_estimator_states else None,
                "raw_kalman_mastery_before": raw_estimator_states.get("raw_kalman_mastery_before") if raw_estimator_states else None,
                "raw_kalman_covariance_before": raw_estimator_states.get("raw_kalman_covariance_before") if raw_estimator_states else None,
                "raw_lyapunov_mastery_after": raw_estimator_states.get("raw_lyapunov_mastery_after") if raw_estimator_states else None,
                "raw_bayesian_alpha_after": raw_estimator_states.get("raw_bayesian_alpha_after") if raw_estimator_states else None,
                "raw_bayesian_beta_after": raw_estimator_states.get("raw_bayesian_beta_after") if raw_estimator_states else None,
                "raw_kalman_mastery_after": raw_estimator_states.get("raw_kalman_mastery_after") if raw_estimator_states else None,
                "raw_kalman_covariance_after": raw_estimator_states.get("raw_kalman_covariance_after") if raw_estimator_states else None,

                # Metadata
                "capability_manifest_fingerprint": (
                    governance_signals.get("capability_manifest_fingerprint")
                    if governance_signals
                    else None
                ),
                "synthetic": str(user_id).startswith("synthetic:"),
                "traffic_type": determine_traffic_type(user_id, interaction_data),
                "processing_time": interaction_data.get("processing_time") if interaction_data else None,
                "timestamp": datetime.now()
            }
            
            # Convert numpy types to Python types
            record = convert_numpy_types(record)
            
            # 🔥 AUDIT FIX: Add idempotency check to prevent duplicate records
            # Check if record already exists for this (experiment_run_id, user_id, interaction_id)
            existing = self.db_client.query("experiment_trajectories", {
                "experiment_run_id": experiment_run_id,
                "user_id": user_id,
                "interaction_id": interaction_id
            })
            if existing:
                self.logger.debug(f"⏭️ Skipping duplicate trajectory: {user_id}/{concept} interaction {interaction_number} (already exists)")
                return
            
            # Store in database (use experiment_trajectories table to match PostgresInteractionStoreAdapter)
            self.db_client.insert("experiment_trajectories", record)
            
            self.logger.debug(f"Recorded trajectory: {user_id}/{concept} interaction {interaction_number}")
            
        except Exception as e:
            self.logger.error(f"Failed to record trajectory: {e}")
            raise
    
    def record_trajectory(
        self,
        experiment_run_id: str,
        user_id: str,
        concept: str,
        interaction_id: str,
        event_id: str,
        state_before: Dict[str, Any],
        state_after: Dict[str, Any],
        governance_signals: Optional[Dict[str, Any]] = None,
        interaction_data: Optional[Dict[str, Any]] = None,
    ):
        """
        Record a trajectory (simplified interface for UnifiedLearningBrain)
        
        This is a simplified version of record_interaction that doesn't require interaction_number
        and uses a default interaction_data structure.
        
        Args:
            experiment_run_id: Experiment run identifier
            user_id: User identifier
            concept: Learning concept
            interaction_id: Interaction identifier
            event_id: Event identifier for idempotency
            state_before: State before interaction
            state_after: State after interaction
            governance_signals: Governance signals (JT, policy, etc.)
            interaction_data: Interaction payload (correct/correctness, response_time, etc.)
        """
        try:
            # Generate interaction_number from event_id (simple hash)
            interaction_number = abs(hash(event_id)) % 1000000
            
            # Merge interaction_data with governance policy when provided
            merged_interaction_data: Dict[str, Any] = dict(interaction_data or {})
            if governance_signals:
                if merged_interaction_data.get("policy") is None:
                    merged_interaction_data["policy"] = governance_signals.get("policy")
            
            # Call the full record_interaction method
            self.record_interaction(
                experiment_run_id=experiment_run_id,
                user_id=user_id,
                concept=concept,
                interaction_id=interaction_id,
                event_id=event_id,
                interaction_number=interaction_number,
                state_before=state_before,
                state_after=state_after,
                interaction_data=merged_interaction_data or None,
                governance_signals=governance_signals
            )
            
            self.logger.debug(f"Recorded trajectory (simplified): {user_id}/{concept}")
            
        except Exception as e:
            self.logger.error(f"Failed to record trajectory (simplified): {e}")
            # Don't raise - allow system to continue
    
    def get_user_trajectory(
        self,
        experiment_run_id: str,
        user_id: str,
        concept: Optional[str] = None
    ) -> list:
        """
        Retrieve trajectory for a user
        
        Args:
            experiment_run_id: Experiment run identifier
            user_id: User identifier
            concept: Optional concept filter
            
        Returns:
            List of trajectory records
        """
        try:
            query = {
                "experiment_run_id": experiment_run_id,
                "user_id": user_id
            }
            if concept:
                query["concept"] = concept
            
            records = self.db_client.query("trajectory_records", query)
            # Sort by interaction_number
            records.sort(key=lambda x: x["interaction_number"])
            
            return records
            
        except Exception as e:
            logger.error(f"Failed to retrieve trajectory: {e}")
            raise


def determine_traffic_type(user_id: str, interaction_data: Optional[Dict[str, Any]] = None) -> str:
    """
    🔥 Traffic Classification: Determine traffic type from user_id and context
    
    Classifies traffic into:
    - 'research': Junji/synthetic cohorts for paper validation
    - 'human': Real learner interactions for product validation
    - 'demo': Presentation/demonstration runs
    - 'replay': Historical replay for analysis
    
    Args:
        user_id: User identifier
        interaction_data: Optional interaction context for additional classification
    
    Returns:
        Traffic type string
    """
    # Check user_id patterns
    if str(user_id).startswith("run-"):
        return "research"
    if str(user_id).startswith("synthetic:"):
        return "research"
    if str(user_id).startswith("ex_"):
        return "research"  # Experiment synthetic users
    
    # Check interaction_data for explicit traffic_type
    if interaction_data:
        explicit_type = interaction_data.get("traffic_type")
        if explicit_type:
            return explicit_type
    
    # Default to human for non-synthetic users
    return "human"
