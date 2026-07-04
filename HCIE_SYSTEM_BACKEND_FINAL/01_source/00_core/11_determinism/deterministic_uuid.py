"""
Deterministic UUID Generator

Provides replay-safe UUID generation using namespace-based approach
instead of RNG-derived bytes for stability under:
- branching execution
- retries
- partial replay
- parallel consumers
- future async execution

Architecture:
- Uses uuid5(namespace, f"{seed}:{counter}:{event_type}")
- Causally stable, branch stable, replay stable, ordering stable
"""
import uuid


class DeterministicUUIDGenerator:
    """
    Generates deterministic UUIDs using namespace-based approach.
    
    Uses uuid5(namespace, f"{seed}:{counter}:{event_type}") instead of
    RNG-derived bytes for replay stability across branching, retries,
    partial replay, and parallel consumers.
    
    Advantages over RNG-derived UUIDs:
    - Causally stable (same inputs → same UUID)
    - Branch stable (deterministic across execution paths)
    - Replay stable (consistent across replays)
    - Ordering stable (monotonic counter preserves order)
    - Semantic traceability (event_type encoded in UUID)
    """
    
    # Namespace for HCIE deterministic UUIDs (generated from uuid.NAMESPACE_DNS)
    HCIE_NAMESPACE = uuid.UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')
    
    def __init__(self, seed: int = 42):
        """
        Initialize deterministic UUID generator.
        
        Args:
            seed: Deterministic seed for UUID generation
        """
        self.seed = seed
        self.counter = 0
    
    def generate(self, event_type: str = "event") -> uuid.UUID:
        """
        Generate deterministic UUID v5.
        
        Uses uuid5(namespace, f"{seed}:{counter}:{event_type}") for
        causal stability and replay safety.
        
        Args:
            event_type: Type of event (for semantic traceability)
            
        Returns:
            Deterministic UUID v5
        """
        # Create deterministic input string
        input_string = f"{self.seed}:{self.counter}:{event_type}"
        
        # Generate UUID v5 (SHA-1 hash based, deterministic)
        deterministic_uuid = uuid.uuid5(self.HCIE_NAMESPACE, input_string)
        
        # Increment counter for next UUID
        self.counter += 1
        
        return deterministic_uuid
    
    def reset(self):
        """Reset counter to initial state."""
        self.counter = 0
    
    def get_counter(self) -> int:
        """Get current counter value."""
        return self.counter
