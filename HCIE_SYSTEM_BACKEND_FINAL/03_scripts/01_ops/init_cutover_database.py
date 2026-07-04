#!/usr/bin/env python3
"""Apply Alembic migrations to the isolated FINAL cutover Postgres."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


FINAL_ROOT = Path(__file__).resolve().parents[2]
MIGRATIONS_DIR = FINAL_ROOT / "07_database" / "00_migrations"
DEFAULT_DATABASE_URL = "postgresql://hcie_user:hcie_password@localhost:55432/hcie"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--database-url",
        default=os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL),
        help="Postgres URL for hcie-final-postgres (host port 55432)",
    )
    args = parser.parse_args()

    env = dict(os.environ)
    env["DATABASE_URL"] = args.database_url
    cmd = [sys.executable, "-m", "alembic", "upgrade", "head"]
    result = subprocess.run(cmd, cwd=MIGRATIONS_DIR, env=env)
    if result.returncode == 0:
        print(f"[init_cutover_database] OK {args.database_url}")
    else:
        print(f"[init_cutover_database] FAILED exit={result.returncode}", file=sys.stderr)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
