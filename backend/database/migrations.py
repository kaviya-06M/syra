"""
migrations.py
─────────────
Creates all database tables on first run.
Called once at startup (from main.py or scheduler).
"""

import sys, os

try:
    from .database import engine, Base
    from . import models  # noqa: F401  -- registers all models with Base
except ImportError:
    # Fallback when run directly (e.g. from scheduler.py context)
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from database.database import engine, Base
    from database import models  # noqa: F401


def run_migrations():
    """Create tables if they don't already exist."""
    Base.metadata.create_all(bind=engine)
    print("[DB] Tables created / verified OK")


if __name__ == "__main__":
    run_migrations()
