"""
Common Learning API Dependencies

Provides standardized FastAPI dependency functions for learning endpoints.
Improves predictability by centralizing dependency acquisition patterns.

⚠️ CRITICAL: These dependencies preserve authoritative service identity.
DO NOT reconstruct authoritative cores (TaskService, UnifiedBrain, ContextualBandit).
Use adapter for gradual migration to preserve runtime continuity.
"""

import logging
from fastapi import Depends

logger = logging.getLogger(__name__)


def get_task_service():
    """
    FastAPI dependency for TaskService.
    
    ⚠️ AUTHORITATIVE CORE: TaskService owns mastery state.
    Direct DI access (Stage 2) - no adapter fallback.
    
    Usage:
        @router.get("/endpoint")
        async def endpoint(task_service = Depends(get_task_service)):
            ...
    """
    from app.infrastructure.di.dependency_injection import get_di_container
    container = get_di_container()
    return container.get_task_state_reconstruction_service()


def get_unified_brain():
    """
    FastAPI dependency for UnifiedLearningBrain.
    
    ⚠️ AUTHORITATIVE CORE: UnifiedBrain owns learning orchestration.
    Direct DI access (Stage 2) - no adapter fallback.
    
    Usage:
        @router.get("/endpoint")
        async def endpoint(brain = Depends(get_unified_brain)):
            ...
    """
    from app.infrastructure.di.dependency_injection import get_di_container
    container = get_di_container()
    return container.get_unified_brain()


def get_session_service():
    """
    FastAPI dependency for SessionService.
    
    Direct DI access (Stage 2) - no adapter fallback.
    
    Usage:
        @router.get("/endpoint")
        async def endpoint(session_service = Depends(get_session_service)):
            ...
    """
    from app.infrastructure.di.dependency_injection import get_di_container
    container = get_di_container()
    return container.get_session_service()


def get_auth_service():
    """
    FastAPI dependency for AuthService.
    
    Direct DI access (Stage 2) - no adapter fallback.
    
    Usage:
        @router.get("/endpoint")
        async def endpoint(auth_service = Depends(get_auth_service)):
            ...
    """
    from app.infrastructure.di.dependency_injection import get_di_container
    container = get_di_container()
    return container.get_service_dependencies().auth_service


def get_bandit_service():
    """
    FastAPI dependency for bandit service.
    
    ⚠️ AUTHORITATIVE CORE: ContextualBandit owns bandit state.
    Direct DI access (Stage 2) - no adapter fallback.
    
    Usage:
        @router.get("/endpoint")
        async def endpoint(bandit_service = Depends(get_bandit_service)):
            ...
    """
    from app.infrastructure.di.dependency_injection import get_di_container
    container = get_di_container()
    return container.get_contextual_bandit()


# ==============================
# Database Dependencies
# ==============================

def get_postgres_store():
    """
    FastAPI dependency for PostgresInteractionStore.
    
    Provides direct database access for endpoints that need it.
    ⚠️ WARNING: This bypasses repository pattern - use sparingly.
    
    Usage:
        @router.get("/endpoint")
        async def endpoint(db_store = Depends(get_postgres_store)):
            ...
    """
    from storage.postgres_store.interaction_store import PostgresInteractionStore
    return PostgresInteractionStore()


def get_redis_store():
    """
    FastAPI dependency for RedisFeatureStore.
    
    Provides Redis feature store access for caching and optimization.
    
    Usage:
        @router.get("/endpoint")
        async def endpoint(redis_store = Depends(get_redis_store)):
            ...
    """
    from storage.redis_store.redis_store import RedisFeatureStore
    from config.env import settings
    return RedisFeatureStore(settings)


# ==============================
# Learning Engine Dependencies
# ==============================

def get_learning_engine():
    """Phase 14g (Slice 0a): quarantined.

    The shadow-mode integration was the only remaining caller path that
    silently routed to the V2 LearningLoopEngine. Per the FINAL Semantic
    Honesty Law (Slice 0 plan):

      forbidden states = fake-live placeholder / semantic lie / silent
      degradation / partial hidden authority.

    Invoking this dependency previously returned `shadow_integration`,
    which depends on the quarantined `LearningLoopEngineV2`. That is a
    fake authority surface: callers believed they were getting a learning
    engine; they were getting a comparison wrapper around a non-existent
    legacy engine. Routes that need cognition should depend on
    `app.runtime.its_runtime_service.ItsRuntimeService` instead
    (via `app.api.v3.dependencies_its.get_its_runtime_service`).
    """
    raise NotImplementedError(
        "get_learning_engine() was quarantined in Slice 0a (Phase 14g). "
        "The shadow_mode_integration path depended on the V2 LearningLoopEngine "
        "which was quarantined in Phase 14c. Use ItsRuntimeService via "
        "app.api.v3.dependencies_its.get_its_runtime_service instead."
    )


# ==============================
# Migration Tracking
# ==============================

__dependency_registry__ = {
    "get_task_service": "TaskService (authoritative core)",
    "get_unified_brain": "UnifiedLearningBrain (authoritative core)",
    "get_session_service": "SessionService",
    "get_auth_service": "AuthService",
    "get_bandit_service": "BanditService (authoritative core)",
    "get_postgres_store": "PostgresInteractionStore (direct DB access)",
    "get_redis_store": "RedisFeatureStore (cache)",
    "get_learning_engine": "QUARANTINED — Phase 14g Slice 0a (raises NotImplementedError)"
}

logger.info(f"✅ Common learning dependencies loaded: {len(__dependency_registry__)} functions")
