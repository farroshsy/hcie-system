"""
D1 - Full Persistence Closure: Session Runtime PostgreSQL Repositories

PostgreSQL repositories for session runtime entities:
- LearningSessionRepository
- TaskAttemptRepository
- AdaptationEventRepository
- LearnerProjectionRepository
- ConsumerProgressRepository

These replace in-memory repositories with durable PostgreSQL storage,
ensuring every canonical semantic transition is durably reconstructable.
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from core.session.models import (
    LearningSession,
    TaskAttempt,
    AdaptationEvent,
    LearnerProjection,
    SessionStatus,
    TaskOutcome,
    AdaptationType
)

logger = logging.getLogger(__name__)


class LearningSessionRepository:
    """
    PostgreSQL repository for learning session persistence.
    
    Replaces in-memory session storage with durable PostgreSQL storage.
    """
    
    def __init__(self, postgres_store):
        self.postgres_store = postgres_store
        self._ensure_table_exists()
    
    def _ensure_table_exists(self):
        """Ensure learning_sessions table exists"""
        try:
            with self.postgres_store.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS learning_sessions (
                            id VARCHAR(255) PRIMARY KEY,
                            user_id VARCHAR(255) NOT NULL,
                            tenant_id VARCHAR(255) NOT NULL,
                            status VARCHAR(50) NOT NULL DEFAULT 'active',
                            started_at TIMESTAMP WITH TIME ZONE NOT NULL,
                            ended_at TIMESTAMP WITH TIME ZONE,
                            current_concept_id VARCHAR(255),
                            target_concepts JSONB NOT NULL DEFAULT '[]',
                            tasks_completed INTEGER DEFAULT 0,
                            tasks_attempted INTEGER DEFAULT 0,
                            correct_count INTEGER DEFAULT 0,
                            current_streak INTEGER DEFAULT 0,
                            best_streak INTEGER DEFAULT 0,
                            research_metadata JSONB NOT NULL DEFAULT '{}',
                            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                        );
                        
                        CREATE INDEX IF NOT EXISTS idx_learning_sessions_user_id ON learning_sessions(user_id);
                        CREATE INDEX IF NOT EXISTS idx_learning_sessions_status ON learning_sessions(status);
                        CREATE INDEX IF NOT EXISTS idx_learning_sessions_started_at ON learning_sessions(started_at);
                    """)
                    conn.commit()
                    logger.info("✅ learning_sessions table ensured")
        except Exception as e:
            logger.error(f"❌ Failed to ensure learning_sessions table: {e}")
    
    def save(self, session: LearningSession) -> bool:
        """Save learning session to PostgreSQL"""
        try:
            with self.postgres_store.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO learning_sessions (
                            id, user_id, tenant_id, status, started_at, ended_at,
                            current_concept_id, target_concepts, tasks_completed,
                            tasks_attempted, correct_count, current_streak, best_streak,
                            research_metadata, updated_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO UPDATE SET
                            status = EXCLUDED.status,
                            ended_at = EXCLUDED.ended_at,
                            current_concept_id = EXCLUDED.current_concept_id,
                            target_concepts = EXCLUDED.target_concepts,
                            tasks_completed = EXCLUDED.tasks_completed,
                            tasks_attempted = EXCLUDED.tasks_attempted,
                            correct_count = EXCLUDED.correct_count,
                            current_streak = EXCLUDED.current_streak,
                            best_streak = EXCLUDED.best_streak,
                            research_metadata = EXCLUDED.research_metadata,
                            updated_at = CURRENT_TIMESTAMP
                    """, (
                        session.id, session.user_id, session.tenant_id,
                        session.status.value, session.started_at, session.ended_at,
                        session.current_concept_id, session.target_concepts,
                        session.tasks_completed, session.tasks_attempted,
                        session.correct_count, session.current_streak,
                        session.best_streak, session.research_metadata,
                        datetime.utcnow()
                    ))
                    conn.commit()
                    return True
        except Exception as e:
            logger.error(f"❌ Failed to save learning session {session.id}: {e}")
            return False
    
    def get(self, session_id: str) -> Optional[LearningSession]:
        """Get learning session by ID"""
        try:
            with self.postgres_store.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "SELECT * FROM learning_sessions WHERE id = %s",
                        (session_id,)
                    )
                    row = cursor.fetchone()
                    if row:
                        return self._row_to_session(row)
        except Exception as e:
            logger.error(f"❌ Failed to get learning session {session_id}: {e}")
        return None
    
    def get_active_by_user(self, user_id: str) -> Optional[LearningSession]:
        """Get active session for a user"""
        try:
            with self.postgres_store.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "SELECT * FROM learning_sessions WHERE user_id = %s AND status = 'active' ORDER BY started_at DESC LIMIT 1",
                        (user_id,)
                    )
                    row = cursor.fetchone()
                    if row:
                        return self._row_to_session(row)
        except Exception as e:
            logger.error(f"❌ Failed to get active session for user {user_id}: {e}")
        return None
    
    def get_by_user(self, user_id: str, limit: int = 10) -> List[LearningSession]:
        """Get recent sessions for a user"""
        try:
            with self.postgres_store.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "SELECT * FROM learning_sessions WHERE user_id = %s ORDER BY started_at DESC LIMIT %s",
                        (user_id, limit)
                    )
                    rows = cursor.fetchall()
                    return [self._row_to_session(row) for row in rows]
        except Exception as e:
            logger.error(f"❌ Failed to get sessions for user {user_id}: {e}")
        return []
    
    def update_status(self, session_id: str, status: SessionStatus) -> bool:
        """Update session status"""
        try:
            ended_at = None
            if status in [SessionStatus.COMPLETED, SessionStatus.ABANDONED]:
                ended_at = datetime.utcnow()
            
            with self.postgres_store.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "UPDATE learning_sessions SET status = %s, ended_at = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
                        (status.value, ended_at, session_id)
                    )
                    conn.commit()
                    return True
        except Exception as e:
            logger.error(f"❌ Failed to update session status for {session_id}: {e}")
            return False
    
    def _row_to_session(self, row) -> LearningSession:
        """Convert database row to LearningSession"""
        return LearningSession(
            id=row[0],
            user_id=row[1],
            tenant_id=row[2],
            status=SessionStatus(row[3]),
            started_at=row[4],
            ended_at=row[5],
            current_concept_id=row[6],
            target_concepts=row[7],
            tasks_completed=row[8],
            tasks_attempted=row[9],
            correct_count=row[10],
            current_streak=row[11],
            best_streak=row[12],
            research_metadata=row[13]
        )


class TaskAttemptRepository:
    """
    PostgreSQL repository for task attempt persistence.
    
    Replaces in-memory attempt storage with durable PostgreSQL storage.
    """
    
    def __init__(self, postgres_store):
        self.postgres_store = postgres_store
        self._ensure_table_exists()
    
    def _ensure_table_exists(self):
        """Ensure task_attempts table exists"""
        try:
            with self.postgres_store.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS task_attempts (
                            id VARCHAR(255) PRIMARY KEY,
                            session_id VARCHAR(255) NOT NULL,
                            user_id VARCHAR(255) NOT NULL,
                            task_id VARCHAR(255) NOT NULL,
                            concept_id VARCHAR(255) NOT NULL,
                            started_at TIMESTAMP WITH TIME ZONE NOT NULL,
                            completed_at TIMESTAMP WITH TIME ZONE,
                            outcome VARCHAR(50),
                            learner_response TEXT,
                            expected_answer TEXT,
                            hints_used INTEGER DEFAULT 0,
                            time_spent_seconds INTEGER DEFAULT 0,
                            cognitive_diagnostics JSONB NOT NULL DEFAULT '{}',
                            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                        );
                        
                        CREATE INDEX IF NOT EXISTS idx_task_attempts_session_id ON task_attempts(session_id);
                        CREATE INDEX IF NOT EXISTS idx_task_attempts_user_id ON task_attempts(user_id);
                        CREATE INDEX IF NOT EXISTS idx_task_attempts_concept_id ON task_attempts(concept_id);
                        CREATE INDEX IF NOT EXISTS idx_task_attempts_started_at ON task_attempts(started_at);
                    """)
                    conn.commit()
                    logger.info("✅ task_attempts table ensured")
        except Exception as e:
            logger.error(f"❌ Failed to ensure task_attempts table: {e}")
    
    def save(self, attempt: TaskAttempt) -> bool:
        """Save task attempt to PostgreSQL"""
        try:
            with self.postgres_store.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO task_attempts (
                            id, session_id, user_id, task_id, concept_id,
                            started_at, completed_at, outcome, learner_response,
                            expected_answer, hints_used, time_spent_seconds,
                            cognitive_diagnostics, updated_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO UPDATE SET
                            completed_at = EXCLUDED.completed_at,
                            outcome = EXCLUDED.outcome,
                            learner_response = EXCLUDED.learner_response,
                            expected_answer = EXCLUDED.expected_answer,
                            hints_used = EXCLUDED.hints_used,
                            time_spent_seconds = EXCLUDED.time_spent_seconds,
                            cognitive_diagnostics = EXCLUDED.cognitive_diagnostics,
                            updated_at = CURRENT_TIMESTAMP
                    """, (
                        attempt.id, attempt.session_id, attempt.user_id,
                        attempt.task_id, attempt.concept_id, attempt.started_at,
                        attempt.completed_at, attempt.outcome.value if attempt.outcome else None,
                        attempt.learner_response, attempt.expected_answer,
                        attempt.hints_used, attempt.time_spent_seconds,
                        attempt.cognitive_diagnostics, datetime.utcnow()
                    ))
                    conn.commit()
                    return True
        except Exception as e:
            logger.error(f"❌ Failed to save task attempt {attempt.id}: {e}")
            return False
    
    def get_by_id(self, attempt_id: str) -> Optional[TaskAttempt]:
        """Get task attempt by ID"""
        try:
            with self.postgres_store.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "SELECT * FROM task_attempts WHERE id = %s",
                        (attempt_id,)
                    )
                    row = cursor.fetchone()
                    if row:
                        return self._row_to_attempt(row)
        except Exception as e:
            logger.error(f"❌ Failed to get task attempt {attempt_id}: {e}")
        return None
    
    def get_by_session(self, session_id: str) -> List[TaskAttempt]:
        """Get all attempts for a session"""
        try:
            with self.postgres_store.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "SELECT * FROM task_attempts WHERE session_id = %s ORDER BY started_at",
                        (session_id,)
                    )
                    rows = cursor.fetchall()
                    return [self._row_to_attempt(row) for row in rows]
        except Exception as e:
            logger.error(f"❌ Failed to get attempts for session {session_id}: {e}")
        return []
    
    def get_by_user(self, user_id: str, limit: int = 100) -> List[TaskAttempt]:
        """Get recent attempts for a user"""
        try:
            with self.postgres_store.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "SELECT * FROM task_attempts WHERE user_id = %s ORDER BY started_at DESC LIMIT %s",
                        (user_id, limit)
                    )
                    rows = cursor.fetchall()
                    return [self._row_to_attempt(row) for row in rows]
        except Exception as e:
            logger.error(f"❌ Failed to get attempts for user {user_id}: {e}")
        return []
    
    def _row_to_attempt(self, row) -> TaskAttempt:
        """Convert database row to TaskAttempt"""
        return TaskAttempt(
            id=row[0],
            session_id=row[1],
            user_id=row[2],
            task_id=row[3],
            concept_id=row[4],
            started_at=row[5],
            completed_at=row[6],
            outcome=TaskOutcome(row[7]) if row[7] else None,
            learner_response=row[8] or "",
            expected_answer=row[9] or "",
            hints_used=row[10] or 0,
            time_spent_seconds=row[11] or 0,
            cognitive_diagnostics=row[12] or {}
        )


class AdaptationEventRepository:
    """
    PostgreSQL repository for adaptation event persistence.
    
    Replaces in-memory event storage with durable PostgreSQL storage.
    """
    
    def __init__(self, postgres_store):
        self.postgres_store = postgres_store
        self._ensure_table_exists()
    
    def _ensure_table_exists(self):
        """Ensure adaptation_events table exists"""
        try:
            with self.postgres_store.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS adaptation_events (
                            id VARCHAR(255) PRIMARY KEY,
                            session_id VARCHAR(255) NOT NULL,
                            user_id VARCHAR(255) NOT NULL,
                            adaptation_type VARCHAR(50) NOT NULL,
                            from_concept_id VARCHAR(255),
                            to_concept_id VARCHAR(255),
                            reason TEXT,
                            created_at TIMESTAMP WITH TIME ZONE NOT NULL,
                            metadata JSONB NOT NULL DEFAULT '{}',
                            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                        );
                        
                        CREATE INDEX IF NOT EXISTS idx_adaptation_events_session_id ON adaptation_events(session_id);
                        CREATE INDEX IF NOT EXISTS idx_adaptation_events_user_id ON adaptation_events(user_id);
                        CREATE INDEX IF NOT EXISTS idx_adaptation_events_type ON adaptation_events(adaptation_type);
                        CREATE INDEX IF NOT EXISTS idx_adaptation_events_created_at ON adaptation_events(created_at);
                    """)
                    conn.commit()
                    logger.info("✅ adaptation_events table ensured")
        except Exception as e:
            logger.error(f"❌ Failed to ensure adaptation_events table: {e}")
    
    def save(self, event: AdaptationEvent) -> bool:
        """Save adaptation event to PostgreSQL"""
        try:
            with self.postgres_store.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO adaptation_events (
                            id, session_id, user_id, adaptation_type,
                            from_concept_id, to_concept_id, reason, metadata
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO NOTHING
                    """, (
                        event.id, event.session_id, event.user_id,
                        event.adaptation_type.value, event.from_concept_id,
                        event.to_concept_id, event.reason, event.metadata
                    ))
                    conn.commit()
                    return True
        except Exception as e:
            logger.error(f"❌ Failed to save adaptation event {event.id}: {e}")
            return False
    
    def get_by_session(self, session_id: str) -> List[AdaptationEvent]:
        """Get all adaptation events for a session"""
        try:
            with self.postgres_store.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "SELECT * FROM adaptation_events WHERE session_id = %s ORDER BY created_at",
                        (session_id,)
                    )
                    rows = cursor.fetchall()
                    return [self._row_to_event(row) for row in rows]
        except Exception as e:
            logger.error(f"❌ Failed to get events for session {session_id}: {e}")
        return []


class LearnerProjectionRepository:
    """
    PostgreSQL repository for learner projection persistence.
    
    Replaces in-memory projection storage with durable PostgreSQL storage.
    """
    
    def __init__(self, postgres_store):
        self.postgres_store = postgres_store
        self._ensure_table_exists()
    
    def _ensure_table_exists(self):
        """Ensure learner_projections table exists"""
        try:
            with self.postgres_store.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS learner_projections (
                            user_id VARCHAR(255) PRIMARY KEY,
                            concept_mastery JSONB NOT NULL DEFAULT '{}',
                            current_streak INTEGER DEFAULT 0,
                            best_streak INTEGER DEFAULT 0,
                            total_attempts INTEGER DEFAULT 0,
                            total_correct INTEGER DEFAULT 0,
                            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                        );
                        
                        CREATE INDEX IF NOT EXISTS idx_learner_projections_updated_at ON learner_projections(updated_at);
                    """)
                    conn.commit()
                    logger.info("✅ learner_projections table ensured")
        except Exception as e:
            logger.error(f"❌ Failed to ensure learner_projections table: {e}")
    
    def save(self, projection: LearnerProjection) -> bool:
        """Save learner projection to PostgreSQL"""
        try:
            with self.postgres_store.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO learner_projections (
                            user_id, concept_mastery, current_streak, best_streak,
                            total_attempts, total_correct, updated_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (user_id) DO UPDATE SET
                            concept_mastery = EXCLUDED.concept_mastery,
                            current_streak = EXCLUDED.current_streak,
                            best_streak = EXCLUDED.best_streak,
                            total_attempts = EXCLUDED.total_attempts,
                            total_correct = EXCLUDED.total_correct,
                            updated_at = CURRENT_TIMESTAMP
                    """, (
                        projection.user_id, projection.concept_mastery,
                        projection.current_streak, projection.best_streak,
                        projection.total_attempts, projection.total_correct,
                        datetime.utcnow()
                    ))
                    conn.commit()
                    return True
        except Exception as e:
            logger.error(f"❌ Failed to save learner projection for user {projection.user_id}: {e}")
            return False
    
    def get(self, user_id: str) -> Optional[LearnerProjection]:
        """Get learner projection by user ID"""
        try:
            with self.postgres_store.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "SELECT * FROM learner_projections WHERE user_id = %s",
                        (user_id,)
                    )
                    row = cursor.fetchone()
                    if row:
                        return self._row_to_projection(row)
        except Exception as e:
            logger.error(f"❌ Failed to get learner projection for user {user_id}: {e}")
        return None


class ConsumerProgressRepository:
    """
    PostgreSQL repository for consumer progress metadata.
    
    Enables consumer restart recovery by persisting offset and metrics.
    """
    
    def __init__(self, postgres_store):
        self.postgres_store = postgres_store
        self._ensure_table_exists()
    
    def _ensure_table_exists(self):
        """Ensure consumer_progress_metadata table exists"""
        try:
            with self.postgres_store.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS consumer_progress_metadata (
                            consumer_id VARCHAR(255) NOT NULL,
                            topic VARCHAR(255) NOT NULL,
                            partition INTEGER NOT NULL,
                            last_processed_offset BIGINT NOT NULL,
                            processed_count INTEGER DEFAULT 0,
                            error_count INTEGER DEFAULT 0,
                            last_health_check TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                            
                            PRIMARY KEY (consumer_id, topic, partition)
                        );
                        
                        CREATE INDEX IF NOT EXISTS idx_consumer_progress_consumer_id ON consumer_progress_metadata(consumer_id);
                        CREATE INDEX IF NOT EXISTS idx_consumer_progress_topic ON consumer_progress_metadata(topic);
                    """)
                    conn.commit()
                    logger.info("✅ consumer_progress_metadata table ensured")
        except Exception as e:
            logger.error(f"❌ Failed to ensure consumer_progress_metadata table: {e}")
    
    def save_progress(self, consumer_id: str, topic: str, partition: int,
                     offset: int, processed_count: int, error_count: int) -> bool:
        """Save consumer progress metadata"""
        try:
            with self.postgres_store.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO consumer_progress_metadata (
                            consumer_id, topic, partition, last_processed_offset,
                            processed_count, error_count, last_health_check, updated_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (consumer_id, topic, partition) DO UPDATE SET
                            last_processed_offset = EXCLUDED.last_processed_offset,
                            processed_count = EXCLUDED.processed_count,
                            error_count = EXCLUDED.error_count,
                            last_health_check = CURRENT_TIMESTAMP,
                            updated_at = CURRENT_TIMESTAMP
                    """, (
                        consumer_id, topic, partition, offset,
                        processed_count, error_count, datetime.utcnow(), datetime.utcnow()
                    ))
                    conn.commit()
                    return True
        except Exception as e:
            logger.error(f"❌ Failed to save consumer progress for {consumer_id}: {e}")
            return False
    
    def get_progress(self, consumer_id: str, topic: str, partition: int) -> Optional[Dict[str, Any]]:
        """Get consumer progress metadata"""
        try:
            with self.postgres_store.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "SELECT * FROM consumer_progress_metadata WHERE consumer_id = %s AND topic = %s AND partition = %s",
                        (consumer_id, topic, partition)
                    )
                    row = cursor.fetchone()
                    if row:
                        return {
                            'consumer_id': row[0],
                            'topic': row[1],
                            'partition': row[2],
                            'last_processed_offset': row[3],
                            'processed_count': row[4],
                            'error_count': row[5],
                            'last_health_check': row[6]
                        }
        except Exception as e:
            logger.error(f"❌ Failed to get consumer progress for {consumer_id}: {e}")
        return None
