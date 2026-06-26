"""
PostgreSQL Interaction Store
Long-term storage for research data and analytics
"""

import logging
import time
import json
from datetime import datetime
from typing import Dict, Any, Optional, List, Union
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import pool
from contextlib import contextmanager
import queue
import time
from config.env import settings
from core.learning.numpy_converter import serialize_for_storage

logger = logging.getLogger(__name__)


class PostgresInteractionStore:
    """PostgreSQL store for interaction logging and research data"""

    def __init__(self):
        self._dsn = None
        self.connection_pool = None
        # Don't initialize pool in __init__ - do it lazily on first use

    def _initialize_pool(self):
        """Initialize PostgreSQL connection pool"""
        try:
            # Use localhost (127.0.0.1) for local development
            db_url = settings.database_url.replace("localhost", "127.0.0.1")
            self.connection_pool = psycopg2.pool.SimpleConnectionPool(
                1, 10,
                db_url,
                connect_timeout=5
            )
            logger.info("PostgreSQL interaction store initialized")
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL: {e}")
            self.connection_pool = None

    def _ensure_connected(self):
        """Ensure connection pool is initialized (lazy initialization)"""
        if self.connection_pool is None:
            self._initialize_pool()
        return self.connection_pool

    def _get_connection(self):
        """Get a connection from the pool, reinitializing if necessary"""
        pool = self._ensure_connected()
        
        if pool is None:
            return None
            
        try:
            conn = pool.getconn()
            # Verify connection is alive
            with conn.cursor() as cursor:
                cursor.execute('SELECT 1')
            return conn
        except Exception as e:
            logger.error(f"Failed to get connection from pool: {e}")
            # Reset pool to force reconnection on next call
            self.connection_pool = None
            return None

    def _put_connection(self, conn, success: bool = True):
        """Return connection to pool"""
        if conn is None:
            return
        
        pool = self._ensure_connected()
        if pool is None:
            return
        
        if not success:
            # Close bad connection instead of returning to pool
            conn.close()
            return
            
        try:
            pool.putconn(conn)
        except Exception as e:
            logger.error(f"Failed to return connection to pool: {e}")
            conn.close()

    @contextmanager
    def get_connection(self):
        """Public, context-managed pooled connection.

        Repositories consume this as ``with store.get_connection() as conn:``
        (e.g. ``SessionRuntimeRepository`` and ``ConsumerProgressRepository`` in
        ``session_runtime_repository.py``). Yields a connection from the pool and
        returns it on clean exit; on error the connection is discarded (not
        reused) and the exception propagates. Delegates to the existing private
        pool helpers so internal callers are unaffected.

        Fixes the adaptation/learning consumers' "save consumer progress" path,
        which failed with ``'PostgresInteractionStore' object has no attribute
        'get_connection'`` because only the private ``_get_connection`` existed.
        """
        conn = self._get_connection()
        if conn is None:
            raise RuntimeError(
                "PostgresInteractionStore: no database connection available"
            )
        success = True
        try:
            yield conn
        except Exception:
            success = False
            raise
        finally:
            self._put_connection(conn, success=success)

    def save_interaction(self, interaction_data: Dict[str, Any]) -> bool:
        """
        Save interaction to PostgreSQL

        Args:
            interaction_data: Dictionary containing interaction data

        Returns:
            True if saved successfully, False otherwise
        """
        conn = self._get_connection()
        if not conn:
            logger.warning("PostgreSQL not available - interaction not saved")
            return False

        try:
            insert_sql = """
            INSERT INTO interactions (
                user_id, concept_id, representation, correct, reward, 
                response_time, difficulty, task_id, policy_mode, learning_gain, timestamp
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            """

            with conn.cursor() as cursor:
                timestamp = interaction_data.get('timestamp', time.time())
                if isinstance(timestamp, (int, float)):
                    timestamp = datetime.fromtimestamp(timestamp)

                cursor.execute(insert_sql, (
                    interaction_data.get('user_id'),
                    interaction_data.get('concept_id'),
                    interaction_data.get('representation'),
                    interaction_data.get('correct'),
                    interaction_data.get('reward'),
                    interaction_data.get('response_time'),
                    interaction_data.get('difficulty'),
                    interaction_data.get('task_id'),
                    interaction_data.get('policy_mode'),
                    interaction_data.get('learning_gain'),
                    timestamp
                ))
                conn.commit()
                logger.debug(f"Saved interaction for user {interaction_data.get('user_id')}")
                return True

        except Exception as e:
            logger.error(f"Failed to save interaction: {e}")
            conn.rollback()
            return False
        finally:
            self._put_connection(conn, success=True)  # 🔥 FIX: Return connection to pool for reuse

    def get_user_interactions(self, user_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all interactions for a user

        Args:
            user_id: User identifier
            limit: Maximum number of interactions to return

        Returns:
            List of interaction dictionaries
        """
        conn = self._get_connection()
        if not conn:
            return []

        try:
            select_sql = """
            SELECT user_id, concept_id, representation, correct, reward, 
                   response_time, difficulty, task_id, policy_mode, learning_gain, timestamp
            FROM interactions 
            WHERE user_id = %s 
            ORDER BY timestamp DESC 
            LIMIT %s
            """

            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(select_sql, (user_id, limit))
                return [dict(row) for row in cursor.fetchall()]

        except Exception as e:
            logger.error(f"Failed to get user interactions: {e}")
            conn.rollback()
            return []
        finally:
            self._put_connection(conn, success=True)

    def get_all_users_with_interactions(self, limit: int = 100) -> list:
        """
        Get all users who have interactions for state reconstruction
        
        Args:
            limit: Maximum number of users to return
            
        Returns:
            List of user IDs
        """
        conn = self._get_connection()
        if not conn:
            return []
        
        try:
            # 🔥 CRITICAL FIX: Remove DISTINCT to allow ORDER BY
            select_sql = """
            SELECT user_id, MAX(timestamp) as latest_timestamp
            FROM interactions 
            GROUP BY user_id 
            ORDER BY latest_timestamp DESC 
            LIMIT %s
            """
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(select_sql, (limit,))
                results = cursor.fetchall()
            
            # Extract user IDs
            user_ids = [result['user_id'] for result in results if result.get('user_id')]
            
            logger.info(f"Found {len(user_ids)} users with interactions")
            return user_ids
            
        except Exception as e:
            logger.error(f"Failed to get users with interactions: {e}")
            conn.rollback()
            return []
        finally:
            self._put_connection(conn, success=True)

    def get_interactions_for_analysis(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """
        Get interactions for research analysis

        Args:
            limit: Maximum number of interactions to return

        Returns:
            List of interaction dictionaries
        """
        conn = self._get_connection()
        if not conn:
            return []

        try:
            select_sql = """
            SELECT user_id, concept_id, representation, correct, reward, 
                   response_time, difficulty, task_id, policy_mode, learning_gain, timestamp
            FROM interactions 
            ORDER BY timestamp DESC 
            LIMIT %s
            """

            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(select_sql, (limit,))
                return [dict(row) for row in cursor.fetchall()]

        except Exception as e:
            logger.error(f"Failed to get interactions for analysis: {e}")
            conn.rollback()
            return []
        finally:
            self._put_connection(conn, success=True)

    def get_interaction_stats(self) -> Dict[str, Any]:
        """
        Get interaction statistics

        Returns:
            Dictionary with interaction statistics
        """
        conn = self._get_connection()
        if not conn:
            return {}

        try:
            stats_sql = """
            SELECT 
                COUNT(*) as total_interactions,
                AVG(reward) as avg_reward,
                AVG(correct::int) as avg_correct,
                COUNT(DISTINCT user_id) as unique_users,
                COUNT(DISTINCT concept_id) as unique_concepts,
                MIN(timestamp) as first_interaction,
                MAX(timestamp) as last_interaction
            FROM interactions
            """

            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(stats_sql)
                return dict(cursor.fetchone())

        except Exception as e:
            logger.error(f"Failed to get interaction stats: {e}")
            conn.rollback()
            return {}
        finally:
            self._put_connection(conn, success=True)

    def execute_read(self, query: str, params: Optional[tuple] = None, fetch_one: bool = False) -> Optional[Union[Dict[str, Any], List[Dict[str, Any]]]]:
        """Execute a SELECT query and return results"""
        conn = self._get_connection()
        if not conn:
            return [] if not fetch_one else None

        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params or ())
                
                if fetch_one:
                    result = cursor.fetchone()
                    return dict(result) if result else None
                else:
                    return cursor.fetchall()
        except Exception as e:
            logger.error(f"Read query failed: {e}")
            return [] if not fetch_one else None
        finally:
            self._put_connection(conn, success=True)

    def execute_write(self, query: str, params: Optional[tuple] = None, fetch_one: bool = False, timeout_ms: int = 30000) -> Optional[Union[Dict[str, Any], List[Dict[str, Any]]]]:
        """Execute INSERT/UPDATE/DELETE query with explicit commit and timeout"""
        conn = self._get_connection()
        if not conn:
            return [] if not fetch_one else None

        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # 🔥 Set statement timeout to prevent indefinite hangs (default 30s)
                cursor.execute(f"SET statement_timeout = {timeout_ms}")
                cursor.execute(query, params or ())
                
                # Fetch result BEFORE commit for RETURNING clauses
                if fetch_one:
                    try:
                        result = cursor.fetchone()
                        result_dict = dict(result) if result else None
                    except Exception:
                        # Query didn't return rows (e.g., UPDATE without RETURNING)
                        result_dict = None
                else:
                    try:
                        result_list = cursor.fetchall()
                    except Exception:
                        # Query didn't return rows
                        result_list = []
                
                # Explicit commit for write operations
                conn.commit()
                logger.info(f"🟢 DB COMMIT: {query[:50]}...")
                
                if fetch_one:
                    return result_dict
                else:
                    return result_list
        except Exception as e:
            logger.error(f"Write query failed: {e}")
            logger.warning(f"🔴 DB ROLLBACK: {query[:50]}...")
            conn.rollback()
            return [] if not fetch_one else None
        finally:
            self._put_connection(conn, success=True)

    def execute_batch_write(self, batched_writes: List[Dict[str, Any]], timeout_ms: int = 60000) -> bool:
        """
        🔥 BULLETPROOF: Execute multiple writes in a single atomic transaction
        Prevents multiple commits per event and ensures consistency
        """
        conn = self._get_connection()
        if not conn:
            return False

        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # 🔥 Set statement timeout for batch operations (default 60s)
                cursor.execute(f"SET statement_timeout = {timeout_ms}")
                # Start single transaction for all writes
                cursor.execute("BEGIN")
                
                success_count = 0
                for write_op in batched_writes:
                    try:
                        user_id = write_op['user_id']
                        concept = write_op['concept']
                        state_data = write_op['state_data']
                        
                        # Remove timestamp from state_data (Postgres manages it)
                        state_to_save = state_data.copy()
                        if 'updated_at' in state_to_save:
                            del state_to_save['updated_at']
                        
                        sql = """
                            INSERT INTO learning_state (user_id, concept, state_data, updated_at)
                            VALUES (%s, %s, %s, NOW())
                            ON CONFLICT (user_id, concept) DO UPDATE SET
                                state_data = EXCLUDED.state_data,
                                updated_at = NOW()
                            RETURNING updated_at
                        """

                        # Convert NumPy types to native Python types for JSON serialization
                        converted_state = serialize_for_storage(state_to_save, validate=True)

                        cursor.execute(sql, (user_id, concept, json.dumps(converted_state)))
                        success_count += 1
                        
                    except Exception as write_error:
                        logger.error(f"❌ Failed to execute batch write for {write_op.get('user_id', 'unknown')}/{write_op.get('concept', 'unknown')}: {write_error}")
                        raise  # Re-raise to trigger rollback
                
                # Single commit for all writes
                conn.commit()
                logger.info(f"🟢 DB BATCH COMMIT: {success_count}/{len(batched_writes)} writes")
                return True
                
        except Exception as e:
            logger.error(f"❌ Batch write failed: {e}")
            logger.warning(f"🔴 DB BATCH ROLLBACK: {len(batched_writes)} writes")
            try:
                conn.rollback()
            except:
                pass
            return False
        finally:
            self._put_connection(conn, success=True)

    # Backward compatibility (deprecated - REMOVED)
    def execute_query(self, query: str, params: Optional[tuple] = None, fetch_one: bool = False) -> List[Dict[str, Any]]:
        """DEPRECATED: Use execute_read or execute_write instead"""
        raise RuntimeError("execute_query is deprecated - use execute_read or execute_write")

    def _extract_correct_answer(self, task: Dict[str, Any]) -> str:
        """Extract correct answer from K-12 task content"""
        try:
            content = task.get('content', {})
            if isinstance(content, dict):
                return content.get('correct_answer', '')
            return str(content)
        except Exception:
            return ''
    
    def _extract_question_text(self, task: Dict[str, Any]) -> str:
        """Extract question text from K-12 task content"""
        try:
            content = task.get('content', {})
            if isinstance(content, dict):
                return content.get('question', content.get('question_text', ''))
            return str(content)
        except Exception:
            return ''

    def get_task_by_id(self, task_id: str) -> Dict[str, Any]:
        """Fetch a specific task by ID from the canonical tasks table.

        CT fallback retired in Phase 14c; the canonical schema is the unified
        tasks table seeded by 010_seed_k12_tasks (concept_type='k12').
        """
        query = """
            SELECT id, concept_id, difficulty, task_type, content, solution, hints, metadata
            FROM tasks
            WHERE id = %s
        """
        results = self.execute_read(query, (task_id,))
        if not results:
            raise ValueError(f"Task {task_id} not found")
        task = results[0]
        return {
            'id': task['id'],
            'concept_id': task['concept_id'],
            'difficulty': task['difficulty'],
            'task_type': task['task_type'],
            'content': task['content'],
            'solution': task['solution'],
            'hints': task['hints'],
            'metadata': task['metadata'],
            'correct_answer': self._extract_correct_answer(task),
            'question_text': self._extract_question_text(task),
        }

    def get_random_task_for_concept(self, concept_id: str) -> Optional[Dict[str, Any]]:
        """Fetch a random K-12 task for a given concept from the canonical tasks table.

        Per Phase 14c there is no synthetic fallback. Caller observes None.
        """
        query = """
            SELECT id, concept_id, difficulty, task_type, content, solution, hints, metadata
            FROM tasks
            WHERE concept_id = %s AND concept_type = 'k12'
            ORDER BY RANDOM() LIMIT 1
        """
        results = self.execute_read(query, (concept_id,))
        if not results:
            return None
        task = results[0]
        return {
            'id': task['id'],
            'concept_id': task['concept_id'],
            'difficulty': float(task['difficulty']) if task.get('difficulty') is not None else 0.5,
            'task_type': task.get('task_type', 'text'),
            'content': task.get('content', {}),
            'solution': task.get('solution', {}),
            'hints': task.get('hints', []),
            'metadata': task.get('metadata', {}),
            'correct_answer': self._extract_correct_answer(task),
            'question_text': self._extract_question_text(task),
        }

    def get_random_tasks(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Fetch random K-12 tasks from the canonical tasks table."""
        query = """
            SELECT id, concept_id, difficulty, task_type, content, solution, hints, metadata
            FROM tasks
            WHERE concept_type = 'k12'
            ORDER BY RANDOM()
            LIMIT %s
        """
        results = self.execute_read(query, (limit,))
        tasks: List[Dict[str, Any]] = []
        for result in results or []:
            tasks.append({
                'id': result['id'],
                'concept_id': result['concept_id'],
                'difficulty': float(result['difficulty']) if result.get('difficulty') is not None else 0.5,
                'task_type': result.get('task_type', 'text'),
                'content': result.get('content', {}),
                'solution': result.get('solution', {}),
                'hints': result.get('hints', []),
                'metadata': result.get('metadata', {}),
                'correct_answer': self._extract_correct_answer(result),
                'question_text': self._extract_question_text(result),
            })
        logger.info(f"Retrieved {len(tasks)} random K-12 tasks from database")
        return tasks

    def get_concept_dependencies(self) -> List[Dict[str, Any]]:
        """Get concept dependencies from the canonical ``concept_dependencies``
        table.

        The historical query targeted a long-removed schema variant where each
        row stored a ``concept_id`` plus a ``dependent_concepts`` JSON array.
        The live schema is a flat edge table with explicit
        ``source_concept`` / ``target_concept`` columns, so we read it
        directly instead of trying to ``jsonb_array_elements_text`` over
        columns that no longer exist (which produced an
        ``column "concept_id" does not exist`` error on every boot).
        """
        query = """
            SELECT source_concept,
                   target_concept,
                   transfer_weight,
                   dependency_type,
                   confidence_level
            FROM concept_dependencies
            ORDER BY source_concept, target_concept
        """
        
        try:
            results = self.execute_read(query)
            dependencies = []
            for result in results:
                dependencies.append({
                    'source_concept': result['source_concept'],
                    'target_concept': result['target_concept'], 
                    'transfer_weight': float(result['transfer_weight']),
                    'dependency_type': result.get('dependency_type', 'prerequisite'),
                    'confidence_level': float(result['confidence_level'])
                })
            return dependencies
        except Exception as e:
            logger.error(f"❌ Failed to get concept dependencies: {e}")
            return []

    def close(self):
        """Close PostgreSQL connection pool"""
        pool = self._ensure_connected()
        if pool:
            pool.closeall()
            logger.info("PostgreSQL interaction store closed")


# Global instance
_interaction_store: Optional[PostgresInteractionStore] = None


def get_postgres_interaction_store() -> PostgresInteractionStore:
    """Get global PostgreSQL interaction store instance"""
    global _interaction_store
    if _interaction_store is None:
        _interaction_store = PostgresInteractionStore()
    return _interaction_store