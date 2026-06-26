"""
Difficulty Ladders - C1.3 Phase 2

This module defines multi-dimensional difficulty semantics for tasks.

ARCHITECTURAL CONSTRAINT:
- This is a pedagogical semantic layer, NOT a cognitive layer
- Difficulty dimensions are pedagogical design parameters, not learner state
- Difficulty ladders enable nuanced task selection, not cognition mutation
- Ladders must be replay-safe and versioned

MULTI-DIMENSIONAL DIFFICULTY:
- Conceptual Difficulty: Intrinsic complexity of the concept
- Cognitive Load: Working memory demand during task execution
- Transfer Complexity: Difficulty of applying knowledge to new contexts
- Abstraction Depth: How abstract the reasoning must be
- Prerequisite Burden: How many prerequisites must be satisfied
"""

from dataclasses import dataclass
from typing import Optional, Dict, List
from enum import Enum


class DifficultyLevel(str, Enum):
    """Standardized difficulty levels for backward compatibility"""
    TRIVIAL = "trivial"  # 0.0 - 0.2
    EASY = "easy"  # 0.2 - 0.4
    MEDIUM = "medium"  # 0.4 - 0.6
    HARD = "hard"  # 0.6 - 0.8
    EXPERT = "expert"  # 0.8 - 1.0


@dataclass
class DifficultyDimensions:
    """
    Multi-dimensional difficulty representation.
    
    Each dimension is a 0-1 scale representing pedagogical design intent.
    These are NOT learner state measurements - they are task design parameters.
    """
    conceptual_difficulty: float  # Intrinsic concept complexity
    cognitive_load: float  # Working memory demand
    transfer_complexity: float  # Difficulty of knowledge transfer
    abstraction_depth: float  # Level of abstract reasoning required
    prerequisite_burden: float  # Prerequisite dependency weight
    
    def __post_init__(self):
        """Validate all dimensions are in 0-1 range"""
        for field_name, value in [
            ("conceptual_difficulty", self.conceptual_difficulty),
            ("cognitive_load", self.cognitive_load),
            ("transfer_complexity", self.transfer_complexity),
            ("abstraction_depth", self.abstraction_depth),
            ("prerequisite_burden", self.prerequisite_burden),
        ]:
            if not 0 <= value <= 1:
                raise ValueError(f"{field_name} must be between 0 and 1, got {value}")
    
    def to_scalar(self) -> float:
        """
        Convert to single scalar for backward compatibility.
        
        Uses weighted average where cognitive load and conceptual difficulty
        have higher weights as they're most impactful for task selection.
        """
        weights = {
            "conceptual_difficulty": 0.3,
            "cognitive_load": 0.3,
            "transfer_complexity": 0.15,
            "abstraction_depth": 0.15,
            "prerequisite_burden": 0.1,
        }
        
        return (
            self.conceptual_difficulty * weights["conceptual_difficulty"] +
            self.cognitive_load * weights["cognitive_load"] +
            self.transfer_complexity * weights["transfer_complexity"] +
            self.abstraction_depth * weights["abstraction_depth"] +
            self.prerequisite_burden * weights["prerequisite_burden"]
        )
    
    def to_level(self) -> DifficultyLevel:
        """Convert to DifficultyLevel for categorical representation"""
        scalar = self.to_scalar()
        if scalar < 0.2:
            return DifficultyLevel.TRIVIAL
        elif scalar < 0.4:
            return DifficultyLevel.EASY
        elif scalar < 0.6:
            return DifficultyLevel.MEDIUM
        elif scalar < 0.8:
            return DifficultyLevel.HARD
        else:
            return DifficultyLevel.EXPERT


@dataclass
class DifficultyLadder:
    """
    Progressive difficulty sequence for a concept.
    
    Defines how difficulty should progress as learner mastery increases.
    This is pedagogical design, NOT learner state.
    """
    concept_id: str
    ladder_steps: List[DifficultyDimensions]
    version: str = "1.0.0"
    
    def __post_init__(self):
        """Validate ladder is monotonically increasing in complexity"""
        if len(self.ladder_steps) < 1:
            raise ValueError("Ladder must have at least one step")
        
        for i in range(len(self.ladder_steps) - 1):
            current_scalar = self.ladder_steps[i].to_scalar()
            next_scalar = self.ladder_steps[i + 1].to_scalar()
            
            if next_scalar <= current_scalar:
                raise ValueError(
                    f"Ladder steps must be monotonically increasing: "
                    f"step {i} ({current_scalar}) >= step {i+1} ({next_scalar})"
                )
    
    def get_step_for_mastery(self, mastery: float) -> DifficultyDimensions:
        """
        Get appropriate difficulty step based on learner mastery.
        
        Higher mastery → higher difficulty step (within ZPD).
        This is pedagogical design logic, NOT cognition mutation.
        """
        # Map mastery (0-1) to ladder step index
        # Mastery 0 → step 0 (easiest)
        # Mastery 1 → last step (hardest)
        
        step_index = int(mastery * (len(self.ladder_steps) - 1))
        step_index = max(0, min(step_index, len(self.ladder_steps) - 1))
        
        return self.ladder_steps[step_index]
    
    def get_next_step(self, current_difficulty: DifficultyDimensions) -> Optional[DifficultyDimensions]:
        """Get the next harder step in the ladder"""
        current_index = -1
        
        for i, step in enumerate(self.ladder_steps):
            if step.to_scalar() == current_difficulty.to_scalar():
                current_index = i
                break
        
        if current_index >= 0 and current_index < len(self.ladder_steps) - 1:
            return self.ladder_steps[current_index + 1]
        
        return None


class DifficultyLadderRegistry:
    """
    Registry of difficulty ladders for all concepts.
    
    This is a pedagogical semantic layer, NOT a cognitive state layer.
    Ladders are versioned and replay-safe.
    """
    
    def __init__(self, version: str = "1.0.0"):
        self.version = version
        self._ladders: Dict[str, DifficultyLadder] = {}
    
    def register(self, ladder: DifficultyLadder) -> None:
        """Register a difficulty ladder"""
        self._ladders[ladder.concept_id] = ladder
    
    def get(self, concept_id: str) -> Optional[DifficultyLadder]:
        """Get a ladder by concept ID"""
        return self._ladders.get(concept_id)
    
    def all(self) -> List[DifficultyLadder]:
        """Get all registered ladders"""
        return list(self._ladders.values())
    
    def count(self) -> int:
        """Get total number of ladders"""
        return len(self._ladders)


# Initialize with sample difficulty ladders for algorithms domain
def initialize_algorithmic_ladders() -> DifficultyLadderRegistry:
    """Initialize registry with sample difficulty ladders for algorithms"""
    registry = DifficultyLadderRegistry(version="1.0.0")
    
    # Binary search difficulty ladder
    binary_search_ladder = DifficultyLadder(
        concept_id="k2_algorithms",
        ladder_steps=[
            # Step 0: Trivial - recognize binary search, basic halving
            DifficultyDimensions(
                conceptual_difficulty=0.1,
                cognitive_load=0.2,
                transfer_complexity=0.1,
                abstraction_depth=0.1,
                prerequisite_burden=0.2
            ),
            # Step 1: Easy - trace execution, understand mid calculation
            DifficultyDimensions(
                conceptual_difficulty=0.3,
                cognitive_load=0.4,
                transfer_complexity=0.2,
                abstraction_depth=0.2,
                prerequisite_burden=0.3
            ),
            # Step 2: Medium - implement binary search, handle edge cases
            DifficultyDimensions(
                conceptual_difficulty=0.5,
                cognitive_load=0.6,
                transfer_complexity=0.4,
                abstraction_depth=0.4,
                prerequisite_burden=0.4
            ),
            # Step 3: Hard - analyze complexity, compare with linear search
            DifficultyDimensions(
                conceptual_difficulty=0.7,
                cognitive_load=0.7,
                transfer_complexity=0.6,
                abstraction_depth=0.6,
                prerequisite_burden=0.5
            ),
            # Step 4: Expert - optimize variants, understand halving property deeply
            DifficultyDimensions(
                conceptual_difficulty=0.9,
                cognitive_load=0.8,
                transfer_complexity=0.8,
                abstraction_depth=0.8,
                prerequisite_burden=0.6
            ),
        ]
    )
    
    # Complexity analysis difficulty ladder
    complexity_ladder = DifficultyLadder(
        concept_id="k2_complexity",
        ladder_steps=[
            # Step 0: Trivial - recognize O(1), O(n), O(n^2)
            DifficultyDimensions(
                conceptual_difficulty=0.1,
                cognitive_load=0.2,
                transfer_complexity=0.1,
                abstraction_depth=0.2,
                prerequisite_burden=0.2
            ),
            # Step 1: Easy - count operations in simple loops
            DifficultyDimensions(
                conceptual_difficulty=0.3,
                cognitive_load=0.4,
                transfer_complexity=0.3,
                abstraction_depth=0.4,
                prerequisite_burden=0.3
            ),
            # Step 2: Medium - analyze nested loops, understand growth rates
            DifficultyDimensions(
                conceptual_difficulty=0.5,
                cognitive_load=0.6,
                transfer_complexity=0.5,
                abstraction_depth=0.6,
                prerequisite_burden=0.5
            ),
            # Step 3: Hard - analyze divide-and-conquer, logarithmic complexity
            DifficultyDimensions(
                conceptual_difficulty=0.7,
                cognitive_load=0.7,
                transfer_complexity=0.7,
                abstraction_depth=0.8,
                prerequisite_burden=0.6
            ),
            # Step 4: Expert - amortized analysis, space-time tradeoffs
            DifficultyDimensions(
                conceptual_difficulty=0.9,
                cognitive_load=0.9,
                transfer_complexity=0.9,
                abstraction_depth=0.9,
                prerequisite_burden=0.7
            ),
        ]
    )
    
    # Register all ladders
    registry.register(binary_search_ladder)
    registry.register(complexity_ladder)
    
    return registry


# Global ladder registry instance
_global_ladder_registry: Optional[DifficultyLadderRegistry] = None


def get_difficulty_ladder_registry() -> DifficultyLadderRegistry:
    """Get the global difficulty ladder registry instance"""
    global _global_ladder_registry
    if _global_ladder_registry is None:
        _global_ladder_registry = initialize_algorithmic_ladders()
    return _global_ladder_registry
