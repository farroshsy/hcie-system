"""FINAL-native auto-healing controller.

This worker watches Prometheus health signals and performs conservative
Docker-level remediation with cooldowns. It is intentionally opt-in because
it mounts the Docker socket. The Phase-3 sweep can run without it; production
demonstrations can enable it through the ``self-healing`` compose profile.
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass, field
from typing import Dict, Optional

import docker
import requests
from prometheus_client import Counter, Gauge, start_http_server

logger = logging.getLogger(__name__)

HEALER_ACTIONS = Counter("hcie_auto_healer_actions_total", "Auto-healer actions", ["action", "target"])
HEALER_ERRORS = Counter("hcie_auto_healer_errors_total", "Auto-healer loop/action errors", ["stage"])
HEALER_LAST_LOOP_TS = Gauge("hcie_auto_healer_last_loop_timestamp", "Unix timestamp of last healer loop")


@dataclass(frozen=True)
class HealerConfig:
    prometheus_url: str = os.getenv("PROMETHEUS_URL", "http://prometheus:9090")
    metrics_port: int = int(os.getenv("AUTO_HEALER_METRICS_PORT", "8004"))
    interval_s: float = float(os.getenv("AUTO_HEALER_INTERVAL_S", "30"))
    cooldown_s: float = float(os.getenv("AUTO_HEALER_COOLDOWN_S", "180"))
    enabled: bool = os.getenv("AUTO_HEALER_ENABLED", "true").lower() in {"1", "true", "yes"}
    dry_run: bool = os.getenv("AUTO_HEALER_DRY_RUN", "false").lower() in {"1", "true", "yes"}
    container_names: Dict[str, str] = field(
        default_factory=lambda: {
            "api": os.getenv("AUTO_HEALER_API_CONTAINER", "hcie-final-api"),
            "kafka": os.getenv("AUTO_HEALER_KAFKA_CONTAINER", "hcie-final-kafka"),
            "redis": os.getenv("AUTO_HEALER_REDIS_CONTAINER", "hcie-final-redis"),
            "postgres": os.getenv("AUTO_HEALER_POSTGRES_CONTAINER", "hcie-final-postgres"),
            "kafka_connect": os.getenv("AUTO_HEALER_KAFKA_CONNECT_CONTAINER", "hcie-final-kafka-connect"),
            "learning_consumer": os.getenv("AUTO_HEALER_LEARNING_CONTAINER", "hcie-final-learning-consumer"),
            "projection_consumer": os.getenv("AUTO_HEALER_PROJECTION_CONTAINER", "hcie-final-projection-consumer"),
            "trajectory_recorder": os.getenv("AUTO_HEALER_TRAJECTORY_CONTAINER", "hcie-final-trajectory-recorder"),
            "dlq_replay": os.getenv("AUTO_HEALER_DLQ_CONTAINER", "hcie-final-dlq-replay-worker"),
        }
    )


class AutoHealer:
    """Conservative remediation loop driven by Prometheus signals."""

    def __init__(self, config: Optional[HealerConfig] = None) -> None:
        self.config = config or HealerConfig()
        self.client = docker.from_env()
        self.last_actions: Dict[str, float] = {}

    def query(self, expression: str) -> Optional[float]:
        try:
            response = requests.get(
                f"{self.config.prometheus_url}/api/v1/query",
                params={"query": expression},
                timeout=10,
            )
            response.raise_for_status()
            payload = response.json()
            results = payload.get("data", {}).get("result", [])
            if not results:
                return None
            return float(results[0]["value"][1])
        except Exception as exc:  # noqa: BLE001
            logger.warning("Prometheus query failed: %s -> %r", expression, exc)
            HEALER_ERRORS.labels(stage="prometheus_query").inc()
            return None

    def can_act(self, action: str) -> bool:
        now = time.time()
        last = self.last_actions.get(action, 0.0)
        if now - last < self.config.cooldown_s:
            return False
        self.last_actions[action] = now
        return True

    def restart_container(self, logical_name: str, reason: str) -> None:
        container_name = self.config.container_names[logical_name]
        action = f"restart:{container_name}:{reason}"
        if not self.config.enabled or not self.can_act(action):
            return
        logger.warning("Auto-healer restarting %s because %s", container_name, reason)
        HEALER_ACTIONS.labels(action="restart", target=container_name).inc()
        if self.config.dry_run:
            logger.warning("AUTO_HEALER_DRY_RUN=true, not restarting %s", container_name)
            return
        try:
            self.client.containers.get(container_name).restart(timeout=20)
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to restart %s: %r", container_name, exc)
            HEALER_ERRORS.labels(stage="restart_container").inc()

    def check_up_metric(self, job: str, logical_name: str) -> None:
        value = self.query(f'up{{job="{job}"}}')
        if value == 0:
            self.restart_container(logical_name, f"prometheus job {job} is down")

    def check_api_error_ratio(self) -> None:
        error_rate = self.query('sum(rate(http_requests_total{job="hcie-api",status=~"5.."}[2m]))')
        total_rate = self.query('sum(rate(http_requests_total{job="hcie-api"}[2m]))')
        if error_rate is None or total_rate is None or total_rate <= 0:
            return
        ratio = error_rate / total_rate
        if ratio > 0.50:
            self.restart_container("api", f"5xx ratio {ratio:.2f} > 0.50")

    def check_postgres_connections(self) -> None:
        active = self.query('pg_stat_activity_count{datname="hcie"}')
        max_conn = self.query("pg_settings_max_connections")
        if active is None or max_conn is None or max_conn <= 0:
            return
        if active / max_conn > 0.90:
            logger.critical("Postgres connection pressure %.0f/%.0f; leaving DB up for manual triage", active, max_conn)
            HEALER_ACTIONS.labels(action="alert_only", target="hcie-final-postgres").inc()

    def check_kafka_connect(self) -> None:
        # Kafka Connect is profile-gated; if the container is absent we do not
        # treat that as a failure.
        try:
            self.client.containers.get(self.config.container_names["kafka_connect"])
        except Exception:  # noqa: BLE001
            return
        try:
            response = requests.get("http://kafka-connect:8083/connectors", timeout=5)
            if response.status_code >= 500:
                self.restart_container("kafka_connect", f"connectors endpoint {response.status_code}")
        except Exception as exc:  # noqa: BLE001
            self.restart_container("kafka_connect", f"unreachable: {exc!r}")

    def loop_once(self) -> None:
        HEALER_LAST_LOOP_TS.set(time.time())
        self.check_up_metric("hcie-api", "api")
        self.check_up_metric("redpanda", "kafka")
        self.check_up_metric("postgres", "postgres")
        self.check_up_metric("redis", "redis")
        self.check_api_error_ratio()
        self.check_postgres_connections()
        self.check_kafka_connect()

    def run_forever(self) -> None:
        logger.info("Starting FINAL auto-healer enabled=%s dry_run=%s", self.config.enabled, self.config.dry_run)
        start_http_server(self.config.metrics_port)
        while True:
            try:
                self.loop_once()
            except Exception as exc:  # noqa: BLE001
                logger.exception("Auto-healer loop error: %r", exc)
                HEALER_ERRORS.labels(stage="loop").inc()
            time.sleep(self.config.interval_s)


def main() -> int:
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
    AutoHealer().run_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
