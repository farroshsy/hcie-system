"""
ServiceFactory Adapter - Compatibility Layer for DI Migration

Provides ServiceFactory-like interface backed by DI container.
Allows gradual migration from ServiceFactory to DI.

⚠️ CRITICAL: This is a COMPATIBILITY LAYER for gradual migration.
DO NOT use this as a permanent solution. The goal is to migrate
all usage to direct DI container access, then remove this adapter.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class ServiceFactoryAdapter:
    """
    Compatibility layer for gradual migration from ServiceFactory to DI container.
    
    ⚠️ CRITICAL: This adapter preserves singleton semantics during migration.
    DO NOT reconstruct authoritative cores via lambdas until lifecycle semantics are fully understood.
    
    Authoritative cores (TaskService, UnifiedBrain, ContextualBandit, ReplayEngine) are stateful
    runtime engines, not simple services. Their lifecycle requirements are complex:
    - Reconstruction order matters
    - Replay consistency matters
    - Singleton identity matters
    - Cache warming matters
    
    ⚠️ DEPRECATED (Stage 2): Use direct DI access from common dependencies.
    This adapter will be removed in Stage 3.
    """
    
    def __init__(self):
        from .dependency_injection import get_di_container
        self._container = get_di_container()
        self._services_cache = {}  # Preserve singleton semantics during migration
        logger.warning("⚠️ ServiceFactoryAdapter DEPRECATED (Stage 2) - Use direct DI access from common dependencies")
    
    def get_task_service(self):
        """
        Get TaskService from DI container.
        
        ⚠️ CRITICAL: TaskService is an authoritative core (mastery ownership).
        Preserve its singleton identity during migration.
        
        STAGE 1: Prefer DI container, fallback to ServiceFactory
        """
        if 'task_service' not in self._services_cache:
            # Prefer DI container (Stage 1)
            try:
                task_service = self._container.get_task_state_reconstruction_service()
                if task_service is not None:
                    self._services_cache['task_service'] = task_service
                    logger.info("TaskService retrieved via DI container (Stage 1)")
                    return task_service
            except (AttributeError, RuntimeError) as e:
                logger.debug(f"DI container not available for TaskService: {e}")
            
            # Fallback to ServiceFactory during migration
            from app.services.service_factory import ServiceFactory
            factory = ServiceFactory()
            task_service = factory.get_task_service()
            self._services_cache['task_service'] = task_service
            logger.info("TaskService retrieved via ServiceFactory fallback (Stage 1)")
        return self._services_cache['task_service']
    
    def get_unified_brain(self):
        """
        Get UnifiedLearningBrain from DI container.
        
        ⚠️ CRITICAL: UnifiedBrain is an authoritative core (learning orchestration).
        Preserve its singleton identity during migration.
        
        STAGE 1: Prefer DI container, fallback to ServiceFactory
        """
        if 'unified_brain' not in self._services_cache:
            # Prefer DI container (Stage 1)
            try:
                unified_brain = self._container.get_unified_brain()
                if unified_brain is not None:
                    self._services_cache['unified_brain'] = unified_brain
                    logger.info("UnifiedLearningBrain retrieved via DI container (Stage 1)")
                    return unified_brain
            except (AttributeError, RuntimeError) as e:
                logger.debug(f"DI container not available for UnifiedLearningBrain: {e}")
            
            # Fallback to ServiceFactory during migration
            from app.services.service_factory import ServiceFactory
            factory = ServiceFactory()
            unified_brain = factory.unified_brain if hasattr(factory, 'unified_brain') else None
            self._services_cache['unified_brain'] = unified_brain
            logger.info("UnifiedLearningBrain retrieved via ServiceFactory fallback (Stage 1)")
        return self._services_cache['unified_brain']
    
    def get_auth_service(self):
        """
        Get AuthService from DI container.
        
        STAGE 1: Prefer DI container, fallback to ServiceFactory
        """
        if 'auth_service' not in self._services_cache:
            # Prefer DI container (Stage 1)
            try:
                auth_service = self._container.get_service_dependencies().auth_service
                if auth_service is not None:
                    self._services_cache['auth_service'] = auth_service
                    logger.info("AuthService retrieved via DI container (Stage 1)")
                    return auth_service
            except (AttributeError, RuntimeError) as e:
                logger.debug(f"DI container not available for AuthService: {e}")
            
            # Fallback to ServiceFactory during migration
            from app.services.service_factory import ServiceFactory
            factory = ServiceFactory()
            auth_service = factory.get_auth_service()
            self._services_cache['auth_service'] = auth_service
            logger.info("AuthService retrieved via ServiceFactory fallback (Stage 1)")
        return self._services_cache['auth_service']
    
    def get_session_service(self):
        """
        Get SessionService from DI container.
        
        STAGE 1: Prefer DI container, fallback to ServiceFactory
        """
        if 'session_service' not in self._services_cache:
            # Prefer DI container (Stage 1)
            try:
                session_service = self._container.get_session_service()
                if session_service is not None:
                    self._services_cache['session_service'] = session_service
                    logger.info("SessionService retrieved via DI container (Stage 1)")
                    return session_service
            except (AttributeError, RuntimeError) as e:
                logger.debug(f"DI container not available for SessionService: {e}")
            
            # Fallback to ServiceFactory during migration
            from app.services.service_factory import ServiceFactory
            factory = ServiceFactory()
            session_service = factory.get_session_service()
            self._services_cache['session_service'] = session_service
            logger.info("SessionService retrieved via ServiceFactory fallback (Stage 1)")
        return self._services_cache['session_service']
    
    def get_bandit_service(self):
        """
        Get bandit service from DI container.
        
        ⚠️ CRITICAL: ContextualBandit is an authoritative core (bandit state ownership).
        Preserve its singleton identity during migration.
        
        STAGE 1: Prefer DI container, fallback to ServiceFactory
        """
        if 'bandit_service' not in self._services_cache:
            # Prefer DI container (Stage 1)
            try:
                bandit_service = self._container.get_contextual_bandit()
                if bandit_service is not None:
                    self._services_cache['bandit_service'] = bandit_service
                    logger.info("ContextualBandit retrieved via DI container (Stage 1)")
                    return bandit_service
            except (AttributeError, RuntimeError) as e:
                logger.debug(f"DI container not available for ContextualBandit: {e}")
            
            # Fallback to ServiceFactory during migration
            from app.services.service_factory import ServiceFactory
            factory = ServiceFactory()
            bandit_service = factory.get_bandit_service() if hasattr(factory, 'get_bandit_service') else None
            self._services_cache['bandit_service'] = bandit_service
            logger.info("ContextualBandit retrieved via ServiceFactory fallback (Stage 1)")
        return self._services_cache['bandit_service']


# Singleton instance for backward compatibility during migration
_service_factory_adapter: Optional[ServiceFactoryAdapter] = None


def get_service_factory_adapter() -> ServiceFactoryAdapter:
    """
    Get singleton ServiceFactoryAdapter instance.
    
    This provides a drop-in replacement for ServiceFactory during migration.
    Code can replace:
        from app.services.service_factory import ServiceFactory
        factory = ServiceFactory()
    with:
        from app.infrastructure.di.service_factory_adapter import get_service_factory_adapter
        adapter = get_service_factory_adapter()
    """
    global _service_factory_adapter
    if _service_factory_adapter is None:
        _service_factory_adapter = ServiceFactoryAdapter()
    return _service_factory_adapter
