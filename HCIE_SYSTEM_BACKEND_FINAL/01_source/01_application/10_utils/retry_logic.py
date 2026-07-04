"""
Retry Logic Utilities

Provides retry mechanisms with exponential backoff for resilient operations.
Supports configurable retry strategies, backoff policies, and jitter.
"""

from typing import Callable, Optional, Any, List, Type
from enum import Enum
from datetime import datetime
import logging
import asyncio
import random

logger = logging.getLogger(__name__)


class RetryStrategy(str, Enum):
    """Retry strategies"""
    FIXED = "fixed"  # Fixed delay between retries
    EXPONENTIAL = "exponential"  # Exponential backoff
    LINEAR = "linear"  # Linear backoff
    CUSTOM = "custom"  # Custom backoff function


class RetryError(Exception):
    """Raised when all retry attempts are exhausted"""
    def __init__(self, message: str, attempts: int, last_exception: Exception):
        super().__init__(message)
        self.attempts = attempts
        self.last_exception = last_exception


class RetryConfig:
    """Configuration for retry logic"""
    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
        backoff_multiplier: float = 2.0,
        jitter: bool = True,
        jitter_amount: float = 0.1,
        retryable_exceptions: Optional[List[Type[Exception]]] = None,
        on_retry_callback: Optional[Callable] = None
    ):
        """
        Initialize retry configuration.
        
        Args:
            max_attempts: Maximum number of retry attempts
            base_delay: Base delay in seconds
            max_delay: Maximum delay in seconds
            strategy: Backoff strategy
            backoff_multiplier: Multiplier for exponential backoff
            jitter: Whether to add jitter to delays
            jitter_amount: Amount of jitter (0-1)
            retryable_exceptions: List of exception types to retry on
            on_retry_callback: Callback function called on each retry
        """
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.strategy = strategy
        self.backoff_multiplier = backoff_multiplier
        self.jitter = jitter
        self.jitter_amount = jitter_amount
        self.retryable_exceptions = retryable_exceptions or [Exception]
        self.on_retry_callback = on_retry_callback


class RetryExecutor:
    """
    Retry executor with configurable backoff strategies.
    
    Provides resilient operation execution with automatic retries
    and configurable backoff policies.
    """
    
    def __init__(self, config: Optional[RetryConfig] = None):
        """
        Initialize retry executor.
        
        Args:
            config: Retry configuration (uses default if not provided)
        """
        self.config = config or RetryConfig()
    
    def execute(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute a function with retry logic.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            RetryError: If all retry attempts are exhausted
        """
        last_exception = None
        
        for attempt in range(self.config.max_attempts):
            try:
                result = func(*args, **kwargs)
                if attempt > 0:
                    logger.info(f"Function succeeded on attempt {attempt + 1}")
                return result
            except Exception as e:
                last_exception = e
                
                # Check if exception is retryable
                if not self._is_retryable(e):
                    logger.error(f"Exception {type(e).__name__} is not retryable")
                    raise e
                
                # Check if this was the last attempt
                if attempt == self.config.max_attempts - 1:
                    logger.error(f"All {self.config.max_attempts} retry attempts exhausted")
                    raise RetryError(
                        f"All retry attempts exhausted after {self.config.max_attempts} attempts",
                        attempts=self.config.max_attempts,
                        last_exception=last_exception
                    )
                
                # Calculate delay
                delay = self._calculate_delay(attempt)
                
                logger.warning(
                    f"Attempt {attempt + 1} failed with {type(e).__name__}: {e}. "
                    f"Retrying in {delay:.2f}s..."
                )
                
                # Call retry callback if configured
                if self.config.on_retry_callback:
                    self.config.on_retry_callback(attempt + 1, e, delay)
                
                # Wait before retry
                self._wait(delay)
    
    async def execute_async(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute an async function with retry logic.
        
        Args:
            func: Async function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            RetryError: If all retry attempts are exhausted
        """
        last_exception = None
        
        for attempt in range(self.config.max_attempts):
            try:
                result = await func(*args, **kwargs)
                if attempt > 0:
                    logger.info(f"Async function succeeded on attempt {attempt + 1}")
                return result
            except Exception as e:
                last_exception = e
                
                # Check if exception is retryable
                if not self._is_retryable(e):
                    logger.error(f"Exception {type(e).__name__} is not retryable")
                    raise e
                
                # Check if this was the last attempt
                if attempt == self.config.max_attempts - 1:
                    logger.error(f"All {self.config.max_attempts} retry attempts exhausted")
                    raise RetryError(
                        f"All retry attempts exhausted after {self.config.max_attempts} attempts",
                        attempts=self.config.max_attempts,
                        last_exception=last_exception
                    )
                
                # Calculate delay
                delay = self._calculate_delay(attempt)
                
                logger.warning(
                    f"Async attempt {attempt + 1} failed with {type(e).__name__}: {e}. "
                    f"Retrying in {delay:.2f}s..."
                )
                
                # Call retry callback if configured
                if self.config.on_retry_callback:
                    self.config.on_retry_callback(attempt + 1, e, delay)
                
                # Wait before retry
                await self._wait_async(delay)
    
    def _is_retryable(self, exception: Exception) -> bool:
        """Check if exception is retryable."""
        return any(isinstance(exception, exc_type) for exc_type in self.config.retryable_exceptions)
    
    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay before next retry."""
        if self.config.strategy == RetryStrategy.FIXED:
            delay = self.config.base_delay
        elif self.config.strategy == RetryStrategy.EXPONENTIAL:
            delay = self.config.base_delay * (self.config.backoff_multiplier ** attempt)
        elif self.config.strategy == RetryStrategy.LINEAR:
            delay = self.config.base_delay * (attempt + 1)
        else:
            delay = self.config.base_delay
        
        # Cap at max delay
        delay = min(delay, self.config.max_delay)
        
        # Add jitter if configured
        if self.config.jitter:
            jitter = delay * self.config.jitter_amount * (random.random() * 2 - 1)
            delay = max(0, delay + jitter)
        
        return delay
    
    def _wait(self, delay: float):
        """Wait for specified delay (synchronous)."""
        import time
        time.sleep(delay)
    
    async def _wait_async(self, delay: float):
        """Wait for specified delay (asynchronous)."""
        await asyncio.sleep(delay)


def retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
    backoff_multiplier: float = 2.0,
    jitter: bool = True,
    retryable_exceptions: Optional[List[Type[Exception]]] = None
):
    """
    Decorator for retry logic.
    
    Args:
        max_attempts: Maximum number of retry attempts
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        strategy: Backoff strategy
        backoff_multiplier: Multiplier for exponential backoff
        jitter: Whether to add jitter to delays
        retryable_exceptions: List of exception types to retry on
    """
    config = RetryConfig(
        max_attempts=max_attempts,
        base_delay=base_delay,
        max_delay=max_delay,
        strategy=strategy,
        backoff_multiplier=backoff_multiplier,
        jitter=jitter,
        retryable_exceptions=retryable_exceptions
    )
    
    def decorator(func):
        executor = RetryExecutor(config)
        
        def sync_wrapper(*args, **kwargs):
            return executor.execute(func, *args, **kwargs)
        
        async def async_wrapper(*args, **kwargs):
            return await executor.execute_async(func, *args, **kwargs)
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator
