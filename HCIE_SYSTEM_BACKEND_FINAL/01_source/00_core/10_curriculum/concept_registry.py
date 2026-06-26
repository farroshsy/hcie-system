"""
Concept Registry - Bridge between Curriculum Ontology and Adaptive Runtime

This registry operationalizes curriculum nodes into learner interaction objects.
It is the bridge between:
  Curriculum Ontology → Adaptive Runtime → Learner Experience

Without it, the DAG is only academic structure, not operational cognition.

C1.3 - Task Semantics Hardening: Integrated difficulty ladders for multi-dimensional
difficulty semantics (conceptual difficulty, cognitive load, transfer complexity,
abstraction depth, prerequisite burden).
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Literal
from enum import Enum


class ConceptType(Enum):
    """Types of concepts in the curriculum"""
    KNOWLEDGE = "knowledge"
    SKILL = "skill"
    PRACTICE = "practice"
    ASSESSMENT = "assessment"


class GradeBand(Enum):
    """K-12 grade bands from K12CS framework"""
    K_2 = "K-2"
    K_5 = "K-5"
    K_8 = "K-8"
    K_12 = "K-12"


class TaskType(Enum):
    """Types of learning tasks"""
    MCQ = "mcq"
    SHORT_ANSWER = "short_answer"
    PARSONS = "parsons"
    CODE_TRACE = "code_trace"
    DEBUG = "debug"


class CognitiveOperation(Enum):
    """Cognitive operations learners perform"""
    TRACE = "trace"
    PREDICT = "predict"
    DEBUG = "debug"
    DECOMPOSE = "decompose"
    ABSTRACT = "abstract"
    GENERALIZE = "generalize"


@dataclass
class ConceptNode:
    """
    Canonical cognitive node with 7 layers of semantic metadata.
    
    This converts curriculum ontology into operational cognition.
    """
    
    # === Layer 1: Canonical Identity Layer ===
    # Language-independent runtime identity
    id: str  # e.g., "algorithms_sequence" NOT "algoritma_urutan"
    canonical_name: str
    concept_type: ConceptType
    grade_band: GradeBand
    
    # === Layer 2: Curriculum Mapping Layer ===
    # Academic defensibility and curriculum traceability
    framework_mapping: Dict[str, str] = field(default_factory=dict)
    # e.g., {"k12cs": "K12-CS-ALG-2", "csta": "2-AP-10", "iste": "1.5.a"}
    
    # === Layer 3: Dependency Layer ===
    # Operationalizes the DAG for traversal
    prerequisites: List[str] = field(default_factory=list)
    supports: List[str] = field(default_factory=list)
    transfer_edges: List[str] = field(default_factory=list)
    difficulty_progression: float = 0.5  # 0-1 scale
    
    # === Layer 4: Interaction Semantics Layer ===
    # How this concept can be experienced
    allowed_task_types: List[TaskType] = field(default_factory=list)
    misconception_profiles: List[str] = field(default_factory=list)
    cognitive_operations: List[CognitiveOperation] = field(default_factory=list)
    
    # === Layer 5: Adaptation Semantics Layer ===
    # How adaptation behaves for this concept
    remediation_strategy: str = "repeat_with_hints"
    escalation_strategy: str = "increase_difficulty"
    transfer_sensitivity: float = 0.5  # 0-1 scale
    uncertainty_tolerance: float = 0.3  # 0-1 scale
    mastery_threshold: float = 0.7  # Threshold for considering concept mastered
    
    # === Layer 6: Localization Layer ===
    # Bilingual pedagogy (language-agnostic cognition, localized presentation)
    translations: Dict[str, Dict[str, str]] = field(default_factory=dict)
    # e.g., {"en": {"title": "Algorithms", "description": "..."}, 
    #        "id": {"title": "Algoritma", "description": "..."}}
    
    # === Layer 7: Research Metadata Layer ===
    # Observability and replay support
    research_metadata: Dict[str, str] = field(default_factory=dict)
    # e.g., {"created_by": "handcrafted", "validated": true, "version": "1.0"}


@dataclass
class LearningTask:
    """
    Learning task that binds TO a concept.
    
    Tasks should NOT exist independently - they bind to concepts.
    This operationalizes: concept → measurable cognition
    
    C1.3 - Task Semantics Hardening: Added difficulty_dimensions for multi-dimensional
    difficulty semantics. The 'difficulty' field is retained for backward compatibility
    but should be derived from difficulty_dimensions.to_scalar().
    """
    id: str
    concept_id: str  # Binds to ConceptNode
    
    # Content (non-default, must come first)
    prompt: str
    expected_answer: str
    
    # Interaction semantics
    task_type: TaskType
    difficulty: float  # 0-1 scale (legacy, derived from difficulty_dimensions)
    difficulty_dimensions: Optional['DifficultyDimensions'] = None  # C1.3 multi-dimensional
    
    # Educational semantics
    misconception_target: Optional[str] = None
    evaluation_mode: Literal["binary", "partial", "rubric"] = "binary"
    
    # Support
    hints: List[str] = field(default_factory=list)
    explanation: str = ""
    estimated_time_seconds: int = 60
    
    # Localization
    translations: Dict[str, Dict[str, str]] = field(default_factory=dict)
    # e.g., {"en": {"prompt": "...", "explanation": "..."},
    #        "id": {"prompt": "...", "explanation": "..."}}
    
    # Research metadata
    research_metadata: Dict[str, str] = field(default_factory=dict)


class ConceptRegistry:
    """
    Registry of all concept nodes in the curriculum.
    
    This is the central source of truth for:
    - Concept identity and semantics
    - Curriculum mappings
    - Dependency structure
    - Interaction affordances
    - Adaptation behavior
    - Localization
    """
    
    def __init__(self):
        self._concepts: Dict[str, ConceptNode] = {}
        self._tasks: Dict[str, LearningTask] = {}
    
    def register_concept(self, concept: ConceptNode):
        """Register a concept node"""
        self._concepts[concept.id] = concept
    
    def register_task(self, task: LearningTask):
        """Register a learning task (must bind to existing concept)"""
        if task.concept_id not in self._concepts:
            raise ValueError(f"Task references unknown concept: {task.concept_id}")
        self._tasks[task.id] = task
    
    def get_concept(self, concept_id: str) -> Optional[ConceptNode]:
        """Get a concept by ID"""
        return self._concepts.get(concept_id)
    
    def get_tasks_for_concept(self, concept_id: str) -> List[LearningTask]:
        """Get all tasks for a given concept"""
        return [task for task in self._tasks.values() if task.concept_id == concept_id]
    
    def get_prerequisite_chain(self, concept_id: str) -> List[str]:
        """Get full prerequisite chain for a concept (transitive closure)"""
        chain = []
        visited = set()
        
        def _collect_prereqs(concept_id: str):
            if concept_id in visited:
                return
            visited.add(concept_id)
            concept = self._concepts.get(concept_id)
            if concept:
                for prereq in concept.prerequisites:
                    chain.append(prereq)
                    _collect_prereqs(prereq)
        
        _collect_prereqs(concept_id)
        return chain
    
    def get_supported_concepts(self, concept_id: str) -> List[str]:
        """Get all concepts that this concept supports (forward traversal)"""
        supported = []
        for concept in self._concepts.values():
            if concept_id in concept.prerequisites:
                supported.append(concept.id)
        return supported
    
    def get_concepts_by_grade_band(self, grade_band: GradeBand) -> List[ConceptNode]:
        """Get all concepts in a specific grade band"""
        return [concept for concept in self._concepts.values() if concept.grade_band == grade_band]
    
    def get_all_concepts(self) -> List[ConceptNode]:
        """Get all registered concepts (tactical stabilization for P2)"""
        return list(self._concepts.values())
    
    def validate_registry(self) -> Dict[str, List[str]]:
        """
        Validate the registry for consistency.
        
        Returns dict of error_type -> list of error messages
        """
        errors = {
            "missing_prerequisites": [],
            "circular_dependencies": [],
            "orphaned_concepts": [],
            "orphaned_tasks": []
        }
        
        # Check for missing prerequisites
        for concept_id, concept in self._concepts.items():
            for prereq in concept.prerequisites:
                if prereq not in self._concepts:
                    errors["missing_prerequisites"].append(
                        f"Concept {concept_id} references missing prerequisite {prereq}"
                    )
        
        # Check for circular dependencies
        for concept_id in self._concepts:
            chain = self.get_prerequisite_chain(concept_id)
            if concept_id in chain:
                errors["circular_dependencies"].append(
                    f"Circular dependency detected for {concept_id}"
                )
        
        # Check for orphaned concepts (no prerequisites and nothing depends on it)
        all_prereqs = set()
        all_supported = set()
        for concept in self._concepts.values():
            all_prereqs.update(concept.prerequisites)
            for supported in self.get_supported_concepts(concept.id):
                all_supported.add(supported)
        
        for concept_id in self._concepts:
            if concept_id not in all_prereqs and concept_id not in all_supported:
                # Root concepts are OK if they have tasks
                if not self.get_tasks_for_concept(concept_id):
                    errors["orphaned_concepts"].append(
                        f"Concept {concept_id} has no prerequisites, nothing depends on it, and has no tasks"
                    )
        
        return errors


# Global registry instance
_registry: Optional[ConceptRegistry] = None


def get_registry() -> ConceptRegistry:
    """Get the global concept registry instance"""
    global _registry
    if _registry is None:
        _registry = ConceptRegistry()
    return _registry


def initialize_intro_python_curriculum():
    """
    Initialize the minimal Intro Python curriculum.
    
    This creates 8-12 concepts for first live testing:
    - sequence
    - conditionals
    - loops
    - decomposition
    - variables
    - functions
    - lists
    - dictionaries
    """
    registry = get_registry()
    
    # === Core Concepts ===
    
    # 1. Sequence
    sequence = ConceptNode(
        id="sequence",
        canonical_name="Sequence",
        concept_type=ConceptType.KNOWLEDGE,
        grade_band=GradeBand.K_5,
        framework_mapping={
            "k12cs": "K12-CS-ALG-2",
            "csta": "2-AP-10"
        },
        prerequisites=[],
        supports=["conditionals", "loops", "functions"],
        transfer_edges=[],
        difficulty_progression=0.3,
        allowed_task_types=[TaskType.MCQ, TaskType.PARSONS, TaskType.CODE_TRACE],
        misconception_profiles=["order_matters", "sequential_execution"],
        cognitive_operations=[CognitiveOperation.TRACE, CognitiveOperation.PREDICT],
        remediation_strategy="repeat_with_hints",
        escalation_strategy="increase_complexity",
        transfer_sensitivity=0.4,
        uncertainty_tolerance=0.3,
        mastery_threshold=0.75,
        translations={
            "en": {
                "title": "Sequence",
                "description": "Understanding that computers execute instructions in order"
            },
            "id": {
                "title": "Urutan",
                "description": "Memahami bahwa komputer mengeksekusi instruksi secara berurutan"
            }
        },
        research_metadata={
            "created_by": "handcrafted",
            "validated": True,
            "version": "1.0"
        }
    )
    registry.register_concept(sequence)
    
    # 2. Variables
    variables = ConceptNode(
        id="variables",
        canonical_name="Variables",
        concept_type=ConceptType.SKILL,
        grade_band=GradeBand.K_5,
        framework_mapping={
            "k12cs": "K12-CS-VAR-2",
            "csta": "2-AP-11"
        },
        prerequisites=["sequence"],
        supports=["conditionals", "loops", "functions"],
        transfer_edges=[],
        difficulty_progression=0.4,
        allowed_task_types=[TaskType.MCQ, TaskType.SHORT_ANSWER, TaskType.CODE_TRACE],
        misconception_profiles=["variable_assignment", "variable_update", "scope"],
        cognitive_operations=[CognitiveOperation.TRACE, CognitiveOperation.PREDICT],
        remediation_strategy="scaffolded_examples",
        escalation_strategy="increase_context",
        transfer_sensitivity=0.5,
        uncertainty_tolerance=0.3,
        mastery_threshold=0.7,
        translations={
            "en": {
                "title": "Variables",
                "description": "Storing and using named values in programs"
            },
            "id": {
                "title": "Variabel",
                "description": "Menyimpan dan menggunakan nilai bernama dalam program"
            }
        },
        research_metadata={
            "created_by": "handcrafted",
            "validated": True,
            "version": "1.0"
        }
    )
    registry.register_concept(variables)
    
    # 3. Conditionals
    conditionals = ConceptNode(
        id="conditionals",
        canonical_name="Conditionals",
        concept_type=ConceptType.SKILL,
        grade_band=GradeBand.K_5,
        framework_mapping={
            "k12cs": "K12-CS-CTRL-2",
            "csta": "2-AP-12"
        },
        prerequisites=["sequence", "variables"],
        supports=["loops", "functions"],
        transfer_edges=[],
        difficulty_progression=0.5,
        allowed_task_types=[TaskType.MCQ, TaskType.PARSONS, TaskType.CODE_TRACE],
        misconception_profiles=["boolean_logic", "branching", "nested_conditionals"],
        cognitive_operations=[CognitiveOperation.TRACE, CognitiveOperation.PREDICT, CognitiveOperation.DEBUG],
        remediation_strategy="truth_table_practice",
        escalation_strategy="increase_nesting",
        transfer_sensitivity=0.6,
        uncertainty_tolerance=0.4,
        mastery_threshold=0.7,
        translations={
            "en": {
                "title": "Conditionals",
                "description": "Making decisions in programs using if/else statements"
            },
            "id": {
                "title": "Kondisional",
                "description": "Membuat keputusan dalam program menggunakan pernyataan if/else"
            }
        },
        research_metadata={
            "created_by": "handcrafted",
            "validated": True,
            "version": "1.0"
        }
    )
    registry.register_concept(conditionals)
    
    # 4. Loops
    loops = ConceptNode(
        id="loops",
        canonical_name="Loops",
        concept_type=ConceptType.SKILL,
        grade_band=GradeBand.K_5,
        framework_mapping={
            "k12cs": "K12-CS-LOOP-2",
            "csta": "2-AP-13"
        },
        prerequisites=["sequence", "variables"],
        supports=["functions", "lists"],
        transfer_edges=[],
        difficulty_progression=0.6,
        allowed_task_types=[TaskType.MCQ, TaskType.PARSONS, TaskType.CODE_TRACE],
        misconception_profiles=["iteration", "loop_termination", "accumulation"],
        cognitive_operations=[CognitiveOperation.TRACE, CognitiveOperation.PREDICT, CognitiveOperation.DEBUG],
        remediation_strategy="step_through_execution",
        escalation_strategy="increase_complexity",
        transfer_sensitivity=0.7,
        uncertainty_tolerance=0.4,
        mastery_threshold=0.7,
        translations={
            "en": {
                "title": "Loops",
                "description": "Repeating actions using for and while loops"
            },
            "id": {
                "title": "Perulangan",
                "description": "Mengulang tindakan menggunakan for dan while loop"
            }
        },
        research_metadata={
            "created_by": "handcrafted",
            "validated": True,
            "version": "1.0"
        }
    )
    registry.register_concept(loops)
    
    # 5. Decomposition
    decomposition = ConceptNode(
        id="decomposition",
        canonical_name="Decomposition",
        concept_type=ConceptType.PRACTICE,
        grade_band=GradeBand.K_8,
        framework_mapping={
            "k12cs": "K12-CS-DECOMP-3",
            "csta": "2-AP-14"
        },
        prerequisites=["sequence", "variables"],
        supports=["functions"],
        transfer_edges=["problem_solving"],
        difficulty_progression=0.7,
        allowed_task_types=[TaskType.MCQ, TaskType.SHORT_ANSWER],
        misconception_profiles=["subproblem_breakdown", "abstraction"],
        cognitive_operations=[CognitiveOperation.DECOMPOSE, CognitiveOperation.ABSTRACT],
        remediation_strategy="guided_breakdown",
        escalation_strategy="increase_problem_size",
        transfer_sensitivity=0.8,
        uncertainty_tolerance=0.5,
        mastery_threshold=0.65,
        translations={
            "en": {
                "title": "Decomposition",
                "description": "Breaking complex problems into smaller, manageable parts"
            },
            "id": {
                "title": "Dekomposisi",
                "description": "Memecah masalah kompleks menjadi bagian-bagian yang lebih kecil dan mudah dikelola"
            }
        },
        research_metadata={
            "created_by": "handcrafted",
            "validated": True,
            "version": "1.0"
        }
    )
    registry.register_concept(decomposition)
    
    # 6. Functions
    functions = ConceptNode(
        id="functions",
        canonical_name="Functions",
        concept_type=ConceptType.SKILL,
        grade_band=GradeBand.K_8,
        framework_mapping={
            "k12cs": "K12-CS-MOD-3",
            "csta": "2-AP-15"
        },
        prerequisites=["sequence", "variables", "conditionals", "loops"],
        supports=["lists", "dictionaries"],
        transfer_edges=[],
        difficulty_progression=0.8,
        allowed_task_types=[TaskType.MCQ, TaskType.PARSONS, TaskType.DEBUG],
        misconception_profiles=["parameters", "return_values", "scope", "reusability"],
        cognitive_operations=[CognitiveOperation.TRACE, CognitiveOperation.PREDICT, CognitiveOperation.ABSTRACT],
        remediation_strategy="parameter_practice",
        escalation_strategy="increase_nesting",
        transfer_sensitivity=0.7,
        uncertainty_tolerance=0.5,
        mastery_threshold=0.65,
        translations={
            "en": {
                "title": "Functions",
                "description": "Creating reusable blocks of code with inputs and outputs"
            },
            "id": {
                "title": "Fungsi",
                "description": "Membuat blok kode yang dapat digunakan kembali dengan input dan output"
            }
        },
        research_metadata={
            "created_by": "handcrafted",
            "validated": True,
            "version": "1.0"
        }
    )
    registry.register_concept(functions)
    
    # 7. Lists
    lists = ConceptNode(
        id="lists",
        canonical_name="Lists",
        concept_type=ConceptType.SKILL,
        grade_band=GradeBand.K_8,
        framework_mapping={
            "k12cs": "K12-CS-DATA-3",
            "csta": "2-AP-16"
        },
        prerequisites=["variables", "loops"],
        supports=["functions", "dictionaries"],
        transfer_edges=[],
        difficulty_progression=0.8,
        allowed_task_types=[TaskType.MCQ, TaskType.CODE_TRACE, TaskType.DEBUG],
        misconception_profiles=["indexing", "list_operations", "iteration"],
        cognitive_operations=[CognitiveOperation.TRACE, CognitiveOperation.PREDICT],
        remediation_strategy="visual_indexing",
        escalation_strategy="increase_operations",
        transfer_sensitivity=0.6,
        uncertainty_tolerance=0.5,
        mastery_threshold=0.65,
        translations={
            "en": {
                "title": "Lists",
                "description": "Storing and manipulating collections of ordered items"
            },
            "id": {
                "title": "Daftar",
                "description": "Menyimpan dan memanipulasi kumpulan item yang terurut"
            }
        },
        research_metadata={
            "created_by": "handcrafted",
            "validated": True,
            "version": "1.0"
        }
    )
    registry.register_concept(lists)
    
    # 8. Dictionaries
    dictionaries = ConceptNode(
        id="dictionaries",
        canonical_name="Dictionaries",
        concept_type=ConceptType.SKILL,
        grade_band=GradeBand.K_8,
        framework_mapping={
            "k12cs": "K12-CS-DATA-3",
            "csta": "2-AP-17"
        },
        prerequisites=["variables", "lists"],
        supports=[],
        transfer_edges=[],
        difficulty_progression=0.9,
        allowed_task_types=[TaskType.MCQ, TaskType.CODE_TRACE, TaskType.DEBUG],
        misconception_profiles=["key_value_pairs", "lookup", "hash_collision"],
        cognitive_operations=[CognitiveOperation.TRACE, CognitiveOperation.PREDICT],
        remediation_strategy="key_value_practice",
        escalation_strategy="increase_complexity",
        transfer_sensitivity=0.6,
        uncertainty_tolerance=0.6,
        mastery_threshold=0.6,
        translations={
            "en": {
                "title": "Dictionaries",
                "description": "Storing and retrieving data using key-value pairs"
            },
            "id": {
                "title": "Kamus",
                "description": "Menyimpan dan mengambil data menggunakan pasangan kunci-nilai"
            }
        },
        research_metadata={
            "created_by": "handcrafted",
            "validated": True,
            "version": "1.0"
        }
    )
    registry.register_concept(dictionaries)
    
    # Validate registry
    errors = registry.validate_registry()
    if any(errors.values()):
        print("⚠️ Registry validation errors:")
        for error_type, error_list in errors.items():
            if error_list:
                print(f"  {error_type}: {error_list}")
    else:
        print("✅ Concept registry validated successfully")
    
    return registry


if __name__ == "__main__":
    # Initialize and test the registry
    registry = initialize_intro_python_curriculum()
    
    print("\n📊 Registry Statistics:")
    print(f"  Total concepts: {len(registry._concepts)}")
    print(f"  Total tasks: {len(registry._tasks)}")
    
    print("\n📚 Concept Overview:")
    for concept_id, concept in registry._concepts.items():
        print(f"  {concept_id}: {concept.canonical_name} (difficulty: {concept.difficulty_progression})")
        print(f"    Prerequisites: {concept.prerequisites}")
        print(f"    Supports: {concept.supports}")
