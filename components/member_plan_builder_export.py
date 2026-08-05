from __future__ import annotations

import io
from typing import Any, Dict, List, Tuple

import pandas as pd
import streamlit as st

from components.pbm_core import clean
from components.recommendation_profile_store import (
    EVENT_TABLE,
    PROFILE_TABLE,
    _client,
    _rows,
)
from components.recommendation_profile_viewer import (
    load_profile_detail_readonly,
    render_view_profiles,
)


def meal_review_rows(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    output: List[Dict[str, Any]] = []
    for row in items or []:
        if clean(row.get("item_type")).lower() != "meal":
            continue
        output.append(
            {
                "Day": int(row.get("day_number") or 0),
                "Meal Slot": clean(row.get("slot_name")),
                "Recipe": clean(row.get("reference_label")),
                "Portion Guidance": clean(row.get("portion")),
                "Instruction": clean(row.get("instruction")),
                "Order": int(row.get("item_order") or 1),
            }
        )
    return sorted(
        output,
        key=lambda row: (row["Day"], row["Meal Slot"], row["Order"]),
    )


@st.cache_data(ttl=60, show_spinner=False)
def load_member_plan_events(member_id: str) -> Tuple[bool, List[Dict[str, Any]], str]:
    clean_member_id = clean(member_id)
    if not clean_member_id:
        return False, [], "Select a member to view the plan history."
    try:
        client = _client()
        profile_result = (
            client.table(PROFILE_TABLE)
            .select("id,profile_name,status,start_date,updated_at")
            .eq("assigned_member_id", clean_member_id)
            .order("updated_at", desc=True)
            .limit(200)
            .execute()
        )
        profiles = _rows(profile_result)
        profile_ids = [clean(row.get("id")) for row in profiles if clean(row.get("id"))]
        if not profile_ids:
            return True, [], "No plan history exists for this member."
        profile_map = {
            clean(row.get("id")): {
                "Plan": clean(row.get("profile_name")) or "Untitled",
                "Current Status": clean(row.get("status")).title(),
                "Plan Start": clean(row.get("start_date")),
            }
            for row in profiles
        }
        event_result = (
            client.table(EVENT_TABLE)
            .select(
                "profile_id,event_type,event_note,created_by_user_id,"
                "created_by_email,created_at"
            )
            .in_("profile_id", profile_ids)
            .order("created_at", desc=True)
            .limit(1000)
            .execute()
        )
        events: List[Dict[str, Any]] = []
        for row in _rows(event_result):
            profile_info = profile_map.get(clean(row.get("profile_id")), {})
            events.append(
                {
                    "Changed At": clean(row.get("created_at"))[:19],
                    "Plan": profile_info.get("Plan", "Untitled"),
                    "Plan Status": profile_info.get("Current Status", ""),
                    "Plan Start": profile_info.get("Plan Start", ""),
                    "Action": clean(row.get("event_type")).replace("_", " ").title(),
                    "Change Detail": clean(row.get("event_note")),
                    "Changed By": clean(row.get("created_by_email"))
                    or clean(row.get("created_by_user_id"))
                    or "System",
                    "Profile ID": clean(row.get("profile_id")),
                }
            )
        return True, events, f"Loaded {len(events)} plan change event(s)."
    except Exception as exc:
        return False, [], f"Could not load plan change history: {exc}"


@st.cache_data(ttl=60, show_spinner=False)
def load_profile_plan_events(profile_id: str) -> Tuple[bool, List[Dict[str, Any]], str]:
    clean_profile_id = clean(profile_id)
    if not clean_profile_id:
        return False, [], "Select a profile to view its change history."
    try:
        client = _client()
        profile_result = (
            client.table(PROFILE_TABLE)
            .select("id,profile_name,status,start_date,updated_at")
            .eq("id", clean_profile_id)
            .limit(1)
            .execute()
        )
        profiles = _rows(profile_result)
        if not profiles:
            return True, [], "No plan history exists for this profile."
        profile = profiles[0]
        event_result = (
            client.table(EVENT_TABLE)
            .select(
                "profile_id,event_type,event_note,created_by_user_id,"
                "created_by_email,created_at"
            )
            .eq("profile_id", clean_profile_id)
            .order("created_at", desc=True)
            .limit(1000)
            .execute()
        )
        events = [
            {
                "Changed At": clean(row.get("created_at"))[:19],
                "Plan": clean(profile.get("profile_name")) or "Untitled",
                "Plan Status": clean(profile.get("status")).title(),
                "Plan Start": clean(profile.get("start_date")),
                "Action": clean(row.get("event_type")).replace("_", " ").title(),
                "Change Detail": clean(row.get("event_note")),
                "Changed By": clean(row.get("created_by_email"))
                or clean(row.get("created_by_user_id"))
                or "System",
                "Profile ID": clean(row.get("profile_id")),
            }
            for row in _rows(event_result)
        ]
        return True, events, f"Loaded {len(events)} profile change event(s)."
    except Exception as exc:
        return False, [], f"Could not load profile change history: {exc}"


def build_member_plan_workbook(
    profile: Dict[str, Any],
    items: List[Dict[str, Any]],
    events: List[Dict[str, Any]],
) -> bytes:
    summary = [
        {"Field": "Plan Name", "Value": clean(profile.get("profile_name"))},
        {"Field": "Profile ID", "Value": clean(profile.get("id"))},
        {"Field": "Status", "Value": clean(profile.get("status")).title()},
        {
            "Field": "Member",
            "Value": clean(profile.get("assigned_member_label")) or "Unallocated",
        },
        {"Field": "Member ID", "Value": clean(profile.get("assigned_member_id"))},
        {"Field": "Plan Start Date", "Value": clean(profile.get("start_date"))},
        {"Field": "Region / Food Culture", "Value": clean(profile.get("region"))},
        {"Field": "Diet Type", "Value": clean(profile.get("diet_type"))},
        {
            "Field": "Health Concerns",
            "Value": ", ".join(profile.get("health_concerns") or []),
        },
        {"Field": "Nutritionist Note", "Value": clean(profile.get("profile_note"))},
        {"Field": "Change Note", "Value": clean(profile.get("change_note"))},
    ]
    meals = meal_review_rows(items)
    non_meal_history = [
        {
            "Type": clean(row.get("item_type")).title(),
            "Day": int(row.get("day_number") or 0),
            "Slot / Timing": clean(row.get("slot_name"))
            or clean(row.get("scheduled_time")),
            "Item": clean(row.get("reference_label")),
            "Dose / Portion": clean(row.get("dosage_frequency"))
            or clean(row.get("portion")),
            "Instruction": clean(row.get("instruction")),
        }
        for row in items or []
        if clean(row.get("item_type")).lower() in {"exercise", "supplement"}
    ]

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        pd.DataFrame(summary).to_excel(writer, sheet_name="Plan Summary", index=False)
        pd.DataFrame(meals).to_excel(writer, sheet_name="Seven Day Meals", index=False)
        pd.DataFrame(events).to_excel(writer, sheet_name="Change Log", index=False)
        if non_meal_history:
            pd.DataFrame(non_meal_history).to_excel(
                writer,
                sheet_name="Legacy Profile Rows",
                index=False,
            )
        for sheet in writer.book.worksheets:
            sheet.freeze_panes = "A2"
            for column_cells in sheet.columns:
                values = [str(cell.value or "") for cell in column_cells]
                width = min(55, max(12, max(len(value) for value in values) + 2))
                sheet.column_dimensions[column_cells[0].column_letter].width = width
    buffer.seek(0)
    return buffer.getvalue()


def render_publish_log_and_download(
    profile: Dict[str, Any],
    items: List[Dict[str, Any]],
) -> None:
    profile_id = clean(profile.get("id"))
    st.markdown(
        "<div class='hm-title'>Publish & Change Log</div>"
        "<div class='hm-sub'>A read-only record of what changed, when it changed and who made the change.</div>",
        unsafe_allow_html=True,
    )
    ok, events, message = load_profile_plan_events(profile_id)
    if not ok:
        st.warning(message)
        events = []
    elif events:
        st.dataframe(pd.DataFrame(events), use_container_width=True, hide_index=True)
    else:
        st.info(message)

    workbook = build_member_plan_workbook(profile, items, events)
    filename = (
        f"{clean(profile.get('profile_name')) or 'member_plan'}_"
        f"{clean(profile.get('assigned_member_label')) or 'unallocated'}_history.xlsx"
    ).replace(" ", "_")
    st.download_button(
        "Download Detailed Plan & Change Log",
        data=workbook,
        file_name=filename,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
        key=f"mpb_publish_download_{clean(profile.get('id')) or 'new'}",
    )


def render_view_member_plan() -> None:
    render_view_profiles()
    selected_id = clean(st.session_state.get("view_profiles_profile_id"))
    if not selected_id:
        return
    ok, profile, items, message = load_profile_detail_readonly(selected_id)
    if not ok:
        st.warning(message)
        return
    events_ok, events, _ = load_profile_plan_events(
        clean(profile.get("id"))
    )
    workbook = build_member_plan_workbook(
        profile,
        items,
        events if events_ok else [],
    )
    filename = (
        f"{clean(profile.get('profile_name')) or 'member_plan'}_details.xlsx"
    ).replace(" ", "_")
    st.download_button(
        "Download Selected Member Plan",
        data=workbook,
        file_name=filename,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
        key=f"mpb_view_download_{selected_id}",
    )
