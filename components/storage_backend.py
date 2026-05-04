import copy
import json
import pathlib
import time
from typing import Any, Dict, Optional, Tuple

from utils.secret_reader import get_supabase_database_url

BASE_DIR = pathlib.Path(__file__).resolve().parents[1]
LOCAL_DB_PATH = BASE_DIR / "data" / "db.json"
SAMPLE_DB_PATH = BASE_DIR / "data" / "db_sample.json"

APP_STATE_ID = "healthyme_app_state_v1"
APP_STATE_TABLE = "healthyme_app_state"
STATE_CACHE_TTL_SECONDS = 8

_ENGINE: Optional[Any] = None
_ENGINE_SOURCE: Optional[str] = None
_LAST_HEALTH_CHECK_TS = 0.0
_TABLE_READY = False

LAST_STATUS = {
    "mode": "unknown",
    "supabase_configured": False,
    "supabase_connected": False,
    "fallback_active": True,
    "users_count": "-",
    "members_count": "-",
    "last_error": "",
    "last_action": "",
    "secret_source": "-",
}

DEFAULT_STORES = {
    "users": [],
    "profiles": {},
    "workflow": {},
    "laf_responses": {},
    "nsp1_responses": {},
    "nsp2_responses": {},
    "nsp_scores": {},
    "admin_assessments": {},
    "body_mind_responses": {},
    "daily_logs": {},
    "notifications": [],
    "recipes": [],
    "exercises": [],
    "audit_logs": [],
    "response_audit_log": [],
    "assessment_instances": {},
    "assessment_instance_responses": {},
    "auth_sessions": {},
}


def _set_status(**kwargs):
    LAST_STATUS.update(kwargs)


def _count_users(db: Dict[str, Any]) -> str:
    try:
        return str(len(db.get("users", []) or []))
    except Exception:
        return "-"


def _count_members(db: Dict[str, Any]) -> str:
    try:
        return str(len([u for u in db.get("users", []) or [] if u.get("role") == "member"]))
    except Exception:
        return "-"


def _read_initial_local_state() -> Dict[str, Any]:
    for path in [LOCAL_DB_PATH, SAMPLE_DB_PATH]:
        try:
            if path.exists():
                return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return copy.deepcopy(DEFAULT_STORES)


def normalize_state(db: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    base = copy.deepcopy(DEFAULT_STORES)
    if isinstance(db, dict):
        base.update(db)
    # Keep backward-compatible stores present even when older db.json files miss them.
    for key, default_value in DEFAULT_STORES.items():
        if key not in base or base[key] is None:
            base[key] = copy.deepcopy(default_value)
    return base


def _get_streamlit_session_state():
    try:
        import streamlit as st
        return st.session_state
    except Exception:
        return None


def _get_cached_state() -> Optional[Dict[str, Any]]:
    """Small per-session cache to avoid repeated DB reads during one page render."""
    ss = _get_streamlit_session_state()
    if ss is None:
        return None
    try:
        cached = ss.get("_healthyme_state_cache")
        cached_at = float(ss.get("_healthyme_state_cache_at", 0))
        if cached is not None and (time.monotonic() - cached_at) <= STATE_CACHE_TTL_SECONDS:
            return copy.deepcopy(cached)
    except Exception:
        return None
    return None


def _set_cached_state(db: Dict[str, Any]) -> None:
    ss = _get_streamlit_session_state()
    if ss is None:
        return
    try:
        ss["_healthyme_state_cache"] = copy.deepcopy(normalize_state(db))
        ss["_healthyme_state_cache_at"] = time.monotonic()
    except Exception:
        pass


def _clear_cached_state() -> None:
    ss = _get_streamlit_session_state()
    if ss is None:
        return
    try:
        ss.pop("_healthyme_state_cache", None)
        ss.pop("_healthyme_state_cache_at", None)
    except Exception:
        pass


def _sql_text(sql: str):
    from sqlalchemy import text
    return text(sql)


def _get_engine() -> Tuple[Optional[Any], Optional[str], Optional[str]]:
    """Return SQLAlchemy engine, secret source, and error message."""
    global _ENGINE, _ENGINE_SOURCE

    database_url, secret_source = get_supabase_database_url()
    if not database_url:
        return None, None, "Supabase secrets are not configured."

    if "\x00" in database_url or "%00" in database_url:
        return None, secret_source, "Supabase database URL contains a null character or encoded null sequence."

    if _ENGINE is not None and _ENGINE_SOURCE == database_url:
        return _ENGINE, secret_source, None

    try:
        from sqlalchemy import create_engine

        _ENGINE = create_engine(
            database_url,
            pool_pre_ping=True,
            pool_recycle=1800,
            pool_size=3,
            max_overflow=2,
            connect_args={
                "connect_timeout": 10,
                "options": "-c statement_timeout=15000",
            },
        )
        _ENGINE_SOURCE = database_url
        return _ENGINE, secret_source, None
    except Exception as exc:
        return None, secret_source, f"{type(exc).__name__}: {exc}"


def supabase_configured() -> bool:
    database_url, _source = get_supabase_database_url()
    return bool(database_url)


def _ensure_supabase_table(engine: Any) -> None:
    """
    Create the single JSONB app-state table only once per server process.

    Speed fix:
    The older build attempted table/trigger setup repeatedly during normal page
    loads. This version performs the lightweight CREATE TABLE check once and
    skips trigger churn.
    """
    global _TABLE_READY

    if _TABLE_READY:
        return

    create_sql = f"""
    CREATE TABLE IF NOT EXISTS public.{APP_STATE_TABLE} (
        id TEXT PRIMARY KEY,
        data JSONB NOT NULL DEFAULT '{{}}'::jsonb,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
    )
    """

    with engine.begin() as conn:
        conn.execute(_sql_text(create_sql))

    _TABLE_READY = True


def _decode_db_data(value: Any) -> Dict[str, Any]:
    if isinstance(value, dict):
        return normalize_state(value)
    if isinstance(value, str):
        return normalize_state(json.loads(value))
    return normalize_state({})


def _load_from_supabase() -> Tuple[bool, Dict[str, Any], str]:
    engine, secret_source, err = _get_engine()
    if not engine:
        return False, {}, err or "Supabase database URL is not available."

    try:
        _ensure_supabase_table(engine)
        with engine.begin() as conn:
            row = conn.execute(
                _sql_text(f"SELECT data FROM public.{APP_STATE_TABLE} WHERE id = :id"),
                {"id": APP_STATE_ID},
            ).fetchone()

            if row and row[0] is not None:
                db = _decode_db_data(row[0])
                _set_status(
                    mode="SUPABASE",
                    supabase_configured=True,
                    supabase_connected=True,
                    fallback_active=False,
                    users_count=_count_users(db),
                    members_count=_count_members(db),
                    last_error="",
                    last_action="Loaded from Supabase.",
                    secret_source=secret_source or "-",
                )
                _set_cached_state(db)
                return True, db, ""

            initial = normalize_state(_read_initial_local_state())
            conn.execute(
                _sql_text(
                    f"""
                    INSERT INTO public.{APP_STATE_TABLE} (id, data, updated_at)
                    VALUES (:id, CAST(:data AS jsonb), now())
                    ON CONFLICT (id)
                    DO UPDATE SET data = EXCLUDED.data, updated_at = now()
                    """
                ),
                {"id": APP_STATE_ID, "data": json.dumps(initial, ensure_ascii=False)},
            )
            _set_status(
                mode="SUPABASE",
                supabase_configured=True,
                supabase_connected=True,
                fallback_active=False,
                users_count=_count_users(initial),
                members_count=_count_members(initial),
                last_error="",
                last_action="Supabase row was missing; seeded from local/sample state.",
                secret_source=secret_source or "-",
            )
            _set_cached_state(initial)
            return True, initial, "Supabase row was missing; seeded from local/sample state."

    except Exception as exc:
        return False, {}, f"{type(exc).__name__}: {exc}"


def _save_to_supabase(db: Dict[str, Any]) -> Tuple[bool, str]:
    engine, secret_source, err = _get_engine()
    if not engine:
        return False, err or "Supabase database URL is not available."

    db = normalize_state(db)
    try:
        _ensure_supabase_table(engine)
        payload = json.dumps(db, ensure_ascii=False)
        with engine.begin() as conn:
            conn.execute(
                _sql_text(
                    f"""
                    INSERT INTO public.{APP_STATE_TABLE} (id, data, updated_at)
                    VALUES (:id, CAST(:data AS jsonb), now())
                    ON CONFLICT (id)
                    DO UPDATE SET data = EXCLUDED.data, updated_at = now()
                    """
                ),
                {"id": APP_STATE_ID, "data": payload},
            )
        _set_status(
            mode="SUPABASE",
            supabase_configured=True,
            supabase_connected=True,
            fallback_active=False,
            users_count=_count_users(db),
            members_count=_count_members(db),
            last_error="",
            last_action="Saved to Supabase.",
            secret_source=secret_source or "-",
        )
        _set_cached_state(db)
        return True, ""
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


def load_state() -> Dict[str, Any]:
    """Load HealthyMe state.

    Primary: Supabase PostgreSQL via SUPABASE_DATABASE_URL / DATABASE_URL.
    Safe fallback: local data/db.json if Supabase is missing or unhealthy.
    """
    cached = _get_cached_state()
    if cached is not None:
        return cached

    configured = supabase_configured()
    if configured:
        ok, db, msg = _load_from_supabase()
        if ok:
            if msg:
                LAST_STATUS["last_action"] = msg
            return db

        local_db = normalize_state(_read_initial_local_state())
        _set_status(
            mode="LOCAL_FALLBACK",
            supabase_configured=True,
            supabase_connected=False,
            fallback_active=True,
            users_count=_count_users(local_db),
            members_count=_count_members(local_db),
            last_error=msg,
            last_action="Supabase failed; loaded local fallback.",
            secret_source=get_supabase_database_url()[1] or "-",
        )
        _set_cached_state(local_db)
        return local_db

    local_db = normalize_state(_read_initial_local_state())
    _set_status(
        mode="LOCAL_FALLBACK",
        supabase_configured=False,
        supabase_connected=False,
        fallback_active=True,
        users_count=_count_users(local_db),
        members_count=_count_members(local_db),
        last_error="Supabase secrets are not configured.",
        last_action="Loaded local fallback.",
        secret_source="-",
    )
    _set_cached_state(local_db)
    return local_db


def save_state(db: Dict[str, Any]) -> None:
    """Save state to Supabase when healthy; preserve local fallback on failure."""
    db = normalize_state(db)
    configured = supabase_configured()

    if configured:
        ok, msg = _save_to_supabase(db)
        if ok:
            return

        # Do not crash the app; preserve data locally as emergency fallback.
        _set_status(
            mode="LOCAL_FALLBACK",
            supabase_configured=True,
            supabase_connected=False,
            fallback_active=True,
            users_count=_count_users(db),
            members_count=_count_members(db),
            last_error=msg,
            last_action="Supabase save failed; saved local fallback.",
            secret_source=get_supabase_database_url()[1] or "-",
        )

    LOCAL_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOCAL_DB_PATH.write_text(json.dumps(db, indent=2, ensure_ascii=False), encoding="utf-8")
    _set_cached_state(db)


def get_storage_status() -> Dict[str, Any]:
    """Return active storage health using the same backend that the app uses."""
    global _LAST_HEALTH_CHECK_TS

    configured = supabase_configured()
    if not configured:
        local_db = normalize_state(_read_initial_local_state())
        return {
            **LAST_STATUS,
            "mode": "LOCAL_FALLBACK",
            "supabase_configured": False,
            "supabase_connected": False,
            "fallback_active": True,
            "users_count": _count_users(local_db),
            "members_count": _count_members(local_db),
            "last_error": LAST_STATUS.get("last_error") or "Supabase secrets are not configured.",
            "last_action": LAST_STATUS.get("last_action") or "Loaded local fallback.",
            "secret_source": "-",
        }

    # Use a recent successful status to keep pages responsive.
    if LAST_STATUS.get("mode") == "SUPABASE" and (time.monotonic() - _LAST_HEALTH_CHECK_TS) <= STATE_CACHE_TTL_SECONDS:
        return dict(LAST_STATUS)

    ok, db, msg = _load_from_supabase()
    _LAST_HEALTH_CHECK_TS = time.monotonic()
    if ok:
        return {
            "mode": "SUPABASE",
            "supabase_configured": True,
            "supabase_connected": True,
            "fallback_active": False,
            "users_count": _count_users(db),
            "members_count": _count_members(db),
            "last_error": "",
            "last_action": msg or "Supabase health check passed.",
            "secret_source": get_supabase_database_url()[1] or "-",
        }

    local_db = normalize_state(_read_initial_local_state())
    status = {
        "mode": "LOCAL_FALLBACK",
        "supabase_configured": True,
        "supabase_connected": False,
        "fallback_active": True,
        "users_count": _count_users(local_db),
        "members_count": _count_members(local_db),
        "last_error": msg,
        "last_action": "Supabase health check failed.",
        "secret_source": get_supabase_database_url()[1] or "-",
    }
    _set_status(**status)
    return status


def export_current_state_bytes() -> bytes:
    """Return current active state as downloadable JSON bytes."""
    state = load_state()
    return json.dumps(state, indent=2, ensure_ascii=False).encode("utf-8")


def push_local_data_to_supabase() -> Tuple[bool, str]:
    """Manual migration: push current local db.json/sample data to Supabase."""
    if not supabase_configured():
        return False, "Supabase secrets are not configured."

    local_state = normalize_state(_read_initial_local_state())
    ok, msg = _save_to_supabase(local_state)
    if ok:
        _clear_cached_state()
        _set_cached_state(local_state)
        return True, "Local data pushed to Supabase successfully."
    return False, msg


def pull_supabase_to_local_backup() -> Tuple[bool, str]:
    """Manual backup: pull Supabase state into data/supabase_backup.json."""
    if not supabase_configured():
        return False, "Supabase secrets are not configured."

    _clear_cached_state()
    ok, db, msg = _load_from_supabase()
    if not ok:
        return False, msg

    backup_path = BASE_DIR / "data" / "supabase_backup.json"
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    backup_path.write_text(json.dumps(normalize_state(db), indent=2, ensure_ascii=False), encoding="utf-8")
    return True, f"Supabase backup saved to {backup_path.name}."
