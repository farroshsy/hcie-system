from app.runtime.composition import RuntimeRole
from app.runtime.unified_brain_runtime_service import RuntimeMode, UnifiedBrainRuntimeService


class FakeResult:
    mastery = 0.75
    mastery_delta = 0.05
    transfer_efficiency = 0.8
    transfer_prospective = 0.7
    challenge = 0.6
    uncertainty = 0.2
    zpd_score = 0.81
    zpd_target = 0.75
    zpd_alignment_error = 0.02
    zpd_delta_signal = 0.01
    ensemble_variance = 0.03
    confidence = 0.8
    J_value = 0.85
    lyapunov_mastery = 0.74
    bayesian_alpha = 3.5
    bayesian_beta = 7.2
    bayesian_gamma = 0.5
    kalman_mastery = 0.76
    kalman_covariance = 0.1
    kalman_process_noise = 0.01
    kalman_measurement_noise = 0.01
    ensemble_weights = {"lyapunov": 0.33, "bayesian": 0.33, "kalman": 0.34}
    policy = "hcie"
    policy_multiplier = 1.0
    adaptive_rate = 0.02
    transfer_amounts = {"related_concept": 0.1}
    processing_mode = "jt"
    event_id = None
    timestamp = "2026-05-20T00:00:00"


class FakeBrain:
    def __init__(self):
        self.calls = []

    def process_event(self, **kwargs):
        self.calls.append(kwargs)
        return FakeResult()


class FakeIdempotency:
    def __init__(self):
        self.marked = []
        self.processed = set()

    def is_processed(self, event_id):
        return event_id in self.processed

    def get_cached_result(self, event_id):
        return {"cached": True, "event_id": event_id}

    def acquire_lock(self, event_id):
        return True

    def mark_processed(self, event_id, result):
        self.marked.append((event_id, result))
        self.processed.add(event_id)

    def release_lock(self, event_id):
        self.released = event_id


class FakeOwnership:
    def __init__(self):
        self.events = []

    def set_writer(self, writer):
        self.events.append(("set", str(writer)))

    def clear_writer(self):
        self.events.append(("clear", None))


class FakeTransaction:
    def __init__(self):
        self.saved = []

    def __enter__(self):
        self.entered = True
        return self

    def __exit__(self, exc_type, exc, tb):
        self.exited = True
        self.exc_type = exc_type


class FakeOutbox:
    def __init__(self):
        self.saved = []

    def create_event(self, event_id, event_type, topic, payload):
        return {
            "event_id": event_id,
            "event_type": event_type,
            "topic": topic,
            "payload": payload,
        }

    def save_event(self, event, transaction=None):
        self.saved.append((event, transaction))


class SettingsStub:
    pass


def test_process_interaction_calls_brain_inside_runtime_boundary():
    tx = FakeTransaction()
    brain = FakeBrain()
    outbox = FakeOutbox()
    idem = FakeIdempotency()
    ownership = FakeOwnership()
    service = UnifiedBrainRuntimeService(
        role=RuntimeRole.LEARNING_CONSUMER,
        settings=SettingsStub(),
        unified_brain=brain,
        outbox=outbox,
        idempotency_manager=idem,
        ownership=ownership,
        transaction_factory=lambda: tx,
    )

    result = service.process_interaction(
        user_id="u1",
        concept_id="loops",
        interaction={"correct": True},
        event_id="evt-1",
        event_data={"source": "test"},
    )

    assert result.mode == RuntimeMode.CANONICAL_WRITE
    assert result.payload["mastery"] == 0.75
    assert brain.calls[0]["user_id"] == "u1"
    assert brain.calls[0]["concept"] == "loops"
    assert outbox.saved[0][0]["event_type"] == "CognitionUpdated"
    assert idem.marked[0][0] == "evt-1"
    assert ownership.events[0][0] == "set"
    assert ownership.events[-1] == ("clear", None)
    assert tx.entered is True
    assert tx.exited is True


def test_process_interaction_returns_cached_result_for_duplicate_event():
    brain = FakeBrain()
    idem = FakeIdempotency()
    idem.processed.add("evt-1")
    service = UnifiedBrainRuntimeService(
        role=RuntimeRole.LEARNING_CONSUMER,
        settings=SettingsStub(),
        unified_brain=brain,
        idempotency_manager=idem,
    )

    result = service.process_interaction(
        user_id="u1",
        concept_id="loops",
        interaction={"correct": True},
        event_id="evt-1",
        event_data={},
    )

    assert result.payload == {"cached": True, "event_id": "evt-1"}
    assert brain.calls == []
