"""
Canonical Runtime Exposure API Dependencies (V3)

Provides FastAPI dependency functions for V3 canonical runtime APIs.
Wires projection services to V2 converged systems via DI container.

Authority State: experimental → converging → authoritative → frozen
Runtime Contract Version: 1.0
"""

import logging

logger = logging.getLogger(__name__)


def get_governance_projection():
    """
    FastAPI dependency for GovernanceProjection.
    
    Wires to V2 ConstitutionalJTGovernance and PostgresStore via DI container.
    Projection service is stateless view - NO temporal memory ownership.
    """
    from app.infrastructure.di.dependency_injection import get_di_container
    from app.services.projection import GovernanceProjection
    from storage.postgres_store.interaction_store import PostgresInteractionStore
    
    container = get_di_container()
    
    # Get V2 converged systems via DI
    unified_brain = container.get_unified_brain()
    
    # Access jt_governance attribute (not governance)
    constitutional_jt_governance = unified_brain.jt_governance if hasattr(unified_brain, 'jt_governance') else None
    
    # Create postgres store directly (not via DI)
    postgres_store = PostgresInteractionStore()
    
    # Create projection service (stateless view)
    return GovernanceProjection(
        constitutional_jt_governance=constitutional_jt_governance,
        postgres_store=postgres_store
    )


def get_mutation_projection():
    """
    FastAPI dependency for MutationProjection.
    
    Wires to V2 UnifiedBrain and Outbox via DI container.
    Projection service is stateless view - NO temporal memory ownership.
    All adaptive state mutations must flow through canonical topology.
    """
    from app.infrastructure.di.dependency_injection import get_di_container
    from app.services.projection import MutationProjection
    from app.infrastructure.outbox.outbox_pattern import get_outbox_pattern
    from storage.postgres_store.interaction_store import PostgresInteractionStore
    
    container = get_di_container()
    
    # Get V2 converged systems via DI
    unified_brain = container.get_unified_brain()
    
    # Create postgres store for outbox
    db_store = PostgresInteractionStore()
    
    # Get outbox pattern directly with db_store
    outbox = get_outbox_pattern(db_store)
    
    # Create projection service (stateless view)
    return MutationProjection(
        unified_brain=unified_brain,
        outbox=outbox
    )


def get_event_projection():
    """
    FastAPI dependency for EventProjection.
    
    Wires to V2 Outbox and KafkaConsumer via DI container.
    Projection service is stateless view - NO temporal memory ownership.
    """
    from app.infrastructure.di.dependency_injection import get_di_container
    from app.services.projection import EventProjection
    from app.infrastructure.outbox.outbox_pattern import get_outbox_pattern
    from app.infrastructure.kafka.kafka_factory import KafkaFactory
    from storage.postgres_store.interaction_store import PostgresInteractionStore
    from config.env import settings
    
    container = get_di_container()
    
    # Create postgres store for outbox
    db_store = PostgresInteractionStore()
    
    # Get outbox pattern directly with db_store
    outbox = get_outbox_pattern(db_store)
    
    # Create kafka consumer via factory (using create_consumer method)
    kafka_factory = KafkaFactory(settings)
    kafka_consumer = kafka_factory.create_consumer(group_id="hcie-consumer", topics=["hcie.events"])
    
    # Create projection service (stateless view)
    return EventProjection(
        outbox=outbox,
        kafka_consumer=kafka_consumer
    )


def get_replay_projection():
    """
    FastAPI dependency for ReplayProjection.
    
    Wires to V2 ReplayEngine via DI container.
    Projection service is stateless view - NO temporal memory ownership.
    """
    from app.infrastructure.di.dependency_injection import get_di_container
    from app.services.projection import ReplayProjection
    
    container = get_di_container()
    
    # Get V2 converged systems via DI
    replay_engine = container.get_replay_engine()
    
    # Create projection service (stateless view)
    return ReplayProjection(
        replay_engine=replay_engine
    )


def get_lifecycle_projection():
    """
    FastAPI dependency for LifecycleProjection.
    
    Wires to V2 SessionService via DI container.
    Projection service is stateless view - NO temporal memory ownership.
    """
    from app.infrastructure.di.dependency_injection import get_di_container
    from app.services.projection import LifecycleProjection
    
    container = get_di_container()
    
    # Get V2 converged systems via DI
    session_service = container.get_session_service()
    
    # Create projection service (stateless view)
    return LifecycleProjection(
        session_service=session_service
    )


def get_trajectory_projection():
    """
    FastAPI dependency for TrajectoryProjection.
    
    Wires to V2 PostgresStore via DI container.
    Projection service is stateless view - NO temporal memory ownership.
    """
    from app.infrastructure.di.dependency_injection import get_di_container
    from app.services.projection import TrajectoryProjection
    from storage.postgres_store.interaction_store import PostgresInteractionStore
    
    # Create postgres store directly (not via DI)
    postgres_store = PostgresInteractionStore()
    
    # Create projection service (stateless view)
    return TrajectoryProjection(
        postgres_store=postgres_store
    )


def get_authority_projection():
    """
    FastAPI dependency for AuthorityProjection.
    
    Projection service is stateless view - NO temporal memory ownership.
    """
    from app.services.projection import AuthorityProjection
    
    # Create projection service (stateless view)
    return AuthorityProjection()


def get_transfer_projection():
    """
    FastAPI dependency for TransferProjection.
    
    Wires to V2 UnifiedBrain via DI container.
    Projection service is stateless view - NO temporal memory ownership.
    """
    from app.infrastructure.di.dependency_injection import get_di_container
    from app.services.projection import TransferProjection
    
    container = get_di_container()
    
    # Get V2 converged systems via DI
    unified_brain = container.get_unified_brain()
    
    # Create projection service (stateless view)
    return TransferProjection(
        unified_brain=unified_brain
    )


def get_policy_projection():
    """
    FastAPI dependency for PolicyProjection.
    
    Wires to V2 UnifiedBrain via DI container.
    Projection service is stateless view - NO temporal memory ownership.
    """
    from app.infrastructure.di.dependency_injection import get_di_container
    from app.services.projection import PolicyProjection
    
    container = get_di_container()
    
    # Get V2 converged systems via DI
    unified_brain = container.get_unified_brain()
    
    # Create projection service (stateless view)
    return PolicyProjection(
        unified_brain=unified_brain
    )


def get_attribution_projection():
    """
    FastAPI dependency for AttributionProjection.
    
    Wires to V2 UnifiedBrain via DI container.
    Projection service is stateless view - NO temporal memory ownership.
    """
    from app.infrastructure.di.dependency_injection import get_di_container
    from app.services.projection import AttributionProjection
    
    container = get_di_container()
    
    # Get V2 converged systems via DI
    unified_brain = container.get_unified_brain()
    
    # Create projection service (stateless view)
    return AttributionProjection(
        unified_brain=unified_brain
    )


def get_objective_projection():
    """
    FastAPI dependency for ObjectiveProjection.
    
    Wires to V2 UnifiedBrain via DI container.
    Projection service is stateless view - NO temporal memory ownership.
    """
    from app.infrastructure.di.dependency_injection import get_di_container
    from app.services.projection import ObjectiveProjection
    
    container = get_di_container()
    
    # Get V2 converged systems via DI
    unified_brain = container.get_unified_brain()
    
    # Create projection service (stateless view)
    return ObjectiveProjection(
        unified_brain=unified_brain
    )


def get_recommendation_projection():
    """
    FastAPI dependency for RecommendationProjection.
    
    Wires to V2 UnifiedBrain via DI container.
    Projection service is stateless view - NO temporal memory ownership.
    """
    from app.infrastructure.di.dependency_injection import get_di_container
    from app.services.projection import RecommendationProjection
    
    container = get_di_container()
    
    # Get V2 converged systems via DI
    unified_brain = container.get_unified_brain()
    
    # Wire postgres_store so latest_projection_for_user() can read

    # learner_projections. Previously omitted → store=None → every call
    # short-circuited to projection_missing / recommended_concept="unknown".
    pg_store = None
    try:
        from infrastructure.storage.postgres_store.interaction_store import PostgresInteractionStore
        pg_store = PostgresInteractionStore()
    except Exception:
        pass

    # Create projection service (stateless view)
    return RecommendationProjection(
        unified_brain=unified_brain,
        postgres_store=pg_store,
    )


# ==============================
# Dependency Registry
# ==============================

DEPENDENCY_REGISTRY = {
    'governance': get_governance_projection,
    'mutation': get_mutation_projection,
    'event': get_event_projection,
    'replay': get_replay_projection,
    'lifecycle': get_lifecycle_projection,
    'trajectory': get_trajectory_projection,
    'authority': get_authority_projection,
    'transfer': get_transfer_projection,
    'policy': get_policy_projection,
    'attribution': get_attribution_projection,
    'objective': get_objective_projection,
    'recommendation': get_recommendation_projection
}

logger.info(f"✅ V3 canonical runtime dependencies loaded: {len(DEPENDENCY_REGISTRY)} functions")
