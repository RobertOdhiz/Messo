"""
SQLite database: engine, session, and initialization.
Database file is created on first use; migrations run on app startup.
"""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.config import DATABASE_URL

# SQLite needs check_same_thread=False when used with FastAPI
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Session:
    """Dependency: yield a DB session, close after request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all tables (Base.metadata). Call after Alembic upgrades or instead of migrations."""
    Base.metadata.create_all(bind=engine)


def run_migrations() -> None:
    """Run Alembic migrations up to head. Safe to call on every startup."""
    import os
    from alembic import command
    from alembic.config import Config
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ini_path = os.path.join(base_dir, "alembic.ini")
    script_location = os.path.join(base_dir, "alembic")
    if not os.path.isdir(script_location):
        return
    alembic_cfg = Config(ini_path) if os.path.isfile(ini_path) else Config()
    alembic_cfg.set_main_option("script_location", script_location)
    alembic_cfg.set_main_option("sqlalchemy.url", DATABASE_URL)
    command.upgrade(alembic_cfg, "head")
