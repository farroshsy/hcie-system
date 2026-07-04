#!/usr/bin/env python3
"""
Seed script — creates the default admin user and ensures the default tenant exists.

Idempotent: safe to run multiple times. Will not overwrite an existing admin.

Usage (direct):
    python 03_scripts/01_ops/seed_admin.py

Usage (via Docker, after stack is up):
    docker exec hcie-final-api python /app/03_scripts/01_ops/seed_admin.py

Environment variables (all have defaults matching docker-compose.final.yml):
    POSTGRES_HOST       default: localhost
    POSTGRES_PORT       default: 55432   (host-mapped port)
    POSTGRES_DB         default: hcie
    POSTGRES_USER       default: hcie_user
    POSTGRES_PASSWORD   default: hcie_password
    ADMIN_EMAIL         default: admin@hcie.local
    ADMIN_PASSWORD      default: (required — no default, must be set)
    ADMIN_NAME          default: Admin
"""

import os
import sys
import uuid
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)

DEFAULT_TENANT_ID = "00000000-0000-0000-0000-000000000000"

def get_dsn() -> str:
    host = os.environ.get("POSTGRES_HOST", "localhost")
    port = os.environ.get("POSTGRES_PORT", "55432")
    db   = os.environ.get("POSTGRES_DB",   "hcie")
    user = os.environ.get("POSTGRES_USER", "hcie_user")
    pw   = os.environ.get("POSTGRES_PASSWORD", "hcie_password")
    return f"postgresql://{user}:{pw}@{host}:{port}/{db}"


def hash_password(password: str) -> str:
    import bcrypt
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def run():
    try:
        import psycopg2
        import psycopg2.extras
    except ImportError:
        log.error("psycopg2 not installed — run: pip install psycopg2-binary")
        sys.exit(1)

    admin_email    = os.environ.get("ADMIN_EMAIL", "admin@hcie.local")
    admin_password = os.environ.get("ADMIN_PASSWORD", "")
    admin_name     = os.environ.get("ADMIN_NAME", "Admin")

    if not admin_password:
        log.error("ADMIN_PASSWORD env var is required")
        sys.exit(1)

    dsn = get_dsn()
    log.info("Connecting to %s", dsn.replace(os.environ.get("POSTGRES_PASSWORD", ""), "***"))

    conn = psycopg2.connect(dsn)
    conn.autocommit = False
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    try:
        # 1. Ensure default tenant exists
        cur.execute(
            """
            INSERT INTO tenants (id, name)
            VALUES (%s, 'Default Tenant')
            ON CONFLICT (id) DO NOTHING
            """,
            (DEFAULT_TENANT_ID,),
        )
        log.info("✓ Default tenant ensured (id=%s)", DEFAULT_TENANT_ID)

        # 2. Check if admin already exists
        cur.execute("SELECT id, email, role FROM users WHERE email = %s", (admin_email,))
        existing = cur.fetchone()

        if existing:
            log.info(
                "Admin user already exists — email=%s id=%s role=%s (no change)",
                existing["email"], existing["id"], existing["role"],
            )
            conn.commit()
            return

        # 3. Create admin user
        new_id = str(uuid.uuid4())
        pw_hash = hash_password(admin_password)

        cur.execute(
            """
            INSERT INTO users
              (id, email, password_hash, name, role, tenant_id,
               policy_mode, learning_rate, forgetting_rate, user_type)
            VALUES
              (%s, %s, %s, %s, 'admin', %s,
               'hcie', 0.01, 0.001, 'real')
            """,
            (new_id, admin_email, pw_hash, admin_name, DEFAULT_TENANT_ID),
        )

        conn.commit()
        log.info("✅ Admin user created — email=%s id=%s", admin_email, new_id)
        log.info("   Login via POST /auth/login with those credentials")

    except Exception as exc:
        conn.rollback()
        log.error("❌ Seed failed: %s", exc)
        sys.exit(1)
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    run()
