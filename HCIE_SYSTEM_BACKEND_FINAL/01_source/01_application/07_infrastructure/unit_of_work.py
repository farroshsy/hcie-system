"""
Unit of Work Pattern
Ensures true transaction atomicity across multiple operations
"""

import logging
from typing import List, Callable, Any
from contextlib import contextmanager
from datetime import datetime

logger = logging.getLogger(__name__)

class UnitOfWork:
    """
    Unit of Work pattern for transaction management
    Ensures all operations succeed or fail together
    """
    
    def __init__(self, db_store):
        self.db_store = db_store
        self._operations: List[Callable] = []
        self._transaction_active = False
    
    def add_operation(self, operation: Callable):
        """Add operation to transaction"""
        if self._transaction_active:
            raise RuntimeError("Cannot add operations after transaction started")
        self._operations.append(operation)
    
    @contextmanager
    def transaction(self):
        """Execute all operations in a single transaction"""
        if self._transaction_active:
            raise RuntimeError("Nested transactions not supported")
        
        self._transaction_active = True
        try:
            # Begin transaction
            logger.debug("🔄 Starting Unit of Work transaction")
            
            # Execute all operations
            for operation in self._operations:
                operation()
            
            # Commit transaction
            self.db_store.execute_write("COMMIT")
            logger.debug("✅ Unit of Work transaction committed")
            yield
            
        except Exception as e:
            # Rollback transaction
            try:
                self.db_store.execute_write("ROLLBACK")
                logger.error(f"❌ Unit of Work transaction rolled back: {e}")
            except Exception as rollback_error:
                logger.error(f"❌ Failed to rollback transaction: {rollback_error}")
            raise
        finally:
            self._transaction_active = False
            self._operations.clear()
    
    def execute_read(self, query: str, params: tuple = None) -> Any:
        """Execute read operation (outside transaction)"""
        return self.db_store.execute_read(query, params)
    
    def execute_write(self, query: str, params: tuple = None) -> Any:
        """Execute write operation (within current transaction)"""
        if not self._transaction_active:
            # Auto-transaction for single writes
            try:
                result = self.db_store.execute_write(query, params)
                self.db_store.execute_write("COMMIT")
                return result
            except Exception:
                try:
                    self.db_store.execute_write("ROLLBACK")
                except Exception:
                    pass
                raise
        else:
            return self.db_store.execute_write(query, params)

class DatabaseTransaction:
    """
    Database transaction context manager
    Provides explicit transaction boundaries
    """
    
    def __init__(self, db_store):
        self.db_store = db_store
        self._active = False
    
    @contextmanager
    def __enter__(self):
        """Begin transaction"""
        if self._active:
            raise RuntimeError("Nested transactions not supported")
        
        self._active = True
        try:
            self.db_store.execute_write("BEGIN")
            logger.debug("🔄 Database transaction started")
            yield self
        except Exception as e:
            try:
                self.db_store.execute_write("ROLLBACK")
            except Exception:
                pass
            raise
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Commit or rollback transaction"""
        if not self._active:
            return
        
        try:
            if exc_type is None:
                # Success - commit
                self.db_store.execute_write("COMMIT")
                logger.debug("✅ Database transaction committed")
            else:
                # Error - rollback
                self.db_store.execute_write("ROLLBACK")
                logger.debug(f"❌ Database transaction rolled back: {exc_type}")
        except Exception as e:
            logger.error(f"❌ Transaction completion failed: {e}")
        finally:
            self._active = False

@contextmanager
def get_transaction(db_store):
    """Get transaction context manager"""
    transaction = DatabaseTransaction(db_store)
    with transaction:
        yield transaction
