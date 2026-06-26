"""
Experiment Registry - Pedagogical Orchestration Layer

Stores experiment metadata for controlled pedagogical hypothesis validation.
This layer enables:
- Controlled pedagogical experiments
- Replay comparison
- Longitudinal educational analysis
- Policy evaluation
- Cohort science

Critical: Experiment assignment must be replay-deterministic.
Same learner + same experiment seed → same policy assignment.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum
import hashlib

logger = logging.getLogger(__name__)


class ExperimentStatus(str, Enum):
    """Experiment lifecycle states"""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class ExperimentType(str, Enum):
    """Types of pedagogical experiments"""
    POLICY_COMPARISON = "policy_comparison"  # Compare different adaptation policies
    COHORT_SEGMENTATION = "cohort_segmentation"  # Test on different learner segments
    PARAMETER_TUNING = "parameter_tuning"  # Tune policy parameters
    FEATURE_FLAG = "feature_flag"  # Enable/disable pedagogical features
    LONGITUDINAL_STUDY = "longitudinal_study"  # Track long-term effects


class Experiment:
    """
    Represents a pedagogical experiment with hypothesis, policy assignment, and evaluation.
    
    This is NOT the same as A/B testing frameworks for UI optimization.
    These are educational research experiments with pedagogical hypotheses.
    """
    
    def __init__(
        self,
        experiment_id: str,
        name: str,
        description: str,
        hypothesis: str,
        experiment_type: ExperimentType,
        policy_versions: List[str],  # e.g., ["v1.0.0", "v1.1.0"] for comparison
        cohort_criteria: Dict[str, Any],  # Learner segmentation criteria
        rollout_percentage: float,  # 0.0 to 1.0
        start_date: datetime,
        end_date: Optional[datetime] = None,
        status: ExperimentStatus = ExperimentStatus.DRAFT,
        evaluation_metrics: Optional[List[str]] = None,  # Metrics to track
        replay_compatible: bool = True,  # Can this experiment be replayed?
        metadata: Optional[Dict[str, Any]] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        self.experiment_id = experiment_id
        self.name = name
        self.description = description
        self.hypothesis = hypothesis
        self.experiment_type = experiment_type
        self.policy_versions = policy_versions
        self.cohort_criteria = cohort_criteria
        self.rollout_percentage = rollout_percentage
        self.start_date = start_date
        self.end_date = end_date
        self.status = status
        self.evaluation_metrics = evaluation_metrics or []
        self.replay_compatible = replay_compatible
        self.metadata = metadata or {}
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for persistence"""
        return {
            "experiment_id": self.experiment_id,
            "name": self.name,
            "description": self.description,
            "hypothesis": self.hypothesis,
            "experiment_type": self.experiment_type.value,
            "policy_versions": self.policy_versions,
            "cohort_criteria": self.cohort_criteria,
            "rollout_percentage": self.rollout_percentage,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "status": self.status.value,
            "evaluation_metrics": self.evaluation_metrics,
            "replay_compatible": self.replay_compatible,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Experiment":
        """Create from dictionary"""
        return cls(
            experiment_id=data["experiment_id"],
            name=data["name"],
            description=data["description"],
            hypothesis=data["hypothesis"],
            experiment_type=ExperimentType(data["experiment_type"]),
            policy_versions=data["policy_versions"],
            cohort_criteria=data["cohort_criteria"],
            rollout_percentage=data["rollout_percentage"],
            start_date=datetime.fromisoformat(data["start_date"]),
            end_date=datetime.fromisoformat(data["end_date"]) if data.get("end_date") else None,
            status=ExperimentStatus(data["status"]),
            evaluation_metrics=data.get("evaluation_metrics", []),
            replay_compatible=data.get("replay_compatible", True),
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None
        )


class ExperimentRegistry:
    """
    Pedagogical experiment orchestration layer.
    
    Manages experiment lifecycle, assignment, and lineage tracking.
    Critical for replay-deterministic cohort assignment.
    
    🔥 C2.1.5: Now creates immutable policy snapshots when experiments are registered.
    This ensures that if policies change later, old replay remains valid.
    """
    
    def __init__(self, postgres_store=None):
        self._experiments: Dict[str, Experiment] = {}
        self._assignments: Dict[str, str] = {}  # user_id -> experiment_id
        self._policy_assignments: Dict[str, str] = {}  # user_id -> policy_version
        self._policy_snapshots: Dict[str, str] = {}  # experiment_id -> snapshot_id mapping
        self._postgres_store = postgres_store  # 🔥 C2.1.5: For snapshot persistence
    
    def register_experiment(self, experiment: Experiment) -> bool:
        """
        Register a new experiment in the registry.
        
        🔥 C2.1.5: Creates immutable policy snapshots for all policy versions
        in the experiment. This ensures replay validity even if policies change later.
        
        Returns True if registered successfully, False if experiment_id already exists.
        """
        if experiment.experiment_id in self._experiments:
            logger.warning(f"Experiment {experiment.experiment_id} already exists")
            return False
        
        self._experiments[experiment.experiment_id] = experiment
        
        # 🔥 C2.1.5: Create immutable policy snapshots
        from core.adaptation.policy_snapshot import get_policy_snapshot_service
        from core.adaptation.policy_isolation import get_policy_runtime_registry
        
        # 🔥 C2.1.5: Initialize snapshot service with postgres_store for persistence
        snapshot_service = get_policy_snapshot_service(postgres_store=self._postgres_store)
        policy_registry = get_policy_runtime_registry()
        
        snapshot_ids = []
        for policy_version in experiment.policy_versions:
            policy_runtime = policy_registry.get_runtime(policy_version)
            if policy_runtime:
                snapshot = snapshot_service.create_snapshot_from_runtime(
                    policy_runtime,
                    experiment_id=experiment.experiment_id
                )
                snapshot_ids.append(snapshot.snapshot_id)
                logger.info(
                    f"🔒 Created policy snapshot {snapshot.snapshot_id} "
                    f"for experiment {experiment.experiment_id}"
                )
            else:
                logger.warning(
                    f"⚠️ Policy version {policy_version} not found in registry, "
                    f"skipping snapshot creation"
                )
        
        # Store snapshot mapping for this experiment
        self._policy_snapshots[experiment.experiment_id] = snapshot_ids
        
        logger.info(f"Registered experiment: {experiment.experiment_id} - {experiment.name}")
        return True
    
    def get_experiment(self, experiment_id: str) -> Optional[Experiment]:
        """Get experiment by ID"""
        return self._experiments.get(experiment_id)
    
    def list_experiments(
        self,
        status: Optional[ExperimentStatus] = None,
        experiment_type: Optional[ExperimentType] = None
    ) -> List[Experiment]:
        """List experiments with optional filtering"""
        experiments = list(self._experiments.values())
        
        if status:
            experiments = [e for e in experiments if e.status == status]
        
        if experiment_type:
            experiments = [e for e in experiments if e.experiment_type == experiment_type]
        
        return experiments
    
    def get_policy_snapshots(self, experiment_id: str) -> list[str]:
        """
        🔥 C2.1.5: Get policy snapshot IDs for an experiment.
        
        Returns the immutable snapshot IDs that were created when the experiment
        was registered. These snapshots preserve the policy state at experiment
        creation time for replay validity.
        """
        return self._policy_snapshots.get(experiment_id, [])
    
    def assign_user_to_experiment(
        self,
        user_id: str,
        experiment_seed: Optional[str] = None
    ) -> Optional[str]:
        """
        Assign user to an active experiment using deterministic hashing.
        
        Critical: This must be replay-deterministic.
        Same user_id + same experiment_seed → same experiment assignment.
        
        Args:
            user_id: Learner identifier
            experiment_seed: Optional seed for deterministic assignment (e.g., date, experiment_id)
        
        Returns:
            experiment_id if assigned, None if no active experiment matches
        """
        # Create deterministic assignment key
        assignment_key = f"{user_id}:{experiment_seed or 'default'}"
        
        # Check cache for existing assignment
        if assignment_key in self._assignments:
            return self._assignments[assignment_key]
        
        # Get active experiments
        active_experiments = [
            e for e in self._experiments.values()
            if e.status == ExperimentStatus.ACTIVE
            and (e.start_date <= datetime.utcnow())
            and (e.end_date is None or e.end_date > datetime.utcnow())
        ]
        
        if not active_experiments:
            return None
        
        # Deterministic hash-based assignment
        hash_input = assignment_key.encode('utf-8')
        hash_value = int(hashlib.sha256(hash_input).hexdigest(), 16)
        
        # Normalize hash to [0, 1]
        normalized_hash = (hash_value % 10000) / 10000.0
        
        # Find experiment based on rollout percentage
        cumulative_rollout = 0.0
        for experiment in sorted(active_experiments, key=lambda e: e.experiment_id):
            cumulative_rollout += experiment.rollout_percentage
            if normalized_hash < cumulative_rollout:
                self._assignments[assignment_key] = experiment.experiment_id
                logger.debug(f"Assigned user {user_id} to experiment {experiment.experiment_id}")
                return experiment.experiment_id
        
        return None
    
    def assign_policy_for_user(
        self,
        user_id: str,
        experiment_id: str
    ) -> Optional[str]:
        """
        Assign specific policy version to user within experiment.
        
        For multi-policy experiments (e.g., v1.0.0 vs v1.1.0),
        this determines which policy the user receives.
        
        Critical: Must be replay-deterministic.
        Same user_id + same experiment_id → same policy assignment.
        """
        experiment = self.get_experiment(experiment_id)
        if not experiment:
            logger.error(f"Experiment {experiment_id} not found")
            return None
        
        if len(experiment.policy_versions) == 1:
            # Single policy experiment
            policy_version = experiment.policy_versions[0]
        else:
            # Multi-policy experiment - deterministic assignment
            assignment_key = f"{user_id}:{experiment_id}"
            
            # Check cache
            if assignment_key in self._policy_assignments:
                return self._policy_assignments[assignment_key]
            
            # Deterministic hash-based policy selection
            hash_input = assignment_key.encode('utf-8')
            hash_value = int(hashlib.sha256(hash_input).hexdigest(), 16)
            
            # Select policy based on hash
            policy_index = hash_value % len(experiment.policy_versions)
            policy_version = experiment.policy_versions[policy_index]
            
            self._policy_assignments[assignment_key] = policy_version
        
        logger.debug(f"Assigned policy {policy_version} to user {user_id} in experiment {experiment_id}")
        return policy_version
    
    def get_user_assignment(self, user_id: str) -> Optional[Dict[str, str]]:
        """
        Get current experiment and policy assignment for user.
        
        Returns:
            Dict with 'experiment_id' and 'policy_version' if assigned, None otherwise
        """
        experiment_id = self.assign_user_to_experiment(user_id)
        if not experiment_id:
            return None
        
        policy_version = self.assign_policy_for_user(user_id, experiment_id)
        if not policy_version:
            return None
        
        return {
            "experiment_id": experiment_id,
            "policy_version": policy_version
        }
    
    def update_experiment_status(
        self,
        experiment_id: str,
        new_status: ExperimentStatus
    ) -> bool:
        """Update experiment lifecycle status"""
        experiment = self.get_experiment(experiment_id)
        if not experiment:
            logger.error(f"Experiment {experiment_id} not found")
            return False
        
        experiment.status = new_status
        experiment.updated_at = datetime.utcnow()
        logger.info(f"Updated experiment {experiment_id} status to {new_status.value}")
        return True
    
    def record_experiment_metric(
        self,
        experiment_id: str,
        user_id: str,
        metric_name: str,
        metric_value: float,
        timestamp: Optional[datetime] = None
    ) -> bool:
        """
        Record evaluation metric for experiment.
        
        This is a simplified version - production would need proper metrics storage.
        For now, we'll just log it.
        """
        experiment = self.get_experiment(experiment_id)
        if not experiment:
            logger.error(f"Experiment {experiment_id} not found")
            return False
        
        if metric_name not in experiment.evaluation_metrics:
            logger.warning(f"Metric {metric_name} not in experiment evaluation metrics")
        
        logger.info(
            f"Experiment metric: {experiment_id} - user {user_id} - "
            f"{metric_name} = {metric_value} at {timestamp or datetime.utcnow()}"
        )
        
        # TODO: Persist to database in production
        return True
    
    def get_experiment_lineage(self, experiment_id: str) -> Dict[str, Any]:
        """
        Get experiment lineage for replay and analysis.
        
        Returns:
            Dict with experiment metadata and assignment information
        """
        experiment = self.get_experiment(experiment_id)
        if not experiment:
            return {}
        
        # Count assignments
        assignment_count = sum(
            1 for exp_id in self._assignments.values()
            if exp_id == experiment_id
        )
        
        return {
            "experiment": experiment.to_dict(),
            "assignment_count": assignment_count,
            "policy_distribution": self._get_policy_distribution(experiment_id)
        }
    
    def _get_policy_distribution(self, experiment_id: str) -> Dict[str, int]:
        """Get distribution of policy assignments within experiment"""
        experiment = self.get_experiment(experiment_id)
        if not experiment:
            return {}
        
        distribution = {policy: 0 for policy in experiment.policy_versions}
        
        for assignment_key, assigned_exp_id in self._assignments.items():
            if assigned_exp_id == experiment_id:
                user_id = assignment_key.split(":")[0]
                policy_version = self._policy_assignments.get(f"{user_id}:{experiment_id}")
                if policy_version and policy_version in distribution:
                    distribution[policy_version] += 1
        
        return distribution


# Global registry instance
_experiment_registry = None


def get_experiment_registry() -> ExperimentRegistry:
    """Get global experiment registry instance"""
    global _experiment_registry
    if _experiment_registry is None:
        _experiment_registry = ExperimentRegistry()
    return _experiment_registry
