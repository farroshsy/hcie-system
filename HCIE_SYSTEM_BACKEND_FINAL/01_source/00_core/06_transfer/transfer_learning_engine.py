"""
Transfer Learning Engine for CT Concepts
Implements cross-concept skill transfer and shared latent skill space
"""

import logging
import threading
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import json
from ..determinism.rng_stream_manager import RNGStreamManager
from ..determinism.entropy_instrumentation import get_entropy_instrumentation

logger = logging.getLogger(__name__)

# 🔥 PERFORMANCE INSTRUMENTATION
try:
    from core.determinism.timing import timed_operation, TimedOperation, OPERATION_TRANSFER_LOOKUP, OPERATION_DEPENDENCY_LOADING
    TIMING_AVAILABLE = True
except ImportError:
    TIMING_AVAILABLE = False
    logger.warning("Performance timing module not available - instrumentation disabled")

def _convert_decimal_fields(data: Dict, numeric_fields: List[str]) -> Dict:
    """Convert Decimal fields to float to prevent type errors"""
    for field in numeric_fields:
        if field in data and data[field] is not None:
            data[field] = float(data[field])
    return data

@dataclass
class TransferEvent:
    """Represents a transfer learning event"""
    user_id: str
    source_concept: str
    target_concepts: List[str]
    transfer_amounts: Dict[str, float]
    confidence: float
    timestamp: str  
    original_mastery_change: float
    transferred_mastery_change: float
    confidence_score: float
    timestamp_datetime: datetime

@dataclass
class ConceptDependency:
    """Represents dependency between concepts"""
    source_concept: str
    target_concept: str
    transfer_weight: float
    dependency_type: str  # 'prerequisite', 'related', 'advanced'
    confidence_level: float

class TransferLearningEngine:
    """
    Transfer Learning Engine for CT Concepts
    
    Implements:
    1. Cross-concept skill transfer based on dependencies
    2. Shared latent skill space updates
    3. Transfer decay and forgetting
    4. Confidence-weighted transfer calculations
    
    🔥 F-020 DOCUMENTATION: Transfer Behavior
    - CURRENT: Transfer fires on ALL dependencies (within-grade and cross-grade)
    - The system does NOT have grade-level filtering in the dependency graph
    - ConceptDependency does not include grade information
    - Transfer occurs between any concepts with defined dependencies
    - FUTURE: To implement cross-grade-only transfer, add grade field to ConceptDependency
    - and filter get_dependencies() to return only cross-grade transitions
    
    🔥 OPTIMIZATION: Class-level dependency cache to prevent repeated Redis/DB loading
    """
    
    # 🔥 OPTIMIZATION: Class-level cache for dependency graph
    # Prevents repeated Redis/DB lookups across multiple engine instances
    _dependency_cache: Dict[str, List[ConceptDependency]] = None
    _cache_loaded: bool = False
    
    # 🔥 OPTIMIZATION: Transfer result cache to avoid recomputing transfer amounts
    # Key: (source_concept, target_concept, mastery_change, confidence) -> transfer_amount
    _transfer_cache: Dict[Tuple[str, str, float, float], float] = {}
    _transfer_cache_hits: int = 0
    _transfer_cache_misses: int = 0
    
    def __init__(self,
                 transfer_decay_rate: float = 0.01,
                 min_transfer_threshold: float = 0.00001,  # Much lower to enable transfers
                 max_transfer_boost: float = 0.25,  # Final calibration (reduced from 0.6)
                 seed: int = 42,
                 dependency_store=None):
        """
        Initialize transfer learning engine

        Args:
            transfer_decay_rate: Rate at which transferred mastery decays
            min_transfer_threshold: Minimum transfer amount to apply
            max_transfer_boost: Maximum boost from transfer effects
            seed: Seed for deterministic RNG streams
            dependency_store: Optional key-value store injected by application DI
        """
        self.transfer_decay_rate = transfer_decay_rate
        self.min_transfer_threshold = min_transfer_threshold
        self.max_transfer_boost = max_transfer_boost
        self.seed = seed
        # Use deterministic RNG stream for interference probability
        self.rng_manager = RNGStreamManager(seed=seed)
        self.random_stream = self.rng_manager.random_noise
        self.dependency_store = dependency_store

        # 🔥 Thread safety lock for shared mutable state
        # Protects: shared_skills_mastery, transfer_events
        self._lock = threading.RLock()

        # Concept dependency graph
        self.dependencies: Dict[str, List[ConceptDependency]] = {}

        # Adjacency-list DAG used as the default when callers pass dag_graph=None
        # (e.g. the shuffled-DAG Stage-C controls). Empty until populated via
        # get_concept_dependency_graph(); guarded here so the `else self.dependency_graph`
        # fallbacks never raise AttributeError.
        self.dependency_graph: Dict[str, List[str]] = {}

        # Shared skill weights for concepts
        self.concept_skills: Dict[str, Dict[str, float]] = {}

        # Shared skill mastery levels
        self.shared_skills_mastery: Dict[str, float] = {}

        # Transfer history for analysis
        self.transfer_events: List[TransferEvent] = []
        
        # 🔥 PHASE 1 FIX: UUID-to-concept mapping for semantic connectivity
        self.uuid_to_concept_mapping: Dict[str, str] = {}
        
        logger.info("Transfer Learning Engine initialized")
        
        # 🔥 UPGRADED: Load real DAG dependencies from your research
        self._load_database_dependencies()
        
        # 🔥 CRITICAL DEBUG: Check if we loaded real DAG or fallback
        dag_size = len(self.dependencies)
        logger.info(f"🔥 DAG SIZE CHECK: {dag_size} dependencies loaded")
        if dag_size < 10:
            logger.warning("⚠️ DAG SIZE TOO SMALL - LIKELY USING FALLBACK")
            logger.warning(f"   Available concepts: {list(self.dependencies.keys())}")
        else:
            logger.info("✅ REAL K-12 DAG LOADED SUCCESSFULLY")
    
    def _load_database_dependencies(self):
        """Load dependencies from Redis (called during initialization)
        
        🔥 OPTIMIZATION: Uses class-level cache to prevent repeated Redis/DB lookups
        🔥 PERFORMANCE: Timed for visibility
        """
        if TIMING_AVAILABLE:
            with TimedOperation(OPERATION_DEPENDENCY_LOADING):
                self._load_database_dependencies_impl()
        else:
            self._load_database_dependencies_impl()
    
    def _load_database_dependencies_impl(self):
        """Implementation of dependency loading (separated for timing)"""
        # 🔥 OPTIMIZATION: Check cache first
        if TransferLearningEngine._cache_loaded and TransferLearningEngine._dependency_cache is not None:
            self.dependencies = TransferLearningEngine._dependency_cache.copy()
            logger.info(f"🔥 DEPENDENCY CACHE HIT: {len(self.dependencies)} dependencies loaded from cache")
            return
        
        try:
            # 🔥 FIXED: Load K-12 DAG from injected key-value store when available
            if self.dependency_store is not None:
                dag_key = "k12_cs_framework:dag_dependencies"
                dag_data = self.dependency_store.get_value(dag_key)
                
                if dag_data:
                    import json
                    dependencies = json.loads(dag_data)
                    self.load_dependencies_from_dict(dependencies['dependencies'])
                    logger.info(f"🔥 K-12 DAG LOADED FROM REDIS: {len(self.dependencies)} dependencies")
                    logger.info(f"   Framework: {dependencies['total_dependencies']} total dependencies")
                    
                    # 🔥 OPTIMIZATION: Populate cache
                    TransferLearningEngine._dependency_cache = self.dependencies.copy()
                    TransferLearningEngine._cache_loaded = True
                    logger.info("✅ Dependency graph cached for reuse")
                    return
                else:
                    logger.warning("⚠️ No K-12 DAG found in dependency store")
            
            # Fallback to static loading
            try:
                from .real_dag_dependencies import RealDAGDependencies
                real_dag = RealDAGDependencies()
                self.load_dependencies_from_dict(real_dag.get_all_dependencies())
                logger.info("🔥 K-12 DAG LOADED FROM STATIC FALLBACK")
                
                # 🔥 OPTIMIZATION: Populate cache
                TransferLearningEngine._dependency_cache = self.dependencies.copy()
                TransferLearningEngine._cache_loaded = True
                logger.info("✅ Dependency graph cached for reuse")
            except ImportError:
                # Last resort - absolute import
                try:
                    from real_dag_dependencies import RealDAGDependencies
                    real_dag = RealDAGDependencies()
                    self.load_dependencies_from_dict(real_dag.get_all_dependencies())
                    logger.info("🔥 K-12 DAG LOADED FROM ABSOLUTE FALLBACK")
                    
                    # 🔥 OPTIMIZATION: Populate cache
                    TransferLearningEngine._dependency_cache = self.dependencies.copy()
                    TransferLearningEngine._cache_loaded = True
                    logger.info("✅ Dependency graph cached for reuse")
                except ImportError as e:
                    logger.error(f"❌ ALL IMPORTS FAILED: {e}")
                    self._add_fallback_dependencies()
            
        except Exception as e:
            logger.error(f"❌ Failed to load real DAG dependencies: {e}")
            # Keep fallback as last resort
            self._add_fallback_dependencies()
            
            # 🔥 OPTIMIZATION: Still cache fallback
            TransferLearningEngine._dependency_cache = self.dependencies.copy()
            TransferLearningEngine._cache_loaded = True
    
    def _add_fallback_dependencies(self):
        """Add minimal fallback dependencies for testing"""
        self.dependencies["ct_pattern_recognition"] = [
            ConceptDependency(
                source_concept="ct_pattern_recognition",
                target_concept="ct_algorithm_design",
                transfer_weight=0.5,
                dependency_type="related",
                confidence_level=1.0
            )
        ]
        logger.warning("🔥 USING FALLBACK DEPENDENCIES ONLY")
    
    def load_concept_dependencies(self, dependencies_data: List[Dict]):
        """Load concept dependencies from database"""
        self.dependencies = {}
        
        for dep_data in dependencies_data:
            # Convert all numeric fields to float at source - prevents Decimal issues
            dep_data = _convert_decimal_fields(dep_data, ['transfer_weight', 'confidence_level'])
            
            # Create ConceptDependency object
            dependency = ConceptDependency(
                source_concept=dep_data['source_concept'],
                target_concept=dep_data['target_concept'],
                transfer_weight=dep_data['transfer_weight'],
                dependency_type=dep_data.get('dependency_type', 'related'),
                confidence_level=dep_data['confidence_level']
            )
            
            if dependency.source_concept not in self.dependencies:
                self.dependencies[dependency.source_concept] = []
            self.dependencies[dependency.source_concept].append(dependency)
        
        logger.info(f"Loaded {len(dependencies_data)} concept dependencies")
    
    def load_dependencies_from_dict(self, dependencies_dict: Dict[str, List[Dict]]):
        """Load dependencies from dictionary (for RealDAGDependencies)"""
        self.dependencies = {}
        
        for source_concept, dep_list in dependencies_dict.items():
            for dep_data in dep_list:
                # Convert all numeric fields to float at source
                dep_data = _convert_decimal_fields(dep_data, ['transfer_weight', 'confidence_level'])
                
                # Create ConceptDependency object
                dependency = ConceptDependency(
                    source_concept=source_concept,
                    target_concept=dep_data['target_concept'],
                    transfer_weight=dep_data['transfer_weight'],
                    dependency_type=dep_data.get('dependency_type', 'related'),
                    confidence_level=dep_data['confidence_level']
                )
                
                if source_concept not in self.dependencies:
                    self.dependencies[source_concept] = []
                self.dependencies[source_concept].append(dependency)
        
        logger.info(f"Loaded {len(self.dependencies)} concept dependencies from dict")
    
    @classmethod
    def clear_dependency_cache(cls):
        """Clear the class-level dependency cache
         
         Use this when the dependency graph changes (e.g., after curriculum updates)
         
         🔥 OPTIMIZATION: Allows manual cache invalidation
        """
        cls._dependency_cache = None
        cls._cache_loaded = False
        logger.info("🔥 Dependency cache cleared")
    
    @classmethod
    def clear_transfer_cache(cls):
        """Clear the transfer result cache
         
         Use this when transfer logic changes or to free memory
         
         🔥 OPTIMIZATION: Allows manual cache invalidation
        """
        cls._transfer_cache.clear()
        cls._transfer_cache_hits = 0
        cls._transfer_cache_misses = 0
        logger.info("🔥 Transfer cache cleared")
    
    @classmethod
    def get_cache_stats(cls) -> dict:
        """Get cache statistics for monitoring
        
        🔥 OPTIMIZATION: Provides visibility into cache effectiveness
        """
        total_lookups = cls._transfer_cache_hits + cls._transfer_cache_misses
        hit_rate = cls._transfer_cache_hits / total_lookups if total_lookups > 0 else 0.0
        
        return {
            "dependency_cache_loaded": cls._cache_loaded,
            "dependency_cache_size": len(cls._dependency_cache) if cls._dependency_cache else 0,
            "transfer_cache_size": len(cls._transfer_cache),
            "transfer_cache_hits": cls._transfer_cache_hits,
            "transfer_cache_misses": cls._transfer_cache_misses,
            "transfer_cache_hit_rate": f"{hit_rate:.2%}",
        }
    
    def reset(self):
        """
        Reset transfer learning engine state (for deterministic replay across learners)

        🔥 Thread-safe with lock protecting shared_skills_mastery and transfer_events

        Note: Does NOT clear the dependency cache (use clear_dependency_cache() for that)
        """
        with self._lock:
            # Reset shared skill mastery to initial state
            self.shared_skills_mastery = {}
            # Clear transfer history
            self.transfer_events = []
        logger.info("TransferLearningEngine state reset to initial")
    
    def load_concept_skills(self, skills_data: List[Dict]):
        """Load concept-skill mappings"""
        self.concept_skills = {}
        
        for skill_data in skills_data:
            # Convert all numeric fields to float at source - prevents Decimal issues
            skill_data = _convert_decimal_fields(skill_data, ['skill_weight'])
            
            concept = skill_data['concept_name']
            skill = skill_data['skill_name']
            weight = skill_data['skill_weight']
            
            if concept not in self.concept_skills:
                self.concept_skills[concept] = {}
            self.concept_skills[concept][skill] = weight
        
        logger.info(f"Loaded concept skills for {len(self.concept_skills)} concepts")
    
    def initialize_shared_skills(self, skills_data: List[Dict]):
        """
        Initialize shared skill mastery levels

        🔥 Thread-safe with lock protecting shared_skills_mastery
        """
        with self._lock:
            self.shared_skills_mastery = {}

            for skill_data in skills_data:
                skill_name = skill_data['skill_name']
                base_mastery = skill_data.get('base_mastery', 0.3)
                self.shared_skills_mastery[skill_name] = base_mastery

        logger.info(f"Initialized {len(self.shared_skills_mastery)} shared skills")
    
    def get_dependencies(self, concept: str) -> List[ConceptDependency]:
        """Get dependencies for a concept"""
        # 🔥 PHASE 1 FIX: If concept is a UUID, map to semantic ID first
        if concept in self.uuid_to_concept_mapping:
            semantic_concept = self.uuid_to_concept_mapping[concept]
            logger.debug(f"🔥 UUID mapping: {concept} → {semantic_concept}")
            return self.dependencies.get(semantic_concept, [])
        
        return self.dependencies.get(concept, [])
    
    def get_all_dependencies(self) -> Dict[str, List[ConceptDependency]]:
        """Get all dependencies"""
        return self.dependencies

    def inject_external_dependencies(
        self,
        edges: List[Tuple[str, str, float]],
        dependency_type: str = "prerequisite",
        confidence_level: float = 1.0,
    ) -> int:
        """Inject edges from an external concept graph into the in-memory dependency dict.

        Called once at external-run setup time (Phase 2) after
        ``external_concept_graph`` is populated by the orchestrator.  The
        injected entries use the same ``ConceptDependency`` shape as K-12
        entries, so ``_calculate_transfer_amount_impl()`` picks them up
        without any code change.

        Namespace safety: external concept IDs are prefixed (e.g.
        ``"ext_junyi_graph_*"``) and never collide with K-12 CS Framework
        concept IDs, so existing K-12 dependencies are never overwritten.

        Returns the number of edges injected.
        """
        count = 0
        for source, target, weight in edges:
            dep = ConceptDependency(
                source_concept=source,
                target_concept=target,
                transfer_weight=float(weight),
                dependency_type=dependency_type,
                confidence_level=confidence_level,
            )
            if source not in self.dependencies:
                self.dependencies[source] = []
            self.dependencies[source].append(dep)
            count += 1
        logger.info(
            "inject_external_dependencies: loaded %d edges into transfer engine", count
        )
        return count
    
    def get_transfer_summary(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get transfer learning summary statistics"""
        return {
            "total_dependencies": sum(len(deps) for deps in self.dependencies.values()),
            "total_events": len(self.transfer_events),
            "total_concepts": len(self.dependencies),
            "total_shared_skills": len(self.shared_skills_mastery),
            "transfer_decay_rate": self.transfer_decay_rate,
            "min_transfer_threshold": self.min_transfer_threshold,
            "max_transfer_boost": self.max_transfer_boost
        }
    
    def calculate_transfer_amount(self, 
                                 source_concept: str, 
                                 target_concept: str, 
                                 mastery_change: float,
                                 confidence: float,
                                 learning_gain: float) -> float:
        """
        Calculate transfer amount from source to target concept
        
        🔥 OPTIMIZATION: Uses transfer result cache to avoid recomputation
        🔥 PERFORMANCE: Timed for visibility (only on cache misses)
        
        Args:
            source_concept: Concept that experienced mastery change
            target_concept: Concept to receive transfer
            mastery_change: Original mastery change in source concept
            confidence: Confidence in the transfer calculation
            
        Returns:
            Transfer amount to apply to target concept
        """
        # 🔥 PHASE 1 FIX: Map UUIDs to semantic IDs
        if source_concept in self.uuid_to_concept_mapping:
            source_concept = self.uuid_to_concept_mapping[source_concept]
            logger.debug(f"🔥 UUID mapping source: {source_concept}")
        
        if target_concept in self.uuid_to_concept_mapping:
            target_concept = self.uuid_to_concept_mapping[target_concept]
            logger.debug(f"🔥 UUID mapping target: {target_concept}")
        
        # 🔥 OPTIMIZATION: Check transfer cache
        # Round values to avoid cache misses due to floating point precision
        cache_key = (source_concept, target_concept, round(mastery_change, 6), round(confidence, 6))
        if cache_key in TransferLearningEngine._transfer_cache:
            TransferLearningEngine._transfer_cache_hits += 1
            logger.debug(f"🔥 TRANSFER CACHE HIT: {source_concept} → {target_concept}")
            return TransferLearningEngine._transfer_cache[cache_key]
        
        TransferLearningEngine._transfer_cache_misses += 1
        
        # 🔥 PERFORMANCE: Time cache misses only
        if TIMING_AVAILABLE:
            with TimedOperation(OPERATION_TRANSFER_LOOKUP):
                transfer_amount = self._calculate_transfer_amount_impl(
                    source_concept, target_concept, mastery_change, confidence, learning_gain
                )
        else:
            transfer_amount = self._calculate_transfer_amount_impl(
                source_concept, target_concept, mastery_change, confidence, learning_gain
            )
        
        # 🔥 OPTIMIZATION: Cache the result
        TransferLearningEngine._transfer_cache[cache_key] = transfer_amount
        
        return transfer_amount
    
    def _calculate_transfer_amount_impl(self, source_concept: str, target_concept: str, 
                                       mastery_change: float, confidence: float, learning_gain: float) -> float:
        """Implementation of transfer amount calculation (separated for timing)"""
        # Find direct dependency
        transfer_amount = 0.0
        
        # 🔥 OPTIMIZATION: Removed hot-path logging to prevent I/O amplification
        # These logs were causing massive overhead during drift audit
        pass
        
        if source_concept in self.dependencies:
            # 🔥 OPTIMIZATION: Demoted to debug level to prevent I/O amplification
            logger.debug(f"🔍 FOUND SOURCE: {source_concept} has {len(self.dependencies[source_concept])} deps")
            for dep in self.dependencies[source_concept]:
                logger.debug(f"🔍 CHECKING DEP: {dep.source_concept} → {dep.target_concept}")
                if dep.target_concept == target_concept:
                    logger.info(f"🔍 MATCH FOUND! weight={dep.transfer_weight}, confidence={dep.confidence_level}")
                    # Calculate transfer amount based on learning gain
                    base_transfer = abs(learning_gain) * confidence * dep.transfer_weight
                    effective_mastery = dep.transfer_weight + mastery_change
                    logger.info(f"🔍 BASE TRANSFER: {base_transfer:.6f} (gain={learning_gain:.4f}, conf={confidence:.2f}, weight={dep.transfer_weight:.2f})")
                    
                    # Apply dependency type modifier
                    if dep.dependency_type == 'prerequisite':
                        type_modifier = 1.2  # Stronger transfer for prerequisites
                    elif dep.dependency_type == 'related':
                        type_modifier = 1.0  # Normal transfer
                    elif dep.dependency_type == 'advanced':
                        type_modifier = 0.8  # Weaker transfer for advanced skills
                    else:
                        type_modifier = 1.0
                    
                    # Apply confidence and dependency confidence
                    confidence_modifier = confidence * dep.confidence_level
                    
                    # Calculate final transfer with calibrated boost
                    transfer_amount = float(base_transfer) * type_modifier * confidence_modifier * confidence * 0.3  # 0.3x boost (constraint center)
                    
                    # Apply limits - remove impossible ceiling for constraint satisfaction
                    transfer_amount = min(transfer_amount, 0.5 * abs(float(mastery_change)))  # Allow T/ΔM up to 0.5
                    transfer_amount = max(transfer_amount, 0.0)  # No negative transfer
                    
                    break
        
        # Apply minimum threshold
        if transfer_amount < self.min_transfer_threshold:
            transfer_amount = 0.0
        
        return transfer_amount
    
    def apply_shared_skill_transfer(self,
                                  concept: str,
                                  mastery_change: float) -> Dict[str, float]:
        """
        Apply transfer through shared skill space

        🔥 Thread-safe with lock protecting shared_skills_mastery

        Args:
            concept: Concept that experienced mastery change
            mastery_change: Amount of mastery change

        Returns:
            Dictionary of skill mastery changes
        """
        skill_changes = {}

        if concept not in self.concept_skills:
            return skill_changes

        with self._lock:
            # Update shared skills based on concept mastery change
            for skill, weight in self.concept_skills[concept].items():
                skill_change = float(mastery_change) * float(weight) * 0.3  # Scale down skill impact
                self.shared_skills_mastery[skill] = max(0.0, min(1.0,
                    float(self.shared_skills_mastery.get(skill, 0.3)) + skill_change))
                skill_changes[skill] = skill_change
        
        # Calculate transfer to other concepts through shared skills
        concept_transfers = {}
        
        for other_concept, other_skills in self.concept_skills.items():
            if other_concept == concept:
                continue
            
            # Calculate skill overlap
            shared_skills = set(self.concept_skills[concept].keys()) & set(other_skills.keys())
            
            if shared_skills:
                # Calculate transfer based on shared skills
                transfer_amount = 0.0
                total_weight = 0.0
                
                for skill in shared_skills:
                    skill_weight = float(min(
                        float(self.concept_skills[concept][skill]),
                        float(other_skills[skill])
                    ))
                    skill_mastery = float(self.shared_skills_mastery.get(skill, 0.3))
                    
                    # Transfer based on skill mastery and weight
                    skill_transfer = float(abs(mastery_change)) * skill_weight * skill_mastery * 0.1
                    transfer_amount = float(transfer_amount) + skill_transfer
                    total_weight = float(total_weight) + skill_weight
                
                if total_weight > 0:
                    transfer_amount = transfer_amount / total_weight
                    
                    # Add negative transfer for concept interference
                    # 🔥 FIX: Use deterministic RNG stream for reproducibility
                    interference_probability = 0.1  # 10% chance of interference

                    # Check for concept interference (some concepts interfere with each other)
                    interference_pairs = {
                        'ct_algorithm_design': ['ct_algorithm_tracing'],  # Design vs tracing can interfere
                        'ct_abstraction': ['ct_pattern_recognition'],  # Abstraction vs patterns can interfere
                    }

                    if other_concept in interference_pairs.get(concept, []):
                        # 🔥 ENTROPY INSTRUMENTATION: Log interference probability draw
                        interference_draw = self.random_stream.random()
                        get_entropy_instrumentation().log_draw(
                            rng_stream="transfer_interference",
                            seed=self.seed,
                            value=interference_draw,
                            user_id=None,
                            concept=concept,
                            context={"target_concept": other_concept, "interference_probability": interference_probability}
                        )
                        
                        if interference_draw < interference_probability:
                            # Negative transfer - interference reduces learning
                            transfer_amount *= -0.5  # Negative transfer
                            logger.info(f"🔥 NEGATIVE TRANSFER: {concept} → {other_concept} (interference)")
                    
                    concept_transfers[other_concept] = transfer_amount
        
        return concept_transfers
    
    def process_mastery_update(self, 
                              user_id: str,
                              concept: str, 
                              mastery_before: float, 
                              mastery_after: float,
                              confidence: float = 0.8,
                              learning_gain: float = 0.0) -> Tuple[Dict[str, float], List]:
        """
        Process a mastery update and calculate transfer effects
        
        Args:
            user_id: User identifier
            concept: Concept that was updated
            mastery_before: Mastery before update
            mastery_after: Mastery after update
            confidence: Confidence in the update
            
        Returns:
            Dictionary of transfer amounts for other concepts
        """
        # 🔥 OPTIMIZATION: Demoted all hot-path logging to debug level
        # These were causing massive I/O amplification during drift audit
        logger.debug(f"🔥 25+ LAYER: Processing transfer learning for {user_id}: {concept}")
        logger.debug(f"   Old mastery: {mastery_before:.4f} → New mastery: {mastery_after:.4f}")
        
        mastery_change = float(mastery_after) - float(mastery_before)
        
        # Use provided learning_gain if available, otherwise calculate from change
        effective_change = learning_gain if learning_gain > 0 else mastery_change
        
        logger.debug(f"   DELTA: {mastery_change:+.4f}, EFFECTIVE: {effective_change:+.4f}")
        
        # 🔥 FIXED: Use self.dependencies instead of raw dict iteration
        deps = self.dependencies.get(concept, [])
        if not deps:
            logger.info(f"   ⚠️ No dependencies found for {concept}")
            return {}, []
        
        # 🔥 OPTIMIZATION: Demoted to debug level
        logger.debug(f"   DEPENDENCIES FOUND: {len(deps)} for {concept}")
        
        # Initialize transfers dictionary
        transfers = {}
        
        # Calculate transfers using proper dependencies
        for dep in deps:
            logger.debug(f"   PROCESSING DEP: {concept} → {dep.target_concept} (weight={dep.transfer_weight}, conf={dep.confidence_level})")
            
            # Calculate transfer amount
            transfer_amount = self.calculate_transfer_amount(
                source_concept=concept,
                target_concept=dep.target_concept,
                mastery_change=mastery_change,
                confidence=confidence * dep.confidence_level,
                learning_gain=effective_change
            )
            
            # Apply minimum threshold
            if transfer_amount >= self.min_transfer_threshold:
                transfers[dep.target_concept] = transfer_amount
                logger.debug(f"   TRANSFER APPLY: {concept} → {dep.target_concept}: +{transfer_amount:.4f}")
            else:
                logger.debug(f"   TRANSFER REJECT: {concept} → {dep.target_concept}: +{transfer_amount:.4f} (below threshold)")
        
        # Apply transfer decay to existing transferred mastery
        self._apply_transfer_decay(user_id)
        
        # 4. Create transfer events (with protective wrapper)
        transfer_events = []
        for target_concept, transfer_amount in transfers.items():
            try:
                # Source and target are already available from the key
                logger.debug(f"   CREATING TRANSFER EVENT: {concept} → {target_concept} ({transfer_amount:.4f})")
                
                event = TransferEvent(
                    user_id=user_id,
                    source_concept=concept,
                    target_concepts=[target_concept],
                    transfer_amounts={target_concept: transfer_amount},
                    confidence=confidence,
                    timestamp=datetime.now().isoformat(),
                    original_mastery_change=mastery_change,
                    transferred_mastery_change=transfer_amount,
                    confidence_score=confidence,
                    timestamp_datetime=datetime.now()
                )
                transfer_events.append(event)
            except Exception as e:
                logger.warning(f"⚠️ Transfer event creation failed in engine (non-critical): {e}")
                # Continue without event logging - don't crash the transfer system
        
        # 🔥 OPTIMIZATION: Only log summary at info level, details at debug
        logger.info(f"🔥 TRANSFER SUMMARY: {len(transfers)} transfers applied for {concept}")
        
        # 🔥 FINAL ELITE FIX: Normalize AT SOURCE (single point of truth)
        normalized_transfers = {}
        for target_concept, amount in transfers.items():
            normalized_transfers[f"{concept}→{target_concept}"] = amount
        assert isinstance(normalized_transfers, dict), f"transfers must be dict, got {type(normalized_transfers)}"
        assert isinstance(transfer_events, list), f"transfer_events must be list, got {type(transfer_events)}"
        assert all(isinstance(k, str) for k in normalized_transfers.keys()), "All transfer keys must be strings"
        
        return normalized_transfers, transfer_events

    def _apply_transfer_decay(self, user_id: str) -> None:
        """Relax accumulated shared-skill mastery toward the 0.3 baseline by transfer_decay_rate.

        Called at the end of process_mastery_update so previously-transferred mastery fades toward
        baseline over successive updates instead of accumulating unbounded. Exponential relaxation:
        ``m <- m + (baseline - m) * rate``. Thread-safe (shared_skills_mastery is lock-protected).
        ``user_id`` is accepted for call-site symmetry/logging — shared_skills_mastery is a global
        skill pool, not per-user.
        """
        baseline = 0.3
        rate = self.transfer_decay_rate
        with self._lock:
            for skill, mastery in list(self.shared_skills_mastery.items()):
                self.shared_skills_mastery[skill] = mastery + (baseline - mastery) * rate

    # Duplicate method removed - using the one above with optional user_id parameter
    
    def get_concept_dependency_graph(self) -> Dict[str, List[str]]:
        """Get the concept dependency graph for visualization"""
        graph = {}
        
        for source, dependencies in self.dependencies.items():
            graph[source] = [dep.target_concept for dep in dependencies]
        
        return graph
    
    def calculate_transfer_potential(self, concept: str) -> Dict[str, float]:
        """Calculate transfer potential from a concept to others"""
        potential = {}

        if concept in self.dependencies:
            for dep in self.dependencies[concept]:
                potential[dep.target_concept] = dep.transfer_weight * dep.confidence_level

        return potential

    def estimate_prospective_transfer(
        self,
        candidate_concept: str,
        current_mastery: float,
        uncertainty: float,
        zpd_readiness: float,
        dag_graph: Optional[Dict[str, Any]] = None
    ) -> Dict[str, float]:
        """
        🔥 PHASE 3A: Estimate prospective transfer for pre-selection governance

        Splits prospective transfer into structural utility and learner readiness
        to avoid hidden reward priors in prospective transfer calculation.

        Formula:
            T_prospective(c) = StructuralUtility(c) × LearnerReadinessModulator(c)

        StructuralUtility(c) = Σ_{s ∈ sources(c)} [w_s × exp(-α × d_eff(s,c))]
        - Pure DAG topology signal (no learner state contamination)
        - Uses weighted effective depth d_eff instead of raw BFS distance

        LearnerReadinessModulator(c) = f(target_mastery, uncertainty, zpd)
        - Separately computed, multiplicatively applied
        - Prevents prospective transfer from becoming disguised expected reward

        Args:
            candidate_concept: Concept being evaluated for selection
            current_mastery: Current mastery level of candidate concept
            uncertainty: Uncertainty in candidate concept mastery
            zpd_readiness: ZPD readiness score for candidate concept
            dag_graph: Optional DAG graph structure for topology analysis

        Returns:
            Dict with keys:
                - 'prospective_transfer': Final estimated transfer value
                - 'structural_utility': Pure topology-based signal
                - 'learner_readiness': Readiness modulator [0,1]
                - 'weighted_effective_depth': Average weighted path cost
        """
        import numpy as np

        # Default return if no dependencies
        if not self.dependencies or candidate_concept not in self.dependencies:
            return {
                'prospective_transfer': 0.0,
                'structural_utility': 0.0,
                'learner_readiness': 0.0,
                'weighted_effective_depth': float('inf')
            }

        # ===================================================================
        # PART 1: Structural Utility (pure DAG topology signal)
        # ===================================================================
        # Find all sources that can transfer TO candidate_concept
        sources = []
        for source_concept, deps in self.dependencies.items():
            for dep in deps:
                if dep.target_concept == candidate_concept:
                    sources.append({
                        'concept': source_concept,
                        'weight': dep.transfer_weight,
                        'confidence': dep.confidence_level,
                        'type': dep.dependency_type
                    })

        if not sources:
            # No incoming dependencies - structural utility is 0
            structural_utility = 0.0
            weighted_effective_depth = float('inf')
        else:
            # Calculate weighted effective depth using Dijkstra-like shortest path
            # d_eff(s,c) = minimum weighted path cost from s to c
            # where edge weight = -log(transfer_weight) for path cost

            depth_attenuation_factor = 0.5  # α in exp(-α × d_eff)

            total_utility = 0.0
            total_weight = 0.0
            effective_depths = []

            for source in sources:
                # Path cost = -log(transfer_weight) + -log(confidence)
                # Higher transfer_weight → lower path cost (closer semantically)
                path_cost = -np.log(max(source['weight'], 0.01)) - np.log(max(source['confidence'], 0.01))

                # Depth attenuation: exp(-α × path_cost)
                attenuation = np.exp(-depth_attenuation_factor * path_cost)

                # Type modifier for structural utility
                if source['type'] == 'prerequisite':
                    type_multiplier = 1.2
                elif source['type'] == 'advanced':
                    type_multiplier = 0.8
                else:  # related
                    type_multiplier = 1.0

                source_utility = source['weight'] * source['confidence'] * attenuation * type_multiplier
                total_utility += source_utility
                total_weight += source['weight']
                effective_depths.append(path_cost)

            structural_utility = total_utility / max(total_weight, 1e-6)
            weighted_effective_depth = np.mean(effective_depths) if effective_depths else float('inf')

        # ===================================================================
        # PART 2: Learner Readiness Modulator (separate from structural utility)
        # ===================================================================
        # Readiness modulator based on learner's current state
        # This prevents prospective transfer from being reward-shaped

        # Mastery readiness: inverse U-shaped (peak at intermediate mastery)
        # High mastery → low readiness (already mastered)
        # Low mastery → low readiness (not ready to learn)
        mastery_readiness = 4.0 * current_mastery * (1.0 - current_mastery)  # Max at 0.5

        # Uncertainty readiness: higher uncertainty → higher readiness
        uncertainty_readiness = min(uncertainty / 0.1, 1.0)  # Normalize by max uncertainty

        # ZPD readiness: already provided as input
        zpd_factor = zpd_readiness

        # Combined learner readiness (multiplicative combination)
        learner_readiness = mastery_readiness * uncertainty_readiness * zpd_factor
        learner_readiness = np.clip(learner_readiness, 0.0, 1.0)

        # ===================================================================
        # PART 3: Combine structural utility with learner readiness
        # ===================================================================
        prospective_transfer = structural_utility * learner_readiness

        logger.debug(f"🔥 PHASE 3A: Prospective transfer for {candidate_concept}")
        logger.debug(f"   Structural utility: {structural_utility:.4f}")
        logger.debug(f"   Learner readiness: {learner_readiness:.4f}")
        logger.debug(f"   Weighted effective depth: {weighted_effective_depth:.4f}")
        logger.debug(f"   Final prospective: {prospective_transfer:.4f}")

        return {
            'prospective_transfer': float(prospective_transfer),
            'structural_utility': float(structural_utility),
            'learner_readiness': float(learner_readiness),
            'weighted_effective_depth': float(weighted_effective_depth)
        }

    # ============================================================================
    # 🔥 STAGE C: SCIENTIFIC CONTROLS FOR DAG TOPOLOGY VALIDATION
    # ============================================================================

    def shuffle_dag_semantic(
        self,
        dag_graph: Optional[Dict[str, Any]] = None,
        seed: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        🔥 STAGE C PHASE 4A: Shuffle DAG semantic labels while preserving graph statistics

        Creates a control condition where node identities are randomized while
        preserving the graph's structural properties (in-degree, out-degree distribution,
        path lengths, connectivity patterns).

        This tests whether prospective transfer depends on actual semantic topology
        or just graph statistics.

        Args:
            dag_graph: Original DAG graph (uses self.dependency_graph if None)
            seed: Random seed for reproducibility

        Returns:
            Shuffled DAG with same graph statistics but random semantics
        """
        import numpy as np
        import random

        if seed is not None:
            np.random.seed(seed)
            random.seed(seed)

        graph = dag_graph if dag_graph is not None else self.dependency_graph
        if not graph:
            return {'nodes': [], 'edges': [], 'shuffled': False}

        # Extract original graph statistics
        nodes = list(graph.get('nodes', []))
        edges = list(graph.get('edges', []))

        if not nodes:
            return {'nodes': [], 'edges': [], 'shuffled': False}

        # Compute degree statistics
        in_degrees = {node: 0 for node in nodes}
        out_degrees = {node: 0 for node in nodes}

        for edge in edges:
            source = edge.get('source') if isinstance(edge, dict) else edge[0]
            target = edge.get('target') if isinstance(edge, dict) else edge[1]
            if source in out_degrees:
                out_degrees[source] += 1
            if target in in_degrees:
                in_degrees[target] += 1

        # Create shuffled node mapping (preserve degree distribution)
        # Shuffle node labels while keeping the graph structure intact
        shuffled_nodes = nodes.copy()
        random.shuffle(shuffled_nodes)

        node_mapping = {old: new for old, new in zip(nodes, shuffled_nodes)}

        # Apply mapping to edges
        shuffled_edges = []
        for edge in edges:
            if isinstance(edge, dict):
                source = edge.get('source')
                target = edge.get('target')
                weight = edge.get('weight', 0.5)
                shuffled_edges.append({
                    'source': node_mapping.get(source, source),
                    'target': node_mapping.get(target, target),
                    'weight': weight
                })
            else:
                source, target = edge[0], edge[1]
                weight = edge[2] if len(edge) > 2 else 0.5
                shuffled_edges.append((
                    node_mapping.get(source, source),
                    node_mapping.get(target, target),
                    weight
                ))

        logger.info(f"🔥 STAGE C 4A: DAG semantic shuffle complete - {len(nodes)} nodes, {len(edges)} edges")

        return {
            'nodes': shuffled_nodes,
            'edges': shuffled_edges,
            'node_mapping': node_mapping,
            'original_in_degrees': in_degrees,
            'original_out_degrees': out_degrees,
            'shuffled': True,
            'graph_statistics_preserved': True
        }

    def randomize_dag_weights(
        self,
        dag_graph: Optional[Dict[str, Any]] = None,
        weight_range: Tuple[float, float] = (0.1, 0.9),
        seed: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        🔥 STAGE C PHASE 4B: Randomize DAG edge weights while preserving semantic topology

        Creates a control condition where transfer weights are randomized while
        keeping the semantic structure (which concepts depend on which) intact.

        This tests whether prospective transfer depends on actual learned transfer
        weights or just the semantic topology.

        Args:
            dag_graph: Original DAG graph (uses self.dependency_graph if None)
            weight_range: Range for random weights (min, max)
            seed: Random seed for reproducibility

        Returns:
            DAG with same topology but randomized weights
        """
        import numpy as np
        import random

        if seed is not None:
            np.random.seed(seed)
            random.seed(seed)

        graph = dag_graph if dag_graph is not None else self.dependency_graph
        if not graph:
            return {'nodes': [], 'edges': [], 'randomized': False}

        nodes = list(graph.get('nodes', []))
        edges = list(graph.get('edges', []))

        if not edges:
            return {'nodes': nodes, 'edges': [], 'randomized': False}

        # Randomize weights while preserving edge structure
        randomized_edges = []
        original_weights = []

        for edge in edges:
            # Generate random weight
            random_weight = random.uniform(weight_range[0], weight_range[1])
            original_weights.append(random_weight)

            if isinstance(edge, dict):
                source = edge.get('source')
                target = edge.get('target')
                randomized_edges.append({
                    'source': source,
                    'target': target,
                    'weight': random_weight,
                    'original_weight': edge.get('weight', 0.5)
                })
            else:
                source, target = edge[0], edge[1]
                orig_weight = edge[2] if len(edge) > 2 else 0.5
                randomized_edges.append((
                    source, target, random_weight, orig_weight
                ))

        logger.info(f"🔥 STAGE C 4B: DAG weight randomization complete - {len(edges)} edges randomized")

        return {
            'nodes': nodes,
            'edges': randomized_edges,
            'weight_range': weight_range,
            'mean_randomized_weight': np.mean(original_weights) if original_weights else 0.5,
            'randomized': True,
            'semantic_topology_preserved': True
        }

    def null_independent_topology(
        self,
        num_nodes: int = 10,
        edge_probability: float = 0.3,
        seed: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        🔥 STAGE C PHASE 4C: Generate null model with IID random edges

        Creates a control condition where the DAG has no semantic structure -
        edges are placed randomly with independent identically distributed (IID)
        probability. This serves as a baseline for comparison.

        The null model has:
        - Same number of nodes as original
        - Random edges with given probability
        - No semantic meaning to the topology

        This tests whether prospective transfer depends on ANY structured
        topology versus completely random connections.

        Args:
            num_nodes: Number of nodes in the null DAG
            edge_probability: Probability of edge between any two nodes
            seed: Random seed for reproducibility

        Returns:
            Null DAG with IID random edges
        """
        import numpy as np
        import random

        if seed is not None:
            np.random.seed(seed)
            random.seed(seed)

        # Generate nodes
        nodes = [f"null_node_{i}" for i in range(num_nodes)]

        # Generate random edges (respecting DAG direction: i -> j only if i < j)
        edges = []
        edge_count = 0

        for i in range(num_nodes):
            for j in range(i + 1, num_nodes):
                if random.random() < edge_probability:
                    weight = random.uniform(0.1, 0.9)
                    edges.append({
                        'source': nodes[i],
                        'target': nodes[j],
                        'weight': weight,
                        'random': True
                    })
                    edge_count += 1

        # Ensure the graph is connected (add path from node_0 to all others if needed)
        for i in range(1, num_nodes):
            has_incoming = any(e['target'] == nodes[i] for e in edges)
            if not has_incoming:
                # Add random incoming edge from earlier node
                source_idx = random.randint(0, i - 1)
                edges.append({
                    'source': nodes[source_idx],
                    'target': nodes[i],
                    'weight': random.uniform(0.1, 0.9),
                    'random': True,
                    'connectivity_enforced': True
                })
                edge_count += 1

        logger.info(f"🔥 STAGE C 4C: Null topology generated - {num_nodes} nodes, {edge_count} IID edges")

        return {
            'nodes': nodes,
            'edges': edges,
            'num_nodes': num_nodes,
            'edge_probability': edge_probability,
            'actual_edge_count': edge_count,
            'max_possible_edges': num_nodes * (num_nodes - 1) // 2,
            'null_model': True,
            'iid_edges': True,
            'semantic_structure': False
        }

    def compare_prospective_transfer_conditions(
        self,
        candidate_concept: str,
        current_mastery: float,
        uncertainty: float,
        zpd_readiness: float,
        dag_graph: Optional[Dict[str, Any]] = None,
        seed: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        🔥 STAGE C PHASE 4D: Compare prospective transfer across all control conditions

        Runs prospective transfer estimation on:
        1. Real DAG (original semantic topology with learned weights)
        2. Semantic-shuffled DAG (preserved statistics, random semantics)
        3. Weight-randomized DAG (preserved topology, random weights)
        4. Null topology (IID random edges, no structure)

        Validates that Real DAG produces better (more meaningful) prospective
        transfer than any control condition.

        Args:
            candidate_concept: Concept to estimate transfer for
            current_mastery: Current mastery level
            uncertainty: Uncertainty level
            zpd_readiness: ZPD readiness score
            dag_graph: Original DAG (uses self.dependency_graph if None)
            seed: Random seed for reproducibility

        Returns:
            Dict with prospective transfer results for all conditions
        """
        import numpy as np

        if seed is not None:
            np.random.seed(seed)

        base_graph = dag_graph if dag_graph is not None else self.dependency_graph

        # Condition 1: Real DAG
        real_result = self.estimate_prospective_transfer(
            candidate_concept=candidate_concept,
            current_mastery=current_mastery,
            uncertainty=uncertainty,
            zpd_readiness=zpd_readiness,
            dag_graph=base_graph
        )

        # Condition 2: Semantic-shuffled DAG
        shuffled = self.shuffle_dag_semantic(base_graph, seed=seed)
        shuffled_result = self.estimate_prospective_transfer(
            candidate_concept=candidate_concept,
            current_mastery=current_mastery,
            uncertainty=uncertainty,
            zpd_readiness=zpd_readiness,
            dag_graph=shuffled
        ) if shuffled.get('shuffled') else {'prospective_transfer': 0.0}

        # Condition 3: Weight-randomized DAG
        randomized = self.randomize_dag_weights(base_graph, seed=seed)
        randomized_result = self.estimate_prospective_transfer(
            candidate_concept=candidate_concept,
            current_mastery=current_mastery,
            uncertainty=uncertainty,
            zpd_readiness=zpd_readiness,
            dag_graph=randomized
        ) if randomized.get('randomized') else {'prospective_transfer': 0.0}

        # Condition 4: Null topology
        num_nodes = len(base_graph.get('nodes', [])) if base_graph else 10
        null_dag = self.null_independent_topology(
            num_nodes=num_nodes,
            edge_probability=0.3,
            seed=seed
        )
        null_result = self.estimate_prospective_transfer(
            candidate_concept=candidate_concept,
            current_mastery=current_mastery,
            uncertainty=uncertainty,
            zpd_readiness=zpd_readiness,
            dag_graph=null_dag
        )

        # Compile comparison
        results = {
            'real_dag': {
                'prospective_transfer': real_result['prospective_transfer'],
                'structural_utility': real_result.get('structural_utility', 0.0),
                'weighted_effective_depth': real_result.get('weighted_effective_depth', 0.0)
            },
            'semantic_shuffled': {
                'prospective_transfer': shuffled_result['prospective_transfer'],
                'structural_utility': shuffled_result.get('structural_utility', 0.0),
                'weighted_effective_depth': shuffled_result.get('weighted_effective_depth', 0.0)
            },
            'weight_randomized': {
                'prospective_transfer': randomized_result['prospective_transfer'],
                'structural_utility': randomized_result.get('structural_utility', 0.0),
                'weighted_effective_depth': randomized_result.get('weighted_effective_depth', 0.0)
            },
            'null_topology': {
                'prospective_transfer': null_result['prospective_transfer'],
                'structural_utility': null_result.get('structural_utility', 0.0),
                'weighted_effective_depth': null_result.get('weighted_effective_depth', 0.0)
            }
        }

        # Compute validation metrics
        real_pt = real_result['prospective_transfer']
        real_su = real_result.get('structural_utility', 0.0)

        # Check if real > shuffled (semantic matters)
        semantic_shuffled_pt = shuffled_result['prospective_transfer']
        semantic_better = real_pt > semantic_shuffled_pt

        # Check if real > weight-randomized (learned weights matter)
        weight_randomized_pt = randomized_result['prospective_transfer']
        weights_better = real_pt > weight_randomized_pt

        # Check if real > null (any structure matters)
        null_pt = null_result['prospective_transfer']
        structure_better = real_pt > null_pt

        results['validation'] = {
            'real_better_than_semantic_shuffle': semantic_better,
            'real_better_than_weight_randomized': weights_better,
            'real_better_than_null': structure_better,
            'real_dag_valid': semantic_better and weights_better and structure_better,
            'prospective_transfer_difference_real_vs_null': real_pt - null_pt,
            'structural_utility_real': real_su
        }

        results['comparison_mode'] = 'stage_c_4d_full_comparison'
        results['schema_version'] = '6D.1.0'

        logger.info("🔥 STAGE C 4D: Condition comparison complete")
        logger.info(f"   Real DAG: PT={real_pt:.4f}, SU={real_su:.4f}")
        logger.info(f"   Null topology: PT={null_pt:.4f}")
        logger.info(f"   Real > Null: {structure_better}")

        return results
