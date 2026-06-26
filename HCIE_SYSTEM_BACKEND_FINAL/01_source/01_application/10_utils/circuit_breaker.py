"""
Circuit Breaker Pattern Implementation

Provides circuit breaker functionality to prevent cascading failures
and improve system resilience when external services are unavailable.
"""

from typing import Callable, Optional, Any, Dict
from enum import Enum
from datetime import datetime, timedelta
import logging
import asyncio

logger = logging.getLogger(__name__)


class CircuitState(str, Enum):
    """Circuit breaker states"""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Circuit is open, blocking calls
    HALF_OPEN = "half_open"  # Testing if service has recovered


class CircuitBreakerError(Exception):
    """Raised when circuit breaker is open"""
    pass


class CircuitBreaker:
    """
    Circuit breaker implementation for resilience.
    
    Prevents cascading failures by opening the circuit when failure
    threshold is reached, and attempting recovery after a cooldown period.
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: Exception = Exception,
        name: str = "default"
    ):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before attempting recovery
            expected_exception: Exception type to track as failures
            name: Circuit breaker identifier
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = timedelta(seconds=recovery_timeout)
        self.expected_exception = expected_exception
        self.name = name
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.last_success_time: Optional[datetime] = None
        
        self.success_count = 0
        self.total_calls = 0
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute a function with circuit breaker protection.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerError: If circuit is open
            Exception: If function fails and circuit is not open
        """
        self.total_calls += 1
        
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                logger.info(f"Circuit breaker {self.name} transitioning to HALF_OPEN")
            else:
                logger.warning(f"Circuit breaker {self.name} is OPEN, blocking call")
                raise CircuitBreakerError(f"Circuit breaker {self.name} is open")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise e
        except Exception as e:
            # Unexpected exceptions don't trigger circuit breaker
            logger.error(f"Unexpected exception in circuit breaker {self.name}: {e}")
            raise e
    
    async def call_async(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute an async function with circuit breaker protection.
        
        Args:
            func: Async function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerError: If circuit is open
            Exception: If function fails and circuit is not open
        """
        self.total_calls += 1
        
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                logger.info(f"Circuit breaker {self.name} transitioning to HALF_OPEN")
            else:
                logger.warning(f"Circuit breaker {self.name} is OPEN, blocking call")
                raise CircuitBreakerError(f"Circuit breaker {self.name} is open")
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise e
        except Exception as e:
            # Unexpected exceptions don't trigger circuit breaker
            logger.error(f"Unexpected exception in circuit breaker {self.name}: {e}")
            raise e
    
    def _on_success(self):
        """Handle successful function execution."""
        self.success_count += 1
        self.last_success_time = datetime.utcnow()
        
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            logger.info(f"Circuit breaker {self.name} reset to CLOSED after successful call")
    
    def _on_failure(self):
        """Handle function execution failure."""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        
        logger.warning(f"Circuit breaker {self.name} failure count: {self.failure_count}/{self.failure_threshold}")
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.error(f"Circuit breaker {self.name} opened due to {self.failure_count} failures")
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit should attempt reset from OPEN to HALF_OPEN."""
        if self.last_failure_time is None:
            return True
        
        return datetime.utcnow() - self.last_failure_time >= self.recovery_timeout
    
    def get_state(self) -> Dict[str, Any]:
        """
        Get circuit breaker state and metrics.
        
        Returns:
            Dictionary with circuit breaker state and metrics
        """
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "total_calls": self.total_calls,
            "failure_threshold": self.failure_threshold,
            "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None,
            "last_success_time": self.last_success_time.isoformat() if self.last_success_time else None,
            "recovery_timeout_seconds": self.recovery_timeout.total_seconds()
        }
    
    def reset(self):
        """Reset circuit breaker to CLOSED state."""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        logger.info(f"Circuit breaker {self.name} manually reset to CLOSED")


def circuit_breaker(
    failure_threshold: int = 5,
    recovery_timeout: int = 60,
    expected_exception: Exception = Exception,
    name: str = "default"
):
    """
    Decorator for circuit breaker protection.
    
    Args:
        failure_threshold: Number of failures before opening circuit
        recovery_timeout: Seconds to wait before attempting recovery
        expected_exception: Exception type to track as failures
        name: Circuit breaker identifier
    """
    def decorator(func):
        breaker = CircuitBreaker(
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            expected_exception=expected_exception,
            name=name or func.__name__
        )
        
        def sync_wrapper(*args, **kwargs):
            return breaker.call(func, *args, **kwargs)
        
        async def async_wrapper(*args, **kwargs):
            return await breaker.call_async(func, *args, **kwargs)
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator
