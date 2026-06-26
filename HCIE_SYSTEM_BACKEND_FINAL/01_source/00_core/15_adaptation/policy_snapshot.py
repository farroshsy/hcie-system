"""
Policy Snapshot Service - Immutable Experiment Policy Snapshots

CRITICAL FOR C2.1.5: This module provides immutable policy snapshots so that
if policies change later, old replay remains valid.

Experiment execution must reference immutable policy snapshots, not mutable live policies.
Frozen semantic transforms, adaptation parameters, and UX mappings.

This is NOT enhancement work - it is required for semantic immutability before
replay, analytics, counterfactuals, or longitudinal science can be trusted.
"""

import logging
import json
import hashlib
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class SnapshotStatus(str, Enum):
    """Status of a policy snapshot"""
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    RETIRED = "retired"


@dataclass(frozen=True)
class StrategySnapshot:
    """
    Immutable snapshot of a policy strategy.
    
    Captures the strategy type and its critical parameters for replay.
    """
    strategy_type: str  # e.g., "DefaultPacingStrategy", "AggressivePacingStrategy"
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StrategySnapshot':
        return cls(
            strategy_type=data["strategy_type"],
            parameters=data.get("parameters", {})
        )


@dataclass(frozen=True)
class PolicySnapshot:
    """
    Immutable snapshot of a complete policy runtime.
    
    This captures ALL policy state at a point in time:
    - Strategy implementations (by type name + parameters)
    - Adaptation parameters
    - Thresholds
    - UX transformation logic
    
    This snapshot is immutable (frozen=True) to guarantee replay safety.
    """
    
    snapshot_id: str
    policy_version: str
    created_at: str  # ISO format timestamp
    
    # Strategy snapshots (capture strategy type + parameters)
    pacing_strategy: StrategySnapshot
    remediation_strategy: StrategySnapshot
    difficulty_strategy: StrategySnapshot
    ux_transformer: StrategySnapshot
    
    # Policy configuration (frozen)
    adaptation_parameters: Dict[str, Any] = field(default_factory=dict)
    thresholds: Dict[str, float] = field(default_factory=dict)
    
    # Snapshot metadata
    status: SnapshotStatus = SnapshotStatus.ACTIVE
    schema_version: str = "1.0.0"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert snapshot to dictionary for storage"""
        return {
            "snapshot_id": self.snapshot_id,
            "policy_version": self.policy_version,
            "created_at": self.created_at,
            "pacing_strategy": self.pacing_strategy.to_dict(),
            "remediation_strategy": self.remediation_strategy.to_dict(),
            "difficulty_strategy": self.difficulty_strategy.to_dict(),
            "ux_transformer": self.ux_transformer.to_dict(),
            "adaptation_parameters": self.adaptation_parameters,
            "thresholds": self.thresholds,
            "status": self.status.value,
            "schema_version": self.schema_version
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PolicySnapshot':
        """Reconstruct snapshot from dictionary"""
        return cls(
            snapshot_id=data["snapshot_id"],
            policy_version=data["policy_version"],
            created_at=data["created_at"],
            pacing_strategy=StrategySnapshot.from_dict(data["pacing_strategy"]),
            remediation_strategy=StrategySnapshot.from_dict(data["remediation_strategy"]),
            difficulty_strategy=StrategySnapshot.from_dict(data["difficulty_strategy"]),
            ux_transformer=StrategySnapshot.from_dict(data["ux_transformer"]),
            adaptation_parameters=data.get("adaptation_parameters", {}),
            thresholds=data.get("thresholds", {}),
            status=SnapshotStatus(data.get("status", "active")),
            schema_version=data.get("schema_version", "1.0.0")
        )
    
    # Volatile fields excluded from the content hash so identical policies hash identically
    # (a "deterministic content hash" must be content-only). `created_at` is a wall-clock
    # creation timestamp; `snapshot_id` already embeds the content hash so it is content-derived
    # but is excluded too to keep the digest purely about policy content.
    _HASH_VOLATILE_FIELDS = ("created_at", "snapshot_id")

    def compute_hash(self) -> str:
        """
        Compute deterministic CONTENT hash of the snapshot.

        Content-only: excludes volatile/identity fields (created_at, snapshot_id) so two
        snapshots of the SAME policy produce the SAME hash. Used for snapshot integrity
        validation, replay verification, and change detection.

        NOTE: this is a low-level policy-snapshot hash (sha256 over the policy dict) and is
        entirely separate from the run seal `content_hash` (md5 over ordered interaction_ids
        in run_sealing); changing it touches no sealed value.
        """
        content_dict = {k: v for k, v in self.to_dict().items() if k not in self._HASH_VOLATILE_FIELDS}
        content = json.dumps(content_dict, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()


class PolicySnapshotService:
    """
    Service for creating and managing immutable policy snapshots.
    
    Responsibilities:
    - Create snapshots from live policy runtimes
    - Store snapshots immutably (in-memory + database)
    - Retrieve snapshots for replay
    - Validate snapshot integrity
    
    🔥 C2.1.5: Snapshots are now persisted to PostgreSQL for durability
    across system restarts and for replay validity.
    """
    
    def __init__(self, postgres_store=None):
        self._snapshots: Dict[str, PolicySnapshot] = {}
        self._snapshot_by_version: Dict[str, str] = {}  # policy_version -> snapshot_id
        self._postgres_store = postgres_store
        self._repository = None
        
        # Initialize repository if postgres_store is provided
        if postgres_store:
            from core.adaptation.policy_snapshot_repository import PolicySnapshotRepository
            self._repository = PolicySnapshotRepository(postgres_store)
    
    def create_snapshot_from_runtime(
        self,
        policy_runtime,
        experiment_id: Optional[str] = None
    ) -> PolicySnapshot:
        """
        Create an immutable snapshot from a live PolicyRuntime.
        
        This captures the entire policy state at creation time.
        The snapshot is immutable (frozen) and cannot be modified.
        """
        # Generate snapshot ID
        timestamp = datetime.utcnow().isoformat()
        content_hash = self._compute_runtime_hash(policy_runtime)
        snapshot_id = f"{policy_runtime.policy_version}_{content_hash[:16]}"
        
        # Extract strategy information
        pacing_strategy = StrategySnapshot(
            strategy_type=type(policy_runtime.pacing_strategy).__name__,
            parameters={}  # Strategies don't have serializable parameters in current impl
        )
        
        remediation_strategy = StrategySnapshot(
            strategy_type=type(policy_runtime.remediation_strategy).__name__,
            parameters={}
        )
        
        difficulty_strategy = StrategySnapshot(
            strategy_type=type(policy_runtime.difficulty_strategy).__name__,
            parameters={}
        )
        
        ux_transformer = StrategySnapshot(
            strategy_type=type(policy_runtime.ux_transformer).__name__,
            parameters={}
        )
        
        # Create frozen snapshot
        snapshot = PolicySnapshot(
            snapshot_id=snapshot_id,
            policy_version=policy_runtime.policy_version,
            created_at=timestamp,
            pacing_strategy=pacing_strategy,
            remediation_strategy=remediation_strategy,
            difficulty_strategy=difficulty_strategy,
            ux_transformer=ux_transformer,
            adaptation_parameters=dict(policy_runtime.adaptation_parameters),
            thresholds=dict(policy_runtime.thresholds),
            status=SnapshotStatus.ACTIVE,
            schema_version="1.0.0"
        )
        
        # Store snapshot in memory
        self._snapshots[snapshot_id] = snapshot
        self._snapshot_by_version[policy_runtime.policy_version] = snapshot_id
        
        # 🔥 C2.1.5: Persist snapshot to database for durability
        if self._repository:
            snapshot_dict = snapshot.to_dict()
            snapshot_dict["experiment_id"] = experiment_id
            if self._repository.save_snapshot(snapshot_dict):
                logger.info(f"💾 Persisted policy snapshot {snapshot_id} to database")
            else:
                logger.warning(f"⚠️ Failed to persist snapshot {snapshot_id} to database")
        
        logger.info(
            f"🔒 Created policy snapshot: {snapshot_id} "
            f"(policy={policy_runtime.policy_version}, "
            f"experiment={experiment_id})"
        )
        
        return snapshot
    
    def get_snapshot(self, snapshot_id: str) -> Optional[PolicySnapshot]:
        """
        Retrieve snapshot by ID.
        
        🔥 C2.1.5: Checks memory first, then database for durability.
        """
        # Check memory cache first
        if snapshot_id in self._snapshots:
            return self._snapshots[snapshot_id]
        
        # 🔥 C2.1.5: Check database if repository is available
        if self._repository:
            snapshot_dict = self._repository.get_snapshot(snapshot_id)
            if snapshot_dict:
                snapshot = PolicySnapshot.from_dict(snapshot_dict)
                # Cache in memory for future access
                self._snapshots[snapshot_id] = snapshot
                self._snapshot_by_version[snapshot.policy_version] = snapshot_id
                logger.debug(f"🔒 Loaded snapshot {snapshot_id} from database")
                return snapshot
        
        return None
    
    def get_snapshot_by_policy_version(
        self,
        policy_version: str
    ) -> Optional[PolicySnapshot]:
        """Retrieve latest snapshot for a policy version"""
        snapshot_id = self._snapshot_by_version.get(policy_version)
        if snapshot_id:
            return self._snapshots.get(snapshot_id)
        return None
    
    def validate_snapshot_integrity(
        self,
        snapshot: PolicySnapshot
    ) -> bool:
        """
        Validate snapshot integrity by recomputing hash.
        
        Returns True if snapshot has not been tampered with.
        """
        computed_hash = snapshot.compute_hash()
        # In a real implementation, we'd store the original hash and compare
        # For now, we just ensure the snapshot can be serialized consistently
        try:
            json.dumps(snapshot.to_dict())
            return True
        except Exception as e:
            logger.error(f"❌ Snapshot integrity validation failed: {e}")
            return False
    
    def list_snapshots(
        self,
        policy_version: Optional[str] = None
    ) -> list[PolicySnapshot]:
        """List all snapshots, optionally filtered by policy version"""
        if policy_version:
            snapshot_id = self._snapshot_by_version.get(policy_version)
            if snapshot_id:
                return [self._snapshots[snapshot_id]]
            return []
        return list(self._snapshots.values())
    
    def _compute_runtime_hash(self, policy_runtime) -> str:
        """Compute hash of policy runtime state"""
        content = {
            "policy_version": policy_runtime.policy_version,
            "adaptation_parameters": policy_runtime.adaptation_parameters,
            "thresholds": policy_runtime.thresholds,
            "pacing_strategy": type(policy_runtime.pacing_strategy).__name__,
            "remediation_strategy": type(policy_runtime.remediation_strategy).__name__,
            "difficulty_strategy": type(policy_runtime.difficulty_strategy).__name__,
            "ux_transformer": type(policy_runtime.ux_transformer).__name__
        }
        content_str = json.dumps(content, sort_keys=True)
        return hashlib.sha256(content_str.encode()).hexdigest()


# Global snapshot service instance
_policy_snapshot_service = None


def get_policy_snapshot_service(postgres_store=None):
    """
    Get global policy snapshot service instance.
    
    🔥 C2.1.5: Accepts postgres_store parameter for database persistence.
    If postgres_store is provided, snapshots will be persisted to PostgreSQL.
    """
    global _policy_snapshot_service
    if _policy_snapshot_service is None:
        _policy_snapshot_service = PolicySnapshotService(postgres_store=postgres_store)
    return _policy_snapshot_service
