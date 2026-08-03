import copy
import json
import os
import pathlib
from typing import Any, Dict, Optional, Tuple

from components.normalized_store import (
    commit_identity_and_state,
    ensure_workflow_projection,
    load_users_workflow_from_normalized,
)

BASE_DIR = pathlib.Path(__file__).resolve().parents[1]
LOCAL_DB_PATH = BASE_DIR / "data" / "db.json"
SAMPLE_DB_PATH = BASE_DIR / "data" / "db_sample.json"

APP_STATE_ID = "healthyme_app_state_v1"
CACHE_KEY = "_hm_db_cache"
STATUS_KEY = "_hm_storage_status"

LAST_STATUS = {
    "mode": "unknown",
    "supabase_configured": False,
    "supabase_connected": False,
    "fallback_active": True,
    "last_error": "",
    "last_action": "",
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
    "assessment_instances": {},
    "assessment_instance_responses": {},
    "login_sessions": {},
    "resource_assignments": {"recipes": {}, "exercises": {}},
    "messages": [],
    # v102.3A: persistent member-specific supplement regimen storage.
    "member_supplements": [],
    "supplement_audit_logs": [],
}


def _session_state():
    try:
        import streamlit as st

        return st.session_state
    except Exception:
        return None


def _set_status(**kwargs):
    LAST_STATUS.update(kwargs)
    ss = _session_state()
    if ss is not None:
        ss[STATUS_KEY] = dict(LAST_STATUS)


def _get_cached_status():
    ss = _session_state()
    if ss is not None and STATUS_KEY in ss:
        return dict(ss[STATUS_KEY])
    return dict(LAST_STATUS)


def _set_cache(db: Dict[str, Any]):
    ss = _session_state()
    if ss is not None:
        ss[CACHE_KEY] = copy.deepcopy(db)


def _get_cache():
    ss = _session_state()
    if ss is not None and CACHE_KEY in ss:
        return copy.deepcopy(ss[CACHE_KEY])
    return None


def clear_state_cache():
    ss = _session_state()
    if ss is not None and CACHE_KEY in ss:
        del ss[CACHE_KEY]


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
    return base


def _users_projection_changed(previous: Optional[Dict[str, Any]], current: Dict[str, Any]) -> bool:
    """Detect any shared User projection change before selecting the save contract."""
    if previous is None:
        return bool(current.get("users"))
    try:
        before = json.dumps(
            previous.get("users", []), sort_keys=True, separators=(",", ":"), default=str
        )
        after = json.dumps(
            current.get("users", []), sort_keys=True, separators=(",", ":"), default=str
        )
        return before != after
    except Exception:
        return previous.get("users", []) != current.get("users", [])


def _workflow_projection_changed(previous: Optional[Dict[str, Any]], current: Dict[str, Any]) -> bool:
    """Detect canonical or shared-only Workflow projection changes."""
    if previous is None:
        return bool(current.get("workflow"))
    try:
        before = json.dumps(
            previous.get("workflow", {}), sort_keys=True, separators=(",", ":"), default=str
        )
        after = json.dumps(
            current.get("workflow", {}), sort_keys=True, separators=(",", ":"), default=str
        )
        return before != after
    except Exception:
        return previous.get("workflow", {}) != current.get("workflow", {})


def _overlay_normalized_users_workflow(db: Dict[str, Any]) -> Dict[str, Any]:
    """Overlay canonical hm_users/hm_workflow when the tables are available."""
    try:
        ok, users, workflow, msg = load_users_workflow_from_normalized()
        if ok:
            db["users"] = users
            db["workflow"] = workflow
            _set_status(normalized_users_workflow=True, normalized_last_action=msg)
        else:
            _set_status(normalized_users_workflow=False, normalized_last_action=msg)
    except Exception as exc:
        _set_status(normalized_users_workflow=False, normalized_last_action=str(exc))
    return db


def _get_secret(name: str, default: str = "") -> str:
    value = os.environ.get(name)
    if value:
        return value
    try:
        import streamlit as st

        value = st.secrets.get(name, default)
        return str(value) if value is not None else default
    except Exception:
        return default


def supabase_configured() -> bool:
    return bool(
        _get_secret("SUPABASE_URL")
        and (_get_secret("SUPABASE_SERVICE_ROLE_KEY") or _get_secret("SUPABASE_ANON_KEY"))
    )


def _supabase_client():
    from supabase import create_client

    url = _get_secret("SUPABASE_URL")
    key = _get_secret("SUPABASE_SERVICE_ROLE_KEY") or _get_secret("SUPABASE_ANON_KEY")
    return create_client(url, key)


def _load_from_supabase() -> Tuple[bool, Dict[str, Any], str]:
    try:
        client = _supabase_client()
        res = client.table("healthyme_app_state").select("data").eq("id", APP_STATE_ID).execute()
        rows = res.data or []
        if rows:
            return True, normalize_state(rows[0].get("data") or {}), ""
        initial = normalize_state(_read_initial_local_state())
        client.table("healthyme_app_state").upsert({"id": APP_STATE_ID, "data": initial}).execute()
        return True, initial, "Supabase row was missing; seeded from local/sample state."
    except Exception as exc:
        return False, {}, str(exc)


def _save_to_supabase(db: Dict[str, Any]) -> Tuple[bool, str]:
    try:
        client = _supabase_client()
        client.table("healthyme_app_state").upsert(
            {"id": APP_STATE_ID, "data": normalize_state(db)}
        ).execute()
        return True, ""
    except Exception as exc:
        return False, str(exc)


def using_supabase() -> bool:
    return _get_cached_status().get("mode") == "SUPABASE"


def load_state(force_refresh: bool = False) -> Dict[str, Any]:
    """Load app state with per-session cache."""
    if not force_refresh:
        cached = _get_cache()
        if cached is not None:
            return normalize_state(cached)

    configured = supabase_configured()
    if configured:
        ok, db, msg = _load_from_supabase()
        if ok:
            db = normalize_state(db)
            db = _overlay_normalized_users_workflow(db)
            _set_cache(db)
            _set_status(
                mode="SUPABASE",
                supabase_configured=True,
                supabase_connected=True,
                fallback_active=False,
                last_error="",
                last_action=msg or "Loaded from Supabase.",
            )
            return db

        db = normalize_state(_read_initial_local_state())
        db = _overlay_normalized_users_workflow(db)
        _set_cache(db)
        _set_status(
            mode="LOCAL_FALLBACK",
            supabase_configured=True,
            supabase_connected=False,
            fallback_active=True,
            last_error=msg,
            last_action="Supabase failed; loaded local fallback.",
        )
        return db

    db = normalize_state(_read_initial_local_state())
    _set_cache(db)
    _set_status(
        mode="LOCAL_FALLBACK",
        supabase_configured=False,
        supabase_connected=False,
        fallback_active=True,
        last_error="Supabase secrets are not configured.",
        last_action="Loaded local fallback.",
    )
    return db


def save_state(db: Dict[str, Any]) -> None:
    """Save state with fail-closed canonical User and Workflow writes after Gate 4.

    Whenever either identity projection changes, changed Users, changed Workflow
    rows and the full compatibility state commit through one database transaction.
    Non-identity saves retain the existing lightweight app-state path.
    """
    db = ensure_workflow_projection(normalize_state(db))
    configured = supabase_configured()
    previous = _get_cache()
    users_changed = _users_projection_changed(previous, db)
    workflow_changed = _workflow_projection_changed(previous, db)
    identity_changed = users_changed or workflow_changed

    if identity_changed and not configured:
        message = "Canonical User/Workflow storage is unavailable; identity changes were not saved."
        _set_status(
            mode="LOCAL_FALLBACK",
            supabase_configured=False,
            supabase_connected=False,
            fallback_active=True,
            last_error=message,
            last_action="Canonical identity write rejected; local User/Workflow fallback is disabled.",
            canonical_user_write=False if users_changed else None,
            canonical_workflow_write=False if workflow_changed else None,
        )
        raise RuntimeError(message)

    if configured:
        state_saved = False
        identity_commit_message = "No User or Workflow projection change detected."
        if identity_changed:
            identity_ok, committed, identity_commit_message, _ = commit_identity_and_state(
                db,
                state_id=APP_STATE_ID,
                source="streamlit_save_state_gate4",
                force_state_commit=True,
            )
            if not identity_ok or not committed:
                _set_status(
                    mode="SUPABASE",
                    supabase_configured=True,
                    supabase_connected=True,
                    fallback_active=False,
                    last_error=identity_commit_message,
                    last_action="Canonical identity write rejected; state was not saved.",
                    canonical_user_write=False if users_changed else None,
                    canonical_workflow_write=False if workflow_changed else None,
                )
                raise RuntimeError(identity_commit_message)
            state_saved = True

        if state_saved:
            ok, msg = True, ""
        else:
            ok, msg = _save_to_supabase(db)

        if ok:
            _set_cache(db)
            _set_status(
                mode="SUPABASE",
                supabase_configured=True,
                supabase_connected=True,
                fallback_active=False,
                last_error="",
                last_action="Saved to Supabase.",
                canonical_user_write=True if users_changed else None,
                canonical_workflow_write=True if workflow_changed else None,
                canonical_identity_last_action=identity_commit_message,
                normalized_users_workflow=True,
                normalized_last_action=identity_commit_message,
            )
            return

        _set_status(
            mode="LOCAL_FALLBACK",
            supabase_configured=True,
            supabase_connected=False,
            fallback_active=True,
            last_error=msg,
            last_action="Supabase save failed; saved local fallback.",
        )

    # Local fallback remains available only when neither identity projection changed.
    LOCAL_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOCAL_DB_PATH.write_text(json.dumps(db, indent=2), encoding="utf-8")
    _set_cache(db)


def get_storage_status(force_check: bool = False) -> Dict[str, Any]:
    """Return storage status without an active call unless force_check=True."""
    configured = supabase_configured()

    if not force_check:
        status = _get_cached_status()
        status["supabase_configured"] = configured
        if status.get("mode") in ["SUPABASE", "LOCAL_FALLBACK"]:
            return status
        return {
            **status,
            "mode": "LOCAL_FALLBACK" if not configured else "UNKNOWN",
            "supabase_configured": configured,
            "fallback_active": not configured,
            "last_error": "" if configured else "Supabase secrets are not configured.",
        }

    if not configured:
        status = {
            "mode": "LOCAL_FALLBACK",
            "supabase_configured": False,
            "supabase_connected": False,
            "fallback_active": True,
            "last_error": "Supabase secrets are not configured.",
            "last_action": "Forced health check: local fallback.",
        }
        _set_status(**status)
        return status

    ok, db, msg = _load_from_supabase()
    if ok:
        status = {
            "mode": "SUPABASE",
            "supabase_configured": True,
            "supabase_connected": True,
            "fallback_active": False,
            "last_error": "",
            "last_action": msg or "Supabase forced health check passed.",
            "users_count": len(db.get("users", [])),
            "members_count": len(
                [u for u in db.get("users", []) if u.get("role") == "member"]
            ),
            "normalized_users_workflow": _get_cached_status().get(
                "normalized_users_workflow", False
            ),
            "normalized_last_action": _get_cached_status().get(
                "normalized_last_action", ""
            ),
        }
        _set_cache(db)
        _set_status(**status)
        return status

    status = {
        "mode": "LOCAL_FALLBACK",
        "supabase_configured": True,
        "supabase_connected": False,
        "fallback_active": True,
        "last_error": msg,
        "last_action": "Supabase forced health check failed.",
        "users_count": 0,
        "members_count": 0,
    }
    _set_status(**status)
    return status


def export_current_state_bytes() -> bytes:
    state = load_state()
    return json.dumps(state, indent=2).encode("utf-8")


def push_local_data_to_supabase() -> Tuple[bool, str]:
    """Push local non-identity state without replacing canonical identity data."""
    if not supabase_configured():
        return False, "Supabase secrets are not configured."
    local_state = normalize_state(_read_initial_local_state())
    normalized_ok, canonical_users, canonical_workflow, normalized_msg = (
        load_users_workflow_from_normalized()
    )
    if not normalized_ok:
        return False, f"Local push blocked because canonical identity data could not be loaded: {normalized_msg}"
    local_state["users"] = canonical_users
    local_state["workflow"] = canonical_workflow
    local_state = ensure_workflow_projection(local_state)
    ok, msg = _save_to_supabase(local_state)
    if ok:
        _set_cache(local_state)
        _set_status(
            mode="SUPABASE",
            supabase_configured=True,
            supabase_connected=True,
            fallback_active=False,
            last_error="",
            last_action="Local non-identity data pushed to Supabase with canonical Users and Workflow preserved.",
        )
        return (
            True,
            "Local non-identity data pushed to Supabase; canonical Users and Workflow were preserved.",
        )
    _set_status(
        mode="LOCAL_FALLBACK",
        supabase_configured=True,
        supabase_connected=False,
        fallback_active=True,
        last_error=msg,
        last_action="Push local to Supabase failed.",
    )
    return False, msg


def pull_supabase_to_local_backup() -> Tuple[bool, str]:
    if not supabase_configured():
        return False, "Supabase secrets are not configured."
    ok, db, msg = _load_from_supabase()
    if not ok:
        return False, msg
    backup_path = BASE_DIR / "data" / "supabase_backup.json"
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    backup_path.write_text(json.dumps(normalize_state(db), indent=2), encoding="utf-8")
    return True, f"Supabase backup saved to {backup_path.name}."
