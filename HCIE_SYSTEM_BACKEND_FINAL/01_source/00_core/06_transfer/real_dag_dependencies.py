"""
Real DAG Dependencies Loader
Loads actual K-12 Computer Science Framework concept dependencies
Based on the K-12 CS Framework with 5 core concepts and 7 practices
"""

import logging
from typing import Dict, List

logger = logging.getLogger(__name__)

class RealDAGDependencies:
    """Real DAG dependencies based on K-12 Computer Science Framework"""
    
    def __init__(self):
        # K-12 CS Framework concept dependencies based on grade band progressions
        # Mapping follows the framework's natural learning progression
        self.dependencies = {
            # Computing Systems Dependencies
            "k2_computing_systems_devices": [
                {
                    "target_concept": "k5_computing_systems_devices",
                    "transfer_weight": 0.85,
                    "confidence_level": 1.0,
                    "rationale": "Basic device usage leads to understanding connected systems"
                },
                {
                    "target_concept": "k2_computing_systems_hardware_software",
                    "transfer_weight": 0.90,
                    "confidence_level": 1.0,
                    "rationale": "Device usage naturally leads to hardware/software understanding"
                }
            ],
            "k2_computing_systems_hardware_software": [
                {
                    "target_concept": "k5_computing_systems_hardware_software",
                    "transfer_weight": 0.80,
                    "confidence_level": 1.0,
                    "rationale": "Basic hardware/software concepts progress to bits and systems"
                }
            ],
            "k2_computing_systems_troubleshooting": [
                {
                    "target_concept": "k5_computing_systems_troubleshooting",
                    "transfer_weight": 0.75,
                    "confidence_level": 1.0,
                    "rationale": "Basic problem description leads to systematic troubleshooting"
                }
            ],
            "k5_computing_systems_devices": [
                {
                    "target_concept": "k8_computing_systems_devices",
                    "transfer_weight": 0.85,
                    "confidence_level": 1.0,
                    "rationale": "Connected devices lead to understanding human-computer interaction"
                }
            ],
            "k5_computing_systems_hardware_software": [
                {
                    "target_concept": "k8_computing_systems_hardware_software",
                    "transfer_weight": 0.80,
                    "confidence_level": 1.0,
                    "rationale": "Hardware/software systems lead to understanding capability tradeoffs"
                }
            ],
            "k8_computing_systems_devices": [
                {
                    "target_concept": "k12_computing_systems_devices",
                    "transfer_weight": 0.85,
                    "confidence_level": 1.0,
                    "rationale": "HCI concepts lead to understanding integrated systems"
                }
            ],
            "k8_computing_systems_hardware_software": [
                {
                    "target_concept": "k12_computing_systems_hardware_software",
                    "transfer_weight": 0.80,
                    "confidence_level": 1.0,
                    "rationale": "System capabilities lead to understanding multi-level interactions"
                }
            ],

            # Networks and Internet Dependencies  
            "k2_networks_communication": [
                {
                    "target_concept": "k5_networks_communication",
                    "transfer_weight": 0.85,
                    "confidence_level": 1.0,
                    "rationale": "Basic network concepts lead to understanding paths and packets"
                }
            ],
            "k2_networks_cybersecurity": [
                {
                    "target_concept": "k5_networks_cybersecurity",
                    "transfer_weight": 0.80,
                    "confidence_level": 1.0,
                    "rationale": "Basic password security leads to understanding information protection"
                }
            ],
            "k5_networks_communication": [
                {
                    "target_concept": "k8_networks_communication",
                    "transfer_weight": 0.85,
                    "confidence_level": 1.0,
                    "rationale": "Path understanding leads to protocol comprehension"
                }
            ],
            "k5_networks_cybersecurity": [
                {
                    "target_concept": "k8_networks_cybersecurity",
                    "transfer_weight": 0.80,
                    "confidence_level": 1.0,
                    "rationale": "Information protection leads to understanding encryption"
                }
            ],
            "k8_networks_communication": [
                {
                    "target_concept": "k12_networks_communication",
                    "transfer_weight": 0.85,
                    "confidence_level": 1.0,
                    "rationale": "Protocol understanding leads to network topology concepts"
                }
            ],
            "k8_networks_cybersecurity": [
                {
                    "target_concept": "k12_networks_cybersecurity",
                    "transfer_weight": 0.80,
                    "confidence_level": 1.0,
                    "rationale": "Encryption concepts lead to comprehensive security understanding"
                }
            ],

            # Data and Analysis Dependencies
            "k2_data_collection": [
                {
                    "target_concept": "k5_data_collection",
                    "transfer_weight": 0.85,
                    "confidence_level": 1.0,
                    "rationale": "Basic data collection leads to tool selection understanding"
                }
            ],
            "k2_data_storage": [
                {
                    "target_concept": "k5_data_storage",
                    "transfer_weight": 0.80,
                    "confidence_level": 1.0,
                    "rationale": "Basic storage concepts lead to understanding file sizes and metadata"
                }
            ],
            "k2_data_visualization": [
                {
                    "target_concept": "k5_data_visualization",
                    "transfer_weight": 0.85,
                    "confidence_level": 1.0,
                    "rationale": "Basic charts lead to data transformation and clustering"
                }
            ],
            "k2_data_inference": [
                {
                    "target_concept": "k5_data_inference",
                    "transfer_weight": 0.80,
                    "confidence_level": 1.0,
                    "rationale": "Basic predictions lead to understanding data relevance"
                }
            ],
            "k5_data_collection": [
                {
                    "target_concept": "k8_data_collection",
                    "transfer_weight": 0.85,
                    "confidence_level": 1.0,
                    "rationale": "Tool selection leads to automated data collection"
                }
            ],
            "k5_data_storage": [
                {
                    "target_concept": "k8_data_storage",
                    "transfer_weight": 0.80,
                    "confidence_level": 1.0,
                    "rationale": "File concepts lead to understanding representations and encoding"
                }
            ],
            "k8_data_collection": [
                {
                    "target_concept": "k12_data_collection",
                    "transfer_weight": 0.85,
                    "confidence_level": 1.0,
                    "rationale": "Automated collection leads to understanding privacy implications"
                }
            ],
            "k8_data_storage": [
                {
                    "target_concept": "k12_data_storage",
                    "transfer_weight": 0.80,
                    "confidence_level": 1.0,
                    "rationale": "Representations lead to understanding data models and tradeoffs"
                }
            ],

            # Algorithms and Programming Dependencies
            "k2_algorithms": [
                {
                    "target_concept": "k5_algorithms",
                    "transfer_weight": 0.85,
                    "confidence_level": 1.0,
                    "rationale": "Basic algorithms lead to understanding multiple solution approaches"
                }
            ],
            "k2_variables": [
                {
                    "target_concept": "k5_variables",
                    "transfer_weight": 0.90,
                    "confidence_level": 1.0,
                    "rationale": "Basic data representation leads to variable concepts"
                }
            ],
            "k2_control": [
                {
                    "target_concept": "k5_control",
                    "transfer_weight": 0.85,
                    "confidence_level": 1.0,
                    "rationale": "Basic sequences lead to loops and conditionals"
                }
            ],
            "k2_modularity": [
                {
                    "target_concept": "k5_modularity",
                    "transfer_weight": 0.80,
                    "confidence_level": 1.0,
                    "rationale": "Basic decomposition leads to program structure"
                }
            ],
            "k2_program_development": [
                {
                    "target_concept": "k5_program_development",
                    "transfer_weight": 0.85,
                    "confidence_level": 1.0,
                    "rationale": "Basic program creation leads to iterative design process"
                }
            ],
            "k5_algorithms": [
                {
                    "target_concept": "k8_algorithms",
                    "transfer_weight": 0.85,
                    "confidence_level": 1.0,
                    "rationale": "Multiple algorithms lead to understanding human-computer interaction"
                }
            ],
            "k5_variables": [
                {
                    "target_concept": "k8_variables",
                    "transfer_weight": 0.90,
                    "confidence_level": 1.0,
                    "rationale": "Variable usage leads to understanding identifiers and naming"
                }
            ],
            "k5_control": [
                {
                    "target_concept": "k8_control",
                    "transfer_weight": 0.85,
                    "confidence_level": 1.0,
                    "rationale": "Basic control structures lead to combining complex structures"
                }
            ],
            "k8_algorithms": [
                {
                    "target_concept": "k12_algorithms",
                    "transfer_weight": 0.85,
                    "confidence_level": 1.0,
                    "rationale": "HCI understanding leads to algorithm performance analysis"
                }
            ],
            "k8_variables": [
                {
                    "target_concept": "k12_variables",
                    "transfer_weight": 0.90,
                    "confidence_level": 1.0,
                    "rationale": "Variable naming leads to data structures"
                }
            ],
            "k8_control": [
                {
                    "target_concept": "k12_control",
                    "transfer_weight": 0.85,
                    "confidence_level": 1.0,
                    "rationale": "Complex control leads to understanding implementation tradeoffs"
                }
            ],
            "k8_modularity": [
                {
                    "target_concept": "k12_modularity",
                    "transfer_weight": 0.80,
                    "confidence_level": 1.0,
                    "rationale": "Procedures lead to understanding complex module systems"
                }
            ],

            # Impacts of Computing Dependencies
            "k2_culture": [
                {
                    "target_concept": "k5_culture",
                    "transfer_weight": 0.85,
                    "confidence_level": 1.0,
                    "rationale": "Basic technology impact leads to understanding cultural influence"
                }
            ],
            "k2_social_interactions": [
                {
                    "target_concept": "k5_social_interactions",
                    "transfer_weight": 0.85,
                    "confidence_level": 1.0,
                    "rationale": "Basic communication changes lead to understanding global collaboration"
                }
            ],
            "k2_safety_law_ethics": [
                {
                    "target_concept": "k5_safety_law_ethics",
                    "transfer_weight": 0.80,
                    "confidence_level": 1.0,
                    "rationale": "Basic safety rules lead to understanding copyright and ethics"
                }
            ],
            "k5_culture": [
                {
                    "target_concept": "k8_culture",
                    "transfer_weight": 0.85,
                    "confidence_level": 1.0,
                    "rationale": "Cultural influence leads to understanding globalization effects"
                }
            ],
            "k5_social_interactions": [
                {
                    "target_concept": "k8_social_interactions",
                    "transfer_weight": 0.85,
                    "confidence_level": 1.0,
                    "rationale": "Collaboration leads to understanding social platforms and engagement"
                }
            ],
            "k8_culture": [
                {
                    "target_concept": "k12_culture",
                    "transfer_weight": 0.85,
                    "confidence_level": 1.0,
                    "rationale": "Globalization understanding leads to analyzing equity and access"
                }
            ],
            "k8_social_interactions": [
                {
                    "target_concept": "k12_social_interactions",
                    "transfer_weight": 0.85,
                    "confidence_level": 1.0,
                    "rationale": "Social platforms lead to understanding career impacts"
                }
            ],
            "k8_safety_law_ethics": [
                {
                    "target_concept": "k12_safety_law_ethics",
                    "transfer_weight": 0.80,
                    "confidence_level": 1.0,
                    "rationale": "Privacy tradeoffs lead to understanding legal frameworks"
                }
            ],

            # Cross-Concept Dependencies (Computational Thinking Practices)
            "practice_inclusive_culture": [
                {
                    "target_concept": "practice_collaboration",
                    "transfer_weight": 0.90,
                    "confidence_level": 1.0,
                    "rationale": "Inclusive mindset enables effective collaboration"
                }
            ],
            "practice_collaboration": [
                {
                    "target_concept": "practice_problem_recognition",
                    "transfer_weight": 0.85,
                    "confidence_level": 1.0,
                    "rationale": "Collaborative skills enhance problem identification"
                }
            ],
            "practice_problem_recognition": [
                {
                    "target_concept": "practice_abstractions",
                    "transfer_weight": 0.90,
                    "confidence_level": 1.0,
                    "rationale": "Problem decomposition requires abstraction skills"
                }
            ],
            "practice_abstractions": [
                {
                    "target_concept": "practice_artifact_creation",
                    "transfer_weight": 0.85,
                    "confidence_level": 1.0,
                    "rationale": "Abstraction enables effective artifact design"
                }
            ],
            "practice_artifact_creation": [
                {
                    "target_concept": "practice_testing_refinement",
                    "transfer_weight": 0.95,
                    "confidence_level": 1.0,
                    "rationale": "Created artifacts must be tested and refined"
                }
            ],
            "practice_testing_refinement": [
                {
                    "target_concept": "practice_communication",
                    "transfer_weight": 0.85,
                    "confidence_level": 1.0,
                    "rationale": "Testing results inform communication about computing"
                }
            ],
            "practice_communication": [
                {
                    "target_concept": "k2_algorithms",
                    "transfer_weight": 0.80,
                    "confidence_level": 1.0,
                    "rationale": "Communication skills reinforce algorithmic thinking"
                }
            ],

            # (Removed duplicate k2_algorithms/k2_variables/k2_control/k2_modularity/
            #  k2_program_development block here — identical to the definitions above; the dict
            #  silently kept only one copy anyway. F601 dedup, no behavior change.)

            # Add remaining impacts concepts for K-2 grade band
            "k2_impacts_culture": [
                {
                    "target_concept": "k5_culture",
                    "transfer_weight": 0.85,
                    "confidence_level": 1.0,
                    "rationale": "Basic technology impact leads to understanding cultural influence"
                }
            ],
            "k2_impacts_social": [
                {
                    "target_concept": "k5_social_interactions",
                    "transfer_weight": 0.85,
                    "confidence_level": 1.0,
                    "rationale": "Basic communication changes lead to understanding global collaboration"
                }
            ],
            "k2_impacts_safety": [
                {
                    "target_concept": "k5_safety_law_ethics",
                    "transfer_weight": 0.80,
                    "confidence_level": 1.0,
                    "rationale": "Basic safety rules lead to understanding copyright and ethics"
                }
            ],

            # Add K-12 grade band completion dependencies
            "k12_algorithms": [
                {
                    "target_concept": "practice_abstractions",
                    "transfer_weight": 0.90,
                    "confidence_level": 1.0,
                    "rationale": "Advanced algorithms reinforce abstraction skills"
                }
            ],
            "k12_variables": [
                {
                    "target_concept": "practice_artifact_creation",
                    "transfer_weight": 0.85,
                    "confidence_level": 1.0,
                    "rationale": "Data structures enable complex artifact creation"
                }
            ],
            "k12_culture": [
                {
                    "target_concept": "practice_inclusive_culture",
                    "transfer_weight": 0.95,
                    "confidence_level": 1.0,
                    "rationale": "Cultural analysis reinforces inclusive design"
                }
            ]
        }
        
        logger.info("🔥 K-12 CS FRAMEWORK DAG DEPENDENCIES LOADED")
        logger.info(f"   {len(self.dependencies)} concept dependencies")
        logger.info("   Core Concepts: Computing Systems, Networks, Data, Algorithms, Impacts")
        logger.info("   Core Practices: Inclusive Culture, Collaboration, Problem Recognition, Abstractions, Creation, Testing, Communication")
        
        # Log dependency statistics
        concept_counts = {}
        practice_counts = {}
        for concept, deps in self.dependencies.items():
            if concept.startswith("practice_"):
                practice_counts[concept] = len(deps)
            else:
                concept_counts[concept] = len(deps)
        
        logger.info(f"   Concept dependencies: {sum(concept_counts.values())} across {len(concept_counts)} concepts")
        logger.info(f"   Practice dependencies: {sum(practice_counts.values())} across {len(practice_counts)} practices")
    
    def get_dependencies(self, concept: str) -> List[Dict]:
        """Get dependencies for a concept"""
        return self.dependencies.get(concept, [])
    
    def get_all_dependencies(self) -> Dict[str, List[Dict]]:
        """Get all dependencies"""
        return self.dependencies
    
    def get_concept_by_grade_band(self, grade_band: str, core_concept: str, subconcept: str) -> str:
        """
        Get concept ID by grade band and concept names
        
        Args:
            grade_band: "k2", "k5", "k8", "k12"
            core_concept: "computing_systems", "networks", "data", "algorithms", "impacts"
            subconcept: "devices", "hardware_software", "communication", etc.
            
        Returns:
            str: Concept ID in format "grade_band_core_concept_subconcept"
        """
        return f"{grade_band}_{core_concept}_{subconcept}"
    
    def get_practice_by_id(self, practice_number: int, practice_name: str) -> str:
        """
        Get practice ID by number and name
        
        Args:
            practice_number: 1-7 (inclusive culture, collaboration, etc.)
            practice_name: "inclusive_culture", "collaboration", etc.
            
        Returns:
            str: Practice ID in format "practice_practice_name"
        """
        practice_map = {
            1: "inclusive_culture",
            2: "collaboration", 
            3: "problem_recognition",
            4: "abstractions",
            5: "artifact_creation",
            6: "testing_refinement",
            7: "communication"
        }
        return f"practice_{practice_map.get(practice_number, practice_name)}"
    
    def get_learning_progression(self, core_concept: str, subconcept: str) -> List[str]:
        """
        Get the natural learning progression for a concept across grade bands
        
        Args:
            core_concept: Core concept area
            subconcept: Specific subconcept
            
        Returns:
            List[str]: Concept IDs in order from K-2 to 12
        """
        progression = []
        for grade_band in ["k2", "k5", "k8", "k12"]:
            concept_id = self.get_concept_by_grade_band(grade_band, core_concept, subconcept)
            if concept_id in self.dependencies:
                progression.append(concept_id)
        return progression
