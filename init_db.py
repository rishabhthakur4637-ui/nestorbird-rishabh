"""
Database Initialization Script.
Ensures the target PostgreSQL database exists and creates necessary tables and indexes.
"""

import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from app.config import settings
from app.database import execute_query


INIT_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS scraped_records (
    id SERIAL PRIMARY KEY,
    source_url TEXT NOT NULL,
    entity_type VARCHAR(100) DEFAULT 'generic',
    title TEXT,
    content TEXT,
    raw_data JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_scraped_records_url ON scraped_records(source_url);
CREATE INDEX IF NOT EXISTS idx_scraped_records_entity ON scraped_records(entity_type);
CREATE INDEX IF NOT EXISTS idx_scraped_records_raw_data ON scraped_records USING gin(raw_data);
"""


def create_database_if_not_exists():
    """Connect to default 'postgres' database and create target database if it doesn't exist."""
    print(f"[*] Checking if database '{settings.DB_NAME}' exists on {settings.DB_HOST}:{settings.DB_PORT}...")
    try:
        conn = psycopg2.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            dbname="postgres",
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()

        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (settings.DB_NAME,))
        exists = cur.fetchone()

        if not exists:
            print(f"[+] Database '{settings.DB_NAME}' does not exist. Creating it now...")
            cur.execute(f'CREATE DATABASE "{settings.DB_NAME}";')
            print(f"[OK] Database '{settings.DB_NAME}' created successfully.")
        else:
            print(f"[OK] Database '{settings.DB_NAME}' already exists.")

        cur.close()
        conn.close()
    except Exception as e:
        print(f"[!] Warning during database existence check: {e}")
        print("[!] Proceeding to table initialization (assuming database exists or user has restricted permissions)...")


def initialize_schema():
    """Create tables and indexes in the target database."""
    print(f"[*] Initializing tables and indexes in '{settings.DB_NAME}'...")
    try:
        execute_query(INIT_TABLE_SQL)
        print("[OK] Table 'scraped_records' and indexes verified successfully.")
    except Exception as e:
        print(f"[X] Failed to initialize schema: {e}")
        raise


if __name__ == "__main__":
    print("=" * 60)
    print(" NestorBird Web Scraper - Database Initializer")
    print("=" * 60)
    create_database_if_not_exists()
    initialize_schema()
    print("[OK] Database setup complete!")
