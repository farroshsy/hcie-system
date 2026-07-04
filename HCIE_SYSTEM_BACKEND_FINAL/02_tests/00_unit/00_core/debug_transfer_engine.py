#!/usr/bin/env python3
"""
Debug Transfer Engine
Tests if the transfer learning engine is working correctly
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from core.learning.transfer_learning_engine import TransferLearningEngine

def test_transfer_engine():
    """Test the transfer learning engine directly"""
    print("=== Transfer Engine Debug Test ===")
    
    # Create transfer engine
    engine = TransferLearningEngine()
    
    # Add some test dependencies
    test_dependencies = [
        {
            "source_concept": "ct_algorithm_design",
            "target_concept": "ct_abstraction", 
            "transfer_weight": 0.3,
            "dependency_type": "prerequisite",
            "confidence_level": 0.9
        },
        {
            "source_concept": "ct_abstraction",
            "target_concept": "ct_pattern_recognition",
            "transfer_weight": 0.2,
            "dependency_type": "related", 
            "confidence_level": 0.8
        }
    ]
    
    engine.load_concept_dependencies(test_dependencies)
    
    # Test transfer calculation
    mastery_change = 0.01  # Larger change
    confidence = 0.8
    
    transfer_amount = engine.calculate_transfer_amount(
        "ct_algorithm_design", "ct_abstraction", mastery_change, confidence
    )
    
    print(f"Mastery change: {mastery_change}")
    print(f"Confidence: {confidence}")
    print(f"Transfer amount: {transfer_amount}")
    print(f"Threshold: {engine.min_transfer_threshold}")
    print(f"Transfer applied: {transfer_amount >= engine.min_transfer_threshold}")
    
    # Test with smaller change
    small_change = 0.002
    small_transfer = engine.calculate_transfer_amount(
        "ct_algorithm_design", "ct_abstraction", small_change, confidence
    )
    
    print(f"\nSmall mastery change: {small_change}")
    print(f"Small transfer amount: {small_transfer}")
    print(f"Small transfer applied: {small_transfer >= engine.min_transfer_threshold}")
    
    # Test the boosted calculation
    print(f"\n=== Boosted Calculation Test ===")
    boosted_transfer = small_transfer * 3.0  # 3x boost
    print(f"Boosted transfer: {boosted_transfer}")
    print(f"Boosted transfer applied: {boosted_transfer >= engine.min_transfer_threshold}")

if __name__ == "__main__":
    test_transfer_engine()
