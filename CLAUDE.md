# CLAUDE.md — working on HCIE from the Mac (Intel, 16 GB)

You are Claude Code running on Farros's MacBook (Intel i9 8-core 2,3 GHz, **16 GB RAM**, Intel UHD 630
— this machine is literally "Perangkat Pengembangan (Laptop)" in thesis **Tabel 3.6**; the 64 GB PC is
"Perangkat Eksperimen"). This repo is the curated **evidence snapshot** of the HCIE thesis system
(sealed anchor `run-94a3b8ba`). Everything here must stay defense-grade: grounded, reproducible, honest.

## Who you're working with
- Farros (ITS, thesis defense in progress). Style: **caveman-lite** — terse, no filler, technical
  substance intact. Ground every claim in a file/DB/artifact you can point to.
- **Never fabricate**: empty tool result ≠ success; never narrate values a tool didn't return; if a
  number can't be reproduced, say so instead of quoting it.
- **Git**: no push without explicit OK. No co-author trailers in commits. Prefer new commits over amend.
- Reproducibility-first: before claiming a metric, re-derive it (see 2-second check below).

## Canonical facts (cite these; everything else is suspect)
- **Headline**: matched cold-start AUC **0,6051** (HCIE, lagged single-Kalman m_K, tie-aware) vs BKT
  0,5963 · DKT 0,5892 · SAKT 0,5730 · GKT 0,5711 (Tabel 4.8; 10 held-out users, sealed run-94a3b8ba).
- Companion n=76: HCIE 0,6871 vs BKT 0,6746 (**+0,0125**, CI [+0,002, +0,023]).
- Transfer: raw 0,091 − placebo 0,038 = residu **0,053**; placebo ratio 0,417; **p<0,001 at K=1000**
  (full corpus N=1.976.020 / 232.440 learners; z=4,91 full / 5,27 registered 1/10 subsample).
- Seal: N=96.727 interactions, content-hash sealed; replay **bit-identical** at the decision layer.
- Kalman: init m=0,3 P=0,1 (worked example Tabel 3.13 uses seed 0,5/0,25) · Q=0,01 · R=0,1 ·
  clip [0,05;0,95]. ADC gates: α_floor=0,01, signal_ratio=0,08.
- **FORBIDDEN numbers** (stale/rejected — never present as current): 0,6364 · 0,673-as-headline ·
  0,609 (rejected 2-learner readout) · run-22f949db / "84-user" results as headline · p=0,0099 ·
  2,8 SD · deployment stats 796/112.290/506/221/40.607/8.339 (old snapshot, not reproducible).
- **Architecture invariant**: the **Thompson bandit selects** concepts+modality (Algoritma 3.6,
  `bandit.py:510`); **J_t is the audited governance VIEW** (ADC) + bounded policy modulation
  [0,8;1,2], neutral at cold start — J_t does NOT select. Keep every text/diagram consistent with this.

## Docker on this Mac — scaled-down tiers (do NOT start everything)
The PC runs ~26 containers on 64 GB. On 16 GB: give **Docker Desktop 8 GB / 6 CPUs** max, and run tiers:

```bash
cd HCIE_SYSTEM_BACKEND_FINAL/05_deployment/00_docker/01_compose

# TIER 1 — CORE loop (~4-5 GB): DB, bus, brain, event pipeline, UI
docker compose -f docker-compose.final.yml up -d postgres redis kafka
docker compose -f docker-compose.final.yml up -d migrations && sleep 5
docker compose -f docker-compose.final.yml up -d api outbox-worker projection-consumer learning-consumer
docker compose -f docker-compose.final.yml --profile frontend up -d frontend
docker compose -f docker-compose.final.yml up -d gateway && docker restart hcie-final-gateway

# TIER 2 — add only if the task needs them:
#   trajectory-recorder-consumer  (recording live interactions)
#   projection-stream-gateway     (websocket-fed dashboards)
#   adaptation-consumer transfer-measurement-consumer exploration-instrumentation-consumer
#   dlq-replay-worker auto-healer seed-admin

# TIER 3 — SKIP on this Mac (observability/optional; the PC runs them):
#   prometheus grafana kafka-ui dozzle cadvisor alertmanager otel-collector loki tempo
#   pyroscope beyla k6 postgres-exporter redis-exporter node-exporter
#   schema-registry kafka-connect kafka-connect-init   (cdc profile — Debezium is OPTIONAL by design)
#   hcie-final-kt-baselines frontend-dev
```
- If RAM squeezes: `docker update --memory 2g hcie-final-postgres` and check Kafka first (Java heap is
  the hog). `docker stats --no-stream` before starting more.
- Ports (same as PC): gateway **:80**, api :8011, postgres :55432, fe internal 3001.
- **Gotcha**: after any `--force-recreate` of frontend, **bounce the gateway** (`docker restart
  hcie-final-gateway`) — stale upstream pool otherwise (502).

## Data: restore, don't re-seal
Follow **MAC_DEPLOY.md** (this repo). Dump `hcie_full.dump` (1,71 GB, 43 tables) comes from the PC —
restore into Tier-1 postgres with `pg_restore --clean --if-exists --no-owner -j 4`. **Never re-run the
sealed replay** (3,5 h) — the data is the migration. Science-only variant (skip
`outbox_event_envelopes` + `learning_traces`) saves ~8 GB restored.

## Verification recipes (fast, honest)
```bash
curl -s localhost:80/healthz                     # 200 = gateway+api alive
# 2-second headline re-derivation (CSV ships in this repo):
python3 - <<'EOF'
import csv; from sklearn.metrics import roc_auc_score
r = list(csv.DictReader(open('docs/figures/data/matched_eval_perrow_run-94a3b8ba.csv')))
print(round(roc_auc_score([int(x['y_true']) for x in r], [float(x['p_hcie']) for x in r]), 4))  # 0.6051
EOF
```
- FE change loop: edit `HCIE_SYSTEM_FRONTENDV3/src` → `docker compose --profile frontend build frontend`
  → `up -d --force-recreate frontend` → **bounce gateway** → `curl localhost:80/<page> | grep <marker>`.
  Docker build uses **Turbopack** (stricter than local webpack).
- ⚠ `comparison_table.json`-style artifacts can carry the 84-user run — validate by AUC==0,6051,
  never trust labels.
- Any "live usage" number must be queried fresh from the DB and labeled with date + query — the old
  deck numbers died because nobody could reproduce them.

## Expo client (student shell)
```bash
cd HCIE_EXPO_CLIENT && npm install && npx expo start --tunnel
```
Scan the QR with the iPhone camera (Expo Go installed). `app.json → extra.tutorUrl` points at the PC's
Tailscale Funnel (`https://farrospc.tailb58de0.ts.net/`); if serving from this Mac's local stack instead,
set it to `http://<mac-ip>:80/` and use LAN mode (drop `--tunnel`). iOS Simulator also works: `npx expo
start` then press `i`. Honesty framing lives in `HCIE_EXPO_CLIENT/README.md` (§3.2.4 wording — shell
over the same API, never claim a native UI).

## Map of this repo
- `HCIE_SYSTEM_BACKEND_FINAL/01_source/00_core/` — the brain: `04_learners/kalman_learner.py`
  (canonical estimator) · `07_bandit/bandit.py:510` (the selector) · `03_ensemble/unified_brain.py`
  (process_event, JT layers) · `03_ensemble/governance_engine.py:820-862` (J_t 6-dim) ·
  `06_transfer/transfer_learning_engine.py:539` (neighbor-only cap 0,5·|ΔM|).
- `HCIE_SYSTEM_FRONTENDV3/src/app/review/` — reviewer surfaces: `algo-compare` (animated Alg 3.5
  stepper §4, verbatim Alg 3.1–3.7 §7, measured runtime §6) · `artifacts` (81-item evidence map) ·
  `baselines` · `methods` (causal sandbox §H) · `run-it-yourself` · `system-journey`.
- `docs/figures/data/` — sealed artifacts: per-row matched CSV (the 2-s check), K=1000 probes
  (full + 1/10), n=76 companion, F5–F8 CSVs.
- `MAC_DEPLOY.md` — storage budget + restore runbook. `HCIE_EXPO_CLIENT/` — Expo shell.
- History note: repo was re-initialized 2026-07-04 (single snapshot); the full dev history lives on
  the PC, not here.
