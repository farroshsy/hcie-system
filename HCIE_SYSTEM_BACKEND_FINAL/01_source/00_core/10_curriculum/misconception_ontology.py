"""
Misconception Ontology - C1.3 Phase 1

This module defines the misconception ontology for the HCIE system.

ARCHITECTURAL CONSTRAINT:
- This is a pedagogical semantic layer, NOT a cognitive layer
- Misconceptions are interpretive, not cognitive state
- Remediation semantics are pedagogical strategies, not cognition mutations
- Ontology must be replay-safe and versioned

ONTLOGY STRUCTURE:
- MisconceptionIdentity: Unique identifier with lineage
- MisconceptionSeverity: Impact on learning progression
- MisconceptionRelationships: Connections between misconceptions
- RemediationSemantics: Pedagogical intervention strategies
"""

from enum import Enum
from typing import Optional, List, Dict, Set
from dataclasses import dataclass
from datetime import datetime


class MisconceptionSeverity(str, Enum):
    """Impact of misconception on learning progression"""
    CRITICAL = "critical"  # Blocks concept mastery completely
    HIGH = "high"  # Significantly impedes progression
    MEDIUM = "medium"  # Moderately affects understanding
    LOW = "low"  # Minor conceptual gap


class MisconceptionCategory(str, Enum):
    """Domain of misconception"""
    ALGORITHMIC = "algorithmic"  # Algorithm logic errors
    DATA_STRUCTURE = "data_structure"  # DS understanding gaps
    COMPLEXITY = "complexity"  # Time/space complexity misconceptions
    SYNTAX = "syntax"  # Language-specific errors
    LOGICAL = "logical"  # Reasoning errors
    PREREQUISITE = "prerequisite"  # Missing foundational knowledge


@dataclass
class MisconceptionIdentity:
    """Unique identifier with lineage tracking"""
    id: str  # e.g., "linear_search_confusion"
    category: MisconceptionCategory
    concept_id: str  # Which concept this relates to
    parent_misconceptions: List[str] = None  # Lineage from simpler misconceptions
    version: str = "1.0.0"  # Ontology version
    
    def __post_init__(self):
        if self.parent_misconceptions is None:
            self.parent_misconceptions = []


@dataclass
class MisconceptionSemantics:
    """Pedagogical meaning of the misconception"""
    description: str  # What the misconception is
    common_patterns: List[str]  # Typical learner behaviors
    detection_signals: List[str]  # How to identify this misconception
    severity: MisconceptionSeverity
    persistence_score: float  # How likely to persist (0-1)
    
    def __post_init__(self):
        if not 0 <= self.persistence_score <= 1:
            raise ValueError("persistence_score must be between 0 and 1")


@dataclass
class RemediationSemantics:
    """Pedagogical intervention strategy"""
    strategy: str  # Type of remediation (e.g., "analogy", "counter_example")
    recommended_concepts: List[str]  # Prerequisites to review
    difficulty_adjustment: float  # How much to reduce task difficulty (-1 to 1)
    explanation_template: str  # Template for learner-facing explanation
    practice_requirements: List[str]  # Types of practice needed
    
    def __post_init__(self):
        if not -1 <= self.difficulty_adjustment <= 1:
            raise ValueError("difficulty_adjustment must be between -1 and 1")


@dataclass
class MisconceptionRelationship:
    """Connection between misconceptions"""
    related_misconception_id: str
    relationship_type: str  # "causes", "caused_by", "co_occurs_with", "resolves"
    strength: float  # Relationship strength (0-1)
    
    def __post_init__(self):
        if not 0 <= self.strength <= 1:
            raise ValueError("strength must be between 0 and 1")


@dataclass
class Misconception:
    """Complete misconception definition"""
    identity: MisconceptionIdentity
    semantics: MisconceptionSemantics
    remediation: RemediationSemantics
    relationships: List[MisconceptionRelationship] = None
    created_at: datetime = None
    updated_at: datetime = None
    
    def __post_init__(self):
        if self.relationships is None:
            self.relationships = []
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()


class MisconceptionOntology:
    """
    Registry of all misconceptions with query and relationship capabilities.
    
    This is a pedagogical semantic layer, NOT a cognitive state layer.
    The ontology is versioned and replay-safe.
    """
    
    def __init__(self, version: str = "1.0.0"):
        self.version = version
        self._misconceptions: Dict[str, Misconception] = {}
        self._category_index: Dict[MisconceptionCategory, Set[str]] = {}
        self._concept_index: Dict[str, Set[str]] = {}
        self._severity_index: Dict[MisconceptionSeverity, Set[str]] = {}
        
    def register(self, misconception: Misconception) -> None:
        """Register a misconception in the ontology"""
        self._misconceptions[misconception.identity.id] = misconception
        
        # Update indices
        if misconception.identity.category not in self._category_index:
            self._category_index[misconception.identity.category] = set()
        self._category_index[misconception.identity.category].add(misconception.identity.id)
        
        if misconception.identity.concept_id not in self._concept_index:
            self._concept_index[misconception.identity.concept_id] = set()
        self._concept_index[misconception.identity.concept_id].add(misconception.identity.id)
        
        if misconception.semantics.severity not in self._severity_index:
            self._severity_index[misconception.semantics.severity] = set()
        self._severity_index[misconception.semantics.severity].add(misconception.identity.id)
    
    def get(self, misconception_id: str) -> Optional[Misconception]:
        """Get a misconception by ID"""
        return self._misconceptions.get(misconception_id)
    
    def by_category(self, category: MisconceptionCategory) -> List[Misconception]:
        """Get all misconceptions in a category"""
        ids = self._category_index.get(category, set())
        return [self._misconceptions[mid] for mid in ids if mid in self._misconceptions]
    
    def by_concept(self, concept_id: str) -> List[Misconception]:
        """Get all misconceptions for a concept"""
        ids = self._concept_index.get(concept_id, set())
        return [self._misconceptions[mid] for mid in ids if mid in self._misconceptions]
    
    def by_severity(self, severity: MisconceptionSeverity) -> List[Misconception]:
        """Get all misconceptions with a severity level"""
        ids = self._severity_index.get(severity, set())
        return [self._misconceptions[mid] for mid in ids if mid in self._misconceptions]
    
    def related(self, misconception_id: str) -> List[Misconception]:
        """Get all related misconceptions"""
        misconception = self.get(misconception_id)
        if not misconception:
            return []
        
        related_ids = [r.related_misconception_id for r in misconception.relationships]
        return [self._misconceptions[rid] for rid in related_ids if rid in self._misconceptions]
    
    def all(self) -> List[Misconception]:
        """Get all misconceptions"""
        return list(self._misconceptions.values())
    
    def count(self) -> int:
        """Get total number of misconceptions"""
        return len(self._misconceptions)


# Initialize with sample misconceptions for algorithms domain
def initialize_algorithmic_misconceptions() -> MisconceptionOntology:
    """Initialize ontology with common algorithmic misconceptions"""
    ontology = MisconceptionOntology(version="1.0.0")
    
    # Linear search confusion
    linear_search_confusion = Misconception(
        identity=MisconceptionIdentity(
            id="linear_search_confusion",
            category=MisconceptionCategory.ALGORITHMIC,
            concept_id="k2_algorithms",
            version="1.0.0"
        ),
        semantics=MisconceptionSemantics(
            description="Learner believes linear search is always O(1) or confuses it with binary search",
            common_patterns=[
                "Assumes linear search has constant time",
                "Confuses linear with binary search mechanics",
                "Ignores iteration count in complexity analysis"
            ],
            detection_signals=[
                "O(1) answer for linear search questions",
                "Fails to identify worst-case scenario",
                "Cannot explain iteration count"
            ],
            severity=MisconceptionSeverity.HIGH,
            persistence_score=0.6
        ),
        remediation=RemediationSemantics(
            strategy="counter_example",
            recommended_concepts=["k1_basics", "k1_iteration"],
            difficulty_adjustment=-0.3,
            explanation_template="Linear search checks every element. If array has N elements, worst case is N checks. That's O(n), not O(1).",
            practice_requirements=["tracing_execution", "worst_case_analysis"]
        )
    )
    
    # Binary search misconception
    binary_search_confusion = Misconception(
        identity=MisconceptionIdentity(
            id="binary_search_confusion",
            category=MisconceptionCategory.ALGORITHMIC,
            concept_id="k2_algorithms",
            parent_misconceptions=["linear_search_confusion"],
            version="1.0.0"
        ),
        semantics=MisconceptionSemantics(
            description="Learner misunderstands divide-and-conquer or halving property of binary search",
            common_patterns=[
                "Does not understand halving property",
                "Confuses mid calculation",
                "Fails to maintain invariant"
            ],
            detection_signals=[
                "O(n) answer for binary search",
                "Incorrect mid formula",
                "Cannot explain why it's faster than linear search"
            ],
            severity=MisconceptionSeverity.CRITICAL,
            persistence_score=0.7
        ),
        remediation=RemediationSemantics(
            strategy="analogy",
            recommended_concepts=["k2_algorithms", "k1_divide_conquer"],
            difficulty_adjustment=-0.4,
            explanation_template="Binary search halves the search space each time. After k steps, remaining space is N/2^k. When N/2^k = 1, we've found the element.",
            practice_requirements=["invariant_tracing", "halving_visualization"]
        ),
        relationships=[
            MisconceptionRelationship(
                related_misconception_id="linear_search_confusion",
                relationship_type="caused_by",
                strength=0.8
            )
        ]
    )
    
    # Complexity notation confusion
    complexity_notation_confusion = Misconception(
        identity=MisconceptionIdentity(
            id="complexity_notation_confusion",
            category=MisconceptionCategory.COMPLEXITY,
            concept_id="k2_complexity",
            version="1.0.0"
        ),
        semantics=MisconceptionSemantics(
            description="Learner confuses Big-O with actual runtime or ignores constants",
            common_patterns=[
                "Thinks O(n) means exactly n operations",
                "Ignores constant factors entirely",
                "Confuses best/worst/average case notation"
            ],
            detection_signals=[
                "Literal interpretation of Big-O",
                "Cannot explain upper bound meaning",
                "Confuses O(1) with constant time in practice"
            ],
            severity=MisconceptionSeverity.MEDIUM,
            persistence_score=0.5
        ),
        remediation=RemediationSemantics(
            strategy="definition",
            recommended_concepts=["k2_complexity"],
            difficulty_adjustment=-0.2,
            explanation_template="Big-O is an upper bound, not exact count. O(n) means 'at most proportional to n' as n grows large. Constants don't matter for large n.",
            practice_requirements=["formal_definition", "growth_rate_comparison"]
        )
    )
    
    # Register all misconceptions
    ontology.register(linear_search_confusion)
    ontology.register(binary_search_confusion)
    ontology.register(complexity_notation_confusion)
    
    return ontology


# Global ontology instance
_global_ontology: Optional[MisconceptionOntology] = None


def get_misconception_ontology() -> MisconceptionOntology:
    """Get the global misconception ontology instance"""
    global _global_ontology
    if _global_ontology is None:
        _global_ontology = initialize_algorithmic_misconceptions()
    return _global_ontology
