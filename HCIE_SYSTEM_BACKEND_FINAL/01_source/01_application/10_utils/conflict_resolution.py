"""
Conflict Resolution Utilities

Provides conflict detection and resolution mechanisms for concurrent operations.
Handles optimistic concurrency control, version checking, and conflict resolution strategies.
"""

from typing import Generic, TypeVar, Optional, Dict, Any, List
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

T = TypeVar("T")


class ConflictType(str, Enum):
    """Types of conflicts that can occur"""
    VERSION_MISMATCH = "version_mismatch"
    OPTIMISTIC_LOCK = "optimistic_lock"
    DATA_CONFLICT = "data_conflict"
    RESOURCE_LOCK = "resource_lock"


class ConflictResolutionStrategy(str, Enum):
    """Strategies for resolving conflicts"""
    LAST_WRITE_WINS = "last_write_wins"
    FIRST_WRITE_WINS = "first_write_wins"
    MERGE = "merge"
    MANUAL = "manual"
    RETRY = "retry"


class Conflict(BaseModel):
    """Represents a conflict that occurred during an operation"""
    conflict_type: ConflictType = Field(description="Type of conflict")
    resource_id: str = Field(description="Identifier of the conflicting resource")
    current_version: Optional[str] = Field(default=None, description="Current version of the resource")
    attempted_version: Optional[str] = Field(default=None, description="Attempted version that caused conflict")
    conflicting_data: Optional[Dict[str, Any]] = Field(default=None, description="Conflicting data")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When the conflict occurred")
    resolved: bool = Field(default=False, description="Whether the conflict has been resolved")
    resolution: Optional[str] = Field(default=None, description="How the conflict was resolved")


class ConflictResolutionResult(BaseModel):
    """Result of conflict resolution"""
    success: bool = Field(description="Whether resolution was successful")
    strategy_used: ConflictResolutionStrategy = Field(description="Strategy used for resolution")
    resolved_data: Optional[Dict[str, Any]] = Field(default=None, description="Resolved data after conflict resolution")
    conflicts: List[Conflict] = Field(default_factory=list, description="List of conflicts that occurred")
    retry_required: bool = Field(default=False, description="Whether retry is required")


class VersionedResource(BaseModel, Generic[T]):
    """Base model for versioned resources with conflict detection"""
    resource_id: str = Field(description="Unique identifier for the resource")
    version: str = Field(description="Version of the resource")
    data: T = Field(description="Resource data")
    last_modified: datetime = Field(default_factory=datetime.utcnow, description="Last modification timestamp")
    
    class Config:
        arbitrary_types_allowed = True


class ConflictResolver:
    """
    Conflict resolution handler for concurrent operations.
    
    Provides optimistic concurrency control and conflict resolution strategies.
    """
    
    def __init__(
        self,
        default_strategy: ConflictResolutionStrategy = ConflictResolutionStrategy.LAST_WRITE_WINS
    ):
        """
        Initialize conflict resolver.
        
        Args:
            default_strategy: Default strategy for resolving conflicts
        """
        self.default_strategy = default_strategy
        self.conflict_history: List[Conflict] = []
    
    def check_version_conflict(
        self,
        resource_id: str,
        expected_version: str,
        current_version: str
    ) -> Optional[Conflict]:
        """
        Check for version conflict.
        
        Args:
            resource_id: Resource identifier
            expected_version: Expected version
            current_version: Current version
            
        Returns:
            Conflict if versions don't match, None otherwise
        """
        if expected_version != current_version:
            conflict = Conflict(
                conflict_type=ConflictType.VERSION_MISMATCH,
                resource_id=resource_id,
                current_version=current_version,
                attempted_version=expected_version
            )
            self.conflict_history.append(conflict)
            logger.warning(f"Version conflict detected for resource {resource_id}: expected {expected_version}, got {current_version}")
            return conflict
        return None
    
    def resolve_conflict(
        self,
        conflict: Conflict,
        current_data: Dict[str, Any],
        new_data: Dict[str, Any],
        strategy: Optional[ConflictResolutionStrategy] = None
    ) -> ConflictResolutionResult:
        """
        Resolve a conflict using the specified strategy.
        
        Args:
            conflict: Conflict to resolve
            current_data: Current data state
            new_data: New data attempting to be applied
            strategy: Resolution strategy (uses default if not specified)
            
        Returns:
            ConflictResolutionResult with resolution outcome
        """
        strategy = strategy or self.default_strategy
        
        try:
            if strategy == ConflictResolutionStrategy.LAST_WRITE_WINS:
                return self._resolve_last_write_wins(conflict, current_data, new_data)
            elif strategy == ConflictResolutionStrategy.FIRST_WRITE_WINS:
                return self._resolve_first_write_wins(conflict, current_data, new_data)
            elif strategy == ConflictResolutionStrategy.MERGE:
                return self._resolve_merge(conflict, current_data, new_data)
            elif strategy == ConflictResolutionStrategy.MANUAL:
                return self._resolve_manual(conflict, current_data, new_data)
            elif strategy == ConflictResolutionStrategy.RETRY:
                return self._resolve_retry(conflict, current_data, new_data)
            else:
                logger.error(f"Unknown conflict resolution strategy: {strategy}")
                return ConflictResolutionResult(
                    success=False,
                    strategy_used=strategy,
                    conflicts=[conflict],
                    retry_required=True
                )
        except Exception as e:
            logger.error(f"Error resolving conflict: {e}")
            return ConflictResolutionResult(
                success=False,
                strategy_used=strategy,
                conflicts=[conflict],
                retry_required=True
            )
    
    def _resolve_last_write_wins(
        self,
        conflict: Conflict,
        current_data: Dict[str, Any],
        new_data: Dict[str, Any]
    ) -> ConflictResolutionResult:
        """Resolve conflict by accepting the last write (new data)."""
        conflict.resolved = True
        conflict.resolution = "last_write_wins"
        
        return ConflictResolutionResult(
            success=True,
            strategy_used=ConflictResolutionStrategy.LAST_WRITE_WINS,
            resolved_data=new_data,
            conflicts=[conflict],
            retry_required=False
        )
    
    def _resolve_first_write_wins(
        self,
        conflict: Conflict,
        current_data: Dict[str, Any],
        new_data: Dict[str, Any]
    ) -> ConflictResolutionResult:
        """Resolve conflict by accepting the first write (current data)."""
        conflict.resolved = True
        conflict.resolution = "first_write_wins"
        
        return ConflictResolutionResult(
            success=False,
            strategy_used=ConflictResolutionStrategy.FIRST_WRITE_WINS,
            resolved_data=current_data,
            conflicts=[conflict],
            retry_required=False
        )
    
    def _resolve_merge(
        self,
        conflict: Conflict,
        current_data: Dict[str, Any],
        new_data: Dict[str, Any]
    ) -> ConflictResolutionResult:
        """Resolve conflict by merging data."""
        merged_data = {**current_data, **new_data}
        
        conflict.resolved = True
        conflict.resolution = "merge"
        
        return ConflictResolutionResult(
            success=True,
            strategy_used=ConflictResolutionStrategy.MERGE,
            resolved_data=merged_data,
            conflicts=[conflict],
            retry_required=False
        )
    
    def _resolve_manual(
        self,
        conflict: Conflict,
        current_data: Dict[str, Any],
        new_data: Dict[str, Any]
    ) -> ConflictResolutionResult:
        """Mark conflict for manual resolution."""
        return ConflictResolutionResult(
            success=False,
            strategy_used=ConflictResolutionStrategy.MANUAL,
            resolved_data=None,
            conflicts=[conflict],
            retry_required=False
        )
    
    def _resolve_retry(
        self,
        conflict: Conflict,
        current_data: Dict[str, Any],
        new_data: Dict[str, Any]
    ) -> ConflictResolutionResult:
        """Mark conflict for retry."""
        return ConflictResolutionResult(
            success=False,
            strategy_used=ConflictResolutionStrategy.RETRY,
            resolved_data=None,
            conflicts=[conflict],
            retry_required=True
        )
    
    def get_conflict_history(
        self,
        resource_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Conflict]:
        """
        Get conflict history.
        
        Args:
            resource_id: Optional resource ID to filter by
            limit: Maximum number of conflicts to return
            
        Returns:
            List of conflicts
        """
        conflicts = self.conflict_history
        if resource_id:
            conflicts = [c for c in conflicts if c.resource_id == resource_id]
        return conflicts[-limit:]


def check_optimistic_lock(
    resource: VersionedResource,
    expected_version: str
) -> Optional[Conflict]:
    """
    Check optimistic lock condition.
    
    Args:
        resource: Versioned resource to check
        expected_version: Expected version
        
    Returns:
        Conflict if lock condition violated, None otherwise
    """
    if resource.version != expected_version:
        return Conflict(
            conflict_type=ConflictType.OPTIMISTIC_LOCK,
            resource_id=resource.resource_id,
            current_version=resource.version,
            attempted_version=expected_version
        )
    return None
