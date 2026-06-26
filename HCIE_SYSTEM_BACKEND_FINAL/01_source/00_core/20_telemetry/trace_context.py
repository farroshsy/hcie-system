"""
Trace Context for Distributed Cognition

Provides trace_id propagation across the entire educational runtime flow:
API → Outbox → Kafka → Consumer → UnifiedBrain → Persistence → Metrics → WebSocket
"""

import uuid
from typing import Optional, Dict, Any
from contextvars import ContextVar
from dataclasses import dataclass, field

# Context variable for trace propagation across async boundaries
_trace_context: ContextVar[Optional['TraceContext']] = ContextVar('trace_context', default=None)


@dataclass
class TraceContext:
    """
    Distributed trace context for educational runtime
    
    Provides end-to-end trace continuity across:
    - API requests
    - Outbox events
    - Kafka messages
    - UnifiedBrain processing
    - Persistence operations
    - Metrics emission
    - WebSocket notifications
    """
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    span_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    parent_span_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    
    # Trace metadata
    source: str = "api"  # api, consumer, worker, etc.
    component: str = "runtime"  # runtime, cognition, persistence, etc.
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "source": self.source,
            "component": self.component
        }
    
    def to_headers(self) -> Dict[str, str]:
        """Convert to HTTP headers for propagation"""
        return {
            "X-Trace-Id": self.trace_id,
            "X-Span-Id": self.span_id,
            "X-Parent-Span-Id": self.parent_span_id or "",
            "X-User-Id": self.user_id or "",
            "X-Session-Id": self.session_id or "",
            "X-Trace-Source": self.source,
            "X-Trace-Component": self.component
        }
    
    def create_child(self, component: str) -> 'TraceContext':
        """Create a child span for nested operations"""
        return TraceContext(
            trace_id=self.trace_id,
            span_id=str(uuid.uuid4())[:8],
            parent_span_id=self.span_id,
            user_id=self.user_id,
            session_id=self.session_id,
            source=self.source,
            component=component
        )
    
    @classmethod
    def from_headers(cls, headers: Dict[str, str]) -> Optional['TraceContext']:
        """Reconstruct TraceContext from HTTP headers"""
        trace_id = headers.get("X-Trace-Id")
        if not trace_id:
            return None
        
        return cls(
            trace_id=trace_id,
            span_id=headers.get("X-Span-Id", str(uuid.uuid4())[:8]),
            parent_span_id=headers.get("X-Parent-Span-Id") or None,
            user_id=headers.get("X-User-Id") or None,
            session_id=headers.get("X-Session-Id") or None,
            source=headers.get("X-Trace-Source", "unknown"),
            component=headers.get("X-Trace-Component", "unknown")
        )
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Optional['TraceContext']:
        """Reconstruct TraceContext from dictionary"""
        trace_id = data.get("trace_id")
        if not trace_id:
            return None
        
        return cls(
            trace_id=trace_id,
            span_id=data.get("span_id", str(uuid.uuid4())[:8]),
            parent_span_id=data.get("parent_span_id"),
            user_id=data.get("user_id"),
            session_id=data.get("session_id"),
            source=data.get("source", "unknown"),
            component=data.get("component", "unknown")
        )


def get_trace_context() -> Optional[TraceContext]:
    """Get current trace context from context variable"""
    return _trace_context.get()


def set_trace_context(context: TraceContext) -> None:
    """Set trace context in context variable"""
    _trace_context.set(context)


def create_trace_context(
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    source: str = "api",
    component: str = "runtime"
) -> TraceContext:
    """Create new trace context"""
    context = TraceContext(
        user_id=user_id,
        session_id=session_id,
        source=source,
        component=component
    )
    set_trace_context(context)
    return context


def with_trace_context(context: TraceContext):
    """
    Context manager for trace context
    
    Usage:
        with with_trace_context(trace_context):
            # operations here will have trace context available
            pass
    """
    token = _trace_context.set(context)
    try:
        yield
    finally:
        _trace_context.reset(token)


def extract_trace_from_event(event_data: Dict[str, Any]) -> Optional[TraceContext]:
    """Extract trace context from event payload"""
    trace_data = event_data.get("trace_context")
    if trace_data:
        return TraceContext.from_dict(trace_data)
    return None


def inject_trace_to_event(event_data: Dict[str, Any], context: Optional[TraceContext] = None) -> Dict[str, Any]:
    """Inject trace context into event payload"""
    if context is None:
        context = get_trace_context()
    
    if context:
        event_data["trace_context"] = context.to_dict()
    
    return event_data
