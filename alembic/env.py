"""
Alembic env: use app.db engine and app.models for target_metadata.
Run from project root: alembic upgrade head
Or run programmatically on app startup (see app.db.run_migrations).
"""
from alembic import context
from sqlalchemy import engine_from_config, pool

from app.config import DATABASE_URL
from app.db import Base

# Import all models so Base.metadata has the tables
from app.models.base import DlrReceipt, SentSms  # noqa: F401

config = context.config
target_metadata = Base.metadata

# Use DATABASE_URL from app config
config.set_main_option("sqlalchemy.url", DATABASE_URL)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (generate SQL only)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode (connect to DB)."""
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = DATABASE_URL
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,  # SQLite-friendly ALTER
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
