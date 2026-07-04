"""
UX Semantics - Pedagogical Projection Layer

C1.1.4 - Projection UX Semantics Transition

Transforms cognition internals into pedagogical semantics for frontend consumption.

Architectural Principle:
- Frontend should expose pedagogy semantics, NOT cognition implementation internals
- Cognition internals (mastery, uncertainty, bayesian_alpha, kalman_covariance, lyapunov_mastery)
  are backend implementation details
- UX semantics (readiness, confidence stability, challenge suitability, pacing responsiveness)
  are pedagogically meaningful to learners

This transformation layer bridges the gap between:
- Internal cognitive models (research-grade, precise, implementation-specific)
- External UX semantics (learner-facing, pedagogical, interpretable)
"""

from enum import Enum

"""Extracted from `HCIE_SYSTEM_BACKENDV2/core/projection/ux_semantics.py` by tools/migrate/split_session_and_ux.py.

Symbols: TransferReadiness.
"""

class TransferReadiness(Enum):
    """Readiness for transfer to new contexts"""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"


# --- traceability ---------------------------------------------------------
__sliced_from__ = 'HCIE_SYSTEM_BACKENDV2/core/projection/ux_semantics.py'
__symbol_ranges__ = {
    'TransferReadiness': (61, 66),
}
