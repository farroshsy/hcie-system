"""
Dependency Injection Container
Explicit dependency injection without ServiceFactory anti-pattern
"""

import logging
from typing import Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class DatabaseDependencies:
    """Database-related dependencies"""
    user_repo: Any
    postgres_store: Any
    redis_store: Any

@dataclass
class ServiceDependencies:
    """Service-related dependencies"""
    auth_service: Any
    user_service: Any
    experiment_service: Any
    task_state_reconstruction_service: Any  # TaskService (authoritative core: mastery ownership)
    unified_brain: Any = None  # UnifiedLearningBrain (authoritative core: orchestration)
    contextual_bandit: Any = None  # ContextualBandit (authoritative core: bandit state)
    replay_engine: Any = None  # ReplayEngine (authoritative core: replay authority)
    session_service: Any = None  # SessionService

@dataclass
class MessagingDependencies:
    """Messaging-related dependencies"""
    kafka_producer: Any
    outbox_pattern: Any

@dataclass
class AllDependencies:
    """All dependencies for explicit injection"""
    db: DatabaseDependencies
    services: ServiceDependencies
    messaging: MessagingDependencies

class DIContainer:
    """
    Dependency Injection Container
    Explicit, testable, no global state
    """
    
    def __init__(self):
        self._dependencies: Optional[AllDependencies] = None
        self._initialized = False
    
    def initialize(self, dependencies: AllDependencies):
        """Initialize container with all dependencies"""
        self._dependencies = dependencies
        self._initialized = True
        logger.info("✅ DI Container initialized")
    
    def get_db_dependencies(self) -> DatabaseDependencies:
        """Get database dependencies"""
        if not self._initialized:
            raise RuntimeError("DI Container not initialized")
        return self._dependencies.db
    
    def get_service_dependencies(self) -> ServiceDependencies:
        """Get service dependencies"""
        if not self._initialized:
            raise RuntimeError("DI Container not initialized")
        return self._dependencies.services
    
    def get_task_state_reconstruction_service(self) -> Any:
        """Get task state reconstruction service specifically (TaskService - authoritative core)"""
        if not self._initialized:
            raise RuntimeError("DI Container not initialized")
        return self._dependencies.services.task_state_reconstruction_service

    def get_unified_brain(self) -> Any:
        """Get UnifiedLearningBrain (authoritative core: orchestration)"""
        if not self._initialized:
            raise RuntimeError("DI Container not initialized")
        return self._dependencies.services.unified_brain

    def get_contextual_bandit(self) -> Any:
        """Get ContextualBandit (authoritative core: bandit state)"""
        if not self._initialized:
            raise RuntimeError("DI Container not initialized")
        return self._dependencies.services.contextual_bandit

    def get_replay_engine(self) -> Any:
        """Get ReplayEngine (authoritative core: replay authority)"""
        if not self._initialized:
            raise RuntimeError("DI Container not initialized")
        return self._dependencies.services.replay_engine

    def get_session_service(self) -> Any:
        """Get SessionService"""
        if not self._initialized:
            raise RuntimeError("DI Container not initialized")
        return self._dependencies.services.session_service
    
    def get_messaging_dependencies(self) -> MessagingDependencies:
        """Get messaging dependencies"""
        if not self._initialized:
            raise RuntimeError("DI Container not initialized")
        return self._dependencies.messaging
    
    def get_all_dependencies(self) -> AllDependencies:
        """Get all dependencies"""
        if not self._initialized:
            raise RuntimeError("DI Container not initialized")
        return self._dependencies

# Global container instance (still needed for bootstrap)
_di_container: Optional[DIContainer] = None

def get_di_container() -> DIContainer:
    """Get global DI container (for bootstrap only)"""
    global _di_container
    if _di_container is None:
        _di_container = DIContainer()
    return _di_container

def initialize_di_container(dependencies: AllDependencies) -> DIContainer:
    """Initialize global DI container"""
    container = get_di_container()
    container.initialize(dependencies)
    return container
