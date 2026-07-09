"""Supabase-backed draft store for HealthyMe recommendation profiles.

Sprint 1 scope:
- backend foundation for Profile Builder drafts
- safe draft save/load helpers for Streamlit admin only
- no publish, replacement, or member-consumption logic yet
"""

from __future__ import annotations

import datetime as dt
import os
import uuid
from typing import Any, Dict, List, Tuple

import streamlit as st


PROFILE_TABLE = "hm_recommendation_profiles"
ITEM_TABLE = "hm_recommendation_profile_items"
EVENT_TABLE = "hm_recommendation_profile_events"
MASTER_TABLE = "hm_recommendation_master_options"

DEFAULT_SOURCES = {
    "age_band": ["Teen", "18-30", "31-45", "46-60", "60+"],
    "health_concern": [
        "Weight Management",
        "Gut Health",
        "Diabetes Support",
        "Energy",
        "Inflammation",
        "Sleep",
        "General Wellness",
    ],
    "diet_type": ["Vegetarian", "Non-vegetarian", "Vegan", "Eggetarian", "Jain", "Custom"],
    "recipe": ["-- Select recipe --", "Moong Chilla", "Paneer Salad", "Fruit + Nuts", "Herbal Tea"],
    "exercise": ["-- Select exercise --", "Brisk Walking", "Cat-Cow Stretch", "Breathing Exercise", "Mobility Flow"],
    "supplement": ["-- Select supplement --", "Magnesium", "Vitamin D", "Omega 3", "Probiotic"],
}

SECRET_SECTIONS = ("auth", "auth0", "authentication", "healthyme", "supabase")


def _clean(value: object, default: str = "") -> str:
    if value is None:
        return default
    return str(value).strip()


def _get_secret(name: str, default: str = "") -> str:
    value = os.environ.get(name)
    if value:
        return _clean(value, default)

    try:
        value = st.secrets.get(name)
        if value is not None:
            return _clean(value, default)

        lower_name = name.lower()
        value = st.secrets.get(lower_name)
        if value is not None:
            return _clean(value, default)

        for section in SECRET_SECTIONS:
            section_values = st.secrets.get(section)
            if not section_values:
                continue
            try:
                value = section_values.get(name)
                if value is None:
                    value = section_values.get(lower_name)
                if value is not None:
                    return _clean(value, default)
            except Exception:
                continue
    except Exception:
        pass

    return default


def _client():
    from supabase import create_client

    url = _get_secret("SUPABASE_URL")
    key = _get_secret("SUPABASE_SERVICE_ROLE_KEY") or _get_secret("SUPABASE_ANON_KEY")
    if not url or not key:
        raise RuntimeError("Supabase URL/key is not configured.")
    return create_client(url, key)


def profile_store_configured() -> bool:
    return bool(_get_secret("SUPABASE_URL") and (_get_secret("SUPABASE_SERVICE_ROLE_KEY") or _get_secret("SUPABASE_ANON_KEY")))


def _rows(response) -> List[dict]:
    return list(getattr(response, "data", None) or [])


def check_profile_builder_store() -> Dict[str, Any]:
    """Return readiness of Sprint 1 profile-builder tables."""
    if not profile_store_configured():
        return {"ok": False, "message": "Supabase secrets are not configured for this app."}

    status: Dict[str, Any] = {"ok": True, "message": "Profile Builder draft store is ready."}
    try:
        c = _client()
        for table in (PROFILE_TABLE, ITEM_TABLE, EVENT_TABLE, MASTER_TABLE):
            try:
                c.table(table).select("id", count="exact").limit(1).execute()
                status[table] = True
            except Exception as exc:
                status[table] = False
                status["ok"] = False
                status.setdefault("missing", []).append(table)
                status[f"{table}_error"] = str(exc)
        if not status["ok"]:
            missing = ", ".join(status.get("missing", []))
            status["message"] = f"Profile Builder tables are not ready yet: {missing}. Run the Sprint 1 SQL script."
        return status
    except Exception as exc:
        return {"ok": False, "message": f"Could not check Profile Builder store: {exc}"}


def load_profile_builder_sources() -> Tuple[Dict[str, List[str]], str]:
    """Load dropdown/master-data options, with safe mock fallback."""
    sources = {key: list(values) for key, values in DEFAULT_SOURCES.items()}
    if not check_profile_builder_store().get("ok"):
        return sources, "Using mock fallback values until Sprint 1 SQL tables are available."

    try:
        c = _client()
        result = (
            c.table(MASTER_TABLE)
            .select("option_group,option_value,sort_order,is_active")
            .eq("is_active", True)
            .order("option_group")
            .order("sort_order")
            .execute()
        )
        grouped: Dict[str, List[str]] = {}
        for row in _rows(result):
            group = _clean(row.get("option_group"))
            value = _clean(row.get("option_value"))
            if group and value:
                grouped.setdefault(group, []).append(value)
        for group, values in grouped.items():
            if values:
                sources[group] = values
        return sources, "Loaded dropdown values from Profile Builder master data."
    except Exception as exc:
        return sources, f"Using mock fallback values because master data could not be loaded: {exc}"


def load_member_options() -> Tuple[List[Dict[str, str]], str]:
    """Load active member assignment options from hm_users."""
    fallback = [{"id": "", "label": "Select member"}, {"id": "example-member", "label": "Example member"}]
    if not profile_store_configured():
        return fallback, "Using mock member values because Supabase is not configured."

    try:
        c = _client()
        result = (
            c.table("hm_users")
            .select("id,name,email,role,is_active")
            .eq("role", "member")
            .eq("is_active", True)
            .order("name")
            .execute()
        )
        options = [{"id": "", "label": "Select member"}]
        for row in _rows(result):
            user_id = _clean(row.get("id"))
            name = _clean(row.get("name")) or _clean(row.get("email")) or "Member"
            email = _clean(row.get("email"))
            label = f"{name} ({email})" if email else name
            options.append({"id": user_id, "label": label})
        return (options or fallback), "Loaded active members from hm_users."
    except Exception as exc:
        return fallback, f"Using mock member values because hm_users could not be loaded: {exc}"


def list_draft_profiles(limit: int = 50) -> Tuple[bool, List[dict], str]:
    if not check_profile_builder_store().get("ok"):
        return False, [], "Profile Builder tables are not ready."
    try:
        c = _client()
        result = (
            c.table(PROFILE_TABLE)
            .select("id,profile_name,status,assigned_member_label,updated_at")
            .eq("status", "draft")
            .order("updated_at", desc=True)
            .limit(limit)
            .execute()
        )
        return True, _rows(result), "Loaded draft profiles."
    except Exception as exc:
        return False, [], f"Could not load draft profiles: {exc}"


def list_profile_sources(limit: int = 50) -> Tuple[bool, List[dict], str]:
    if not check_profile_builder_store().get("ok"):
        return False, [], "Profile Builder tables are not ready."
    try:
        c = _client()
        result = (
            c.table(PROFILE_TABLE)
            .select("id,profile_name,status,updated_at")
            .in_("status", ["draft", "active", "archived"])
            .order("updated_at", desc=True)
            .limit(limit)
            .execute()
        )
        return True, _rows(result), "Loaded available clone/source profiles."
    except Exception as exc:
        return False, [], f"Could not load clone/source profiles: {exc}"


def _now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def save_draft_profile(profile: Dict[str, Any], items: List[Dict[str, Any]]) -> Tuple[bool, str, str]:
    """Upsert one draft profile and replace its draft items.

    This intentionally does not publish or activate anything.
    """
    status = check_profile_builder_store()
    if not status.get("ok"):
        return False, "", status.get("message", "Profile Builder tables are not ready.")

    profile_name = _clean(profile.get("profile_name"))
    if not profile_name:
        return False, "", "Profile Name is required before saving a draft."

    profile_id = _clean(profile.get("id")) or str(uuid.uuid4())
    now = _now_iso()
    row = {
        "id": profile_id,
        "profile_name": profile_name,
        "status": "draft",
        "region": _clean(profile.get("region")),
        "age_band": _clean(profile.get("age_band")),
        "diet_type": _clean(profile.get("diet_type")),
        "health_concerns": list(profile.get("health_concerns") or []),
        "profile_note": _clean(profile.get("profile_note")),
        "change_note": _clean(profile.get("change_note")),
        "cycle_rule": _clean(profile.get("cycle_rule"), "Weekly cyclical until replaced or stopped"),
        "assigned_member_id": _clean(profile.get("assigned_member_id")),
        "assigned_member_label": _clean(profile.get("assigned_member_label")),
        "start_date": _clean(profile.get("start_date")),
        "clone_source_profile_id": _clean(profile.get("clone_source_profile_id")),
        "clone_source_label": _clean(profile.get("clone_source_label")),
        "updated_at": now,
        "created_by_user_id": _clean(profile.get("created_by_user_id")),
        "created_by_email": _clean(profile.get("created_by_email")),
    }

    item_rows = []
    for item in items:
        item_type = _clean(item.get("item_type"))
        day_number = int(item.get("day_number") or 0)
        slot_name = _clean(item.get("slot_name"))
        reference_label = _clean(item.get("reference_label"))
        instruction = _clean(item.get("instruction"))
        if item_type not in {"meal", "exercise", "supplement"} or not (1 <= day_number <= 7) or not slot_name:
            continue
        if not any([
            reference_label,
            _clean(item.get("portion")),
            instruction,
            _clean(item.get("scheduled_time")),
            _clean(item.get("intensity")),
            _clean(item.get("dosage_frequency")),
        ]):
            continue
        item_rows.append({
            "id": str(uuid.uuid4()),
            "profile_id": profile_id,
            "item_type": item_type,
            "day_number": day_number,
            "slot_name": slot_name,
            "item_order": int(item.get("item_order") or 1),
            "reference_label": reference_label,
            "portion": _clean(item.get("portion")),
            "instruction": instruction,
            "scheduled_time": _clean(item.get("scheduled_time")),
            "intensity": _clean(item.get("intensity")),
            "dosage_frequency": _clean(item.get("dosage_frequency")),
            "updated_at": now,
        })

    try:
        c = _client()
        c.table(PROFILE_TABLE).upsert(row, on_conflict="id").execute()
        c.table(ITEM_TABLE).delete().eq("profile_id", profile_id).execute()
        if item_rows:
            c.table(ITEM_TABLE).insert(item_rows).execute()
        c.table(EVENT_TABLE).insert({
            "id": str(uuid.uuid4()),
            "profile_id": profile_id,
            "event_type": "draft_saved",
            "event_note": f"Draft saved with {len(item_rows)} item rows.",
            "created_by_user_id": row.get("created_by_user_id"),
            "created_by_email": row.get("created_by_email"),
            "created_at": now,
        }).execute()
        return True, profile_id, f"Draft saved successfully with {len(item_rows)} recommendation rows."
    except Exception as exc:
        return False, profile_id, f"Could not save draft profile: {exc}"


def load_profile(profile_id: str) -> Tuple[bool, Dict[str, Any], List[Dict[str, Any]], str]:
    clean_id = _clean(profile_id)
    if not clean_id:
        return False, {}, [], "Select a saved draft first."
    if not check_profile_builder_store().get("ok"):
        return False, {}, [], "Profile Builder tables are not ready."

    try:
        c = _client()
        profile_result = c.table(PROFILE_TABLE).select("*").eq("id", clean_id).limit(1).execute()
        profiles = _rows(profile_result)
        if not profiles:
            return False, {}, [], "Selected profile was not found."
        items_result = (
            c.table(ITEM_TABLE)
            .select("*")
            .eq("profile_id", clean_id)
            .order("item_type")
            .order("day_number")
            .order("slot_name")
            .order("item_order")
            .execute()
        )
        return True, profiles[0], _rows(items_result), "Loaded draft profile."
    except Exception as exc:
        return False, {}, [], f"Could not load selected draft: {exc}"
