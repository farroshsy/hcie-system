# Changelog

All notable changes to this project are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com/); this project uses [SemVer](https://semver.org/) (0.x = active R&D).

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
