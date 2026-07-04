# Changelog

All notable changes to this project are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com/); this project uses [SemVer](https://semver.org/) (0.x = active R&D).

## [0.2.0] — 2026-07-04
Defense-ready snapshot (history re-initialized).
- Frontend: animated Algoritma 3.5 stepper + verbatim Alg 3.1–3.7 browser + measured cost/runtime
  panel on `/review/algo-compare`; `/review/artifacts` evidence map (all 81 Bab 3–4 tables/figures
  with provenance, intent, live links); stale-number fixes (headline 0.6051 everywhere, transfer
  stats aligned to K=1000 / p<0.001).
- New: `HCIE_EXPO_CLIENT/` (Expo Go WebView shell over the same gateway) and `MAC_DEPLOY.md`
  (data-migration deploy: Postgres dump restore, storage budget, no re-seal needed).
- Data: added `lagged_kalman_auc.json` (n=76 companion, 0.6871) and
  `prospective_probe_v3_K1000.json` (registered 1/10 subsample, z=5.27) beside the existing
  sealed per-row CSV and full-corpus K=1000 probe.

## [0.1.0] — 2026-06-21
First public release. **Research & Development** — research-grade, reproducible, actively developed.

### Added
- **System** — event-sourced adaptive ITS + research instrument (FastAPI · PostgreSQL · Redis · Kafka/Redpanda · Next.js): API + 7 event workers, ensemble knowledge tracing, constitutional Joint-Task governance + ADC, Thompson-sampling bandit.
- **Reproducibility** — bit-identical deterministic replay (parity md5 `3ab07694…`), content-hash sealed anchor (`seal-bae44d1a`, 96,727 rows), `REPRODUCIBILITY.md`, `make verify` / `make parity`, golden-master gate.
- **Docs** — `README`, `MANUAL.md` (per-directory coverage map), `HOW_IT_WORKS.md` (flow + layout + walkthrough), `CHANGELOG.md`, `CITATION.cff`.
- **API** — `postman/openapi.json` (354 ops) + generated `postman/HCIE.postman_collection.json` + `scripts/gen_postman.sh`.
- **Quality/CI** — `.github/workflows/ci.yml`, Tarjan-SCC dependency analyzer, MIT `LICENSE`, status badges, `CITATION.cff`.

### Verified
- Functional suite green on an isolated stack; backend compile clean; `next build` clean.
- Static analysis: **0 real circular dependencies**, **0 HIGH security findings** (weak-MD5 annotated), dead code removed.
- Deterministic replay bit-identical before and after the `_write_mode` complexity refactor.

[0.1.0]: https://github.com/farroshsy/hcie-system/releases/tag/v0.1.0
