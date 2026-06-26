"""
Transfer-Aware Bandit Service

Combines multi-armed bandit decision making with DAG-based transfer learning
to provide intelligent, transfer-aware task selection.

Flow:
1. Bandit selects candidate concepts based on mastery/uncertainty
2. DAG filters candidates by transfer opportunities
3. Transfer engine calculates potential learning gain from transfer
4. Bandit re-ranks candidates with transfer bonus
5. Select best concept: mastery_gap + transfer_bonus - exploration_cost
"""

import logging
from typing import Dict, List, Any
from core.bandit.bandit import ContextualBandit

logger = logging.getLogger(__name__)


class TransferAwareBandit:
    """
    Transfer-aware bandit that combines multi-armed bandit with DAG transfer learning
    
    This service provides transfer-aware task selection by:
    - Using bandit to select candidates based on mastery/uncertainty
    - Querying DAG for transfer relationships between concepts
    - Calculating transfer bonuses from related concepts
    - Re-ranking candidates with transfer-aware scoring
    """
    
    def __init__(self, bandit: ContextualBandit, pg_store=None, transfer_engine=None):
        """
        Initialize transfer-aware bandit
        
        Args:
            bandit: Base contextual bandit for decision making
            pg_store: PostgreSQL store for DAG queries
            transfer_engine: Adaptive transfer engine for learned transfer weights
        """
        self.bandit = bandit
        self.pg_store = pg_store
        self.transfer_engine = transfer_engine
        
        # Transfer-aware parameters
        self.transfer_weight = 0.3  # Weight of transfer bonus in final score
        self.mastery_gap_weight = 0.5  # Weight of mastery gap
        self.exploration_cost_weight = 0.2  # Weight of exploration penalty
        
        logger.info("🔥 TransferAwareBandit initialized")
    
    def get_transfer_relationships(self, concept: str) -> List[Dict[str, Any]]:
        """
        Query DAG for transfer relationships for a concept
        
        Args:
            concept: Source concept
            
        Returns:
            List of transfer relationships (target_concept, transfer_weight, dependency_type, confidence)
        """
        if not self.pg_store:
            logger.warning("⚠️ No pg_store available for DAG queries")
            return []
        
        try:
            sql = """
            SELECT 
                target_concept,
                transfer_weight,
                dependency_type,
                confidence_level
            FROM concept_dependencies
            WHERE source_concept = %s
            ORDER BY transfer_weight DESC
            """
            results = self.pg_store.execute_read(sql, (concept,), fetch_all=True)
            return results if results else []
        except Exception as e:
            logger.error(f"❌ Failed to query DAG for {concept}: {e}")
            return []
    
    def calculate_transfer_bonus(self, 
                                 target_concept: str, 
                                 source_concept: str,
                                 source_mastery: float,
                                 transfer_weight: float) -> float:
        """
        Calculate transfer bonus from source to target concept
        
        Args:
            target_concept: Target concept
            source_concept: Source concept
            source_mastery: Mastery of source concept
            transfer_weight: Transfer weight from DAG
            
        Returns:
            Transfer bonus in [0, 1] range
        """
        # Use transfer engine if available for learned weights
        if self.transfer_engine:
            try:
                effective_weight = self.transfer_engine.get_effective_transfer_weight(
                    source_concept, target_concept
                )
                # Use effective weight (combines static + learned + online)
                transfer_weight = effective_weight
            except Exception as e:
                logger.warning(f"⚠️ Transfer engine failed, using static weight: {e}")
        
        # Transfer bonus = source_mastery * transfer_weight
        # High source mastery + high transfer weight = high bonus
        bonus = source_mastery * transfer_weight
        return min(1.0, max(0.0, bonus))
    
    def get_aggregate_transfer_bonus(self, 
                                    concept: str, 
                                    mastery_data: Dict[str, float]) -> float:
        """
        Calculate aggregate transfer bonus from all related concepts
        
        Args:
            concept: Target concept
            mastery_data: Current mastery data for all concepts
            
        Returns:
            Aggregate transfer bonus in [0, 1] range
        """
        # Get all transfer relationships TO this concept (reverse lookup)
        if not self.pg_store:
            return 0.0
        
        try:
            sql = """
            SELECT 
                source_concept,
                transfer_weight,
                dependency_type,
                confidence_level
            FROM concept_dependencies
            WHERE target_concept = %s
            ORDER BY transfer_weight DESC
            """
            results = self.pg_store.execute_read(sql, (concept,), fetch_all=True)
            
            if not results:
                return 0.0
            
            # Calculate aggregate bonus from all sources
            total_bonus = 0.0
            for rel in results:
                source_concept = rel['source_concept']
                transfer_weight = rel['transfer_weight']
                source_mastery = mastery_data.get(source_concept, 0.0)
                
                # Calculate individual transfer bonus with transfer engine integration
                bonus = self.calculate_transfer_bonus(concept, source_concept, source_mastery, transfer_weight)
                total_bonus += bonus
            
            # Normalize by number of sources (avoid overcounting)
            return total_bonus / len(results)
            
        except Exception as e:
            logger.error(f"❌ Failed to calculate aggregate transfer bonus for {concept}: {e}")
            return 0.0
    
    def select_transfer_aware_concept(self,
                                    user_id: str,
                                    available_concepts: List[str],
                                    mastery_data: Dict[str, float],
                                    context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Select best concept using transfer-aware bandit scoring
        
        Args:
            user_id: User identifier
            available_concepts: List of available concepts
            mastery_data: Current mastery data for all concepts
            context: Additional context for selection
            
        Returns:
            Selected concept with transfer-aware metadata
        """
        if not available_concepts:
            return None
        
        context = context or {}
        
        # Calculate transfer-aware scores for each concept
        scored_concepts = []
        for concept in available_concepts:
            mastery = mastery_data.get(concept, 0.0)
            
            # Calculate mastery gap (1 - mastery)
            mastery_gap = 1.0 - mastery
            
            # Calculate transfer bonus
            transfer_bonus = self.get_aggregate_transfer_bonus(concept, mastery_data)
            
            # Calculate exploration cost (uncertainty)
            uncertainty = 1.0 - mastery
            exploration_cost = uncertainty * 0.5  # Penalty for high uncertainty
            
            # Combined score
            score = (
                self.mastery_gap_weight * mastery_gap +
                self.transfer_weight * transfer_bonus -
                self.exploration_cost_weight * exploration_cost
            )
            
            scored_concepts.append({
                "concept": concept,
                "mastery": mastery,
                "mastery_gap": mastery_gap,
                "transfer_bonus": transfer_bonus,
                "exploration_cost": exploration_cost,
                "score": score
            })
        
        # Sort by score (highest first)
        scored_concepts.sort(key=lambda x: x["score"], reverse=True)
        
        # Select best concept
        selected = scored_concepts[0] if scored_concepts else None
        
        if selected:
            logger.info(f"🔥 TRANSFER-AWARE SELECTION: {selected['concept']} "
                       f"mastery={selected['mastery']:.3f} "
                       f"transfer_bonus={selected['transfer_bonus']:.3f} "
                       f"score={selected['score']:.3f}")
        
        return selected
    
    def get_transfer_aware_recommendation(self,
                                       user_id: str,
                                       mastery_data: Dict[str, float],
                                       context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Get transfer-aware recommendation for next concept to learn
        
        Args:
            user_id: User identifier
            mastery_data: Current mastery data for all concepts
            context: Additional context for recommendation
            
        Returns:
            Recommendation with transfer-aware metadata
        """
        available_concepts = list(mastery_data.keys())
        
        if not available_concepts:
            return {
                "recommended_concept": None,
                "reason": "no_concepts_available"
            }
        
        # Use transfer-aware selection
        selected = self.select_transfer_aware_concept(
            user_id=user_id,
            available_concepts=available_concepts,
            mastery_data=mastery_data,
            context=context
        )
        
        if not selected:
            return {
                "recommended_concept": None,
                "reason": "selection_failed"
            }
        
        # Get transfer relationships for the selected concept
        transfer_relationships = self.get_transfer_relationships(selected["concept"])
        
        return {
            "recommended_concept": selected["concept"],
            "mastery": selected["mastery"],
            "mastery_gap": selected["mastery_gap"],
            "transfer_bonus": selected["transfer_bonus"],
            "exploration_cost": selected["exploration_cost"],
            "score": selected["score"],
            "transfer_relationships": transfer_relationships,
            "recommendation_reason": "transfer_aware",
            "selection_engine": "transfer_aware_bandit"
        }
