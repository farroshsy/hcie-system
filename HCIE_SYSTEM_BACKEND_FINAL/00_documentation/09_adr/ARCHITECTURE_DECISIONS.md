# Architecture Decision Records — HCIE backend

These ADRs resolve the six "architecture friction" items from the codebase handoff brief.
Each was produced from a deep code read **plus an adversarial safety review** — several of the
obvious "just refactor it" fixes turned out to be wrong or dangerous against the actual code, so
the decision is recorded here rather than encoded as a risky change. Where a friction is a real,
safe code fix, that is noted as such.

> Runtime note: the api and all worker containers run **baked** code (`Dockerfile.cutover`,
> `COPY . /app`; only data volumes are mounted). Any backend source edit is inert until
> `docker compose -f docker-compose.final.yml build api` + recreate. Verify behavioural changes
> on the rebuilt image, not the host edit.

---

## ADR-1 — Keep the numbered module tree + runtime projection resolver; add a static nav map

**Status:** Accepted · **Friction:** F1 (resolver defeats code navigation)

**Context.** `01_source` is organised into a deliberate numbered tree (`00_core/03_ensemble`, …).
At runtime `11_build/00_runtime_projection/sitecustomize.py` (a `MetaPathFinder`) maps clean import
names (`core.learning`, `app.api`, …) onto those numbered dirs by stripping the numeric prefix.
This works for Python but is invisible to `grep`, IDE "go to definition", and AI tools — confirmed:
`from core.projection.ux_semantics` resolves to `01_source/00_core/14_projection/ux_semantics.py`,
which no text search will connect. Several roots are **multi-path** (e.g. `core.learning` → 13 dirs).

**Decision.** Keep the numbering (it is an intentional, valued organisation) and keep the resolver.
Restore navigability with tooling instead of restructuring:
- `11_build/00_runtime_projection/import_map.json` — a **generated** clean-name → ordered-dir map
  (with `exists` flags), produced by `gen_import_map.py` from `PACKAGE_ROOTS` so it cannot drift.
  This is the tool-agnostic, authoritative lookup.
- A pointer comment at the top of `sitecustomize.py`.
- (Optional, IDE-local — kept out of git per the repo's IDE-ignore convention) point your editor's
  Python analysis paths at `01_source` + `11_build/00_runtime_projection`, e.g. VS Code/Pylance
  `"python.analysis.extraPaths": ["11_build/00_runtime_projection", "01_source"]`.

**Rejected:** flattening the numbered tree to physical clean names — it would rewrite ~50+ imports,
the Docker bake, and CI, and discard the numbering on purpose. Not worth it.

**Consequences.** Zero runtime change (docs/tooling only; no image rebuild needed). Humans/IDEs get
a lookup; the trade-off is now explicit, not hidden. `import_map.json` must be regenerated when
`PACKAGE_ROOTS` changes (run `gen_import_map.py`).

---

## ADR-2 — `unified_brain.py`: incremental split only; `_write_mode` stays inline for now

**Status:** Accepted · **Friction:** F2 (god module, ~5041 LOC)

**Context.** The file is genuinely large, but the "split never happened / split files are dead"
premise is **false**. The prior split **succeeded** and is **live**: `governance_engine.py` (1051),
`ensemble_fusion.py` (308), `learner_fusion.py` (121), `brain_state.py` (336) are imported and
instantiated in `unified_brain.py` (≈ lines 327–347). What remains inline is the ~2000-line
`process_event`/`_write_mode` orchestration. That block is **not** a side-effect-free slab: it
mutates `jt_governance`, `jt_ensemble`, `bandit`, `policy_engine` and `working_state`, and it is
**circular** (policy selection feeds JT; JT must influence policy). The adversarial review showed the
tempting "extract a JT Calculation Engine" move would drop 13+ downstream variables (→ `NameError`
on rebuild), has an impossible call-ordering, and would be gated by a golden test that is a
print-only smoke script over a ±0.005 non-deterministic golden — i.e. no real equivalence gate.

**Decision.** Do **not** big-bang split `_write_mode`. The clusters that *could* be cleanly extracted
already were. Any further extraction must be a genuinely leaf, side-effect-free helper (e.g.
`_get_concept_difficulty`, the eta-clamp / ZPD-scaling arithmetic) with a real equivalence gate, and
is only worth doing alongside a governance-constitution redesign that breaks the policy↔JT cycle.
Until then, the orchestration stays inline by design.

**Consequences.** No risky rewrite of the hot path. The remaining size is acknowledged debt with a
known seam boundary, not an accident. Revisit when the constitutional cycle is addressed.

---

## ADR-3 — Frontend separation of concerns: incremental, presentational-first; **do not** touch auth refresh

**Status:** Accepted (in progress) · **Friction:** F3 (frontend SoC) · *this is a real, safe code fix*

**Context.** Confirmed: 13–14 pages over 800 LOC (`dashboard/instructor/page.tsx` ≈ 2166), ~3197
inline `style={{}}` with the `src/lib/ui` token system used by only ~9 of ~72 pages, raw `fetch()` in
~32 pages, two API clients, and token-refresh duplicated **five** ways. The adversarial review found
two traps: (1) the live auth path is `src/contexts/auth_context.tsx` using localStorage key
`hcie_refresh_token`, while `src/lib/api-client.ts` uses a **different** key (`refresh_token`) and is
**not** in the live provider chain — "consolidating" onto it would silently break session
persistence; and (2) `src/components/providers/AuthProvider.tsx` is a dead second `AuthProvider`
(a canonical-copy trap). The big pages are also race-prone (27 `useState`, a 4s polling interval,
`useRef` first-run guards).

**Decision.** Refactor page-by-page, **presentational-first**: extract themed components + replace
inline styles, then lift data/effects into a per-page hook — *preserving* effect/closure/polling
semantics. **Explicitly out of scope:** consolidating the auth-refresh logic and adding any new
`auth-service.ts` (two already exist). The frontend is a **baked Next standalone image**
(`hcie-final-frontend`, `node server.js`, no source mount) — changes require
`docker compose build frontend` + recreate, and must be browser-verified.

**Consequences.** Slop drops incrementally with each page, verifiably, without risking auth or the
hot pages' timing. Auth-refresh de-duplication is deferred to its own carefully-tested change.

---

## ADR-4 — Dual DI authority is a shared-singleton convergence, not a one-way migration

**Status:** Accepted · **Friction:** F4 (DI authority split)

**Context.** Both `ServiceFactory` (a process-wide singleton, `01_services/service_factory.py`) and a
DI container (`07_infrastructure/di/dependency_injection.py`) are live; `main.py` constructs
`TaskService` via `ServiceFactory`, registers that same instance in the container, and asserts
identity. The adversarial review corrected two false beliefs: (1) the assertion is **not** a hard
crash — it is inside a `try/except` that logs and **falls back to ServiceFactory**, so divergence
degrades silently; (2) DI is **not** the sole authority — a dozen+ live endpoints
(`routes/tasks/tasks.py`, `06_learning/endpoints/regret.py`, `admin_routes.py`, `02_analytics/router.py`,
health, cold-start, …) still read `TaskService` **through ServiceFactory**. Convergence holds only
because both reference the same cached singleton. Note there are **two** different DI containers
(`07_infrastructure/00_di/container.py` is a separate Phase-5 Container, unrelated to the assertion).

**Decision.** Keep both. Record the **true** invariant: *ServiceFactory constructs and is still an
active read-authority for many endpoints; the container holds a reference to the same singleton;
single-authority-via-DI is aspirational (not reached).* Do **not** relabel ServiceFactory as
"staging only" (that conflates built-and-wired with retired — the disposition-label trap). A future
unification must migrate all ServiceFactory read-sites first.

**Consequences.** The pattern is documented honestly; no misleading log/comment edits. Unification
remains possible but is scoped as a real migration, not a relabel.

---

## ADR-5 — Async pipeline is container-per-consumer (sound); fix the auth consumer-group rebalance

**Status:** Accepted · **Friction:** F5 (async pipeline "partially dark")

**Context.** Not dark. `docker-compose.final.yml` runs **9 consumer containers** (learning,
projection, trajectory-recorder, adaptation, projection-stream-gateway, auth, exploration-
instrumentation, transfer-measurement, dlq-replay; + optional outbox-worker/auto-healer under
profiles), each `python -m app.workers.<x>`. The outbox processor runs in-process in the API
lifespan and drains to Kafka. `ReplayEngine` exists and is lazily instantiated by the live replay
routes; the `replay_engine=None` DI TODO is tolerated via fallbacks, so it is not "dark" either.

**Decision.** Keep the container-per-consumer topology (good for isolation/scale/restartability).
**Known bug to fix carefully (not done here):** the in-process auth worker (`auth_worker.py`, real
handlers, subscribes to the single live topic `hcie.auth`) and the auth **container**
(`auth_consumer_worker.py`, stub handlers, subscribes to six granular `hcie.auth.*` topics with zero
traffic) **share consumer group `auth-event-consumer`** → perpetual rebalancing. The fix is to
reconcile group/topics (or retire the stub container) — **not** to delete the in-process worker,
which is the only consumer of live auth traffic. (Aside: a rogue `docker-learning-consumer-1` from
the dead BACKENDV2 stack is crash-looping `ModuleNotFoundError: app` — remove it; confirms FINAL is live.)

**Consequences.** Topology documented; the real bug is captured with the correct fix direction so it
is not "fixed" backwards.

---

## ADR-6 — Behavioural tests via replay-equivalence, not golden-value pinning

**Status:** Accepted · **Friction:** F6 (tests validate contracts, not behaviour)

**Context.** The kernel is valid (most tests assert protocol shape; `02_tests/golden/unified_brain_golden.json`
has 7 rows but no test consumes it). But the obvious "pin the golden values within 0.1%" test is
unsafe: (1) the public method is `process_event(...)`, not the proposed `process_interaction(...)`;
(2) the golden was produced with full injected infra (Postgres/Redis/Kafka) + `ENABLE_DETERMINISTIC_MODE`
on the isolated test stack — not a bare constructor; (3) the golden is documented as cache-masked and
**non-deterministic ±0.005**, while some golden fields are themselves < 0.005, so a 0.1% tolerance
goes red on a clean re-run with no code change. `run_tests.sh` already globs the behavioural dir, so
no scope edit is needed (the proposed edit would have shrunk coverage).

**Decision.** Prefer **replay-equivalence**: run `process_event` twice with the same seed/determinism
knobs and assert identical mastery/uncertainty/Kalman outputs (exact, robust — it tests the
determinism guarantee, not noise-sensitive magnitudes). If golden-value pinning is used, tolerance
must be ≥ the documented ±0.005 floor and run on the real harness via `scripts/run_tests.sh`. Tests
are additive (no image rebuild). Register any new pytest markers in `02_tests/conftest.py`.

**Consequences.** A behavioural gate that is robust rather than flaky, matching the existing
deterministic-mode machinery.

## ADR-7 — DI layering + projection are intentional boundaries, not duplication (resolves harsh-review M09/M10/M11/M12)

**Context.** A harsh review flagged "3 DI mechanisms", a `00_di` vs `di` "duplicate dir", "3 stacked
projection mechanisms", and navigability. Investigation (with live import tracing) shows these are
*layers*, not accidental copies:

- **DI is layered, not triplicated.** `07_infrastructure/00_di/` holds the **factory/container layer**
  (`brain_factory`, `container`, `config_factory`, `*_runtime_factory`); `07_infrastructure/di/` holds
  the **container-access layer** (`get_container`, `dependency_injection`, `service_factory_adapter`),
  imported live as `app.infrastructure.di.*` by the v3 API. The projection merges both physical dirs
  under the single clean name `app.infrastructure.di`, so callers see one package. This is the
  shared-singleton convergence of **ADR-4**; the two dirs are different files serving one namespace.
- **Projection** (sitecustomize meta-path finder + `import_map.json` nav map) is **ADR-1**. The
  `__init__`/importlib shims are the boot mechanism, not redundant copies.

**Decision.** Removal/physical merge is unsafe (the resolver is load-bearing; the layers have distinct
roles), so per ADR-1/ADR-4 the boundary is **documented, not collapsed**. Concrete cleanups taken:
`gen_import_map.py` re-run to drop **6 dangling `exists:false` paths → 0** (removed dead
`core.engine`/`05_engines`/`11_validation`/`12_telemetry` roots from `sitecustomize.PACKAGE_ROOTS`),
which also removed a brain-output drift and restored the canonical determinism md5 `3ab07694…`. The
18-line `03_ensemble/idempotency_manager.py` is a **bridge** that re-exports the canonical 510-line
impl (not a stub — see its docstring).

**Consequences.** `import_map.json` has no dangling entries; the DI/projection layering is recorded so
future reviews don't re-flag it as duplication. A *physical* DI/projection flatten remains an optional,
larger follow-up (own change, golden-gated), explicitly out of scope here.
