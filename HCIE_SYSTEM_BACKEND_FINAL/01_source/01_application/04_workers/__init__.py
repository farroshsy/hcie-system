"""Worker package for HCIE_SYSTEM_BACKEND_FINAL.

Live workers (referenced by ``docker-compose.final.yml``):
    - ``learning_consumer``
    - ``projection_consumer``
    - ``trajectory_recorder_consumer``
    - ``adaptation_consumer``
    - ``projection_stream_gateway``
    - ``auth_consumer_worker``
    - ``dlq_replay_worker``
    - ``auto_healer``
    - ``outbox_worker``        (scale-out profile)

Deprecated / legacy workers — NOT compose-wired, kept only for git history:
    - ``phase8_tournament``    (Avro-based; replaced by JSON-based projection
      and the FINAL replay engine)
    - ``research_worker``      (Avro-based; superseded by
      ``exploration_instrumentation_consumer`` + ``transfer_measurement_consumer``)
    - ``multi_worker_coordinator`` (V2 outbox scale-up — superseded by running
      multiple ``outbox-worker`` replicas under the ``scale-out`` profile)

If you find yourself wanting to revive a deprecated worker, audit it against
the FINAL contracts in ``02_infrastructure/02_experiment`` and either port it
into a compose-wired worker or delete it.
"""

