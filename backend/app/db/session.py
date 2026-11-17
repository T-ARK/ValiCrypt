"""Database and persistence layer for MediaVault.

Uses SQLite for local zero-config operation with an architectural design
that supports seamless migration to PostgreSQL.
Strictly persists only non-sensitive operational job metadata.
"""

from contextlib import contextmanager
from datetime import datetime, timezone
import os
from pathlib import Path
import sqlite3
from typing import Generator, List, Optional
from app.core.config import settings


def get_db_path() -> Path:
    """Extracts filesystem path from SQLite database URL."""
    url = settings.DATABASE_URL
    if url.startswith("sqlite:///"):
        rel_or_abs = url.replace("sqlite:///", "")
        return Path(rel_or_abs).resolve()
    return Path("mediavault.db").resolve()


def init_db() -> None:
    """Initializes database tables and indexes."""
    db_path = get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(str(db_path)) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                operation TEXT NOT NULL,
                carrier_type TEXT NOT NULL,
                payload_type TEXT,
                carrier_size INTEGER,
                payload_size INTEGER,
                progress INTEGER DEFAULT 0,
                error_code TEXT,
                error_message TEXT,
                output_file_id TEXT,
                output_filename TEXT,
                mime_type TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                completed_at TEXT
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at)")
        conn.commit()


@contextmanager
def get_db() -> Generator[sqlite3.Connection, None, None]:
    """Provides a transactional database connection context."""
    db_path = get_db_path()
    conn = sqlite3.connect(str(db_path), timeout=30.0)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
