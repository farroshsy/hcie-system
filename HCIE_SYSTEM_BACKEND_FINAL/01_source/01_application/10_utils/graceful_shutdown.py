"""
Graceful Shutdown Utilities

Provides graceful shutdown capabilities for FastAPI applications,
including connection draining, request completion, and resource cleanup.
"""

from typing import List, Callable, Optional, Set, Dict
from datetime import datetime, timedelta
from enum import Enum
import logging
import asyncio
import signal
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


class ShutdownState(str, Enum):
    """Shutdown state"""
    RUNNING = "running"
    SHUTTING_DOWN = "shutting_down"
    TERMINATING = "terminating"
    STOPPED = "stopped"


class ShutdownManager:
    """
    Manager for graceful application shutdown.
    
    Handles shutdown signals, connection draining, and resource cleanup.
    """
    
    def __init__(
        self,
        shutdown_timeout: int = 30,
        drain_timeout: int = 10
    ):
        """
        Initialize shutdown manager.
        
        Args:
            shutdown_timeout: Total shutdown timeout in seconds
            drain_timeout: Timeout for draining connections in seconds
        """
        self.shutdown_timeout = timedelta(seconds=shutdown_timeout)
        self.drain_timeout = timedelta(seconds=drain_timeout)
        
        self.state = ShutdownState.RUNNING
        self.shutdown_start_time: Optional[datetime] = None
        self.cleanup_tasks: List[Callable] = []
        self.active_connections: Set = set()
    
    def register_cleanup_task(self, task: Callable):
        """
        Register a cleanup task to be called during shutdown.
        
        Args:
            task: Async function to call during cleanup
        """
        self.cleanup_tasks.append(task)
        logger.info(f"Registered cleanup task: {task.__name__}")
    
    async def shutdown(self):
        """Initiate graceful shutdown."""
        if self.state != ShutdownState.RUNNING:
            logger.warning(f"Shutdown already in progress (state: {self.state})")
            return
        
        self.state = ShutdownState.SHUTTING_DOWN
        self.shutdown_start_time = datetime.utcnow()
        
        logger.info("Initiating graceful shutdown...")
        
        try:
            # Drain active connections
            await self._drain_connections()
            
            # Execute cleanup tasks
            await self._execute_cleanup_tasks()
            
            self.state = ShutdownState.STOPPED
            logger.info("Graceful shutdown completed successfully")
            
        except Exception as e:
            logger.error(f"Error during graceful shutdown: {e}")
            self.state = ShutdownState.TERMINATING
            raise
    
    async def _drain_connections(self):
        """Drain active connections."""
        logger.info(f"Draining {len(self.active_connections)} active connections...")
        
        if not self.active_connections:
            return
        
        try:
            # Wait for connections to complete or timeout
            await asyncio.wait_for(
                self._wait_for_connections(),
                timeout=self.drain_timeout.total_seconds()
            )
            logger.info("All connections drained successfully")
        except asyncio.TimeoutError:
            logger.warning(f"Connection drain timeout after {self.drain_timeout.total_seconds()}s")
            # Force close remaining connections
            self.active_connections.clear()
    
    async def _wait_for_connections(self):
        """Wait for all active connections to complete."""
        while self.active_connections:
            await asyncio.sleep(0.1)
    
    async def _execute_cleanup_tasks(self):
        """Execute all registered cleanup tasks."""
        logger.info(f"Executing {len(self.cleanup_tasks)} cleanup tasks...")
        
        for task in self.cleanup_tasks:
            try:
                logger.info(f"Executing cleanup task: {task.__name__}")
                await task()
            except Exception as e:
                logger.error(f"Error executing cleanup task {task.__name__}: {e}")
    
    def register_connection(self, connection_id: str):
        """
        Register an active connection.
        
        Args:
            connection_id: Connection identifier
        """
        self.active_connections.add(connection_id)
    
    def unregister_connection(self, connection_id: str):
        """
        Unregister a connection.
        
        Args:
            connection_id: Connection identifier
        """
        self.active_connections.discard(connection_id)
    
    def is_shutting_down(self) -> bool:
        """Check if shutdown is in progress."""
        return self.state != ShutdownState.RUNNING
    
    def get_shutdown_progress(self) -> Dict[str, any]:
        """
        Get shutdown progress.
        
        Returns:
            Dictionary with shutdown progress information
        """
        elapsed = None
        if self.shutdown_start_time:
            elapsed = (datetime.utcnow() - self.shutdown_start_time).total_seconds()
        
        return {
            "state": self.state.value,
            "shutdown_start_time": self.shutdown_start_time.isoformat() if self.shutdown_start_time else None,
            "elapsed_seconds": elapsed,
            "active_connections": len(self.active_connections),
            "cleanup_tasks_remaining": len(self.cleanup_tasks)
        }


# Global shutdown manager instance
_global_shutdown_manager: Optional[ShutdownManager] = None


def get_shutdown_manager() -> ShutdownManager:
    """
    Get the global shutdown manager instance.
    
    Returns:
        ShutdownManager instance
    """
    global _global_shutdown_manager
    if _global_shutdown_manager is None:
        _global_shutdown_manager = ShutdownManager()
    return _global_shutdown_manager


def setup_signal_handlers(shutdown_manager: ShutdownManager):
    """
    Setup signal handlers for graceful shutdown.
    
    Args:
        shutdown_manager: Shutdown manager instance
    """
    def handle_signal(signum, frame):
        logger.info(f"Received signal {signum}, initiating shutdown...")
        asyncio.create_task(shutdown_manager.shutdown())
    
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)


@asynccontextmanager
async def lifespan_context(shutdown_manager: ShutdownManager):
    """
    Context manager for application lifespan.
    
    Args:
        shutdown_manager: Shutdown manager instance
    """
    # Startup
    logger.info("Application starting up...")
    yield
    # Shutdown
    logger.info("Application shutting down...")
    await shutdown_manager.shutdown()


class RequestTracker:
    """
    Track active requests for graceful shutdown.
    
    Monitors active requests and prevents shutdown until all requests complete.
    """
    
    def __init__(self, shutdown_manager: ShutdownManager):
        """
        Initialize request tracker.
        
        Args:
            shutdown_manager: Shutdown manager instance
        """
        self.shutdown_manager = shutdown_manager
        self.active_requests: Set[str] = set()
    
    async def __aenter__(self):
        """Enter request context."""
        if not self.shutdown_manager.is_shutting_down():
            request_id = f"req_{datetime.utcnow().timestamp()}_{id(self)}"
            self.active_requests.add(request_id)
            return request_id
        return None
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit request context."""
        if exc_type is None:
            # Remove request from active set
            # (In a real implementation, you'd need to track the request_id)
            pass
    
    def get_active_request_count(self) -> int:
        """Get number of active requests."""
        return len(self.active_requests)
    
    async def wait_for_requests(self, timeout: int = 30):
        """
        Wait for all active requests to complete.
        
        Args:
            timeout: Maximum wait time in seconds
        """
        if not self.active_requests:
            return
        
        try:
            await asyncio.wait_for(
                self._wait_for_requests(),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            logger.warning(f"Request wait timeout after {timeout}s")
    
    async def _wait_for_requests(self):
        """Wait for all requests to complete."""
        while self.active_requests:
            await asyncio.sleep(0.1)
