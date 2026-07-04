"""Stage-0 golden-master for the unified_brain split.

Runs a FIXED event sequence through UnifiedLearningBrain (deterministic mode) against the
ISOLATED test stack, and snapshots every observable output field. Same inputs + fresh state
+ seeded RNG => identical outputs, so this is the regression gate: capture once before the
refactor, then re-run after each extraction — any drift beyond tolerance FAILS the split.

Run in-container (brain wired) against the isolated stack:
  docker run --rm -i --network hcie-final-net -e <test infra envs> \
    -e ENABLE_DETERMINISTIC_MODE=true -e DETERMINISTIC_SEED=42 \
    01_compose-api python - < scripts/brain_golden_master.py > golden.json

NEVER touches the live DB (envs point at hcie-test-pg). Resets only its own golden_* rows.
"""
import json
import sys

# brain emits heavy print() debug to stdout — route it to stderr so stdout stays pure JSON.
_REAL_STDOUT = sys.stdout
sys.stdout = sys.stderr

# Fixed, varied event sequence: cold-start, repeat (warm state), correct/incorrect,
# multiple concepts, a prerequisite pair (k2->k5 transfer).
EVENTS = [
    ("golden_u1", "k2_algorithms",    {"correct": True,  "response_time": 5.0}),
    ("golden_u1", "k2_algorithms",    {"correct": True,  "response_time": 4.0}),
    ("golden_u1", "k2_algorithms",    {"correct": False, "response_time": 9.0}),
    ("golden_u1", "k5_algorithms",    {"correct": True,  "response_time": 6.0}),
    ("golden_u2", "k2_variables",     {"correct": False, "response_time": 12.0}),
    ("golden_u2", "k2_variables",     {"correct": True,  "response_time": 5.0}),
    ("golden_u3", "k2_control",       {"correct": True,  "response_time": 3.0}),
]

FIELDS = ["mastery", "uncertainty", "J_value", "zpd_score", "processing_mode",
          "mastery_delta", "transfer_amount", "lyapunov_mastery", "bayesian_alpha",
          "bayesian_beta", "kalman_mastery", "effective_learning_rate"]

def _f(v):
    return round(v, 6) if isinstance(v, float) else v

try:
    from config.env import settings
    from storage.postgres_store.interaction_store import PostgresInteractionStore
    from storage.redis_store.redis_store import RedisFeatureStore
    from app.repositories.learning_state_repository import LearningStateRepository
    from app.infrastructure.kafka.kafka_factory import KafkaFactory, DefaultKafkaProducerFactory
    from app.infrastructure.outbox.outbox_pattern import get_outbox_pattern
    from core.learning.unified_brain import UnifiedLearningBrain

    pg = PostgresInteractionStore()
    # reset only our golden rows so reruns are reproducible
    for tbl in ("experiment_trajectories", "interactions", "learning_state"):
        try:
            pg.execute_write(f"DELETE FROM {tbl} WHERE user_id LIKE 'golden_%%'")
        except Exception:
            pass
    rs = RedisFeatureStore()
    try:
        rs.redis_client.flushdb()
    except Exception:
        pass
    lsr = LearningStateRepository(pg, redis_store=rs)
    kf = KafkaFactory(settings, producer_factory=DefaultKafkaProducerFactory())
    ob = get_outbox_pattern(pg, event_bus=kf.create_producer())
    brain = UnifiedLearningBrain(event_bus=None, outbox=ob, redis_store=rs,
                                 postgres_store=pg, learning_state_repo=lsr,
                                 environment="production")

    snapshot = {}
    for i, (uid, concept, interaction) in enumerate(EVENTS):
        eid = f"golden-{i}"
        r = brain.process_event(user_id=uid, concept=concept, interaction=interaction,
                                mode="write", event_id=eid, interaction_id=eid)
        snapshot[f"{i}:{uid}:{concept}:{interaction['correct']}"] = {
            k: _f(getattr(r, k, None)) for k in FIELDS
        }
    # restore real stdout: emit pure JSON only
    sys.stdout = _REAL_STDOUT
    sys.stderr.write("GOLDEN_DONE\n")
    print(json.dumps(snapshot, indent=2, sort_keys=True))
except Exception as e:
    import traceback
    traceback.print_exc()
    sys.stdout = _REAL_STDOUT
    print(json.dumps({"_error": f"{type(e).__name__}: {str(e)[:200]}"}))
    sys.exit(1)
