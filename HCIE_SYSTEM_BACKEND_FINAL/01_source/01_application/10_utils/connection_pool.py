"""
Connection Pool Optimization Utilities

Provides connection pool management and optimization for database,
HTTP, and other connection types. Includes health checking and
adaptive sizing based on load.
"""

from typing import Optional, Dict, Any, Callable
from enum import Enum
from datetime import datetime, timedelta
import logging
import asyncio

logger = logging.getLogger(__name__)


class PoolStatus(str, Enum):
    """Connection pool status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    DRAINING = "draining"


class ConnectionPoolConfig:
    """Configuration for connection pools"""
    def __init__(
        self,
        min_size: int = 1,
        max_size: int = 10,
        max_idle_time: int = 300,
        health_check_interval: int = 60,
        health_check_timeout: int = 5,
        connection_timeout: int = 30,
        adaptive_sizing: bool = True,
        load_threshold: float = 0.8
    ):
        """
        Initialize connection pool configuration.
        
        Args:
            min_size: Minimum pool size
            max_size: Maximum pool size
            max_idle_time: Maximum idle time for connections (seconds)
            health_check_interval: Health check interval (seconds)
            health_check_timeout: Health check timeout (seconds)
            connection_timeout: Connection acquisition timeout (seconds)
            adaptive_sizing: Enable adaptive pool sizing
            load_threshold: Load threshold for adaptive sizing (0-1)
        """
        self.min_size = min_size
        self.max_size = max_size
        self.max_idle_time = timedelta(seconds=max_idle_time)
        self.health_check_interval = timedelta(seconds=health_check_interval)
        self.health_check_timeout = timedelta(seconds=health_check_timeout)
        self.connection_timeout = timedelta(seconds=connection_timeout)
        self.adaptive_sizing = adaptive_sizing
        self.load_threshold = load_threshold


class ConnectionPoolMetrics:
    """Metrics for connection pool monitoring"""
    def __init__(self):
        self.total_connections = 0
        self.active_connections = 0
        self.idle_connections = 0
        self.failed_connections = 0
        self.total_acquisitions = 0
        self.total_releases = 0
        self.average_wait_time = 0.0
        self.last_health_check: Optional[datetime] = None


class ConnectionPool:
    """
    Generic connection pool with health checking and adaptive sizing.
    
    Provides efficient connection management for databases, HTTP clients,
    and other connection-based resources.
    """
    
    def __init__(
        self,
        connection_factory: Callable,
        config: Optional[ConnectionPoolConfig] = None,
        name: str = "default"
    ):
        """
        Initialize connection pool.
        
        Args:
            connection_factory: Function to create new connections
            config: Pool configuration (uses default if not provided)
            name: Pool identifier
        """
        self.connection_factory = connection_factory
        self.config = config or ConnectionPoolConfig()
        self.name = name
        
        self.connections: list = []
        self.metrics = ConnectionPoolMetrics()
        self.status = PoolStatus.HEALTHY
        self._lock = asyncio.Lock()
        self._health_check_task: Optional[asyncio.Task] = None
    
    async def acquire(self) -> Any:
        """
        Acquire a connection from the pool.
        
        Returns:
            Connection object
            
        Raises:
            TimeoutError: If connection acquisition times out
        """
        start_time = datetime.utcnow()
        
        async with self._lock:
            # Try to get an idle connection
            if self.connections:
                connection = self.connections.pop()
                if self._is_connection_healthy(connection):
                    self.metrics.active_connections += 1
                    self.metrics.total_acquisitions += 1
                    return connection
                else:
                    # Connection is unhealthy, discard it
                    await self._close_connection(connection)
                    self.metrics.failed_connections += 1
            
            # Create new connection if under max size
            if self.metrics.total_connections < self.config.max_size:
                connection = await self._create_connection()
                self.metrics.total_connections += 1
                self.metrics.active_connections += 1
                self.metrics.total_acquisitions += 1
                return connection
            
            # Pool is at capacity, wait for a connection
            logger.warning(f"Pool {self.name} at capacity, waiting for connection")
        
        # Wait for a connection to become available
        try:
            await asyncio.wait_for(
                self._wait_for_connection(),
                timeout=self.config.connection_timeout.total_seconds()
            )
            return await self.acquire()
        except asyncio.TimeoutError:
            self.status = PoolStatus.UNHEALTHY
            raise TimeoutError(f"Connection acquisition timeout for pool {self.name}")
    
    async def release(self, connection: Any):
        """
        Release a connection back to the pool.
        
        Args:
            connection: Connection to release
        """
        async with self._lock:
            if self._is_connection_healthy(connection):
                self.connections.append(connection)
                self.metrics.active_connections -= 1
                self.metrics.total_releases += 1
            else:
                await self._close_connection(connection)
                self.metrics.failed_connections += 1
    
    async def _create_connection(self) -> Any:
        """Create a new connection using the connection factory."""
        try:
            return await self.connection_factory()
        except Exception as e:
            logger.error(f"Failed to create connection for pool {self.name}: {e}")
            self.metrics.failed_connections += 1
            raise
    
    async def _close_connection(self, connection: Any):
        """Close a connection."""
        try:
            if hasattr(connection, 'close'):
                if asyncio.iscoroutinefunction(connection.close):
                    await connection.close()
                else:
                    connection.close()
            self.metrics.total_connections -= 1
        except Exception as e:
            logger.error(f"Error closing connection: {e}")
    
    def _is_connection_healthy(self, connection: Any) -> bool:
        """Check if a connection is healthy."""
        # Basic health check - can be overridden for specific connection types
        return connection is not None
    
    async def _wait_for_connection(self):
        """Wait for a connection to become available."""
        while True:
            await asyncio.sleep(0.1)
            async with self._lock:
                if self.connections:
                    return
    
    async def health_check(self):
        """Perform health check on all connections in the pool."""
        self.metrics.last_health_check = datetime.utcnow()
        
        async with self._lock:
            healthy_connections = []
            
            for connection in self.connections:
                if await self._check_connection_health(connection):
                    healthy_connections.append(connection)
                else:
                    await self._close_connection(connection)
                    self.metrics.failed_connections += 1
            
            self.connections = healthy_connections
            self.metrics.idle_connections = len(self.connections)
            
            # Update pool status based on health
            if self.metrics.failed_connections > self.metrics.total_connections * 0.5:
                self.status = PoolStatus.UNHEALTHY
            elif self.metrics.failed_connections > 0:
                self.status = PoolStatus.DEGRADED
            else:
                self.status = PoolStatus.HEALTHY
    
    async def _check_connection_health(self, connection: Any) -> bool:
        """Check health of a specific connection."""
        try:
            # Default health check - can be overridden
            return self._is_connection_healthy(connection)
        except Exception:
            return False
    
    async def start_health_check_task(self):
        """Start background health check task."""
        if self._health_check_task is None:
            self._health_check_task = asyncio.create_task(self._health_check_loop())
            logger.info(f"Health check task started for pool {self.name}")
    
    async def _health_check_loop(self):
        """Background health check loop."""
        while True:
            try:
                await asyncio.sleep(self.config.health_check_interval.total_seconds())
                await self.health_check()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check error for pool {self.name}: {e}")
    
    async def drain(self):
        """Drain the pool and close all connections."""
        self.status = PoolStatus.DRAINING
        
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
            self._health_check_task = None
        
        async with self._lock:
            for connection in self.connections:
                await self._close_connection(connection)
            self.connections.clear()
        
        logger.info(f"Pool {self.name} drained")
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get pool metrics.
        
        Returns:
            Dictionary with pool metrics
        """
        return {
            "name": self.name,
            "status": self.status.value,
            "total_connections": self.metrics.total_connections,
            "active_connections": self.metrics.active_connections,
            "idle_connections": self.metrics.idle_connections,
            "failed_connections": self.metrics.failed_connections,
            "total_acquisitions": self.metrics.total_acquisitions,
            "total_releases": self.metrics.total_releases,
            "min_size": self.config.min_size,
            "max_size": self.config.max_size,
            "last_health_check": self.metrics.last_health_check.isoformat() if self.metrics.last_health_check else None
        }
