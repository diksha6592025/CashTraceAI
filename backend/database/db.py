"""
Database helper utilities for SQLite connection and querying.
"""

import sqlite3
from config import Config


def get_db_connection():
    """Returns a SQLite connection with row factory enabled."""
    conn = sqlite3.connect(Config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db():
    """Initializes the database schema and loads demo data."""

    conn = sqlite3.connect(Config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row

    with open(Config.SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema_script = f.read()

    # Disable FK checks while creating/updating the schema.
    conn.execute("PRAGMA foreign_keys = OFF;")
    conn.executescript(schema_script)
    conn.commit()

    # Re-enable FK checks for normal application queries.
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.close()

    print("[OK] Database schema initialized successfully.")

    # Load CashTrace AI demo data.
    try:
        from backend.database.sample_data import load_sample_data
        load_sample_data()
    except Exception as e:
        print(f"[WARN] Sample data auto-load note: {e}")


def query_db(query, args=(), one=False):
    """Executes a SELECT query and returns results."""

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(query, args)
    rows = cur.fetchall()
    conn.close()

    if rows:
        results = [dict(row) for row in rows]
        return results[0] if one else results

    return None if one else []


def execute_db(query, args=()):
    """Executes an INSERT, UPDATE, or DELETE query."""

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(query, args)
    conn.commit()
    last_id = cur.lastrowid
    conn.close()

    return last_id