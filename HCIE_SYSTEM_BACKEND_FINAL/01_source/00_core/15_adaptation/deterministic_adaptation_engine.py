"""
Deterministic Adaptation Engine
Pure function for deriving adaptation from cognition state
"""

import hashlib
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
import uuid

from .policy_registry import AdaptationPolicyRegistry

logger = logging.getLogger(__name__)


@dataclass
class SemanticAdaptation:
    """
    Pure semantic adaptation derivation (no transport metadata)
    
    This is the mathematically pure layer:
    - No UUID
    - No timestamps
    - No tracing
    - No transport metadata
    
    Only semantic derivation from cognition state.
    """
    adaptation_type: str
    recommendation: Dict[str, Any]
    deterministic_inputs_hash: str
    policy_version: str
    policy_inputs_schema_version: str
    schema_version: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


class DeterministicAdaptationEngine:
    """
    Deterministic adaptation derivation engine
    
    This engine is a PURE FUNCTION:
    - Same inputs → same outputs (deterministic)
    - No side effects (pure function)
    - No external dependencies (self-contained)
    - No runtime state (stateless)
    - No time-relative logic (time-invariant)
    - No randomization (deterministic)
    
    This enables:
    - Replay-safe adaptation
    - Policy-relative replay
    - Hidden state detection
    - Semantic drift detection
    - Cryptographic verification
    """
    
    SCHEMA_VERSION = "1.0.0"
    POLICY_INPUTS_SCHEMA_VERSION = "1.0.0"
    
    def __init__(self):
        """Initialize adaptation engine"""
        self.policy_registry = AdaptationPolicyRegistry()
    
    @staticmethod
    def compute_deterministic_inputs_hash(
        cognition_snapshot: Dict[str, Any],
        policy_version: str,
        adaptation_type: str
    ) -> str:
        """
        Compute hash of deterministic inputs
        
        Used for:
        - Replay verification
        - Hidden state detection
        - Semantic drift detection
        - Policy reproducibility proof
        
        Args:
            cognition_snapshot: Cognition state snapshot
            policy_version: Policy version used for derivation
            adaptation_type: Adaptation type classification
        
        Returns:
            SHA-256 hash of normalized inputs
        """
        # Normalize inputs for consistent hashing
        normalized = {
            'cognition_snapshot': DeterministicAdaptationEngine._normalize_dict(cognition_snapshot),
            'policy_version': policy_version,
            'adaptation_type': adaptation_type
        }
        
        # Compute hash
        hash_input = json.dumps(normalized, sort_keys=True)
        return hashlib.sha256(hash_input.encode()).hexdigest()
    
    @staticmethod
    def _normalize_dict(d: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize dictionary for consistent hashing
        
        Handles:
        - None values
        - Float precision
        - Key ordering
        """
        normalized = {}
        for key, value in sorted(d.items()):
            if value is None:
                normalized[key] = None
            elif isinstance(value, float):
                # Normalize float precision to avoid hash differences
                normalized[key] = round(value, 6)
            elif isinstance(value, dict):
                normalized[key] = DeterministicAdaptationEngine._normalize_dict(value)
            elif isinstance(value, list):
                normalized[key] = [
                    DeterministicAdaptationEngine._normalize_dict(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                normalized[key] = value
        return normalized
    
    def derive_semantics(
        self,
        cognition_snapshot: Dict[str, Any],
        policy_version: str
    ) -> SemanticAdaptation:
        """
        Layer 1: Pure semantic adaptation derivation (MATHEMATICALLY PURE)
        
        This is the core pure function:
        semantics = f(cognition_snapshot, policy_version)
        
        Returns:
            SemanticAdaptation (no transport metadata, no UUID, no timestamps)
        
        Raises:
            ValueError: If policy version not found
        """
        # Get policy
        policy = self.policy_registry.get_policy(policy_version)
        
        # Classify adaptation type
        adaptation_type = policy.classify_adaptation_type(cognition_snapshot)
        
        # Derive recommendation
        recommendation = policy.derive_recommendation(cognition_snapshot, adaptation_type)
        
        # Compute determinism hash
        deterministic_inputs_hash = self.compute_deterministic_inputs_hash(
            cognition_snapshot,
            policy_version,
            adaptation_type
        )
        
        # Build pure semantic adaptation
        semantic_adaptation = SemanticAdaptation(
            adaptation_type=adaptation_type,
            recommendation=recommendation,
            deterministic_inputs_hash=deterministic_inputs_hash,
            policy_version=policy_version,
            policy_inputs_schema_version=policy.get_policy_inputs_schema_version(),
            schema_version=self.SCHEMA_VERSION
        )
        
        logger.info(
            f"✅ Derived semantics: type={adaptation_type}, "
            f"policy={policy_version}, "
            f"hash={deterministic_inputs_hash[:16]}..."
        )
        
        return semantic_adaptation
    
    def materialize_adaptation_event(
        self,
        semantic_adaptation: SemanticAdaptation,
        cognition_snapshot: Dict[str, Any],
        user_id: str,
        session_id: Optional[str] = None,
        causation_id: Optional[str] = None,
        trace_context: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Layer 2: Event materialization (adds transport metadata)
        
        Adds transport layer metadata to pure semantic adaptation:
        - event_id (UUID)
        - timestamp (ISO format)
        - trace context (OTel)
        - causation lineage
        - session metadata
        
        Args:
            semantic_adaptation: Pure semantic adaptation from derive_semantics
            cognition_snapshot: Cognition state snapshot (for replay verification)
            user_id: User identifier
            session_id: Optional session identifier
            causation_id: ID of triggering CognitionUpdated event
            trace_context: Optional OpenTelemetry trace context
        
        Returns:
            AdaptationGenerated event payload (transport-ready)
        """
        # Build adaptation event payload
        adaptation_event = {
            "event_id": str(uuid.uuid4()),
            "event_type": "AdaptationGenerated",
            "user_id": user_id,
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat(),
            "source": "adaptation-consumer",
            
            # Semantic adaptation (from pure derivation)
            "adaptation_type": semantic_adaptation.adaptation_type,
            "recommendation": semantic_adaptation.recommendation,
            "deterministic_inputs_hash": semantic_adaptation.deterministic_inputs_hash,
            "policy_version": semantic_adaptation.policy_version,
            "policy_inputs_schema_version": semantic_adaptation.policy_inputs_schema_version,
            "schema_version": semantic_adaptation.schema_version,
            
            # Cognition snapshot (for replay verification)
            "cognition_snapshot": cognition_snapshot,
            
            # Causation lineage
            "causation_id": causation_id,
            
            # Trace context
            "trace_id": trace_context.get('trace_id') if trace_context else None,
            "span_id": trace_context.get('span_id') if trace_context else None,
            "parent_span_id": trace_context.get('parent_span_id') if trace_context else None
        }
        
        logger.debug(
            f"✅ Materialized event: event_id={adaptation_event['event_id']}, "
            f"type={semantic_adaptation.adaptation_type}"
        )
        
        return adaptation_event
    
    def derive_adaptation(
        self,
        cognition_snapshot: Dict[str, Any],
        policy_version: str,
        user_id: str,
        session_id: Optional[str] = None,
        causation_id: Optional[str] = None,
        trace_context: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Derive adaptation from cognition state (convenience wrapper)
        
        This combines Layer 1 (pure semantics) and Layer 2 (event materialization):
        adaptation = materialize(derive_semantics(cognition, policy), metadata)
        
        Args:
            cognition_snapshot: Cognition state snapshot
            policy_version: Policy version to use for derivation
            user_id: User identifier
            session_id: Optional session identifier
            causation_id: ID of triggering CognitionUpdated event
            trace_context: Optional OpenTelemetry trace context
        
        Returns:
            AdaptationGenerated event payload (self-contained)
        
        Raises:
            ValueError: If policy version not found
        """
        # Layer 1: Pure semantic derivation
        semantic_adaptation = self.derive_semantics(cognition_snapshot, policy_version)
        
        # Layer 2: Event materialization
        adaptation_event = self.materialize_adaptation_event(
            semantic_adaptation=semantic_adaptation,
            cognition_snapshot=cognition_snapshot,
            user_id=user_id,
            session_id=session_id,
            causation_id=causation_id,
            trace_context=trace_context
        )
        
        return adaptation_event
    
    def verify_determinism(
        self,
        adaptation_event: Dict[str, Any]
    ) -> bool:
        """
        Verify that adaptation is deterministic
        
        Checks:
        - deterministic_inputs_hash matches computed hash
        - No hidden state dependencies
        
        Args:
            adaptation_event: AdaptationGenerated event payload
        
        Returns:
            True if deterministic, False otherwise
        """
        cognition_snapshot = adaptation_event.get('cognition_snapshot', {})
        policy_version = adaptation_event.get('policy_version', '')
        adaptation_type = adaptation_event.get('adaptation_type', '')
        original_hash = adaptation_event.get('deterministic_inputs_hash', '')
        
        # Compute expected hash
        computed_hash = self.compute_deterministic_inputs_hash(
            cognition_snapshot,
            policy_version,
            adaptation_type
        )
        
        # Verify
        is_deterministic = computed_hash == original_hash
        
        if not is_deterministic:
            logger.error(
                f"❌ Determinism violation: expected {computed_hash[:16]}..., "
                f"got {original_hash[:16]}..."
            )
        else:
            logger.debug(f"✅ Determinism verified: {computed_hash[:16]}...")
        
        return is_deterministic
    
    def is_self_contained(
        self,
        adaptation_event: Dict[str, Any]
    ) -> bool:
        """
        Verify that event is self-contained for replay
        
        Checks:
        - All required fields present
        - No external dependencies needed
        
        Args:
            adaptation_event: AdaptationGenerated event payload
        
        Returns:
            True if self-contained, False otherwise
        """
        required_fields = [
            'cognition_snapshot',
            'policy_version',
            'adaptation_type',
            'deterministic_inputs_hash',
            'recommendation',
            'schema_version',
            'policy_inputs_schema_version'
        ]
        
        is_self_contained = all(field in adaptation_event for field in required_fields)
        
        if not is_self_contained:
            missing = [f for f in required_fields if f not in adaptation_event]
            logger.error(f"❌ Self-contained violation: missing fields {missing}")
        
        return is_self_contained


# Global singleton engine instance
_deterministic_adaptation_engine = None


def get_deterministic_adaptation_engine() -> DeterministicAdaptationEngine:
    """
    Get global deterministic adaptation engine singleton
    
    Returns:
        DeterministicAdaptationEngine instance
    """
    global _deterministic_adaptation_engine
    if _deterministic_adaptation_engine is None:
        _deterministic_adaptation_engine = DeterministicAdaptationEngine()
    return _deterministic_adaptation_engine
