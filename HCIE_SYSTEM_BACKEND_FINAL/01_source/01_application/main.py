"""
HCIE Real System API — Canonical FastAPI Entry Point.

Lives at the IDEAL_STRUCTURE.md canonical location (line 375):
``01_source/01_application/main.py``. The ``sitecustomize.py`` runtime
projection exposes it as ``app.main`` so the Docker CMD
``uvicorn app.main:app`` and every existing import keeps working.

Phase 14e additions (additive merge — no V2 routes removed):
  - ``/healthz`` and ``/readyz`` (canonical health probes for k8s + Docker)
  - Phase 14e DI container wired into ``app.state.container``
  - Best-effort ``/v3/its/*`` mount via the new ``ItsRuntimeService`` spine
  - V3 auth fallback (``HCIE_AUTH_TRUST_JWT=1``) so the new ITS spine is
    not blocked by V2 ``UnifiedLearningBrain`` boot defects (tracked for
    Phase 14f brain shrink)

Phase 14g Slice 0a:
  - ``@app.on_event('startup' | 'shutdown')`` migrated to FastAPI lifespan
    (the on_event API is deprecated since FastAPI 0.110). The unused
    ``HCIE_USE_LIFESPAN`` env flag (documented but never branched on)
    was removed — lifespan is now unconditional.
"""

import sys
import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.middleware.metrics import PrometheusMiddleware, add_metrics_endpoint

# Add project root to Python path for clean absolute imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from config.env import settings, is_production_environment, is_docker_environment
from app.api import (
    learning_router,
    analytics_router,
    system_router,
    admin_router,
    experiments_router,
    auth_router,
    users_router
)
from app.api.ux import ux_router
from app.api.routes import health_router
from .telemetry.opentelemetry_setup import setup_opentelemetry
TELEMETRY_AVAILABLE = True

# Try to import messaging, but don't fail if not available
try:
    from messaging import start_event_worker, start_auth_event_worker
    from messaging.analytics_worker import start_analytics_worker
    from app.infrastructure.outbox.outbox_pattern import get_outbox_pattern
    from app.infrastructure.di.dependency_injection import initialize_di_container, AllDependencies
    from app.infrastructure.unit_of_work import UnitOfWork
    from app.infrastructure.kafka.kafka_factory import KafkaFactory
except ImportError:
    # Fallback for when messaging module is not available
    def start_event_worker():
        pass
    def start_analytics_worker():
        pass
    def start_auth_event_worker():
        pass
    def get_outbox_pattern():
        return None
    def initialize_di_container(dependencies):
        pass
    def UnitOfWork():
        pass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global guard for OpenTelemetry initialization
_telemetry_initialized = False

# CRITICAL: Setup OpenTelemetry BEFORE any other imports that might use metrics
logger.info("Setting up OpenTelemetry...")
setup_opentelemetry(service_name="hcie-api")
_telemetry_initialized = True
logger.info("OpenTelemetry setup complete")

# Initialize dependency injection
from app.infrastructure.di.dependency_injection import initialize_di_container

# Initialize dependency container
# _di_container = initialize_di_container(
#     dependencies=AllDependencies()
# )

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Phase 14g Slice 0a: replaces the deprecated @app.on_event handlers."""
    logger.info("🚀 Starting HCIE System...")

    try:
        from app.infrastructure.di.get_container import get_container as get_p14e_container
        app.state.container = get_p14e_container()
        logger.info("✅ Phase 14e container attached to app.state.container")
    except Exception as exc:
        logger.warning("⚠️ Phase 14e container init skipped: %s", exc)
        app.state.container = None

    try:
        import subprocess
        logger.info("🔄 Running database migrations...")
        result = subprocess.run(
            ["python", "-m", "alembic", "upgrade", "head"],
            capture_output=True,
            text=True,
            timeout=60,
            # alembic.ini lives in the migrations dir with script_location=. ,
            # so alembic MUST run from there (running from /app finds no ini →
            # "No 'script_location' key" → migrations silently never applied).
            cwd="/app/07_database/00_migrations",
        )
        if result.returncode == 0:
            logger.info("✅ Database migrations completed successfully")
        else:
            if "DuplicateTable" in result.stderr or "already exists" in result.stderr:
                logger.warning("⚠️ Migration tables already exist - stamping version")
                subprocess.run(
                    ["python", "-m", "alembic", "stamp", "head"],
                    capture_output=True,
                    timeout=10,
                    cwd="/app/07_database/00_migrations",
                )
                logger.info("✅ Migration version stamped to head")
            else:
                logger.error(f"❌ Migration failed: {result.stderr}")
    except Exception as e:
        logger.warning(f"⚠️ Migration skipped or failed: {e}")

    from app.runtime.composition import build_api_runtime
    app.state.runtime = build_api_runtime(settings)
    logger.info("✅ Runtime composition root initialized")

    di_container = setup_dependency_injection()
    if not di_container:
        logger.warning("⚠️ Dependency injection failed - falling back to ServiceFactory")

    try:
        if not di_container:
            logger.error("❌ DI container failed - running without workers")
        else:
            task_state_reconstruction_service = di_container.get_task_state_reconstruction_service()

            if settings.enable_background_workers:
                import threading

                def background_reconstruction():
                    try:
                        logger.info("🔄 Starting background state reconstruction...")
                        reconstruction_result = task_state_reconstruction_service.reconstruct_user_state()
                        if reconstruction_result.get("total_users", 0) > 0:
                            total_users = reconstruction_result["total_users"]
                            total_steps = reconstruction_result["total_steps"]
                            logger.info(
                                f"✅ Background state reconstruction completed: "
                                f"{total_users} users, {total_steps} total steps"
                            )
                        else:
                            logger.warning("⚠️ Background state reconstruction returned empty results")
                    except Exception as e:
                        logger.error(f"❌ Background state reconstruction failed: {e}")

                reconstruction_thread = threading.Thread(target=background_reconstruction, daemon=True)
                reconstruction_thread.start()
                logger.info("🔄 Background state reconstruction started")
            else:
                logger.info("ℹ️ State reconstruction disabled (background workers disabled)")
    except Exception as e:
        logger.error(f"❌ State reconstruction failed on startup: {e}", exc_info=True)

    if settings.enable_background_workers:
        try:
            if settings.enable_analytics_worker:
                start_analytics_worker()
                logger.info("📊 Analytics worker started")

            if di_container:
                service_deps = di_container.get_service_dependencies()
                db_deps = di_container.get_db_dependencies()

                kafka_factory = KafkaFactory(settings)
                kafka_consumer = kafka_factory.create_consumer(
                    group_id="auth-event-consumer",
                    topics=["hcie.auth"],
                )

                start_auth_event_worker(
                    user_service=service_deps.user_service,
                    experiment_service=service_deps.experiment_service,
                    redis_client=db_deps.redis_store.client,
                    kafka_consumer=kafka_consumer,
                )
                logger.info("🔥 Auth event worker started (DI + Kafka consumer injected)")
            else:
                logger.error("❌ DI container failed - cannot start workers")

            if settings.enable_outbox_processor and di_container:
                messaging_deps = di_container.get_messaging_dependencies()
                outbox = messaging_deps.outbox_pattern
                outbox.start_background_processor(interval_seconds=5)
                logger.info("🔄 Outbox background processor started")

            logger.info("✅ Background workers started successfully")
        except Exception as e:
            logger.error(f"❌ Failed to start background workers: {e}")
            raise
    else:
        logger.info("ℹ️ Background workers disabled by configuration")

    # Re-spawn cohort runs orphaned by a prior crash/restart. Resume logic in
    # _run_cohort skips already-completed steps, so re-spawning is idempotent.
    try:
        from app.api.v3.experiments.cohorts import resume_pending_runs
        resumed = resume_pending_runs()
        if resumed:
            logger.info(f"🔁 Resumed {resumed} orphaned cohort run(s)")
    except Exception as e:
        logger.warning(f"⚠️ Cohort run resume skipped: {e}")

    logger.info(f"{settings.app_name} started successfully")

    yield

    logger.info("Shutting down application")


app = FastAPI(
    title=settings.app_name,
    description="HCIE Adaptive Learning System Backend",
    version=settings.app_version,
    docs_url="/docs" if settings.debug else None,
    redoc_url=None,
    lifespan=lifespan,
)


V2_DEPRECATION_MESSAGE = (
    "Deprecated V2 route; migrate to /v3/learner/*, /v3/research/*, "
    "or /v3/admin/* as appropriate."
)


def include_v2_router(router_obj, *args, **kwargs) -> None:
    """Include a transitional V2 router with OpenAPI deprecation metadata."""
    kwargs.setdefault("deprecated", True)
    app.include_router(router_obj, *args, **kwargs)


@app.middleware("http")
async def v2_deprecation_headers(request: Request, call_next):
    response = await call_next(request)
    path = request.url.path
    if not (
        path.startswith("/v3")
        or path in {"/", "/healthz", "/readyz", "/metrics", "/docs", "/openapi.json"}
    ):
        response.headers.setdefault("Deprecation", "true")
        response.headers.setdefault("Sunset", "Phase 14h")
        response.headers.setdefault("X-HCIE-Deprecated-Route", V2_DEPRECATION_MESSAGE)
    return response

# Include metrics routes
from app.api.metrics_routes import router as metrics_router
include_v2_router(metrics_router, prefix="/api")

# Debug routers expose internals (incl. outbox envelopes containing user PII). SECURITY: OFF by
# default; enable only in trusted dev with ENABLE_DEBUG_ROUTES=1.
if os.getenv("ENABLE_DEBUG_ROUTES", "0") == "1":
    from app.api.debug_routes import router as debug_router
    include_v2_router(debug_router, prefix="/debug")
    from app.api.routes.debug.debug import router as constitutional_debug_router
    include_v2_router(constitutional_debug_router, prefix="/api/v1/debug")
    logger.warning("⚠️ Debug routers ENABLED (/debug, /api/v1/debug) — development only")

# Include V3 canonical runtime exposure APIs (Phase 3a - Governance Vertical Slice)
# Authority State: converging
# Phase 14e: this same import now also picks up /v3/its/* because v3/__init__.py
# was extended to include the new its_router. No separate mount needed.
try:
    from app.api.v3 import router as v3_router
    app.include_router(v3_router)
    logger.info("✅ V3 canonical runtime exposure APIs enabled (Authority State: converging)")
except ImportError as e:
    logger.warning("⚠️ V3 canonical runtime exposure APIs not available - %s", e)

# Phase 14e safety net: if v3.__init__'s composite import failed for any reason
# (one bad sub-router shouldn't kill the rest), guard-mount each sub-router
# individually with the same _safe_include pattern used by the FINAL spine.
def _safe_include_v3(import_path: str, attr: str, label: str) -> None:
    try:
        mod = __import__(import_path, fromlist=[attr])
        router_obj = getattr(mod, attr)
        if router_obj not in [r for r in app.router.routes if hasattr(app.router, 'routes')]:
            app.include_router(router_obj)
            logger.info("Phase 14e fallback mount: %s via %s.%s", label, import_path, attr)
    except Exception as exc:
        logger.debug("Phase 14e fallback skipped %s: %s", label, exc)

# Best-effort mount of /v3/learner/* (no-op if the composite v3 mount above already covered it).
_safe_include_v3("app.api.v3.learner", "router", "/v3/learner (Slice 1 learner spine)")

# Add metrics middleware (if available)
prometheus_middleware = None
try:
    from app.middleware.metrics import PrometheusMiddleware
    app.add_middleware(PrometheusMiddleware)
    logger.info("✅ PrometheusMiddleware enabled - metrics available at /metrics")
except ImportError:
    logger.warning("⚠️ PrometheusMiddleware not available - metrics disabled")

# 🔥 PRODUCTION: Add security headers middleware
try:
    from app.middleware.security_headers import register_security_headers
    register_security_headers(app)
    logger.info("✅ Security headers middleware enabled")
except ImportError:
    logger.warning("⚠️ Security headers middleware not available - security headers disabled")

# 🔥 PRODUCTION: Add global exception handlers
try:
    from app.middleware.exception_handler import register_exception_handlers
    register_exception_handlers(app)
    logger.info("✅ Global exception handlers enabled")
except ImportError:
    logger.warning("⚠️ Global exception handlers not available - error handling may be inconsistent")

# 🔥 PRODUCTION: Add rate limiting middleware
try:
    from app.middleware.rate_limit import register_rate_limiting
    register_rate_limiting(app)
    logger.info("✅ Rate limiting middleware enabled")
except ImportError:
    logger.warning("⚠️ Rate limiting middleware not available - API abuse protection disabled")

# 🔥 PRODUCTION: Add request validation middleware
try:
    from app.middleware.request_validation import register_request_validation
    register_request_validation(app)
    logger.info("✅ Request validation middleware enabled")
except ImportError:
    logger.warning("⚠️ Request validation middleware not available - input validation disabled")

# 🔥 PRODUCTION: Add compression middleware
try:
    from app.middleware.compression import register_compression
    register_compression(app)
    logger.info("✅ Compression middleware enabled")
except ImportError:
    logger.warning("⚠️ Compression middleware not available - response compression disabled")

# 🔥 PRODUCTION: Add caching middleware
try:
    from app.middleware.caching import register_caching
    from storage.redis_store.redis_store import create_redis_feature_store
    redis_client = create_redis_feature_store(settings.redis_host)
    redis_backend = redis_client.redis_client if redis_client.redis_available else None
    register_caching(app, cache_backend=redis_backend)
    logger.info("✅ Caching middleware enabled")
except ImportError:
    logger.warning("⚠️ Caching middleware not available - response caching disabled")

# 🔥 PRODUCTION: Add request logging middleware
try:
    from app.middleware.request_logging import register_request_logging
    register_request_logging(app)
    logger.info("✅ Request logging middleware enabled")
except ImportError:
    logger.warning("⚠️ Request logging middleware not available - request logging disabled")

# Add CORS middleware
# SECURITY: wildcard origins together with credentials would leak credentialed responses to any
# site (and browsers reject the combo). If origins are '*', force credentials off.
_cors_origins = settings.cors_origins
_cors_creds = settings.cors_allow_credentials
_cors_wildcard = _cors_origins in ("*", ["*"]) or (isinstance(_cors_origins, (list, tuple)) and "*" in _cors_origins)
if _cors_wildcard and _cors_creds:
    logger.warning("⚠️ CORS wildcard origins with credentials is unsafe — disabling allow_credentials")
    _cors_creds = False
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=_cors_creds,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add metrics endpoint
add_metrics_endpoint(app)

# HEALTH API - Production health monitoring
include_v2_router(health_router)

# AUTH API - Authentication and authorization
include_v2_router(auth_router)

# USERS API - User management and profiles
include_v2_router(users_router)

# CORE PRODUCT API - Learning system
include_v2_router(learning_router, prefix="/api")

# ANALYTICS API - Research analytics and insights
include_v2_router(analytics_router)

# SYSTEM API - Infrastructure and monitoring
include_v2_router(system_router)

# RESEARCH API - Experiments and evaluation
include_v2_router(experiments_router)

# EXPERIMENTATION API - Pedagogical experiment registry with replay-deterministic assignment
from app.api.routes.experimentation.experiment_routes import router as experimentation_router
include_v2_router(experimentation_router)

# RESEARCH RESULTS API - Cold start and experimental data
from app.api.routes.research.research_api import router as research_router
include_v2_router(research_router)

# WEBSOCKET API - Real-time updates
from app.api.routes.websocket_routes import router as websocket_router
include_v2_router(websocket_router)

# ADMIN API - Internal debugging and management
include_v2_router(admin_router)

# ADMIN ROUTES API - Interaction testing and debugging
from app.api.routes.admin.interactions import router as interactions_router
include_v2_router(interactions_router, prefix="/api")

# SESSION API - Session lifecycle and history
from app.api.routes.session_routes import router as session_router
include_v2_router(session_router, prefix="/api/sessions")

from app.api.routes.session_history_routes import router as session_history_router
include_v2_router(session_history_router)

# UX API - User-friendly endpoints
include_v2_router(ux_router, prefix="/api")

# Legacy admin routes for reconstruction monitoring (keep for compatibility)
from app.api.admin_routes import router as legacy_admin_router
include_v2_router(legacy_admin_router, prefix="/admin/legacy", tags=["admin", "legacy"])

# TEST API - Learning loop validation (Phase 1)
from app.api.routes.test.learning_loop import router as test_learning_router
include_v2_router(test_learning_router)

# TEST API - B4.1 Frontend validation
from app.api.routes.test_routes import router as test_router
include_v2_router(test_router)

# COLD START VALIDATION API - Cold start deployment validation
from app.api.routes.cold_start_routes import router as cold_start_router
include_v2_router(cold_start_router)

# Session API - C1.1.2 Session Interaction Loop
from app.api.routes.session_routes import router as session_router
include_v2_router(session_router)

# REPLAY API - Deterministic replay for research validation
from app.api.routes.replay import router as replay_router
include_v2_router(replay_router)

# ARCHITECTURE SHOWCASE API - Runtime authority and lifecycle governance (Phase 2+ maturity)
from app.api.architecture.endpoints.runtime_authority import router as architecture_router
include_v2_router(architecture_router)


# Phase 14e canonical health endpoints (k8s probes + Docker healthcheck)
@app.get("/healthz")
async def healthz():
    """Liveness probe — process is up and event loop is responsive."""
    return {
        "status": "ok",
        "entrypoint": "app.main",
        "phase": "14e",
        "canonical_path": "01_source/01_application/main.py",
    }


@app.get("/readyz")
async def readyz():
    """Readiness probe — Phase 14e container + brain available."""
    container = getattr(app.state, "container", None)
    has_brain = False
    if container is not None and hasattr(container, "has"):
        try:
            has_brain = container.has("unified_brain:production")
        except Exception:
            has_brain = False
    return {
        "status": "ready" if has_brain else "degraded",
        "container_initialized": container is not None,
        "has_brain": has_brain,
        "phase": "14e",
    }


def setup_dependency_injection():
    """Setup proper dependency injection container with config injection - NO ServiceFactory"""
    global _di_container
    
    try:
        # Import dependencies directly - NO ServiceFactory
        from app.infrastructure.di.dependency_injection import (
            DatabaseDependencies, ServiceDependencies, MessagingDependencies, AllDependencies,
            get_di_container, initialize_di_container
        )
        from app.repositories.user_repository import UserRepository
        from app.repositories.redis_token_store import RedisTokenStore
        from storage.postgres_store.interaction_store import PostgresInteractionStore
        from storage.redis_store.redis_store import RedisFeatureStore
        from app.services.kafka.kafka_service import KafkaService
        from app.infrastructure.kafka.kafka_factory import KafkaFactory
        from app.infrastructure.messaging.event_bus import KafkaEventBus
        from app.services.auth.auth_service import AuthService
        from app.services.task_state_reconstruction_service import TaskStateReconstructionService
        from app.domains.user.service import UserService
        from app.domains.experiment.service import ExperimentService
        from app.domains.auth.events import AuthEventProducer
        from app.infrastructure.outbox.outbox_pattern import get_outbox_pattern
        from app.api.metrics_routes import router as metrics_router
        
        # Create database stores with config injection
        from storage.postgres_store.interaction_store import PostgresInteractionStore
        postgres_store = PostgresInteractionStore()
        redis_store = RedisFeatureStore(settings)
        
        # Create repositories directly
        user_repo = UserRepository(postgres_store)
        redis_token_store = RedisTokenStore(redis_store.client)
        
        # Create messaging with config injection via factory and event bus
        from app.infrastructure.kafka.kafka_factory import DefaultKafkaProducerFactory
        
        kafka_factory = KafkaFactory(settings, producer_factory=DefaultKafkaProducerFactory())
        kafka_producer = kafka_factory.create_producer()
        kafka_service = KafkaService(settings, kafka_producer)
        auth_event_producer = AuthEventProducer(kafka_producer)
        
        # Create event bus for outbox
        event_bus = KafkaEventBus(kafka_producer)
        
        # Create services directly
        auth_service = AuthService(
            user_repo=user_repo,
            token_store=redis_token_store,
            event_producer=auth_event_producer
        )
        
        user_service = UserService(
            user_repo=user_repo,
            event_producer=auth_event_producer
        )
        
        experiment_service = ExperimentService(
            experiment_repo=None,  # TODO: Create experiment repo directly
            user_repo=user_repo
        )
        
        # 🔥 CRITICAL: Use ServiceFactory as canonical TaskService constructor
        # This ensures single source of truth for TaskService instance
        # ServiceFactory has tiered reconstruction, batch loading, Redis persistence
        from app.services.service_factory import ServiceFactory
        service_factory = ServiceFactory()
        task_state_reconstruction_service = service_factory.get_task_service()
        logger.info("🔥 Using ServiceFactory as canonical TaskService constructor - authority convergence established")
        
        # 🔥 CRITICAL: Hard runtime assertion - ensure authority convergence
        # This prevents future regressions where DI container and ServiceFactory diverge
        # NOTE: This assertion will be verified after DI container initialization below
        # We store the canonical instance for later verification
        
        # Create outbox pattern with event bus injection
        outbox_pattern = get_outbox_pattern(postgres_store, event_bus=event_bus)
        
        # 🔥 CRITICAL: Create authoritative cores for DI registration
        # These are documented as authoritative cores but were NOT registered in DI runtime authority
        # This is the critical architectural gap identified in validation phase
        
        # Initialize trajectory recorder for UnifiedBrain
        trajectory_recorder = None
        try:
            if getattr(settings, "enable_trajectory_recording", False):
                from infrastructure.experiment.trajectory_recorder import TrajectoryRecorder
                trajectory_recorder = TrajectoryRecorder(postgres_store)
                logger.info("🔥 Trajectory recorder initialized for UnifiedBrain")
        except Exception as e:
            logger.warning(f"⚠️ Failed to initialize trajectory recorder: {e}")
        
        # Create UnifiedLearningBrain (authoritative core: orchestration)
        # Slice 0a removed `system_mode` (was hardcoded JT in practice).
        from core.learning.unified_brain import UnifiedLearningBrain
        unified_brain = UnifiedLearningBrain(
            event_bus=event_bus,
            outbox=outbox_pattern,
            environment="production",  # 🔥 CRITICAL: Explicitly set production mode for _learning_state_repo initialization
            trajectory_recorder=trajectory_recorder
        )
        logger.info("🔥 UnifiedLearningBrain created and registered in DI container")
        
        # Create ContextualBandit (authoritative core: bandit state)
        from core.bandit.bandit import ContextualBandit
        contextual_bandit = ContextualBandit(
            uncertainty_weight=0.1,
            learning_gain_weight=0.05,
            representations=["text", "code", "multiple_choice", "video", "interactive"]
        )
        logger.info("🔥 ContextualBandit created and registered in DI container")

        # Create dependencies
        db_deps = DatabaseDependencies(
            user_repo=user_repo,
            postgres_store=postgres_store,
            redis_store=redis_store
        )
        
        service_deps = ServiceDependencies(
            auth_service=auth_service,
            user_service=user_service,
            experiment_service=experiment_service,
            task_state_reconstruction_service=task_state_reconstruction_service,
            unified_brain=unified_brain,  # 🔥 AUTHORITATIVE CORE
            contextual_bandit=contextual_bandit,  # 🔥 AUTHORITATIVE CORE
            replay_engine=None,  # TODO: Create ReplayEngine
            session_service=None  # TODO: Create SessionService
        )
        
        messaging_deps = MessagingDependencies(
            kafka_producer=kafka_producer,
            outbox_pattern=outbox_pattern
        )
        
        # Initialize DI container
        all_deps = AllDependencies(
            db=db_deps,
            services=service_deps,
            messaging=messaging_deps
        )
        
        initialize_di_container(all_deps)
        logger.info("✅ Dependency injection container initialized (config injected)")
        
        # 🔥 CRITICAL: Hard runtime assertion - ensure authority convergence
        # This prevents future regressions where DI container and ServiceFactory diverge
        from app.api.dependencies.learning import get_task_service
        di_task_service = get_task_service()
        assert di_task_service is task_state_reconstruction_service, \
            "CRITICAL: Authority divergence detected - DI container and ServiceFactory returning different TaskService instances"
        logger.info("🔥 Authority convergence assertion passed - single TaskService instance verified")

        return get_di_container()
        
    except Exception as e:
        logger.error(f"❌ Failed to setup dependency injection: {e}")
        import traceback
        logger.error(f"❌ Full traceback: {traceback.format_exc()}")
        return None

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "environment": settings.app_name
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
