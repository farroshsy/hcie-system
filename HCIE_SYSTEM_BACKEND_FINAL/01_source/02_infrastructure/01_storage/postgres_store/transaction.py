"""
PostgreSQL Transaction Context Manager
Safe, automatic transaction handling with proper cleanup
"""

import logging
from typing import Any, Optional
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)

class DatabaseTransaction:
    """Context manager for safe database transactions"""
    
    def __init__(self, postgres_store):
        self.postgres_store = postgres_store
        self.conn = None
        self.cursor = None
        self.committed = False
        self.rolled_back = False
    
    def __enter__(self):
        """Get connection and cursor, start transaction"""
        self.conn = self.postgres_store._get_connection()
        if not self.conn:
            raise RuntimeError("Failed to get database connection")
        
        self.cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        logger.debug("🔐 Transaction started")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Handle transaction commit/rollback and cleanup"""
        if exc_type is not None:
            # Exception occurred - rollback
            if not self.rolled_back:
                try:
                    self.conn.rollback()
                    logger.warning(f"🔴 Transaction rolled back due to: {exc_val}")
                except Exception as e:
                    logger.error(f"Failed to rollback transaction: {e}")
        else:
            # No exception - commit
            if not self.committed:
                try:
                    self.conn.commit()
                    logger.info("🟢 Transaction committed")
                except Exception as e:
                    logger.error(f"Failed to commit transaction: {e}")
                    try:
                        self.conn.rollback()
                        logger.warning("🔴 Transaction rolled back after commit failure")
                    except Exception as rollback_err:
                        logger.error(f"Failed to rollback after commit failure: {rollback_err}")
        
        # Cleanup
        try:
            if self.cursor:
                self.cursor.close()
            if self.conn:
                # Return connection to pool with success status
                success = exc_type is None
                self.postgres_store._put_connection(self.conn, success=success)
        except Exception as e:
            logger.error(f"Error during transaction cleanup: {e}")
        
        # Reset state
        self.conn = None
        self.cursor = None
        self.committed = False
        self.rolled_back = False
    
    def execute(self, query: str, params: Optional[tuple] = None) -> Any:
        """Execute a query within the transaction"""
        if not self.cursor:
            raise RuntimeError("Transaction not active - use 'with transaction:'")
        
        return self.cursor.execute(query, params or ())
    
    def fetchone(self) -> Optional[dict]:
        """Fetch one row and return as dict"""
        if not self.cursor:
            raise RuntimeError("Transaction not active")
        
        result = self.cursor.fetchone()
        return dict(result) if result else None
    
    def fetchall(self) -> list:
        """Fetch all rows and return as list of dicts"""
        if not self.cursor:
            raise RuntimeError("Transaction not active")
        
        return [dict(row) for row in self.cursor.fetchall()]
    
    def commit(self):
        """Manually commit the transaction"""
        if not self.conn:
            raise RuntimeError("Transaction not active")
        
        try:
            self.conn.commit()
            self.committed = True
            logger.info("🟢 Transaction manually committed")
        except Exception as e:
            logger.error(f"Manual commit failed: {e}")
            raise
    
    def rollback(self):
        """Manually rollback the transaction"""
        if not self.conn:
            raise RuntimeError("Transaction not active")
        
        try:
            self.conn.rollback()
            self.rolled_back = True
            logger.warning("🔴 Transaction manually rolled back")
        except Exception as e:
            logger.error(f"Manual rollback failed: {e}")
            raise

# Extend PostgresInteractionStore with transaction support
def get_transaction(postgres_store):
    """Get a transaction context manager for the given postgres store"""
    return DatabaseTransaction(postgres_store)
