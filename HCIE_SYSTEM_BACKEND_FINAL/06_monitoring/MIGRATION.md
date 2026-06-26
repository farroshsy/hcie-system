# 06_monitoring — Canonical home for FINAL-stack observability

This directory is the **single canonical source of truth** for all
HCIE FINAL observability configuration (Prometheus, Grafana,
Alertmanager, OpenTelemetry Collector, Tempo, Loki).

## Why a canonical home

Before this consolidation, FINAL-stack monitoring configs were split
between:

  - **schema-canonical** (`06_monitoring/`) — the directory documented
    in `IDEAL_STRUCTURE.md`, holding ~19 historical Grafana dashboards
    and pre-FINAL Prometheus configs;
  - **compose-active** (`05_deployment/00_docker/01_compose/monitoring/`)
    — the Phase-3-tuned configs actually bind-mounted by
    `docker-compose.final.yml`.

That split meant the schema home was unused by the runtime, and the
compose-active configs were invisible to anyone reading the
documentation. The consolidation promotes the FINAL configs into the
schema home and updates the compose bind mounts to read from this
directory.

## Layout

```
06_monitoring/
├── 00_prometheus/
│   ├── prometheus.final.yml         ← active FINAL config (Phase-3 scrapes)
│   ├── prometheus.yml               ← legacy general config (retained)
│   ├── 00_alerts/
│   │   ├── alertmanager.final.yml   ← active FINAL alertmanager config
│   │   ├── alertmanager.yml         ← legacy
│   │   └── alerts.yml               ← legacy rule definitions
│   ├── 01_recording_rules/
│   └── 02_scrapers/
├── 01_grafana/
│   ├── 00_dashboards/               ← all dashboards (FINAL + legacy)
│   │   ├── phase3_sweep_overview.json      ← active Phase-3 dashboard
│   │   ├── cognitive-governance-observatory.json
│   │   └── ...
│   └── 01_provisioning/
│       ├── dashboards/
│       │   ├── dashboards.final.yml ← active FINAL dashboard provisioner
│       │   └── dashboards.yml       ← legacy
│       └── datasources/
│           ├── prometheus.final.yml ← active FINAL datasource
│           └── prometheus.yml       ← legacy
├── 02_loki/
├── 03_tempo/
│   ├── tempo-config.final.yaml      ← active FINAL tempo config
│   └── tempo-config.yaml            ← legacy
├── 04_otel/
│   ├── otel-collector-config.final.yaml  ← active FINAL OTEL config
│   ├── otel-collector-config.yaml        ← legacy
│   ├── otel-collector-config-minimal.yaml
│   └── otel-collector-config-simple.yaml
└── 05_debezium/
```

## How compose reads from here

`HCIE_SYSTEM_BACKEND_FINAL/05_deployment/00_docker/01_compose/docker-compose.final.yml`
uses compose-relative paths up three levels then down into
`06_monitoring/`. The active mounts as of the consolidation commit:

| Service     | Container path                               | Host source                                                              |
|-------------|----------------------------------------------|--------------------------------------------------------------------------|
| prometheus  | `/etc/prometheus/prometheus.yml`             | `06_monitoring/00_prometheus/prometheus.final.yml`                       |
| alertmanager| `/etc/alertmanager/alertmanager.yml`         | `06_monitoring/00_prometheus/00_alerts/alertmanager.final.yml`           |
| grafana     | `/etc/grafana/provisioning`                  | `06_monitoring/01_grafana/01_provisioning`                                |
| grafana     | `/var/lib/grafana/dashboards`                | `06_monitoring/01_grafana/00_dashboards`                                  |
| otel-collector | `/etc/otel-collector-config.yaml`         | `06_monitoring/04_otel/otel-collector-config.final.yaml`                  |
| tempo       | `/etc/tempo.yaml`                            | `06_monitoring/03_tempo/tempo-config.final.yaml`                          |

## When do containers pick up changes?

The bind-mount path change is metadata-only. Existing running containers
continue to read from whatever bind mount they were started with.
Containers will switch to the canonical path on next restart, e.g.:

```bash
docker compose -f HCIE_SYSTEM_BACKEND_FINAL/05_deployment/00_docker/01_compose/docker-compose.final.yml \
    --profile observability up -d --no-deps prometheus grafana alertmanager
```

This is intentionally non-disruptive during research sweeps: starting
or restarting Prometheus/Grafana while a Phase-3 sweep is in flight
does not affect the API/consumer/database that the sweep depends on.

## Legacy directory

`05_deployment/00_docker/01_compose/monitoring/` is retained but marked
deprecated (`DEPRECATED.md` in that directory). It can be removed once
external tooling stops referencing those paths.
