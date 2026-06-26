"""
Cold-start priors for all learners
Ensures fair comparison and controlled experiments
"""

DEFAULT_PRIORS = {
    "lyapunov": {
        "mastery": 0.3,  # Novice baseline
    },
    "bayesian": {
        "alpha": 3.0,
        "beta": 7.0,  # mean = 0.3, moderate uncertainty
    },
    "kalman": {
        "mastery": 0.3,
        "covariance": 0.05,  # 🔥 FIXED: Reduced uncertainty for better ensemble consistency
    }
}

# Research scenarios for controlled experiments
RESEARCH_SCENARIOS = {
    "novice": {"mastery": 0.2},
    "intermediate": {"mastery": 0.5}, 
    "advanced": {"mastery": 0.8},
    "expert": {"mastery": 0.95}
}

def get_prior(learner_type: str, scenario: str = None, user_id: str = None, concept: str = None, personalizer=None) -> dict:
    """Get prior configuration for learner type and scenario with personalization"""
    if scenario and scenario in RESEARCH_SCENARIOS:
        # Override mastery for scenario-based experiments
        prior = DEFAULT_PRIORS[learner_type].copy()
        prior["mastery"] = RESEARCH_SCENARIOS[scenario]["mastery"]
        
        # Adjust other parameters proportionally
        if learner_type == "bayesian":
            # Keep alpha/beta ratio but scale to new mastery
            ratio = prior["alpha"] / (prior["alpha"] + prior["beta"])
            prior["alpha"] = ratio * 10  # Keep sum = 10
            prior["beta"] = 10 - prior["alpha"]
        elif learner_type == "kalman":
            prior["covariance"] = DEFAULT_PRIORS["kalman"]["covariance"]
            
        return prior
    
    # ✅ PERSONALIZED: Use ColdStartOptimizer for real users
    if user_id and concept and personalizer is not None:
        try:
            personalized_mastery = personalizer.get_personalized_mastery(user_id, concept)
            
            # Create personalized prior
            prior = DEFAULT_PRIORS[learner_type].copy()
            prior["mastery"] = personalized_mastery
            
            # Adjust Bayesian parameters to match personalized mastery
            if learner_type == "bayesian":
                strength = 10  # Pseudo-count strength
                mastery = personalized_mastery
                prior["alpha"] = mastery * strength
                prior["beta"] = (1 - mastery) * strength
            
            return prior
        except Exception:
            # Fallback to default if optimizer not available
            pass
    
    return DEFAULT_PRIORS[learner_type]
