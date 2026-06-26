# Learning rate configuration for A/B experiments

FIXED_LEARNING_RATES = {
    "fixed_low": 0.05,
    "fixed_mid": 0.11, 
    "fixed_high": 0.20
}

def get_fixed_learning_rate(mode):
    """Get fixed learning rate for experimental mode"""
    return FIXED_LEARNING_RATES.get(mode, 0.11)
