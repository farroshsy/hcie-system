"""
Learning Trace Repository - Research and Debugging Data Access
"""

import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from storage.postgres_store.interaction_store import PostgresInteractionStore
from core.learning.numpy_converter import serialize_for_storage

logger = logging.getLogger(__name__)

class LearningTraceRepository:
    """Repository for learning algorithm traces and research data"""
    
    # 🔥 OPTIMIZATION: Cache table existence check to prevent hot-path overhead
    _table_ensured = False
    
    def __init__(self, postgres_store: PostgresInteractionStore):
        self.postgres = postgres_store
    
    def save_trace(self, event_id: str, user_id: str, concept: str, trace_data: Dict[str, Any], experiment_id: str = "production") -> bool:
        """
        Save a learning trace for research/debugging

        🔥 PERSISTENCE GOVERNANCE: Returns True only if trace was actually persisted
        False-positive success logging removed to prevent governance corruption
        """
        try:
            # First ensure table exists (persistence governance)
            self._ensure_traces_table()

            query = """
                INSERT INTO learning_traces (event_id, user_id, concept, experiment_id, trace_data, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (event_id) DO UPDATE SET
                    trace_data = EXCLUDED.trace_data,
                    created_at = EXCLUDED.created_at,
                    experiment_id = EXCLUDED.experiment_id
            """

            # Convert NumPy types to native Python types for JSON serialization
            converted_trace = serialize_for_storage(trace_data, validate=True)

            result = self.postgres.execute_write(
                query,
                (event_id, user_id, concept, experiment_id, json.dumps(converted_trace), datetime.now())
            )

            # 🔥 GOVERNANCE: Only log success after confirming persistence
            if result is not None:
                logger.info(f"✅ Saved learning trace: {event_id} for user {user_id}")
                # Record persistence governance metric
                try:
                    from core.learning.metrics_governance import record_persistence_write
                    record_persistence_write("trace", True)
                except ImportError:
                    pass
                return True
            else:
                logger.warning(f"⚠️ Trace save returned None (persistence uncertain): {event_id}")
                try:
                    from core.learning.metrics_governance import record_persistence_write, record_persistence_violation
                    record_persistence_write("trace", False)
                    record_persistence_violation("trace_save_none")
                except ImportError:
                    pass
                return False

        except Exception as e:
            logger.error(f"❌ Failed to save learning trace {event_id}: {e}")
            try:
                from core.learning.metrics_governance import record_persistence_write
                record_persistence_write("trace", False)
            except ImportError:
                pass
            return False

    def _ensure_traces_table(self):
        """
        🔥 PERSISTENCE GOVERNANCE: Ensure learning_traces table exists
        🔥 OPTIMIZATION: Class-level caching prevents hot-path overhead
        """
        if LearningTraceRepository._table_ensured:
            return
            
        try:
            create_table_query = """
                CREATE TABLE IF NOT EXISTS learning_traces (
                    event_id VARCHAR(255) PRIMARY KEY,
                    user_id VARCHAR(255) NOT NULL,
                    concept VARCHAR(255) NOT NULL,
                    experiment_id VARCHAR(255) DEFAULT 'production',
                    trace_data JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            self.postgres.execute_write(create_table_query)
            LearningTraceRepository._table_ensured = True
            logger.info("✅ learning_traces table ensured (cached)")
        except Exception as e:
            logger.error(f"❌ Failed to ensure learning_traces table: {e}")
            # Don't raise - allow system to continue without traces
    
    def get_trace(self, event_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific learning trace"""
        try:
            query = """
                SELECT event_id, user_id, concept, trace_data, created_at
                FROM learning_traces
                WHERE event_id = %s
            """
            
            result = self.postgres.execute_read(query, (event_id,))
            
            if result and len(result) > 0:
                row = result[0]
                return {
                    "event_id": row[0],
                    "user_id": row[1], 
                    "concept": row[2],
                    "trace_data": json.loads(row[3]) if row[3] else {},
                    "created_at": row[4].isoformat()
                }
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Failed to get learning trace {event_id}: {e}")
            return None
    
    def get_user_traces(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get all traces for a user (for research analysis)"""
        try:
            query = """
                SELECT event_id, user_id, concept, trace_data, created_at
                FROM learning_traces
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT %s
            """
            
            results = self.postgres.execute_read(query, (user_id, limit))
            
            traces = []
            for row in results:
                traces.append({
                    "event_id": row[0],
                    "user_id": row[1],
                    "concept": row[2], 
                    "trace_data": json.loads(row[3]) if row[3] else {},
                    "created_at": row[4].isoformat()
                })
            
            return traces
            
        except Exception as e:
            logger.error(f"❌ Failed to get user traces {user_id}: {e}")
            return []
    
    def get_learning_timeline(self, user_id: str, concept: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get optimized learning timeline using SQL aggregation"""
        try:
            if concept:
                query = """
                    SELECT 
                        event_id,
                        concept,
                        created_at,
                        (trace_data->'state_before'->>'mastery')::float AS mastery_before,
                        (trace_data->'state_after'->>'mastery')::float AS mastery_after,
                        (trace_data->'state_after'->>'confidence')::float AS confidence,
                        (trace_data->'state_after'->>'uncertainty')::float AS uncertainty,
                        trace_data->'input'->>'interaction_type' AS interaction_type,
                        (trace_data->'input'->>'difficulty')::float AS difficulty,
                        (trace_data->'input'->>'response_time')::float AS response_time,
                        (trace_data->'zpd'->>'score')::float AS zpd_score,
                        (trace_data->'transfer'->>'total_transfer')::float AS transfer_amount,
                        (trace_data->'objective'->>'J_t')::float AS J_t
                    FROM learning_traces
                    WHERE user_id = %s AND concept = %s
                    ORDER BY created_at ASC
                    LIMIT %s
                """
                results = self.postgres.execute_read(query, (user_id, concept, limit))
            else:
                query = """
                    SELECT 
                        event_id,
                        concept,
                        created_at,
                        (trace_data->'state_before'->>'mastery')::float AS mastery_before,
                        (trace_data->'state_after'->>'mastery')::float AS mastery_after,
                        (trace_data->'state_after'->>'confidence')::float AS confidence,
                        (trace_data->'state_after'->>'uncertainty')::float AS uncertainty,
                        trace_data->'input'->>'interaction_type' AS interaction_type,
                        (trace_data->'input'->>'difficulty')::float AS difficulty,
                        (trace_data->'input'->>'response_time')::float AS response_time,
                        (trace_data->'zpd'->>'score')::float AS zpd_score,
                        (trace_data->'transfer'->>'total_transfer')::float AS transfer_amount,
                        (trace_data->'objective'->>'J_t')::float AS J_t
                    FROM learning_traces
                    WHERE user_id = %s
                    ORDER BY created_at ASC
                    LIMIT %s
                """
                results = self.postgres.execute_read(query, (user_id, limit))
            
            timeline = []
            for row in results:
                mastery_before = row[3] if row[3] is not None else 0.0  # Already cast to float
                mastery_after = row[4] if row[4] is not None else 0.0  # Already cast to float
                mastery_delta = mastery_after - mastery_before
                
                timeline.append({
                    "event_id": row[0],
                    "concept": row[1],
                    "t": row[2].isoformat() if row[2] else "",
                    "mastery_before": mastery_before,
                    "mastery": mastery_after,
                    "delta": mastery_delta,
                    "confidence": row[5] if row[5] is not None else 0.0,  # Already cast to float
                    "uncertainty": row[6] if row[6] is not None else 0.0,  # Already cast to float
                    "interaction_type": row[7] or "unknown",
                    "difficulty": row[8] if row[8] is not None else 0.5,  # Already cast to float
                    "response_time": row[9] if row[9] is not None else 0.0,  # Already cast to float
                    "zpd_score": row[10] if row[10] is not None else 0.0,  # Already cast to float
                    "transfer_amount": row[11] if row[11] is not None else 0.0,  # Already cast to float
                    "J_t": row[12] if row[12] is not None else 0.0  # Already cast to float
                })
            
            return timeline
            
        except Exception as e:
            logger.error(f"❌ Failed to get learning timeline {user_id}: {e}")
            return []
    
    def get_algorithm_summary(self, user_id: str) -> Dict[str, Any]:
        """Get algorithm performance summary using SQL aggregation"""
        cursor = self.postgres.get_cursor()
        try:
            # Aggregate by concept with SQL
            cursor.execute(
                """
                SELECT 
                    concept,
                    COUNT(*) as total_events,
                    AVG((trace_data->'state_after'->>'mastery')::float) as avg_mastery,
                    AVG((trace_data->'state_after'->>'confidence')::float) as avg_confidence,
                    AVG((trace_data->'transfer'->>'total_transfer')::float) as avg_transfer,
                    AVG((trace_data->'objective'->>'J_t')::float) as avg_J_t,
                    MAX(created_at) as last_event,
                    MIN(created_at) as first_event
                FROM learning_traces
                WHERE user_id = %s
                GROUP BY concept
                ORDER BY total_events DESC
                """,
                (user_id,)
            )
            
            concept_rows = cursor.fetchall()
            
            # Aggregate learner performance using SQL (no Python loops)
            cursor.execute(
                """
                SELECT 
                    COUNT(*) as total_events,
                    AVG((trace_data->'learners'->'lyapunov'->>'mastery')::float) as avg_lyapunov_mastery,
                    AVG((trace_data->'learners'->'bayesian'->>'alpha')::float) as avg_bayesian_alpha,
                    AVG((trace_data->'learners'->'bayesian'->>'beta')::float) as avg_bayesian_beta,
                    AVG(CASE 
                        WHEN (trace_data->'learners'->'bayesian'->>'alpha')::float > 0 
                        AND (trace_data->'learners'->'bayesian'->>'beta')::float > 0
                        THEN (trace_data->'learners'->'bayesian'->>'alpha')::float / 
                             ((trace_data->'learners'->'bayesian'->>'alpha')::float + (trace_data->'learners'->'bayesian'->>'beta')::float)
                        ELSE 0.0
                    END) as avg_bayesian_mastery,
                    AVG((trace_data->'learners'->'kalman'->>'mastery')::float) as avg_kalman_mastery,
                    AVG((trace_data->'learners'->'kalman'->>'covariance')::float) as avg_kalman_covariance
                FROM learning_traces
                WHERE user_id = %s
                AND trace_data->'learners' IS NOT NULL
                """,
                (user_id,)
            )
            
            learner_row = cursor.fetchone()
            
            # Build learner statistics from SQL aggregation
            learner_stats = {
                "lyapunov": {
                    "event_count": learner_row[0] if learner_row[0] else 0,
                    "avg_mastery": learner_row[1] if learner_row[1] is not None else 0.0
                },
                "bayesian": {
                    "event_count": learner_row[0] if learner_row[0] else 0,
                    "avg_alpha": learner_row[2] if learner_row[2] is not None else 0.0,
                    "avg_beta": learner_row[3] if learner_row[3] is not None else 0.0,
                    "avg_mastery": learner_row[4] if learner_row[4] is not None else 0.0
                },
                "kalman": {
                    "event_count": learner_row[0] if learner_row[0] else 0,
                    "avg_mastery": learner_row[5] if learner_row[5] is not None else 0.0,
                    "avg_covariance": learner_row[6] if learner_row[6] is not None else 0.0
                }
            }
            
            # Build summary
            summary = {
                "user_id": user_id,
                "total_events": sum(row[1] for row in concept_rows),
                "concepts": [
                    {
                        "concept": row[0],
                        "total_events": row[1],
                        "avg_mastery": float(row[2]) if row[2] else 0.0,
                        "avg_confidence": float(row[3]) if row[3] else 0.0,
                        "avg_transfer": float(row[4]) if row[4] else 0.0,
                        "avg_J_t": float(row[5]) if row[5] else 0.0,
                        "last_event": row[6].isoformat() if row[6] else None,
                        "first_event": row[7].isoformat() if row[7] else None
                    }
                    for row in concept_rows
                ],
                "algorithm_performance": learner_stats,
                "learning_velocity": 0.0,  # Calculate from timeline if needed
                "transfer_efficiency": 0.0
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"❌ Failed to get algorithm summary {user_id}: {e}")
            return {
                "user_id": user_id,
                "total_events": 0,
                "concepts": [],
                "algorithm_performance": {},
                "learning_velocity": 0.0,
                "transfer_efficiency": 0.0
            }
        finally:
            cursor.close()
    
    def get_concept_traces(self, concept: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get all traces for a concept (for research analysis)"""
        try:
            query = """
                SELECT event_id, user_id, concept, trace_data, created_at
                FROM learning_traces
                WHERE concept = %s
                ORDER BY created_at DESC
                LIMIT %s
            """
            
            results = self.postgres.execute_read(query, (concept, limit))
            
            traces = []
            for row in results:
                traces.append({
                    "event_id": row[0],
                    "user_id": row[1],
                    "concept": row[2],
                    "trace_data": json.loads(row[3]) if row[3] else {},
                    "created_at": row[4].isoformat()
                })
            
            return traces
            
        except Exception as e:
            logger.error(f"❌ Failed to get concept traces {concept}: {e}")
            return []
