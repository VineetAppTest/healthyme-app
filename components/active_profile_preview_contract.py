import datetime as dt
import os
import re
from typing import Any, Dict, List, Tuple

import pandas as pd
import streamlit as st

from components.recommendation_profile_store import load_member_options

PROFILE_TABLE = "hm_recommendation_profiles"
ITEM_TABLE = "hm_recommendation_profile_items"
SECRET_SECTIONS = ("auth", "auth0", "authentication", "healthyme", "supabase")
SUPPLEMENT_TIMELINE = [
    "Before Breakfast",
    "After Breakfast",
    "Before Lunch",
    "After Lunch",
    "Before Dinner",
    "After Dinner",
    "Before Bed",
]


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


def _rows(response) -> List[dict]:
    return list(getattr(response, "data", None) or [])


def parse_dosage_frequency(value: object) -> Tuple[int, str]:
    raw = _clean(value)
    if not raw:
        return 0, ""
    match = re.match(r"^Frequency:\s*(\d+)\s*;\s*Dosage:\s*(.*)$", raw)
    if match:
        return int(match.group(1) or 0), _clean(match.group(2))
    return 0, raw


def parse_timeline(value: object) -> List[str]:
    raw = _clean(value)
    if not raw:
        return []
    return [part.strip() for part in raw.split(",") if part.strip()]


def date_label(start_date: object, day: int) -> str:
    try:
        start = dt.date.fromisoformat(str(start_date or "")[:10])
    except Exception:
        start = dt.date.today()
    return f"Day {day} · {(start + dt.timedelta(days=day - 1)).strftime('%a, %d %b')}"


@st.cache_data(ttl=90, show_spinner=False)
def load_members_for_preview() -> Tuple[bool, List[dict], str]:
    try:
        rows, message = load_member_options()
        return True, list(rows or []), message
    except Exception as exc:
        return False, [], f"Could not load members: {exc}"


@st.cache_data(ttl=90, show_spinner=False)
def load_active_profile_for_member(member_id: str) -> Tuple[bool, Dict[str, Any], List[dict], str]:
    clean_member_id = _clean(member_id)
    if not clean_member_id:
        return False, {}, [], "Select a member first."
    try:
        c = _client()
        profile_result = (
            c.table(PROFILE_TABLE)
            .select("*")
            .eq("assigned_member_id", clean_member_id)
            .eq("status", "active")
            .order("updated_at", desc=True)
            .limit(1)
            .execute()
        )
        profiles = _rows(profile_result)
        if not profiles:
            return True, {}, [], "No active recommendation profile found for this member."
        profile = profiles[0]
        item_result = (
            c.table(ITEM_TABLE)
            .select("item_type,day_number,slot_name,item_order,reference_label,portion,instruction,scheduled_time,intensity,dosage_frequency")
            .eq("profile_id", profile.get("id"))
            .order("day_number")
            .order("item_type")
            .order("item_order")
            .execute()
        )
        return True, profile, _rows(item_result), "Loaded active profile preview contract."
    except Exception as exc:
        return False, {}, [], f"Could not load active profile preview: {exc}"


def clear_active_preview_cache() -> None:
    load_members_for_preview.clear()
    load_active_profile_for_member.clear()


def row_has_content(row: dict) -> bool:
    return any(_clean(row.get(field)) for field in ("reference_label", "portion", "instruction", "scheduled_time", "intensity", "dosage_frequency"))


def contract_summary(profile: dict, items: List[dict]) -> Dict[str, Any]:
    active_items = [row for row in items if row_has_content(row)]
    counts = {
        "meal": len([row for row in active_items if row.get("item_type") == "meal"]),
        "exercise": len([row for row in active_items if row.get("item_type") == "exercise"]),
        "supplement": len([row for row in active_items if row.get("item_type") == "supplement"]),
        "total": len(active_items),
    }
    issues = []
    guidance = []
    if not profile:
        issues.append("No active recommendation profile found for this member.")
    if profile and _clean(profile.get("status")).lower() != "active":
        issues.append("Selected profile is not active.")
    if profile and not _clean(profile.get("assigned_member_id")):
        issues.append("Active profile has no assigned member id.")
    if profile and not active_items:
        issues.append("Active profile has no recommendation rows.")
    if profile and counts["meal"] == 0:
        guidance.append("No meal rows found in active profile.")
    if profile and counts["exercise"] == 0:
        guidance.append("No exercise rows found in active profile.")
    if profile and counts["supplement"] == 0:
        guidance.append("No supplement rows found in active profile.")
    day_numbers = {int(row.get("day_number") or 0) for row in active_items if int(row.get("day_number") or 0) in range(1, 8)}
    missing_days = [day for day in range(1, 8) if day not in day_numbers]
    if profile and missing_days:
        guidance.append(f"No rows found for Day(s): {', '.join(str(day) for day in missing_days)}.")
    for row in active_items:
        if row.get("item_type") == "supplement":
            frequency, _ = parse_dosage_frequency(row.get("dosage_frequency"))
            timeline_count = len(parse_timeline(row.get("scheduled_time")))
            if frequency and timeline_count != frequency:
                guidance.append(
                    f"Supplement validation: Day {row.get('day_number')} has frequency {frequency} but {timeline_count} timeline selection(s)."
                )
    return {"items": active_items, "counts": counts, "issues": issues, "guidance": guidance}


def display_rows_for_day(items: List[dict], day: int) -> List[dict]:
    rows = []
    for row in items:
        if int(row.get("day_number") or 0) != day:
            continue
        item_type = row.get("item_type")
        if item_type == "meal":
            rows.append({
                "Type": "Meal",
                "Timing / Slot": row.get("slot_name") or "NA",
                "Item": row.get("reference_label") or "NA",
                "Portion / Dosage": row.get("portion") or "NA",
                "Intensity / Frequency": "NA",
                "Instruction": row.get("instruction") or "NA",
            })
        elif item_type == "exercise":
            rows.append({
                "Type": "Exercise",
                "Timing / Slot": row.get("scheduled_time") or row.get("slot_name") or "NA",
                "Item": row.get("reference_label") or "NA",
                "Portion / Dosage": "NA",
                "Intensity / Frequency": row.get("intensity") or "NA",
                "Instruction": row.get("instruction") or "NA",
            })
        elif item_type == "supplement":
            frequency, dosage = parse_dosage_frequency(row.get("dosage_frequency"))
            rows.append({
                "Type": "Supplement",
                "Timing / Slot": row.get("scheduled_time") or row.get("slot_name") or "NA",
                "Item": row.get("reference_label") or "NA",
                "Portion / Dosage": dosage or "NA",
                "Intensity / Frequency": frequency or "NA",
                "Instruction": row.get("instruction") or "NA",
            })
    return rows


def render_profile_summary(profile: dict, summary: dict) -> None:
    counts = summary["counts"]
    status_class = "hm-error" if summary["issues"] else ("hm-pending" if summary["guidance"] else "hm-ok")
    status_label = "Contract issue" if summary["issues"] else ("Preview guidance" if summary["guidance"] else "Ready for member consumption review")
    st.markdown(f"""
<div class='hm-preview'>
<b>Active Profile Summary</b><br>
<span class='hm-pill {status_class}'>{status_label}</span><br>
<b>Profile:</b> {profile.get('profile_name') or 'NA'}<br>
<b>Member:</b> {profile.get('assigned_member_label') or 'NA'}<br>
<b>Status:</b> {profile.get('status') or 'NA'}<br>
<b>Start Date:</b> {profile.get('start_date') or 'NA'}<br>
<b>Tags:</b> {profile.get('region') or 'NA'} · {profile.get('age_band') or 'NA'} · {profile.get('diet_type') or 'NA'}<br>
<b>Profile Note:</b> {profile.get('profile_note') or 'NA'}
</div>
""", unsafe_allow_html=True)
    st.markdown(f"""
<div class='hm-count-grid'>
  <div class='hm-count-card'><b>{counts['meal']}</b><span>Meal rows</span></div>
  <div class='hm-count-card'><b>{counts['exercise']}</b><span>Exercise rows</span></div>
  <div class='hm-count-card'><b>{counts['supplement']}</b><span>Supplement rows</span></div>
  <div class='hm-count-card'><b>{counts['total']}</b><span>Total rows</span></div>
</div>
""", unsafe_allow_html=True)


def render_active_profile_preview_contract() -> None:
    st.markdown(
        "<div class='hm-title'>Active Profile Member Preview Contract</div>"
        "<div class='hm-sub'>Admin-only preview of the active profile exactly as the member-facing layer should consume it. No Flutter/member display is changed in this sprint.</div>",
        unsafe_allow_html=True,
    )
    ok_members, members, member_message = load_members_for_preview()
    if not ok_members:
        st.error(member_message)
        return
    if not members:
        st.warning("No active members found. Create/activate a member first.")
        return

    if st.button("Refresh Active Profile Preview", use_container_width=True):
        clear_active_preview_cache()
        st.rerun()

    member_label_to_id = {row.get("label"): row.get("id") for row in members if row.get("label") and row.get("id")}
    selected_label = st.selectbox("Select member", list(member_label_to_id.keys()), key="active_profile_preview_member")
    member_id = member_label_to_id.get(selected_label, "")
    ok_profile, profile, items, message = load_active_profile_for_member(member_id)
    st.caption(f"Member source: {member_message}. Preview source: {message}")
    if not ok_profile:
        st.error(message)
        return
    if not profile:
        st.info("No active recommendation profile found for this member. Publish/Activate a draft profile first.")
        return

    summary = contract_summary(profile, items)
    render_profile_summary(profile, summary)
    for issue in summary["issues"]:
        st.error(issue)
    for guidance in summary["guidance"][:10]:
        st.warning(guidance)

    st.markdown("<div class='hm-title'>Day-wise Member Preview</div>", unsafe_allow_html=True)
    day_tabs = st.tabs([f"Day {day}" for day in range(1, 8)])
    for day, tab in zip(range(1, 8), day_tabs):
        with tab:
            st.markdown(f"<div class='hm-slot'>{date_label(profile.get('start_date'), day)}</div>", unsafe_allow_html=True)
            rows = display_rows_for_day(summary["items"], day)
            if rows:
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
            else:
                st.info("No recommendation rows found for this day.")

    with st.expander("Raw active profile contract payload", expanded=False):
        st.json({"profile": profile, "items": summary["items"]})
