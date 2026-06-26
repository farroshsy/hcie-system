#!/usr/bin/env python3
"""
Trajectory Recorder Consumer - Phase 1 Infrastructure

Consumes learning events from Kafka and records state evolution to trajectory_records table
for experiment analysis and deterministic replay validation (Contribution A).
"""

import os
import sys
import logging
import signal
import time
import json
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from infrastructure.experiment.trajectory_recorder import TrajectoryRecorder
from app.infrastructure.kafka.kafka_factory import KafkaFactory, DefaultKafkaProducerFactory
from config.env import settings

logger = logging.getLogger(__name__)

class TrajectoryRecorderConsumer:
    """
    Kafka consumer that records learning trajectories for experiment analysis
    
    RESPONSIBILITIES:
    - Consume CognitionUpdated events from Kafka
    - Record state evolution to trajectory_records table
    - Capture governance signals (JT, volatility, stability)
    - Support deterministic replay validation
    """
    
    def __init__(self):
        """Initialize trajectory recorder consumer"""
        self.consumer = None
        self.recorder = None
        self.running = False
        
        # Get database client (use same pattern as other consumers)
        from storage.postgres_store.interaction_store import PostgresInteractionStore
        self.db_client = PostgresInteractionStore()
        
        # Initialize trajectory recorder
        self.recorder = TrajectoryRecorder(self.db_client)
        
        # Kafka topic to consume.
        # Slice 2 authority rule: CognitionUpdated is emitted on
        # `learning_analytics`; the old `cognition_updated` topic has no V3
        # producer and starves this consumer.
        self.topic = "learning_analytics"
        
        logger.info("🔥 TrajectoryRecorderConsumer initialized")
    
    def start(self):
        """Start consuming events"""
        logger.info(f"🚀 Starting TrajectoryRecorderConsumer on topic: {self.topic}")
        
        # Create Kafka consumer (follow pattern from other consumers)
        kafka_factory = KafkaFactory(settings, producer_factory=DefaultKafkaProducerFactory())
        self.consumer = kafka_factory.create_consumer(
            group_id="trajectory-recorder-consumer"
        )
        
        # Subscribe to topic
        self.consumer.subscribe([self.topic])
        logger.info(f"✅ Kafka consumer subscribed to: {self.topic}")
        
        self.running = True
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)
        
        logger.info("✅ TrajectoryRecorderConsumer started")
        
        # Consume events
        self._consume_loop()
    
    def _consume_loop(self):
        """Main consumption loop"""
        logger.info("🔄 Starting consumption loop")
        
        while self.running:
            try:
                # Poll for messages
                messages = self.consumer.poll(timeout_ms=1000)
                
                if not messages:
                    continue
                
                for topic_partition, records in messages.items():
                    for record in records:
                        try:
                            self._process_message(record)
                        except Exception as e:
                            logger.error(f"❌ Error processing message: {e}")
                            continue
                # auto_commit is enabled in HCIEKafkaConsumer; no manual commit needed
                
            except Exception as e:
                logger.error(f"❌ Error in consumption loop: {e}")
                time.sleep(1)
    
    def _process_message(self, record):
        """
        Process a single Kafka message.

        Bypasses the Phase-1 record_interaction() interface and builds the
        full 78-column experiment_trajectories record directly from the
        CognitionUpdated event's `result` dict, so every Phase-14 governance
        column (jt_clamped, mastery_delta, canonical_mastery_after,
        ensemble_weight_*, learner_jt_contribution_*, transfer_amount_total,
        etc.) is populated on every live interaction.
        """
        try:
            # ── 1. Deserialize ─────────────────────────────────────────────
            raw = record.value
            if isinstance(raw, dict):
                event = raw
            elif isinstance(raw, bytes):
                event = json.loads(raw.decode('utf-8'))
            else:
                event = json.loads(str(raw))

            if event.get("event_type") != "CognitionUpdated":
                logger.debug("⏭️ Skipping non-cognition event: %s", event.get("event_type"))
                return


            # 🔥 #59/#60 TRAJECTORY AUTHORITY RULE — ONE WRITER PER TRAFFIC CLASS.
            #
            # Do NOT skip on the `_cognition` suffix. The CognitionUpdated event
            # (event_id="{base}_cognition") is the ONLY event on the wire that
            # carries the full Phase-14 governance payload (jt_clamped,
            # ensemble_weight_*, learner_jt_contribution_*, etc.). The previous
            # suffix-skip discarded this enriched event and kept only the sparse
            # inline row from unified_brain.process_event (now disabled) — the
            # inverse of what #59 needs.
            #
            # Instead gate on TRAFFIC CLASS:
            #   • Research/synthetic users (run-/synthetic:/ex_ prefixes) are
            #     owned by the dedicated direct-SQL writer in
            #     experiments/cohorts.py (_record_trajectory), which writes the
            #     canonical `run-{run_id}` namespace with full enrichment AND the
            #     correct experiment_run_id. Synthetic CognitionUpdated events
            #     carry NO experiment_run_id (verified: 2999/2999 null), so if we
            #     recorded them here they'd land in a separate `live::{user}`
            #     namespace and DUPLICATE the research rows (this is the origin of
            #     the 20,832 stale `live::` synthetic rows). So: skip research.
            #   • Human/live users (everything else) are owned by THIS consumer —
            #     the enriched CognitionUpdated row is their single authority.
            #
            # Dedup within the human class is handled at step 7 by the
            # idempotency check on (experiment_run_id, user_id, interaction_id);
            # the payload sets interaction_id to the BASE event_id so re-delivered
            # events collapse onto one row without dropping enrichment.
            raw_event_id = event.get("event_id", "")
            _uid = str(event.get("user_id") or "")
            if _uid.startswith("run-") or _uid.startswith("synthetic:") or _uid.startswith("ex_"):
                logger.debug(
                    "⏭️ Skipping research/synthetic event %s (user=%s); "
                    "research trajectories are owned by cohorts._record_trajectory",
                    raw_event_id, _uid,
                )
                return

            # ── 2. Required identity fields ────────────────────────────────
            user_id      = event.get("user_id")
            concept      = event.get("concept_id")
            event_id     = event.get("event_id")
            interaction_id = event.get("interaction_id") or event_id

            if not all([user_id, concept, event_id]):
                logger.warning("⚠️ Skipping event missing required fields: %s", event_id)
                return

            # ── 3. Extract result dict (Phase-14 envelope) ─────────────────
            result              = event.get("result") or {}
            interaction_payload = event.get("interaction") or {}
            governance_snapshot = event.get("governance_snapshot") or {}
            jt_attr             = result.get("jt_attribution") or {}
            ens_weights         = result.get("ensemble_weights") or {}
            transfer_amounts    = result.get("transfer_amounts") or {}

            # ── 4. Derive mastery_before / mastery_after ───────────────────
            mastery_after_val = (
                result.get("canonical_mastery_after")
                or result.get("ensemble_mastery_estimate")
                or result.get("mastery")
            )
            mastery_delta_val = result.get("mastery_delta") or result.get("delta_m")

            mastery_before_val = None
            if mastery_after_val is not None and mastery_delta_val is not None:
                try:
                    mastery_before_val = float(mastery_after_val) - float(mastery_delta_val)
                except (TypeError, ValueError):
                    pass

            # Fall back to Phase-1 state_before/state_after keys if present
            # (cohort replay events still use the old schema)
            state_before = event.get("state_before") or {}
            state_after  = event.get("state_after") or {}
            if mastery_before_val is None:
                mastery_before_val = state_before.get("mastery")
            if mastery_after_val is None:
                mastery_after_val = state_after.get("mastery")

            # ── 5. Correctness (carried in event or interaction payload) ───
            # Use explicit None checks instead of `or` chain — `False` is
            # falsy and `False or x` returns x, which silently drops the
            # "incorrect answer" case (correctness=False would become None).
            def _first_not_none(*vals):
                for v in vals:
                    if v is not None:
                        return v
                return None
            correct_val = _first_not_none(
                event.get("correct"),
                event.get("correctness"),
                result.get("correct"),
                result.get("correctness"),
                interaction_payload.get("correct"),
                interaction_payload.get("correctness"),
            )
            if correct_val is not None:
                correct_val = bool(correct_val)

            # ── 6. Resolve experiment_run_id and interaction_number ───────────
            experiment_run_id = event.get("experiment_run_id") or f"live::{user_id}"

            # interaction_number: use the value from the event if it was
            # explicitly set (batch runs track it themselves), otherwise
            # compute it as COUNT(existing rows) + 1 so that live/human
            # learner trajectories are numbered 1, 2, 3, … instead of all
            # landing on 0.
            raw_interaction_number = event.get("interaction_number")
            if raw_interaction_number is not None:
                interaction_number = int(raw_interaction_number)
            else:
                try:
                    cnt_rows = self.db_client.execute_read(
                        "SELECT COUNT(*) AS n FROM experiment_trajectories "
                        "WHERE user_id = %s AND experiment_run_id = %s",
                        (user_id, experiment_run_id),
                    )
                    interaction_number = int(cnt_rows[0]["n"]) + 1 if cnt_rows else 1
                except Exception as _cnt_err:
                    logger.warning(
                        "Could not compute interaction_number for %s/%s: %s",
                        user_id, experiment_run_id, _cnt_err
                    )
                    interaction_number = 0

            # ── 7. Idempotency check ───────────────────────────────────────
            existing = self.recorder.db_client.query(
                "experiment_trajectories",
                {"experiment_run_id": experiment_run_id, "user_id": user_id, "interaction_id": interaction_id}
            )
            if existing:
                logger.debug("⏭️ Duplicate trajectory skipped: %s/%s", user_id, concept)
                return

            # ── 8. Build full Phase-14 record ──────────────────────────────
            # The defensive column filter in PostgresInteractionStoreAdapter.insert()
            # will silently drop any key that doesn't exist in the live schema,
            # so it's safe to include every field we know about.
            import json as _json

            def _j(v):
                """Serialize to JSON string only if value is a dict/list."""
                if v is None:
                    return None
                if isinstance(v, (dict, list)):
                    return _json.dumps(v)
                return v

            traj_record = {
                # Identity
                "experiment_run_id":    experiment_run_id,
                "user_id":              user_id,
                "concept":              concept,
                "interaction_id":       interaction_id,
                "event_id":             event_id,
                "interaction_number":   interaction_number,

                # ── State BEFORE ──────────────────────────────────────────
                "mastery_before":           mastery_before_val,
                "uncertainty_before":       state_before.get("uncertainty"),
                "confidence_before":        state_before.get("confidence"),

                # ── Interaction ───────────────────────────────────────────
                "correctness":   correct_val,
                "response_time": result.get("response_time") or interaction_payload.get("response_time"),
                "difficulty":    result.get("difficulty")    or interaction_payload.get("difficulty"),
                "policy":        result.get("policy")        or interaction_payload.get("policy"),
                "arm_selected":  result.get("arm_selected")  or result.get("selected_arm"),

                # ── State AFTER ───────────────────────────────────────────
                "mastery_after":           mastery_after_val,
                "uncertainty_after":       result.get("uncertainty") or result.get("ensemble_variance"),
                "confidence_after":        result.get("confidence"),
                "lyapunov_mastery_after":  result.get("lyapunov_mastery"),
                "bayesian_alpha_after":    result.get("bayesian_alpha"),
                "bayesian_beta_after":     result.get("bayesian_beta"),
                "kalman_mastery_after":    result.get("kalman_mastery"),
                "kalman_covariance_after": result.get("kalman_covariance"),

                # ── Mastery delta ─────────────────────────────────────────
                "mastery_delta":        mastery_delta_val,
                "mastery_delta_direct": result.get("mastery_delta_direct"),

                # ── JT composite & decomposition ─────────────────────────
                "jt_value":   result.get("jt_clamped") or result.get("J_value"),
                "jt_clamped": result.get("jt_clamped"),
                "jt_unclamped": result.get("jt_unclamped"),
                "jt_attribution": _j(jt_attr),
                "jt_delta_m_contribution":              result.get("jt_delta_m_contribution")              or jt_attr.get("delta_m"),
                "jt_transfer_contribution":             result.get("jt_transfer_contribution")             or jt_attr.get("transfer_realized"),
                "jt_transfer_prospective_contribution": result.get("jt_transfer_prospective_contribution") or jt_attr.get("transfer_prospective"),
                "jt_challenge_contribution":            result.get("jt_challenge_contribution")            or jt_attr.get("challenge"),
                "jt_uncertainty_contribution":          result.get("jt_uncertainty_contribution")          or jt_attr.get("uncertainty"),
                "jt_zpd_contribution":                  result.get("jt_zpd_contribution")                  or jt_attr.get("zpd"),
                # Tier 2.5 V2 dims. These stay nullable for V1 rows and become
                # first-class replay evidence when HCIE_REDESIGN_V2=1.
                "jt_baseline_difficulty_contribution":  result.get("jt_baseline_difficulty_contribution"),
                "jt_challenge_event_contribution":      result.get("jt_challenge_event_contribution"),
                "jt_population_prior_contribution":     result.get("jt_population_prior_contribution"),
                "jt_t_realized_v2_contribution":        result.get("jt_t_realized_v2_contribution"),
                "jt_v2_active":                         result.get("jt_v2_active"),
                "jt_v2_state_snapshot":                 _j(result.get("jt_v2_state_snapshot")),
                "jt_v2_challenge_event_fired":          result.get("jt_v2_challenge_event_fired"),
                "jt_v2_challenge_event_reason":         result.get("jt_v2_challenge_event_reason"),

                # ── Governance state ──────────────────────────────────────
                "governance_volatility":          result.get("jt_volatility")       or governance_snapshot.get("jt_volatility"),
                "governance_stability_index":     result.get("stability_index")     or governance_snapshot.get("stability_index"),
                "governance_exploration_pressure": result.get("exploration_pressure") or governance_snapshot.get("exploration_pressure"),
                "policy_multiplier":     result.get("policy_multiplier"),
                "effective_learning_rate": result.get("effective_learning_rate"),
                "adaptive_rate":         result.get("adaptive_rate"),

                # ── Ensemble weights ──────────────────────────────────────
                "ensemble_weights":         _j(ens_weights or governance_snapshot.get("ensemble_weights")),
                "weights_snapshot":         _j(result.get("weights_snapshot")),
                "ensemble_weight_kalman":   ens_weights.get("kalman"),
                "ensemble_weight_bayesian": ens_weights.get("bayesian"),
                "ensemble_weight_lyapunov": ens_weights.get("lyapunov"),
                "ensemble_weight_method":   result.get("ensemble_weight_method"),
                "ensemble_ema_alpha":       result.get("ensemble_ema_alpha"),
                "ensemble_softmax_temperature": result.get("ensemble_softmax_temperature"),

                # ── Canonical / estimator posteriors ─────────────────────
                "canonical_mastery_after":  result.get("canonical_mastery_after"),
                "ensemble_mastery_estimate": result.get("ensemble_mastery_estimate"),
                "ensemble_variance_after":  result.get("ensemble_variance_after"),
                "bayesian_mastery_after":   result.get("bayesian_mastery_after"),
                "bayesian_variance_after":  result.get("bayesian_variance_after"),
                "kalman_gain_after":        result.get("kalman_gain_after"),
                "kalman_r_after":           result.get("kalman_R_after"),

                # ── Learner JT contributions per estimator ────────────────
                "learner_jt_contribution_kalman":   result.get("learner_jt_contribution_kalman"),
                "learner_jt_contribution_bayesian": result.get("learner_jt_contribution_bayesian"),
                "learner_jt_contribution_lyapunov": result.get("learner_jt_contribution_lyapunov"),

                # ── Transfer ──────────────────────────────────────────────
                "transfer_amount":       result.get("transfer_realized") or result.get("transfer_amount"),
                "transfer_amount_total": result.get("transfer_amount_total"),
                "transfer_amounts_json": _j(transfer_amounts),

                # ── ZPD ───────────────────────────────────────────────────
                "zpd_target":          result.get("zpd_target"),
                "zpd_alignment_error": result.get("zpd_alignment_error"),
                "zpd_score":           result.get("zpd_score") or result.get("zpd"),
                "zpd_delta_signal":    result.get("zpd_delta_signal") or result.get("zpd_delta_signal_value"),

                # ── Metadata ──────────────────────────────────────────────
                "capability_manifest_fingerprint": (
                    result.get("capability_manifest_fingerprint")
                    or event.get("capability_manifest_fingerprint")
                ),
                "synthetic":     str(user_id).startswith("synthetic:"),
                "traffic_type":  event.get("traffic_type") or "live",
                "timestamp":     datetime.utcnow(),
            }

            self.recorder.db_client.insert("experiment_trajectories", traj_record)
            logger.debug("✅ Recorded full Phase-14 trajectory for %s/%s (run=%s)",
                         user_id, concept, experiment_run_id)

        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON decode error: {e}")
        except Exception as e:
            logger.error(f"❌ Error processing message: {e}", exc_info=True)
    
    def _handle_shutdown(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"🛑 Received shutdown signal: {signum}")
        self.stop()
    
    def stop(self):
        """Stop consuming events"""
        logger.info("🛑 Stopping TrajectoryRecorderConsumer")
        self.running = False
        
        if self.consumer:
            self.consumer.close()
        
        logger.info("✅ TrajectoryRecorderConsumer stopped")


def main():
    """Main entry point"""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger.info("🚀 TrajectoryRecorderConsumer starting...")
    
    # Create and start consumer
    consumer = TrajectoryRecorderConsumer()
    
    try:
        consumer.start()
    except KeyboardInterrupt:
        logger.info("🛑 Keyboard interrupt received")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
    finally:
        consumer.stop()


if __name__ == "__main__":
    main()
