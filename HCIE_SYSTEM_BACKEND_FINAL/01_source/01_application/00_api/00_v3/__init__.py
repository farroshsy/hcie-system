"""
Canonical Runtime Exposure APIs (V3 within V2)

Bounded runtime surfaces around authority domains:
- GovernanceRuntimeAPI (governance authority domain)
- ReplayRuntimeAPI (replay authority domain)
- LifecycleRuntimeAPI (lifecycle authority domain)
- MutationRuntimeAPI (mutation authority domain)
- EventRuntimeAPI (event authority domain)

Authority States:
- experimental: unstable, may bypass
- converging: preferred canonical path
- authoritative: mandatory canonical path
- frozen: deprecated legacy path

Runtime Contract Versioning:
- semantic_version in responses for all canonical APIs
- Current version: 1.0
"""

from fastapi import APIRouter

router = APIRouter(prefix="/v3", tags=["v3-canonical-runtime"])

# Import bounded runtime APIs
from .runtime.governance import governance_router
from .runtime.mutations import mutations_router
from .runtime.events import events_router
from .runtime.replay import replay_router
from .runtime.lifecycle import lifecycle_router
from .runtime.trajectory import trajectory_router
from .runtime.authority import authority_router
from .runtime.objective import objective_router
from .runtime.recommendation import recommendation_router

# Register bounded runtime APIs
router.include_router(governance_router)
router.include_router(mutations_router)
router.include_router(events_router)
router.include_router(replay_router)
router.include_router(lifecycle_router)
router.include_router(trajectory_router)
router.include_router(authority_router)
router.include_router(objective_router)
router.include_router(recommendation_router)

# Import research APIs
from .research.transfer import transfer_router
from .research.policy import policy_router
from .research.attribution import attribution_router
from .research.learner import learner_research_router

# Register research APIs
router.include_router(transfer_router)
router.include_router(policy_router)
router.include_router(attribution_router)
router.include_router(learner_research_router)

# Import enhanced auth and frontend APIs
from .auth.auth import auth_router
from .frontend.dashboard import dashboard_router
from .frontend.thesis_evidence import router as thesis_evidence_router
from .frontend.grounding import router as method_grounding_router
from .frontend.thesis_figures import router as thesis_figures_router
from .concepts import router as concepts_router

# Register enhanced auth and frontend APIs
router.include_router(auth_router)
router.include_router(dashboard_router)
router.include_router(thesis_evidence_router)
router.include_router(method_grounding_router)
router.include_router(thesis_figures_router)
router.include_router(concepts_router)

# Import experiment control plane APIs
from .experiments import router as experiments_router

# Register experiment control plane APIs
router.include_router(experiments_router)
from .experiments.cohorts import router as cohorts_router

router.include_router(cohorts_router)

# Import admin runtime APIs
from .admin import router as admin_runtime_router

# Register admin runtime APIs
router.include_router(admin_runtime_router)

# Internal service-to-service APIs
from .service import router as service_router

router.include_router(service_router)

# Slice 1 canonical learner surface + deprecated ITS redirects
from .learner import router as learner_router
from .its import router as its_router

router.include_router(learner_router)
router.include_router(its_router)

# ADC Review Portal — public read-only surface (no auth required)
from .review import review_router

router.include_router(review_router)
