"""
Entropy Instrumentation for Deterministic Replay Validation

Provides logging infrastructure for all stochastic operations to enable:
- Replay drift diagnosis
- Cross-consumer divergence detection
- Hidden RNG consumption tracking
- Order-dependent entropy bleed identification

Every stochastic operation should emit:
{
    "rng_stream": "lyapunov_noise",
    "seed": 42,
    "draw_index": 187,
    "value": 0.00038192,
    "event_id": "...",
    "interaction_id": "...",
    "user_id": "...",
    "concept": "k2_control",
}
"""

import logging
import json
from typing import Any, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class EntropyInstrumentation:
    """
    Instruments all stochastic operations for deterministic replay validation.
    
    Tracks RNG stream usage, seed derivation, draw indices, and values
    to enable replay causality proof.
    """
    
    def __init__(self, enabled: bool = True):
        """
        Initialize entropy instrumentation.
        
        Args:
            enabled: Whether instrumentation is active
        """
        self.enabled = enabled
        self.draw_counters = {}  # rng_stream -> draw_index
        self.entropy_log = []  # List of entropy events for analysis
    
    def log_draw(
        self,
        rng_stream: str,
        seed: int,
        value: float,
        event_id: Optional[str] = None,
        interaction_id: Optional[str] = None,
        user_id: Optional[str] = None,
        concept: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log a stochastic draw for replay validation.
        
        Args:
            rng_stream: Name of the RNG stream (e.g., "lyapunov_noise")
            seed: Seed used for this RNG stream
            value: Random value drawn
            event_id: Associated event ID
            interaction_id: Associated interaction ID
            user_id: Associated user ID
            concept: Associated concept
            context: Additional context metadata
        """
        if not self.enabled:
            return
        
        # Increment draw counter for this stream
        if rng_stream not in self.draw_counters:
            self.draw_counters[rng_stream] = 0
        draw_index = self.draw_counters[rng_stream]
        self.draw_counters[rng_stream] += 1
        
        # Create entropy event
        entropy_event = {
            "rng_stream": rng_stream,
            "seed": seed,
            "draw_index": draw_index,
            "value": value,
            "timestamp": datetime.now().isoformat(),
        }
        
        # Add optional context
        if event_id:
            entropy_event["event_id"] = event_id
        if interaction_id:
            entropy_event["interaction_id"] = interaction_id
        if user_id:
            entropy_event["user_id"] = user_id
        if concept:
            entropy_event["concept"] = concept
        if context:
            entropy_event["context"] = context
        
        # Log to file
        self.entropy_log.append(entropy_event)
        
        # Log to console (structured)
        logger.debug(
            f"ENTROPY_DRAW: {rng_stream} seed={seed} draw={draw_index} value={value:.8f} "
            f"user={user_id} concept={concept}"
        )
    
    def get_entropy_summary(self) -> Dict[str, Any]:
        """
        Get summary of entropy usage.
        
        Returns:
            Summary of all stochastic operations
        """
        return {
            "total_draws": len(self.entropy_log),
            "streams_used": list(self.draw_counters.keys()),
            "draws_per_stream": self.draw_counters.copy(),
            "entropy_log": self.entropy_log.copy(),
        }
    
    def export_entropy_log(self, filepath: str) -> None:
        """
        Export entropy log to JSON file.
        
        Args:
            filepath: Path to export file
        """
        with open(filepath, 'w') as f:
            json.dump({
                "summary": self.get_entropy_summary(),
                "events": self.entropy_log
            }, f, indent=2)
        
        logger.info(f"Exported entropy log to {filepath}")


# Global entropy instrumentation instance
_global_instrumentation = EntropyInstrumentation(enabled=True)


def get_entropy_instrumentation() -> EntropyInstrumentation:
    """Get the global entropy instrumentation instance."""
    return _global_instrumentation


def enable_entropy_instrumentation(enabled: bool = True) -> None:
    """
    Enable or disable entropy instrumentation.
    
    Args:
        enabled: Whether to enable instrumentation
    """
    _global_instrumentation.enabled = enabled
