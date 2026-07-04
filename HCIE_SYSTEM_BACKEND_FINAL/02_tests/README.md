# HCIE test suite — taxonomy & how it runs

Two kinds of files live here. They are **intentionally distinct**; don't conflate them.

## 1. `test_*.py` — the automated pytest gate
Collected by pytest (default `test_*.py` pattern) and run by `scripts/run_tests.sh` /
`make test` on the **isolated docker stack** (Postgres/Redis/Kafka, deterministic mode).
This is the gate: **387 passed / 28 skipped / 0 failed**.

- Default scope: `00_unit`, `01_integration`, `02_behavioral`. Other tiers run explicitly,
  e.g. `./scripts/run_tests.sh 02_tests/06_security`.
- **Infra-marked tests** (`@pytest.mark.requires_pg`, `@pytest.mark.requires_redis`) run on the
  isolated stack (the runner sets `HCIE_FINALS_RUN_PG/REDIS/KAFKA=1`). In an environment with **no
  stack** (e.g. the GitHub `ci.yml` runner, which starts no services) they **self-skip** — that is
  expected, not a hidden failure. The full infra suite is exercised by `make test`, which *is* the gate.
- The brain golden master lives at `golden/unified_brain_golden.json` (canonical determinism md5
  `3ab07694…`); see `scripts/golden_gate.sh` and ADR-6.

## 2. `*_validation.py` — standalone behavioural validators (NOT pytest tests)
These are `__main__`-run scripts (`python <file>`) that exercise distributed-correctness / safety
properties (ownership, replay-equivalence, governance coherence, lifecycle, mutation safety). They are
**deliberately not** named `test_*` and are **not** part of the pytest gate — they are developer/research
validators you run by hand against a live stack when investigating a specific property. They carry no
pytest assertions by design; treat them as runnable probes, not as suite coverage.

If you want one wired into the automated gate, convert it to a `test_*.py` with real `assert`s (and an
infra marker if it needs the stack) — don't rely on its presence here to mean "covered".
