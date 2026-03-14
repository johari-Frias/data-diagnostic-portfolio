"""
db_logger.py – PostgreSQL usage-logging backend for the Data Diagnostic Dashboard.

Logs each successful CSV upload to a cloud PostgreSQL database (Neon / Supabase).
The database URL is read from the ``DATABASE_URL`` OS environment variable,
making it compatible with Render, Railway, Heroku, Docker, and similar platforms.

Usage::

    from src.db_logger import log_upload

    log_upload(
        file_name="sales_q4.csv",
        total_rows=12_000,
        total_columns=18,
        missing_values_count=254,
    )
"""

from __future__ import annotations

import logging
import os
from typing import Optional

import psycopg2

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Connection helper
# ──────────────────────────────────────────────────────────────────────────────

def get_connection() -> Optional[psycopg2.extensions.connection]:
    """Open a PostgreSQL connection using the ``DATABASE_URL`` env var.

    The variable should follow the format::

        postgresql://user:password@host:port/dbname?sslmode=require

    Returns
    -------
    psycopg2.extensions.connection or None
        A live database connection, or ``None`` if the variable is missing
        or the connection attempt fails.
    """
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        logger.warning(
            "DATABASE_URL not set in environment — database logging is disabled."
        )
        return None

    try:
        conn = psycopg2.connect(database_url, sslmode="require")
        return conn
    except psycopg2.OperationalError as exc:
        logger.error("Failed to connect to PostgreSQL: %s", exc)
        return None


# ──────────────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────────────

_INSERT_SQL = """
    INSERT INTO app_usage_logs (file_name, total_rows, total_columns, missing_values_count)
    VALUES (%s, %s, %s, %s);
"""


def log_upload(
    file_name: str,
    total_rows: int,
    total_columns: int,
    missing_values_count: int,
) -> bool:
    """Write a single usage-log row to the ``app_usage_logs`` table.

    Parameters
    ----------
    file_name : str
        Name of the uploaded file (e.g. ``"sales_q4.csv"``).
    total_rows : int
        Number of rows in the uploaded DataFrame.
    total_columns : int
        Number of columns in the uploaded DataFrame.
    missing_values_count : int
        Total number of null / NaN cells across the entire DataFrame.

    Returns
    -------
    bool
        ``True`` if the row was inserted successfully, ``False`` otherwise.
        Failures are logged but never raise — the user's workflow is
        never interrupted by a database error.
    """
    conn = get_connection()
    if conn is None:
        return False

    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    _INSERT_SQL,
                    (file_name, total_rows, total_columns, missing_values_count),
                )
        return True
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to log upload to database: %s", exc)
        return False
    finally:
        conn.close()
