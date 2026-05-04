"""
HealthyMe Supabase Secret Reader
--------------------------------
Purpose:
- Safely read Supabase/Postgres connection strings from Streamlit Secrets or environment variables.
- Avoid exposing passwords in the UI.
- Prevent false LOCAL_FALLBACK when the secret key name differs.

Place this file at:
utils/secret_reader.py
"""

from __future__ import annotations

import os
from urllib.parse import urlsplit, urlunsplit
from typing import Any, Dict, List, Optional, Tuple



ROOT_SECRET_KEYS: List[str] = [
    "SUPABASE_DATABASE_URL",
    "DATABASE_URL",
    "SUPABASE_DB_URL",
    "SUPABASE_POSTGRES_URL",
    "POSTGRES_URL",
]

NESTED_SECRET_PATHS: List[Tuple[str, str]] = [
    ("supabase", "database_url"),
    ("supabase", "url"),
    ("database", "url"),
    ("postgres", "url"),
]

def _get_streamlit_secrets():
    try:
        import streamlit as st
        return st.secrets
    except Exception:
        return None


def _safe_strip(value: Any) -> Optional[str]:
    """Convert a possible secret value to a clean string."""
    if value is None:
        return None

    value = str(value).strip().strip('"').strip("'")

    if not value:
        return None

    if value.lower() in {"none", "null", "your_database_url", "your_supabase_url"}:
        return None

    return value


def _read_streamlit_root_key(key: str) -> Optional[str]:
    """Read a root key from st.secrets safely."""
    try:
        secrets = _get_streamlit_secrets()
        if secrets is None:
            return None
        return _safe_strip(secrets.get(key))
    except Exception:
        return None


def _read_streamlit_nested_key(section: str, key: str) -> Optional[str]:
    """Read a nested key from st.secrets safely."""
    try:
        secrets = _get_streamlit_secrets()
        if secrets is None:
            return None
        section_value = secrets.get(section, {})
        if hasattr(section_value, "get"):
            return _safe_strip(section_value.get(key))
    except Exception:
        return None

    return None


def _read_environment_key(key: str) -> Optional[str]:
    """Read an environment variable safely."""
    return _safe_strip(os.getenv(key))


def get_supabase_database_url() -> Tuple[Optional[str], Optional[str]]:
    """
    Return:
        (database_url, source_name)

    Reads from multiple possible secret names so the app does not remain in
    LOCAL_FALLBACK just because the key name differs.
    """

    for key in ROOT_SECRET_KEYS:
        value = _read_streamlit_root_key(key)
        if value:
            return value, f"st.secrets[{key}]"

        value = _read_environment_key(key)
        if value:
            return value, f"os.environ[{key}]"

    for section, key in NESTED_SECRET_PATHS:
        value = _read_streamlit_nested_key(section, key)
        if value:
            return value, f"st.secrets[{section}][{key}]"

    return None, None


def mask_database_url(database_url: Optional[str]) -> str:
    """
    Return a password-safe version of the DB URL.
    Example:
    postgresql://postgres.xxxx:***@host:5432/postgres
    """

    if not database_url:
        return "-"

    try:
        parts = urlsplit(database_url)
        username = parts.username or ""
        hostname = parts.hostname or ""
        port = f":{parts.port}" if parts.port else ""

        if username:
            safe_netloc = f"{username}:***@{hostname}{port}"
        else:
            safe_netloc = hostname + port

        return urlunsplit((parts.scheme, safe_netloc, parts.path, parts.query, parts.fragment))
    except Exception:
        return "Unable to safely parse database URL"


def get_secret_diagnostics() -> Dict[str, Any]:
    """
    Safe diagnostic details for Admin Database Status page.
    Shows key names only, never passwords or raw secret values.
    """

    try:
        secrets = _get_streamlit_secrets()
        streamlit_secret_keys_seen = list(secrets.keys()) if secrets is not None else []
    except Exception as exc:
        streamlit_secret_keys_seen = [f"Unable to read st.secrets: {type(exc).__name__}"]

    env_keys_seen = [key for key in ROOT_SECRET_KEYS if _read_environment_key(key)]

    database_url, source = get_supabase_database_url()

    return {
        "expected_root_keys": ROOT_SECRET_KEYS,
        "expected_nested_paths": [f"{section}.{key}" for section, key in NESTED_SECRET_PATHS],
        "streamlit_secret_keys_seen": streamlit_secret_keys_seen,
        "matching_environment_keys_seen": env_keys_seen,
        "supabase_secret_found": bool(database_url),
        "secret_source_used": source or "-",
        "masked_database_url": mask_database_url(database_url),
        "contains_null_character": ("\x00" in database_url) if database_url else False,
        "contains_encoded_null_sequence": ("%00" in database_url) if database_url else False,
        "important_note": "Only key names and a masked URL are shown. Password values are never displayed.",
    }
