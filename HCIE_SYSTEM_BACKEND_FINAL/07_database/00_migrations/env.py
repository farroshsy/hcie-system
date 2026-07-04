"""
Alembic environment configuration
"""

import os
from logging.config import fileConfig
from sqlalchemy import engine_from_config, text
from alembic import context

# this is the Alembic Config object
config = context.config

# Interpret the config file for Python logging
fileConfig(config.config_file_name)

# Set the SQLAlchemy URL from environment
def get_url():
    # Use environment variable or fallback to standard postgres
    return os.getenv("DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/hcie")

config.set_main_option("sqlalchemy.url", get_url())

# Target metadata - using raw SQL migrations
target_metadata = None

def run_migrations_online():
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=None,
    )

    with connectable.connect() as connection:
        # Alembic defaults ``version_num`` to VARCHAR(32). Our revision ids
        # (e.g. ``018_normalized_trajectory_signals``) exceed that limit.
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS alembic_version (
                    version_num VARCHAR(128) NOT NULL
                )
                """
            )
        )
        connection.execute(
            text(
                "ALTER TABLE alembic_version ALTER COLUMN version_num TYPE VARCHAR(128)"
            )
        )
        connection.commit()

        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
