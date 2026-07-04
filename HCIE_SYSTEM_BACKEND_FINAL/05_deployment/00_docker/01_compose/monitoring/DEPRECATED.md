# DEPRECATED — monitoring configs have moved

The active FINAL-stack monitoring configurations have been **promoted to
their canonical home** under
`HCIE_SYSTEM_BACKEND_FINAL/06_monitoring/`.

The `docker-compose.final.yml` bind mounts have been updated to read
from the canonical home; the files in this directory are retained only
as a transition layer for any external tooling that still references
the compose-relative path.

## File-by-file mapping

| Compose-relative (legacy)                                   | Canonical home (use this)                                                       |
|-------------------------------------------------------------|---------------------------------------------------------------------------------|
| `monitoring/prometheus.final.yml`                           | `06_monitoring/00_prometheus/prometheus.final.yml`                              |
| `monitoring/alertmanager.final.yml`                         | `06_monitoring/00_prometheus/00_alerts/alertmanager.final.yml`                  |
| `monitoring/otel-collector-config.final.yaml`               | `06_monitoring/04_otel/otel-collector-config.final.yaml`                        |
| `monitoring/tempo-config.final.yaml`                        | `06_monitoring/03_tempo/tempo-config.final.yaml`                                |
| `monitoring/grafana/provisioning/`                          | `06_monitoring/01_grafana/01_provisioning/`                                     |
| `monitoring/grafana/dashboards/phase3_sweep_overview.json`  | `06_monitoring/01_grafana/00_dashboards/phase3_sweep_overview.json`             |

## How to clean up the legacy files

The legacy files are still byte-identical to the canonical copies as of
the consolidation commit. To remove them once you confirm the canonical
mounts work:

```bash
git rm -r HCIE_SYSTEM_BACKEND_FINAL/05_deployment/00_docker/01_compose/monitoring/
```

Wait until at least one observability stack restart has succeeded against
the canonical paths before deleting. See `06_monitoring/MIGRATION.md`
for the full consolidation rationale.
