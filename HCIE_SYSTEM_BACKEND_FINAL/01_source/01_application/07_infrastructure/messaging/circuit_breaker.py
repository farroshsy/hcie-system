"""
Circuit Breaker Pattern for EventBus
Prevents hammering failed services and provides fallback behavior
"""

import logging
import time
from enum import Enum
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Circuit is open, fail fast
    HALF_OPEN = "half_open" # Testing if service recovered

@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration"""
    failure_threshold: int = 5          # Failures before opening
    recovery_timeout: int = 60          # Seconds to wait before trying again
    expected_exception: type = Exception  # Exception type to track
    fallback_timeout: int = 5            # Timeout for fallback operations

class CircuitBreaker:
    """Circuit breaker for EventBus protection"""
    
    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.next_attempt = None
        
        # Fallback transport (HTTP when Kafka fails)
        self.fallback_transport = None
        
    def set_fallback_transport(self, transport):
        """Set fallback transport for when circuit is open"""
        self.fallback_transport = transport
        logger.info("✅ Fallback transport configured for circuit breaker")
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        try:
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                    logger.info("🔄 Circuit breaker moving to HALF_OPEN state")
                else:
                    # Circuit is open, use fallback or fail fast
                    if self.fallback_transport:
                        logger.warning("⚠️ Circuit open - using fallback transport")
                        return self.fallback_transport.publish(*args, **kwargs)
                    else:
                        raise RuntimeError("❌ Circuit breaker is OPEN - service unavailable")
            
            # Try to execute the function
            result = func(*args, **kwargs)
            
            # Success - reset failure count if in half-open
            if self.state == CircuitState.HALF_OPEN:
                self._reset()
                logger.info("✅ Circuit breaker reset to CLOSED state")
            
            return result
            
        except self.config.expected_exception as e:
            self._on_failure()
            raise
        
        except Exception as e:
            # Unexpected exception - don't count towards circuit breaker
            logger.error(f"❌ Unexpected exception in circuit breaker: {e}")
            raise
    
    def _should_attempt_reset(self) -> bool:
        """Check if we should attempt to reset the circuit"""
        if self.last_failure_time is None:
            return False
        
        return time.time() - self.last_failure_time >= self.config.recovery_timeout
    
    def _on_failure(self):
        """Handle failure event"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        logger.warning(f"⚠️ Circuit breaker failure #{self.failure_count}")
        
        if self.failure_count >= self.config.failure_threshold:
            self.state = CircuitState.OPEN
            self.next_attempt = time.time() + self.config.recovery_timeout
            logger.error(f"💥 Circuit breaker OPENED after {self.failure_count} failures")
    
    def _reset(self):
        """Reset circuit breaker to closed state"""
        self.failure_count = 0
        self.last_failure_time = None
        self.next_attempt = None
        self.state = CircuitState.CLOSED
    
    def get_state(self) -> Dict[str, Any]:
        """Get current circuit breaker state"""
        return {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "last_failure_time": self.last_failure_time,
            "next_attempt": self.next_attempt,
            "has_fallback": self.fallback_transport is not None
        }

class HTTPFallbackTransport:
    """HTTP fallback transport for when Kafka fails"""
    
    def __init__(self, http_client=None):
        self.http_client = http_client
    
    def publish(self, event) -> bool:
        """Publish event via HTTP fallback"""
        try:
            logger.info(f"🌐 Publishing event via HTTP fallback: {event.event_id}")
            
            # TODO: Implement actual HTTP publishing
            # This would send to an HTTP endpoint that handles events
            
            # For now, simulate success
            return True
            
        except Exception as e:
            logger.error(f"❌ HTTP fallback failed: {e}")
            return False
    
    def is_healthy(self) -> bool:
        """Check if HTTP transport is healthy"""
        return self.http_client is not None

# Global circuit breaker instance
_circuit_breaker = None

def get_circuit_breaker(config: Optional[CircuitBreakerConfig] = None) -> CircuitBreaker:
    """Get or create circuit breaker instance"""
    global _circuit_breaker
    
    if _circuit_breaker is None:
        _circuit_breaker = CircuitBreaker(config or CircuitBreakerConfig())
        
        # Configure HTTP fallback
        _circuit_breaker.set_fallback_transport(HTTPFallbackTransport())
    
    return _circuit_breaker
