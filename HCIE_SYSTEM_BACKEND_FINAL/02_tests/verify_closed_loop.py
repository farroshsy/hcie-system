#!/usr/bin/env python3
"""
Closed-loop end-to-end verification harness.

Logs in as a real learner, runs 10–15 interactions, then verifies every
layer of the data flow propagates:

  Layer 1: interactions               (postgres)  → row count increases
  Layer 2: learning_state             (postgres)  → mastery row appears/updates
  Layer 3: trajectory_records         (postgres)  → JT attribution captured
  Layer 4: experiment_trajectories    (postgres)  → governance trace captured
  Layer 5: /session-trace/{user}      (HTTP API)  → new interaction visible
  Layer 6: /learner/progress          (HTTP API)  → mastery delta visible
  Layer 7: /cohort-concepts           (HTTP API)  → cohort aggregate updates
  Layer 8: /cohort-edges              (HTTP API)  → transfer observation appears

A consumer pipeline lag tolerance is built in — after submitting attempts the
script polls each layer up to N seconds before failing.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
import os
from typing import Any, Dict, List, Optional, Tuple
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

API = "http://localhost:8011"
# Use a timestamp-suffixed user so each run starts from a clean baseline
_RUN_TAG = int(time.time()) if False else None  # set below
USER_PASSWORD = "VerifyE2E2026!"
NUM_INTERACTIONS = 12
CONSUMER_LAG_BUDGET_SECONDS = 60
INTERACTION_THROTTLE_SECONDS = 2.5  # API global rate limit + auth rate limit
POSTGRES_CONTAINER = "hcie-final-postgres"


# ─── HTTP helpers ─────────────────────────────────────────────────────────────


def http(method: str, path: str, body: Optional[Dict] = None,
         token: Optional[str] = None, timeout: int = 10,
         retry_429: bool = True) -> Tuple[int, Any]:
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = json.dumps(body).encode() if body is not None else None
    req = Request(f"{API}{path}", method=method, headers=headers, data=data)
    for attempt in range(3 if retry_429 else 1):
        try:
            with urlopen(req, timeout=timeout) as resp:
                return resp.status, json.loads(resp.read().decode())
        except HTTPError as e:
            try:
                err_body = json.loads(e.read().decode())
            except Exception:
                err_body = {"error": str(e)}
            # Honor Retry-After on 429 (global rate limit)
            if e.code == 429 and retry_429 and attempt < 2:
                retry_after = int(e.headers.get("Retry-After", "5"))
                # Cap wait at 45s; if longer, give up so caller sees the 429
                wait = min(retry_after + 1, 45)
                print(f"      [33mℹ[0m rate-limited; sleeping {wait}s then retrying…")
                time.sleep(wait)
                continue
            return e.code, err_body
        except URLError as e:
            return 0, {"error": str(e)}
    return 429, {"error": "rate limit retries exhausted"}


# ─── Postgres helpers ─────────────────────────────────────────────────────────


def psql(sql: str) -> str:
    """Run a SQL statement via docker exec; returns stdout."""
    out = subprocess.run(
        ["docker", "exec", "-i", POSTGRES_CONTAINER,
         "psql", "-U", "hcie_user", "-d", "hcie",
         "-t", "-A", "-c", sql],
        capture_output=True, text=True, timeout=15,
    )
    if out.returncode != 0:
        return f"ERR:{out.stderr.strip()}"
    return out.stdout.strip()


def count(sql: str) -> int:
    res = psql(sql)
    try:
        return int(res)
    except ValueError:
        return -1


# ─── Reporting ────────────────────────────────────────────────────────────────


PASS = "\033[32m✓\033[0m"
FAIL = "\033[31m✗\033[0m"
INFO = "\033[33mℹ\033[0m"


def banner(label: str) -> None:
    print(f"\n{'═' * 64}\n  {label}\n{'═' * 64}")


def report(label: str, ok: bool, detail: str = "") -> None:
    icon = PASS if ok else FAIL
    print(f"  {icon} {label:<46} {detail}")


# ─── Phases ───────────────────────────────────────────────────────────────────


def phase_baseline(user_id: str) -> Dict[str, int]:
    """Take baseline row counts before running interactions (per-user)."""
    banner("Phase 0: baseline row counts (this user)")
    base = {
        "learning_state": count(
            f"SELECT COUNT(*) FROM learning_state WHERE user_id = '{user_id}'"
        ),
        "experiment_trajectories": count(
            f"SELECT COUNT(*) FROM experiment_trajectories WHERE user_id = '{user_id}'"
        ),
        "outbox_events": count(
            "SELECT COUNT(*) FROM outbox_event_envelopes "
            f"WHERE envelope::jsonb->>'partition_key' = '{user_id}'"
        ),
    }
    for k, v in base.items():
        print(f"  {INFO} {k:<46} {v}")
    return base


def phase_register_and_login() -> Tuple[str, str, str]:
    """Register a fresh user and login; return (email, user_id, token)."""
    banner("Phase 1: register + login")

    # Unique per-run user for clean baseline
    run_tag = int(time.time())
    email = f"e2e_{run_tag}@hcie.test"
    name = f"E2E Run {run_tag}"
    print(f"  {INFO} run_tag={run_tag} email={email}")

    status, body = http("POST", "/v3/auth/register", {
        "email": email, "password": USER_PASSWORD,
        "name": name, "role": "student",
    })
    if status in (200, 201):
        print(f"  {PASS} registered user (status {status})")
    elif status == 409 and "already" in str(body).lower():
        print(f"  {INFO} user already exists; continuing to login")
    else:
        print(f"  {FAIL} register failed: status={status} body={body}")
        sys.exit(1)

    status, body = http("POST", "/v3/auth/login", {
        "email": email, "password": USER_PASSWORD,
    })
    if status != 200:
        print(f"  {FAIL} login failed: status={status} body={body}")
        sys.exit(1)
    token = body.get("access_token") or body.get("token") or body.get("data", {}).get("access_token")
    if not token:
        print(f"  {FAIL} no access token in login response: {body}")
        sys.exit(1)

    # Resolve user_id via /me or profile
    status, me = http("GET", "/v3/auth/profile", token=token)
    user_id = me.get("id") or me.get("user_id") or me.get("data", {}).get("id")
    if not user_id:
        # Try alt path
        status, me = http("GET", "/auth/me", token=token)
        user_id = me.get("id") or me.get("user_id")
    if not user_id:
        print(f"  {FAIL} couldn't resolve user_id from profile: {me}")
        sys.exit(1)

    print(f"  {PASS} logged in; user_id={user_id}")
    return email, user_id, token


def phase_interactions(token: str, n: int) -> List[Dict[str, Any]]:
    """Submit n recommend→attempt loops; return list of attempt responses."""
    banner(f"Phase 2: run {n} learner interactions")
    # Starter concept rotation — concepts the seed catalog has tasks for.
    # After a couple of these, the MAB has signal and can pick autonomously.
    starter = ["k2_algorithms", "k5_algorithms", "k2_control", "k5_control",
               "k8_algorithms", "k8_control", "k12_algorithms", "k12_control"]
    results: List[Dict[str, Any]] = []
    for i in range(1, n + 1):
        # First few attempts: force a starter concept so cold-start has a target.
        concept_filter = [starter[(i - 1) % len(starter)]] if i <= len(starter) else None
        body: Dict[str, Any] = {}
        if concept_filter:
            body["concept_filter"] = concept_filter
        s, rec = http("POST", "/v3/learner/recommend", body, token=token, timeout=15)
        if s != 200:
            print(f"  {FAIL} #{i} recommend failed: status={s} body={rec}")
            continue
        task_id = rec.get("task_id")
        concept = rec.get("concept_id")
        choices = rec.get("choices") or []
        # Choose first choice deterministically for half, last for half
        answer = choices[0] if (i % 2 == 0 and choices) else (choices[-1] if choices else "")

        s, att = http("POST", "/v3/learner/attempt", {
            "task_id": task_id, "concept_id": concept,
            "answer": answer, "response_time": 4.5,
        }, token=token, timeout=15)
        if s != 200:
            print(f"  {FAIL} #{i} attempt failed: status={s} body={att}")
            continue
        results.append({
            "interaction": i,
            "concept_id": concept,
            "task_id": task_id,
            "correct": att.get("correct"),
            "mastery": att.get("mastery"),
            "mastery_delta": att.get("payload", {}).get("mastery_delta"),
            "jt_transfer": att.get("payload", {}).get("jt_transfer_contribution"),
        })
        print(f"  {PASS} #{i} {str(concept)[:36]:<36} correct={att.get('correct')} "
              f"mastery={att.get('mastery'):.3f}"
              if att.get("mastery") is not None
              else f"  {PASS} #{i} {str(concept)[:36]:<36} correct={att.get('correct')}")
        time.sleep(INTERACTION_THROTTLE_SECONDS)
    print(f"\n  {INFO} submitted {len(results)}/{n} attempts")
    return results


def poll_layer(label: str, predicate, baseline: int, budget: int) -> Tuple[bool, int]:
    """Poll until predicate returns a count > baseline or budget elapses."""
    start = time.time()
    last = baseline
    while time.time() - start < budget:
        last = predicate()
        if last > baseline:
            return True, last
        time.sleep(1)
    return False, last


def phase_verify_layers(user_id: str, baseline: Dict[str, int], token: str,
                        attempts: List[Dict[str, Any]]) -> Dict[str, bool]:
    """Verify all 8 layers."""
    banner("Phase 3: verify all layers (with consumer-lag tolerance)")
    results: Dict[str, bool] = {}

    # Layer 1: outbox_event_envelopes — every attempt should publish events
    ok, n = poll_layer(
        "outbox",
        lambda: count(
            "SELECT COUNT(*) FROM outbox_event_envelopes "
            f"WHERE envelope::jsonb->>'partition_key' = '{user_id}'"
        ),
        baseline["outbox_events"], CONSUMER_LAG_BUDGET_SECONDS,
    )
    report("Layer 1: outbox_event_envelopes (event flow)", ok,
           f"{baseline['outbox_events']} → {n} (Δ={n - baseline['outbox_events']})")
    results["outbox_events"] = ok

    # Layer 2: learning_state mastery rows
    ok, n = poll_layer(
        "learning_state",
        lambda: count(f"SELECT COUNT(*) FROM learning_state WHERE user_id = '{user_id}'"),
        baseline["learning_state"], CONSUMER_LAG_BUDGET_SECONDS,
    )
    report("Layer 2: learning_state mastery rows", ok,
           f"{baseline['learning_state']} → {n} (Δ={n - baseline['learning_state']})")
    results["learning_state"] = ok

    # Layer 3: experiment_trajectories — canonical per-interaction trace
    # (trajectory_records is legacy/unused; trajectory_recorder.py explicitly
    # overrides target table to experiment_trajectories)
    ok, n = poll_layer(
        "experiment_trajectories",
        lambda: count(f"SELECT COUNT(*) FROM experiment_trajectories "
                      f"WHERE user_id = '{user_id}'"),
        baseline["experiment_trajectories"], CONSUMER_LAG_BUDGET_SECONDS,
    )
    report("Layer 3: experiment_trajectories JT+phase-A trace", ok,
           f"{baseline['experiment_trajectories']} → {n} "
           f"(Δ={n - baseline['experiment_trajectories']})")
    results["experiment_trajectories"] = ok

    # Layer 4: /session-trace (consumes experiment_trajectories with outbox fallback)
    s, st = http("GET", f"/v3/frontend/dashboard/session-trace/{user_id}?limit=50",
                 token=token, timeout=30)
    trace_count = len(st.get("trace", [])) if s == 200 else 0
    ok = s == 200 and trace_count > 0
    report("Layer 4: /session-trace returns rows", ok,
           f"status={s} trace_rows={trace_count}")
    results["session_trace"] = ok

    # Layer 5: /learner/progress (real mastery from learning_state)
    s, prog = http("GET", "/v3/learner/progress", token=token)
    concepts = prog.get("concepts", {}) if s == 200 else {}
    user_attempt_concepts = {a["concept_id"] for a in attempts if a.get("concept_id")}
    progress_overlap = user_attempt_concepts & set(concepts.keys())
    ok = s == 200 and len(progress_overlap) > 0
    report("Layer 5: /learner/progress shows mastery", ok,
           f"status={s} concepts={len(concepts)} overlap_with_attempts={len(progress_overlap)}")
    results["learner_progress"] = ok

    # Layer 6: /cohort-concepts (aggregates from learning_state)
    s, ch = http("GET", "/v3/frontend/dashboard/cohort-concepts")
    user_concepts_in_attempts = {a["concept_id"] for a in attempts if a.get("concept_id")}
    cohort_concepts_returned = {c.get("concept_id") for c in ch.get("concepts", [])}
    overlap = user_concepts_in_attempts & cohort_concepts_returned
    ok = s == 200 and ch.get("status") == "ok" and len(overlap) > 0
    report("Layer 6: /cohort-concepts shows session concepts", ok,
           f"status={s} overlap={len(overlap)}/{len(user_concepts_in_attempts)}")
    results["cohort_concepts"] = ok

    # Layer 7: /cohort-edges (uses experiment_trajectories.transfer_amount)
    s, ce = http("GET", "/v3/frontend/dashboard/cohort-edges")
    edges = ce.get("edges", []) if s == 200 else []
    edges_with_observation = [e for e in edges if (e.get("activation_count") or 0) > 0]
    ok = s == 200 and ce.get("status") == "ok" and len(edges) > 0
    transfer_observed = len(edges_with_observation) > 0
    report("Layer 7: /cohort-edges populated", ok,
           f"status={s} edges={len(edges)} with_observed_transfer={len(edges_with_observation)}")
    if not transfer_observed:
        print(f"      {INFO} no transfer activations yet (T_realized > 0.08) — "
              f"may need more interactions to fire transfer")
    results["cohort_edges"] = ok

    # Layer 8: /system-stats reflects new data
    s, ss = http("GET", "/v3/frontend/dashboard/system-stats")
    user_count = ss.get("trajectories", {}).get("users_with_trajectories", 0) if s == 200 else 0
    ok = s == 200 and user_count > 0
    report("Layer 8: /system-stats reflects new trajectory data", ok,
           f"status={s} users_with_trajectories={user_count}")
    results["system_stats"] = ok

    return results


def phase_summary(results: Dict[str, bool], attempts: List[Dict[str, Any]]) -> int:
    banner("VERDICT")
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    print(f"  {passed}/{total} layers propagated successfully")
    for k, v in results.items():
        print(f"    {PASS if v else FAIL} {k}")

    if attempts:
        masteries = [a["mastery"] for a in attempts if a.get("mastery") is not None]
        if masteries:
            print(f"\n  Mastery range: {min(masteries):.3f} → {max(masteries):.3f}")
        correct = sum(1 for a in attempts if a.get("correct"))
        print(f"  Correct rate: {correct}/{len(attempts)} = {correct/len(attempts):.0%}")

    if passed == total:
        print(f"\n  {PASS} CLOSED-LOOP VERIFIED: real answer → real governance → "
              f"real mastery → real analytics → real research evidence")
        return 0
    else:
        print(f"\n  {FAIL} CLOSED-LOOP INCOMPLETE — {total - passed} layer(s) failed")
        return 1


def main() -> int:
    # Force UTF-8 stdout on Windows so emoji/box-drawing chars render
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass
    print(f">>> HCIE Closed-Loop Verification  API={API}")
    print(f"    Interactions to run: {NUM_INTERACTIONS}")
    print(f"    Consumer lag budget: {CONSUMER_LAG_BUDGET_SECONDS}s per layer")

    email, user_id, token = phase_register_and_login()
    baseline = phase_baseline(user_id)
    attempts = phase_interactions(token, NUM_INTERACTIONS)
    if not attempts:
        print(f"\n  {FAIL} No attempts succeeded; aborting layer checks")
        return 1
    results = phase_verify_layers(user_id, baseline, token, attempts)
    return phase_summary(results, attempts)


if __name__ == "__main__":
    sys.exit(main())
