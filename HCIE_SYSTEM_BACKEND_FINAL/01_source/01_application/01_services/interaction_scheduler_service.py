"""
Interaction Scheduler Service

Separate service for controlling interaction timelines, difficulty schedules, and concept sequences.
Provides API endpoints for schedule creation and management as specified in EXPERIMENT_INFRASTRUCTURE_DESIGN.md.

Design Principles:
- Separate service (not integrated into existing code)
- Provides REST API for schedule control
- Uses existing interaction_scheduler functions
- Supports multiple schedule types
- Deterministic replay via seed
"""

from typing import Dict, Any, List
from datetime import datetime
import logging
import random
import numpy as np

from infrastructure.experiment.interaction_scheduler import (
    sigmoid,
    compute_correctness_probability
)

logger = logging.getLogger(__name__)


class InteractionSchedulerService:
    """
    Service for interaction scheduling with API interface
    
    RESPONSIBILITIES:
    - Provide REST API for schedule creation
    - Control difficulty schedules (adaptive, fixed, progressive, random)
    - Control concept sequences (curriculum-based, transfer-test, random)
    - Support forgetting injections
    - Support stochastic learner behavior
    - Timeline control (spacing, interleaving, blocking)
    """
    
    def __init__(self):
        """Initialize interaction scheduler service"""
        self.active_schedules: Dict[str, Dict[str, Any]] = {}
    
    def create_schedule(
        self,
        schedule_id: str,
        difficulty_schedule: Dict[str, Any],
        concept_sequence: Dict[str, Any],
        forgetting_injections: List[Dict[str, Any]] = None,
        stochastic_behavior: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Create an interaction schedule
        
        API: POST /experiments/schedule/create
        
        Args:
            schedule_id: Schedule identifier
            difficulty_schedule: Difficulty schedule configuration
            concept_sequence: Concept sequence configuration
            forgetting_injections: List of forgetting injection points
            stochastic_behavior: Stochastic behavior configuration
            
        Returns:
            Schedule creation response with schedule_id
        """
        try:
            # Validate inputs
            self._validate_difficulty_schedule(difficulty_schedule)
            self._validate_concept_sequence(concept_sequence)
            
            # Generate schedule
            schedule = {
                "schedule_id": schedule_id,
                "difficulty_schedule": difficulty_schedule,
                "concept_sequence": concept_sequence,
                "forgetting_injections": forgetting_injections or [],
                "stochastic_behavior": stochastic_behavior or {},
                "created_at": datetime.now().isoformat(),
                "status": "active"
            }
            
            # Store schedule
            self.active_schedules[schedule_id] = schedule
            
            logger.info(f"Schedule {schedule_id} created successfully")
            
            return {
                "schedule_id": schedule_id,
                "status": "created",
                "created_at": schedule["created_at"]
            }
            
        except Exception as e:
            logger.error(f"Failed to create schedule {schedule_id}: {e}")
            raise
    
    def get_schedule(self, schedule_id: str) -> Dict[str, Any]:
        """
        Get schedule details
        
        Args:
            schedule_id: Schedule identifier
            
        Returns:
            Schedule details
        """
        if schedule_id not in self.active_schedules:
            raise ValueError(f"Schedule {schedule_id} not found")
        
        return self.active_schedules[schedule_id]
    
    def generate_interaction_sequence(
        self,
        schedule_id: str,
        num_interactions: int,
        seed: int = None
    ) -> List[Dict[str, Any]]:
        """
        Generate interaction sequence based on schedule
        
        Args:
            schedule_id: Schedule identifier
            num_interactions: Number of interactions to generate
            seed: Random seed for reproducibility
            
        Returns:
            List of interaction configurations
        """
        try:
            if schedule_id not in self.active_schedules:
                raise ValueError(f"Schedule {schedule_id} not found")
            
            schedule = self.active_schedules[schedule_id]
            
            # Set seed for reproducibility
            if seed is not None:
                random.seed(seed)
                np.random.seed(seed)
            
            interactions = []
            
            for i in range(num_interactions):
                # Generate difficulty based on schedule
                difficulty = self._generate_difficulty(
                    schedule["difficulty_schedule"],
                    i,
                    num_interactions
                )
                
                # Generate concept based on sequence
                concept = self._generate_concept(
                    schedule["concept_sequence"],
                    i,
                    num_interactions
                )
                
                # Apply forgetting injection if applicable
                forgetting_rate = self._get_forgetting_rate(
                    schedule["forgetting_injections"],
                    i
                )
                
                # Apply stochastic behavior
                response_time_variability = schedule["stochastic_behavior"].get("response_time_variability", 0.2)
                mistake_probability = schedule["stochastic_behavior"].get("mistake_probability", 0.1)
                
                interaction = {
                    "interaction_number": i,
                    "concept": concept,
                    "difficulty": difficulty,
                    "forgetting_rate": forgetting_rate,
                    "response_time_variability": response_time_variability,
                    "mistake_probability": mistake_probability
                }
                
                interactions.append(interaction)
            
            logger.info(f"Generated {num_interactions} interactions for schedule {schedule_id}")
            
            return interactions
            
        except Exception as e:
            logger.error(f"Failed to generate interaction sequence for schedule {schedule_id}: {e}")
            raise
    
    def _validate_difficulty_schedule(self, difficulty_schedule: Dict[str, Any]):
        """Validate difficulty schedule configuration"""
        required_fields = ["type"]
        for field in required_fields:
            if field not in difficulty_schedule:
                raise ValueError(f"Missing required field in difficulty_schedule: {field}")
        
        schedule_type = difficulty_schedule["type"]
        if schedule_type not in ["adaptive", "fixed", "progressive", "random"]:
            raise ValueError(f"Invalid difficulty schedule type: {schedule_type}")
    
    def _validate_concept_sequence(self, concept_sequence: Dict[str, Any]):
        """Validate concept sequence configuration"""
        required_fields = ["type"]
        for field in required_fields:
            if field not in concept_sequence:
                raise ValueError(f"Missing required field in concept_sequence: {field}")
        
        sequence_type = concept_sequence["type"]
        if sequence_type not in ["curriculum", "transfer_test", "random"]:
            raise ValueError(f"Invalid concept sequence type: {sequence_type}")
    
    def _generate_difficulty(
        self,
        difficulty_schedule: Dict[str, Any],
        interaction_index: int,
        total_interactions: int
    ) -> float:
        """Generate difficulty for interaction based on schedule"""
        schedule_type = difficulty_schedule["type"]
        
        if schedule_type == "fixed":
            return difficulty_schedule.get("difficulty", 0.5)
        
        elif schedule_type == "progressive":
            start_difficulty = difficulty_schedule.get("start_difficulty", 0.3)
            end_difficulty = difficulty_schedule.get("end_difficulty", 0.8)
            progress = interaction_index / max(total_interactions - 1, 1)
            return start_difficulty + (end_difficulty - start_difficulty) * progress
        
        elif schedule_type == "random":
            min_difficulty = difficulty_schedule.get("min_difficulty", 0.1)
            max_difficulty = difficulty_schedule.get("max_difficulty", 0.9)
            return random.uniform(min_difficulty, max_difficulty)
        
        elif schedule_type == "adaptive":
            # Adaptive would require learner state - simplified for now
            return 0.5
        
        else:
            return 0.5
    
    def _generate_concept(
        self,
        concept_sequence: Dict[str, Any],
        interaction_index: int,
        total_interactions: int
    ) -> str:
        """Generate concept for interaction based on sequence"""
        sequence_type = concept_sequence["type"]
        
        if sequence_type == "random":
            concepts = concept_sequence.get("concepts", ["concept1", "concept2", "concept3"])
            return random.choice(concepts)
        
        elif sequence_type == "curriculum":
            dag_path = concept_sequence.get("dag_path", ["concept1", "concept2", "concept3"])
            cycle_index = interaction_index % len(dag_path)
            return dag_path[cycle_index]
        
        elif sequence_type == "transfer_test":
            # Transfer test would alternate between source and target concepts
            transfer_edges = concept_sequence.get("transfer_edges", [["concept1", "concept2"]])
            cycle_index = interaction_index % len(transfer_edges)
            return transfer_edges[cycle_index][1]  # Return target concept
        
        else:
            return "concept1"
    
    def _get_forgetting_rate(
        self,
        forgetting_injections: List[Dict[str, Any]],
        interaction_index: int
    ) -> float:
        """Get forgetting rate at specific interaction"""
        for injection in forgetting_injections:
            if injection.get("interaction") == interaction_index:
                return injection.get("forgetting_rate", 0.0)
        return 0.0


def main():
    """Main entry point for interaction scheduler service"""
    import os
    from fastapi import FastAPI
    from pydantic import BaseModel
    
    # Create FastAPI app
    app = FastAPI(title="Interaction Scheduler Service")
    
    # Initialize service
    service = InteractionSchedulerService()
    
    # Pydantic models for API
    class ScheduleCreateRequest(BaseModel):
        schedule_id: str
        difficulty_schedule: Dict[str, Any]
        concept_sequence: Dict[str, Any]
        forgetting_injections: List[Dict[str, Any]] = None
        stochastic_behavior: Dict[str, Any] = None
    
    class GenerateSequenceRequest(BaseModel):
        schedule_id: str
        num_interactions: int
        seed: int = None
    
    # API endpoints
    @app.post("/experiments/schedule/create")
    async def create_schedule(request: ScheduleCreateRequest):
        """Create an interaction schedule"""
        return service.create_schedule(
            schedule_id=request.schedule_id,
            difficulty_schedule=request.difficulty_schedule,
            concept_sequence=request.concept_sequence,
            forgetting_injections=request.forgetting_injections,
            stochastic_behavior=request.stochastic_behavior
        )
    
    @app.get("/experiments/schedule/{schedule_id}")
    async def get_schedule(schedule_id: str):
        """Get schedule details"""
        return service.get_schedule(schedule_id)
    
    @app.post("/experiments/schedule/{schedule_id}/generate")
    async def generate_sequence(schedule_id: str, request: GenerateSequenceRequest):
        """Generate interaction sequence based on schedule"""
        return service.generate_interaction_sequence(
            schedule_id=schedule_id,
            num_interactions=request.num_interactions,
            seed=request.seed
        )
    
    # Run service
    import uvicorn
    port = int(os.getenv("INTERACTION_SCHEDULER_PORT", 8004))
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
