# HCIE — Operator Manual

How to install, run, operate, and verify the HCIE system, plus a **coverage map of every directory**.
HCIE is an event-sourced adaptive Intelligent Tutoring System + thesis research instrument
(FastAPI · PostgreSQL · Redis · Kafka/Redpanda · Next.js). The live system is two trees:
`HCIE_SYSTEM_BACKEND_FINAL/` and `HCIE_SYSTEM_FRONTENDV3/`.

> **Coverage principle.** Every directory below is *covered* — it is imported by the runtime, exercised by
> tests, invoked by a Makefile target / CI job / compose service, a consumed config/data file, or documented
> here. Anything that was none of these was legacy or slop and has been removed (see *What was pruned*).

---

## 1. Requirements
Docker + Docker Compose, GNU Make, ~6 GB free RAM for the full stack. Everything runs in containers — no host Python/Node needed to operate it (only to develop).

## 2. Quickstart
```bash
cd RealSystem
make help              # list every target
cp HCIE_SYSTEM_BACKEND_FINAL/05_deployment/00_docker/01_compose/.env.example \
   HCIE_SYSTEM_BACKEND_FINAL/05_deployment/00_docker/01_compose/.env   # set ADMIN_PASSWORD, JWT_SECRET_KEY
make up                # start api + 7 workers + Postgres/Redis/Kafka
make migrate           # apply the Alembic schema chain
make seed              # idempotent seed (migrate + admin/tenant + verify)
make test              # functional suite on an ISOLATED stack (never the live DB)
```

## 3. Operate
All verbs are thin wrappers over `docker compose -f HCIE_SYSTEM_BACKEND_FINAL/05_deployment/00_docker/01_compose/docker-compose.final.yml`.

| Command | What it does | Ports / notes |
|---|---|---|
| `make up` / `make down` | start / stop the core stack | api **8011**, postgres **55432**, redis **56379**, redpanda **19092/19644** |
| `make build` / `make fe-build` | build api+worker / frontend images | |
| `make migrate` | `alembic upgrade head` (migrations profile) | idempotent |
| `make seed` | `07_database/00_seeds/seed.py` in the api container: migrate + admin/tenant + verify | needs `ADMIN_PASSWORD` to seed admin |
| `make reseal RUN=<id> [NOTE=..]` | seal/re-seal a run via `seal_run()` (else HTTP-only) | idempotent — re-sealing returns the existing manifest |
| `make backup` | off-box `pg_dump -Fc` of the sealed DB (`export_db.sh`) | protects the irreplaceable sealed anchor |
| `make test` | functional suite on the isolated test stack | tmpfs DB, deterministic seed 42 |
| `make logs` / `make ps` | tail / status | |
| `make clean` | stop + drop volumes (**destructive**) | wipes local data |

**Optional tiers** (compose profiles, run directly):
`--profile observability` → Grafana **3000** (admin/admin), Prometheus **9090**, Alertmanager **9093** ·
`--profile tracing` → OTEL 4317/4318, Loki 3100, Tempo 3200, Pyroscope 4040 ·
`--profile frontend` → Next.js + nginx gateway on **80** · `--profile baselines` → KT baselines **8021** ·
`--profile self-healing` → dlq-replay worker 8003 (DLQ replay path) · `--profile cdc` → schema-registry + Debezium.

**Compose files** (under `…/00_docker/01_compose/`): `docker-compose.final.yml` is **the** stack — every `make`
verb wraps it. The rest are task-specific: `docker-compose.test.yml` = isolated test stack; `…cutover.yml` =
API/worker image build (`Dockerfile.cutover`); `…init.yml` = one-shot schema/seed bootstrap; `…schema-registry.yml`
+ `…connect.yml` = the optional CDC/Debezium path; `…sonar.yml` = local SonarQube scan. Use `final` unless a task
specifically needs one of the others.

**Live-pipeline audit:** `python HCIE_SYSTEM_BACKEND_FINAL/03_scripts/02_analysis/audit_worker_pipeline.py --api-url http://localhost:8011 --postgres-container hcie-final-postgres` — proves the event spine `TaskAttemptSubmitted → LearningProcessed → CognitionUpdated → ProjectionUpdated`.

## 4. Verify
- **Tests:** `make test` → `scripts/run_tests.sh` on `docker-compose.test.yml` (isolated pg/redis/kafka, live schema only, pytest in the api image, deterministic mode). Default scope = `02_tests/{00_unit,01_integration,02_behavioral}`; other tiers run explicitly, e.g. `./scripts/run_tests.sh 02_tests/06_security`.
- **Determinism:** `bash scripts/run_determinism_parity.sh` (bit-identical replay envelopes).
- **Compliance (CI):** repo-root `.github/workflows/ci.yml` runs the FERPA/GDPR/PII scanners; locally `bash HCIE_SYSTEM_BACKEND_FINAL/08_security/setup_compliance.sh`.
- **Audit-schema conformance:** `02_tests/06_security/test_audit_schema_conformance.py` makes `08_security/00_audit/audit_schema.json` load-bearing against the live audit sink.

## 5. Directory coverage map
**`HCIE_SYSTEM_BACKEND_FINAL/`**

| Dir | Purpose | Covered by |
|---|---|---|
| `01_source/00_core` | cognitive brain (mastery/Kalman, ensemble, ADC governance, JT, bandit; inline in `unified_brain.py`) | imported by the API at runtime; unit tests |
| `01_source/01_application` | FastAPI app (`app.main:app`), 7 event workers, DI, runtime services | runtime; integration tests |
| `01_source/02_infrastructure` | storage (Postgres/Redis), messaging/outbox | runtime |
| `02_tests` | pytest suite: `00_unit`..`07_*` tiers + `golden/` master + `00_test_utilities` | `make test` |
| `03_scripts/01_ops` | `seed_admin.py`, `init_cutover_database.py` | `make seed` / compose `seed-admin` |
| `03_scripts/01_maintenance/reseal.py` | operator CLI for `seal_run` | `make reseal` |
| `03_scripts/02_analysis/audit_worker_pipeline.py` | live event-spine audit | operator command (above) |
| `04_config/00_schemas/settings.py` | the one pydantic `Settings` (env-driven) | `from config.env import settings` (~20 importers) |
| `config/endpoint_authority_manifest.yaml` | 357-route authority classification | `test_endpoint_authority_manifest.py` |
| `05_deployment/00_docker` | the canonical compose + Dockerfiles | all `make` targets |
| `05_deployment/03_data_portability` | `export_db.sh` / `import_db.sh` | `make backup` |
| `06_monitoring` | Prometheus/Grafana/Alertmanager/Tempo/OTEL configs | bind-mounted by the observability/tracing profiles |
| `07_database/00_migrations/versions` | the 35-revision Alembic chain (schema + data seeds) | `make migrate` |
| `07_database/00_seeds/seed.py` | canonical idempotent seeder | `make seed` |
| `08_security` | FERPA/GDPR/PII scanners + `audit_schema.json` | CI `ci.yml`, pre-commit, conformance test |
| `10_tools/00_linters/ferpa_gdpr_linter.py` | compliance linter | CI + pre-commit |
| `11_build/00_runtime_projection/sitecustomize.py` | **the boot path** — maps clean module names → numbered dirs | every compose service `PYTHONPATH` |
| `09_research/00_results/07_cutover` | audit-pipeline output sink | `audit_worker_pipeline.py` |
| `00_documentation` | ADRs, INTEGRATION_MAP, architecture/research docs | reference |

**`HCIE_SYSTEM_FRONTENDV3/`** — Next.js 16 app-router: `src/app` (live UI: learn loop, dashboards, `/review/*` portal), `src/components`/`src/lib`/`src/contexts`/`src/hooks`, `src/data/thesis_extracts` (sealed extracts), `public/` (sealed artifacts), `messages/` (i18n). Build/run via the `frontend` compose profile.

## 6. What was pruned (legacy/slop — not covered)
Removed because nothing imports/runs/tests/documents them (recoverable from git history):
empty NASA-scaffold slots (`11_build/{binaries,packages,docker_images}`, `04_config/{00_environments,00_templates}`, `03_scripts/00_deployment`, `02_tests/{00_test_data,00_test_fixtures,07_compliance}`, `05_deployment/{01_ci_cd,02_terraform,00_docker/02_kubernetes}`, `06_monitoring/02_loki`, `08_security/00_secrets`/`00_policies`, `09_research` empty leaves); legacy compose flavours (`docker-compose.{yml,production,monitoring,gateway}.yml`) + `auto-healer`; superseded migrations (`07_database/00_migrations/old`, loose `.sql`); one-shot debug scripts (`03_scripts/03_debug`); grep-verified dead source (`experiments_routes.py`, `learning_metrics_routes.py`, `runtime_mode.py`, `logging_config.py`, the duplicate `endpoint_authority_manifest.yaml`); all committed `__pycache__`. Everything is recoverable from git history.

## 7. Provenance
Canonical sealed anchor **`seal-bae44d1a`** / **`run-d2154070`** · content_hash `85690d8b…` · 96,727 rows ·
git_dirty=false. Headline this code produces: cold-start AUC (lagged-Kalman, tie-aware) **0.6051**, leads baselines;
lead positive at all power & significant at n=76 (+0.0125, CI [+0.0017, +0.0226]); transfer = placebo-corrected residual **+0.053**; ADC self-characterization L4 18/24.
`make reseal RUN=run-d2154070-… ` re-derives the same manifest (idempotent).
