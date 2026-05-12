"""
HealthyMe Database Runtime
--------------------------
Purpose:
- Connect to Supabase safely when secrets are present.
- Fall back to local mode without crashing when secrets or connection fail.
- Provide a single database health/status object for the Admin Database Status page.

Place this file at:
utils/db_runtime.py
"""

from __future__ import annotations

import re
from typing import Any, Dict, Optional, Tuple

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine

from utils.secret_reader import get_supabase_database_url


TABLE_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _base_status() -> Dict[str, Any]:
    return {
        "mode": "LOCAL_FALLBACK",
        "supabase_configured": False,
        "supabase_connected": False,
        "fallback_active": True,
        "users_count": "-",
        "members_count": "-",
        "last_action": "Loaded local fallback.",
        "last_error": "",
        "secret_source": "-",
    }


def _safe_count_rows(engine: Engine, table_name: str) -> Optional[int]:
    """
    Count rows only for safe table names.
    Returns None if table does not exist or cannot be read.
    """

    if not TABLE_NAME_RE.match(table_name):
        return None

    try:
        with engine.connect() as conn:
            result = conn.execute(text(f'SELECT COUNT(*) FROM "{table_name}"'))
            return int(result.scalar() or 0)
    except Exception:
        return None


def _first_existing_table_count(engine: Engine, possible_table_names: list[str]) -> str:
    """
    Try multiple likely table names and return the first readable count.
    Returns '-' when no matching table can be read.
    """

    try:
        inspector = inspect(engine)
        existing_tables = set(inspector.get_table_names())
    except Exception:
        existing_tables = set()

    for table_name in possible_table_names:
        if existing_tables and table_name not in existing_tables:
            continue

        count = _safe_count_rows(engine, table_name)
        if count is not None:
            return str(count)

    return "-"


def get_database_engine_and_status() -> Tuple[Optional[Engine], Dict[str, Any]]:
    """
    Main function your app should call.

    Returns:
        engine:
            SQLAlchemy Engine if Supabase connected, otherwise None.
        status:
            Safe status dictionary for UI/debugging.
    """

    status = _base_status()

    database_url, secret_source = get_supabase_database_url()

    if not database_url:
        status["last_error"] = "Supabase secrets are not configured."
        return None, status

    status["supabase_configured"] = True
    status["secret_source"] = secret_source or "-"

    if "\x00" in database_url or "%00" in database_url:
        status["last_error"] = "Supabase database URL contains a null character or encoded null sequence."
        return None, status

    try:
        engine = create_engine(
            database_url,
            pool_pre_ping=True,
            pool_recycle=1800,
            connect_args={
                "connect_timeout": 10,
                "options": "-c statement_timeout=15000",
            },
        )

        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))

        status["mode"] = "SUPABASE"
        status["supabase_connected"] = True
        status["fallback_active"] = False
        status["last_action"] = "Connected to Supabase."
        status["last_error"] = ""

        # These table names are deliberately flexible because app builds often use different names.
        status["users_count"] = _first_existing_table_count(
            engine,
            [
                "healthyme_users",
                "hm_users",
                "app_users",
                "users",
            ],
        )

        status["members_count"] = _first_existing_table_count(
            engine,
            [
                "healthyme_members",
                "hm_members",
                "members",
                "clients",
                "patients",
            ],
        )

        return engine, status

    except Exception as exc:
        status["mode"] = "LOCAL_FALLBACK"
        status["supabase_connected"] = False
        status["fallback_active"] = True
        status["last_action"] = "Supabase connection failed. Loaded local fallback."
        status["last_error"] = f"{type(exc).__name__}: {exc}"
        return None, status


def get_database_status() -> Dict[str, Any]:
    """
    Convenience function for pages that only need the status.

    Important: this now delegates to components.storage_backend so the debug
    status always matches the storage layer that the app actually uses.
    """

    try:
        from components.storage_backend import get_storage_status
        return get_storage_status()
    except Exception:
        _engine, status = get_database_engine_and_status()
        return status
