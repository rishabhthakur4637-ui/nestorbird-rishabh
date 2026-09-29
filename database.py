"""
Database Connection & Execution Layer using psycopg2.
Follows clean context management, parameterization, and connection handling.
"""

from contextlib import contextmanager
from typing import Any, Dict, List, Optional
import psycopg2
from psycopg2.extras import RealDictCursor, Json
from app.config import settings


def get_connection(dbname: Optional[str] = None):
    """
    Establish and return a new psycopg2 connection.
    Defaults to settings.DB_NAME if dbname is not specified.
    """
    target_db = dbname or settings.DB_NAME
    return psycopg2.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        dbname=target_db,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
    )


@contextmanager
def get_db_cursor(commit: bool = True):
    """
    Context manager that yields a psycopg2 cursor with RealDictCursor.
    Automatically commits on success or rolls back on exception.
    """
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        yield cursor
        if commit:
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def execute_query(query: str, params: Optional[tuple] = None, commit: bool = True) -> None:
    """Execute a query that does not return rows (e.g. CREATE, UPDATE, DELETE)."""
    with get_db_cursor(commit=commit) as cur:
        cur.execute(query, params)


def fetch_one(query: str, params: Optional[tuple] = None) -> Optional[Dict[str, Any]]:
    """Execute a SELECT query and return a single row as a dictionary."""
    with get_db_cursor(commit=False) as cur:
        cur.execute(query, params)
        row = cur.fetchone()
        return dict(row) if row else None


def fetch_all(query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
    """Execute a SELECT query and return all matching rows as dictionaries."""
    with get_db_cursor(commit=False) as cur:
        cur.execute(query, params)
        rows = cur.fetchall()
        return [dict(row) for row in rows]


def insert_record(query: str, params: tuple) -> Optional[Dict[str, Any]]:
    """
    Execute an INSERT ... RETURNING query and return the inserted record.
    """
    with get_db_cursor(commit=True) as cur:
        cur.execute(query, params)
        row = cur.fetchone()
        return dict(row) if row else None
