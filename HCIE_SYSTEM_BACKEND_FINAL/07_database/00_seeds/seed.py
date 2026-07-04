#!/usr/bin/env python3
"""Canonical, idempotent database seeder — the single entrypoint for 07_database/00_seeds.

Seeding the live stack has historically been split and undiscoverable:
  - schema + idempotent curriculum/task/material data live in the Alembic chain
    (07_database/00_migrations/versions/, e.g. 009_seed_k12_concepts .. 033_seed_multimodal_materials);
  - the bootstrap admin user + default tenant live in 03_scripts/01_ops/seed_admin.py.

This script COMPOSES those two existing, proven, idempotent seeders behind one command —
it adds no new seed logic of its own. Safe to run repeatedly.

Usage (in-container, after the stack is up):
    docker compose -f .../docker-compose.final.yml exec api python /app/07_database/00_seeds/seed.py
Or via the Makefile:
    make seed

Flags:
    --skip-migrate   don't run `alembic upgrade head`
    --skip-admin     don't seed the admin user (also auto-skipped if ADMIN_PASSWORD is unset)
    --no-verify      don't print post-seed row counts

Environment (defaults match docker-compose.final.yml):
    POSTGRES_HOST/PORT/DB/USER/PASSWORD, DATABASE_URL, ADMIN_EMAIL/PASSWORD/NAME.
"""
from __future__ import annotations

import argparse
import logging
import os
import subprocess
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("seed")

# 00_seeds -> 07_database -> <backend root>
BACKEND_ROOT = Path(__file__).resolve().parents[2]
MIGRATIONS_DIR = BACKEND_ROOT / "07_database" / "00_migrations"
SEED_ADMIN = BACKEND_ROOT / "03_scripts" / "01_ops" / "seed_admin.py"


def _run_migrations() -> None:
    """`alembic upgrade head` — applies schema + all idempotent data-seed migrations.

    Mirrors the compose `migrations` service (cd 07_database/00_migrations && alembic upgrade head).
    """
    if not (MIGRATIONS_DIR / "alembic.ini").exists():
        log.error("alembic.ini not found under %s — cannot migrate", MIGRATIONS_DIR)
        sys.exit(1)
    log.info("→ alembic upgrade head (%s)", MIGRATIONS_DIR)
    res = subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], cwd=str(MIGRATIONS_DIR))
    if res.returncode != 0:
        log.error("alembic upgrade head failed (exit %s)", res.returncode)
        sys.exit(res.returncode)
    log.info("✓ migrations applied")


def _seed_admin() -> None:
    """Run the existing idempotent admin/tenant seeder as a subprocess."""
    if not SEED_ADMIN.exists():
        log.error("seed_admin.py not found at %s", SEED_ADMIN)
        sys.exit(1)
    log.info("→ seed admin/tenant (%s)", SEED_ADMIN)
    res = subprocess.run([sys.executable, str(SEED_ADMIN)])
    if res.returncode != 0:
        log.error("seed_admin failed (exit %s)", res.returncode)
        sys.exit(res.returncode)
    log.info("✓ admin/tenant seeded")


def _verify() -> None:
    """Best-effort post-seed row counts. Tolerant — never fails the seed."""
    try:
        import psycopg2  # noqa: F401
    except ImportError:
        log.info("(verify skipped — psycopg2 not available)")
        return
    dsn = os.environ.get("DATABASE_URL") or (
        f"postgresql://{os.environ.get('POSTGRES_USER','hcie_user')}:"
        f"{os.environ.get('POSTGRES_PASSWORD','hcie_password')}@"
        f"{os.environ.get('POSTGRES_HOST','localhost')}:"
        f"{os.environ.get('POSTGRES_PORT','55432')}/"
        f"{os.environ.get('POSTGRES_DB','hcie')}"
    )
    counts = []
    try:
        import psycopg2
        conn = psycopg2.connect(dsn)
        try:
            for table in ("tenants", "users", "concepts", "tasks"):
                try:
                    cur = conn.cursor()
                    cur.execute(f"SELECT count(*) FROM {table}")  # table names are a fixed literal allow-list
                    counts.append(f"{table}={cur.fetchone()[0]}")
                    cur.close()
                except Exception:
                    conn.rollback()  # table may not exist in this schema variant
        finally:
            conn.close()
    except Exception as exc:
        log.info("(verify skipped — %s)", exc)
        return
    log.info("✓ post-seed counts: %s", ", ".join(counts) if counts else "(none readable)")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Canonical idempotent DB seeder (migrate + admin).")
    ap.add_argument("--skip-migrate", action="store_true", help="skip alembic upgrade head")
    ap.add_argument("--skip-admin", action="store_true", help="skip admin/tenant seeding")
    ap.add_argument("--no-verify", action="store_true", help="skip post-seed row counts")
    args = ap.parse_args(argv)

    if not args.skip_migrate:
        _run_migrations()
    else:
        log.info("(migrations skipped by flag)")

    if args.skip_admin:
        log.info("(admin seed skipped by flag)")
    elif not os.environ.get("ADMIN_PASSWORD"):
        log.warning("ADMIN_PASSWORD unset — skipping admin seed (set it to create the bootstrap admin)")
    else:
        _seed_admin()

    if not args.no_verify:
        _verify()

    log.info("✅ seed complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
