import sys
sys.path.append('RealSystem/HCIE_SYSTEM_BACKENDV2')
import math
from core.mastery.mastery_model import MasteryModel

def debug_zpd_factors():
    """Debug ZPD factor calculations"""
    
    print("=== ZPD Factor Debug Analysis ===")
    print("Case\tMastery\tDifficulty\tSaturation\tZPD Gap\tZPD Factor\tRaw Update\tFinal Update")
    print("-" * 95)
    
    test_cases = [
        {"name": "Too Easy", "mastery": 0.378, "difficulty": 0.1},
        {"name": "Too Hard", "mastery": 0.300, "difficulty": 0.8},
        {"name": "Perfect ZPD", "mastery": 0.468, "difficulty": 0.5},
        {"name": "Slightly Hard", "mastery": 0.378, "difficulty": 0.6},
        {"name": "Slightly Easy", "mastery": 0.378, "difficulty": 0.3},
    ]
    
    for case in test_cases:
        mastery = case["mastery"]
        difficulty = case["difficulty"]
        
        # Calculate factors like the model does
        alpha, beta = 1.0, 2.33  # Base novice prior
        current_mastery = alpha / (alpha + beta)
        
        # Saturation factor
        saturation_factor = max(0.2, 1.0 - mastery)
        
        # Asymmetric ZPD factor - use actual mastery, not current_mastery
        zpd_gap = abs(mastery - difficulty)
        if difficulty > mastery:
            # TOO HARD → stronger penalty
            zpd_factor = max(0.05, math.exp(- (zpd_gap ** 2) / 0.01))
        else:
            # TOO EASY → softer penalty
            zpd_factor = max(0.05, math.exp(- (zpd_gap ** 2) / 0.03))
        
        # Base update (correct answer) - balanced for realistic learning speed
        base_update = 0.14
        time_multiplier = 1.0
        
        # Non-linear ZPD dominance (balanced power)
        effective_saturation = saturation_factor * (zpd_factor ** 1.2)
        
        # Raw update strength (with new base updates)
        raw_update = base_update * time_multiplier * effective_saturation
        
        # Final update (with lower minimum bound)
        final_update = max(0.005, min(0.2, raw_update))
        
        print(f"{case['name']}\t{mastery:.3f}\t\t{difficulty:.1f}\t\t{saturation_factor:.3f}\t\t{zpd_gap:.3f}\t\t{zpd_factor:.3f}\t\t{raw_update:.4f}\t\t{final_update:.4f}")
        
        # Analysis
        if final_update == 0.01:
            print(f"    CLAMPED to minimum bound!")
        elif final_update == 0.2:
            print(f"    CLAMPED to maximum bound!")
        else:
            print(f"    Within bounds")

if __name__ == "__main__":
    debug_zpd_factors()
