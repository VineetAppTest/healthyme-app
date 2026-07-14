from __future__ import annotations

import datetime as dt
import os
from typing import Any, Dict, List

import streamlit as st

from components.member_recommendation_display import (
    build_member_recommendation_contract,
    load_active_recommendation_profile,
)

LOG_TABLE = "hm_member_exercise_logs"
SECRET_SECTIONS = ("auth", "auth0", "authentication", "healthyme", "supabase")


def _clean(value: object, default: str = "") -> str:
    return default if value is None else str(value).strip()


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
            value = section_values.get(name) or section_values.get(lower_name)
            if value is not None:
                return _clean(value, default)
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


def _rows(response) -> List[dict]:
    return list(getattr(response, "data", None) or [])


def load_member_exercise_contract(member_id: str, email: str = "") -> Dict[str, Any]:
    ok, profile, items, message = load_active_recommendation_profile(member_id, email)
    if not ok or not profile:
        return {"ok": ok, "message": message, "profile": {}, "today_day": 1, "exercises": []}
    contract = build_member_recommendation_contract(profile, items)
    today_day = int(contract.get("today_day") or 1)
    day = next((row for row in contract.get("days", []) if int(row.get("day_number") or 0) == today_day), {})
    exercises = [item for item in day.get("items", []) if item.get("type") == "exercise"]
    return {
        "ok": True,
        "message": message,
        "profile": contract.get("profile", {}),
        "today_day": today_day,
        "day_label": day.get("day_label", f"Day {today_day}"),
        "exercises": exercises,
    }


def list_member_exercise_logs(member_id: str, log_date: str) -> List[dict]:
    try:
        response = (
            _client()
            .table(LOG_TABLE)
            .select("*")
            .eq("member_id", member_id)
            .eq("log_date", log_date)
            .order("item_order")
            .execute()
        )
        return _rows(response)
    except Exception:
        return []


def save_member_exercise_log(payload: Dict[str, Any]) -> None:
    required = ("member_id", "log_date", "profile_id", "day_number", "exercise_name", "item_order")
    missing = [field for field in required if not _clean(payload.get(field)) and payload.get(field) != 0]
    if missing:
        raise ValueError(f"Missing exercise log fields: {', '.join(missing)}")
    row = dict(payload)
    row["updated_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
    (
        _client()
        .table(LOG_TABLE)
        .upsert(
            row,
            on_conflict="member_id,log_date,profile_id,day_number,item_order",
        )
        .execute()
    )


def exercise_log_map(member_id: str, log_date: str) -> Dict[int, dict]:
    return {int(row.get("item_order") or 0): row for row in list_member_exercise_logs(member_id, log_date)}
