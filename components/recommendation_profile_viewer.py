from __future__ import annotations

import html
from typing import Any, Dict, List, Tuple

import streamlit as st

from components.profile_publish_control import (
    _review_rows,
    _safe_table,
    clear_publish_cache,
    load_profile_detail,
)
from components.recommendation_profile_store import (
    PROFILE_TABLE,
    _client,
    _rows,
    check_profile_builder_store,
)


PROFILE_STATUSES = ("draft", "active", "replaced", "archived")
STATUS_LABELS = {
    "draft": "Draft",
    "active": "Active",
    "replaced": "Replaced",
    "archived": "Archived",
}


def _clean(value: object, default: str = "") -> str:
    if value is None:
        return default
    return str(value).strip()


def _safe(value: object, default: str = "NA") -> str:
    text = _clean(value)
    return html.escape(text if text else default, quote=True)


@st.cache_data(ttl=60, show_spinner=False)
def load_profile_inventory(limit: int = 250) -> Tuple[bool, List[dict], str]:
    """Load the read-only recommendation-profile inventory.

    The viewer deliberately performs no insert, update, delete, upsert, allocation,
    activation or archive operation.
    """
    status = check_profile_builder_store()
    if not status.get("ok"):
        return False, [], status.get("message", "Profile Builder tables are not ready.")
    try:
        result = (
            _client()
            .table(PROFILE_TABLE)
            .select(
                "id,profile_name,status,assigned_member_id,assigned_member_label,"
                "start_date,region,age_band,diet_type,health_concerns,profile_note,"
                "change_note,cycle_rule,clone_source_label,created_by_email,updated_at"
            )
            .order("updated_at", desc=True)
            .limit(limit)
            .execute()
        )
        return True, _rows(result), "Loaded recommendation profile inventory."
    except Exception as exc:
        return False, [], f"Could not load recommendation profiles: {exc}"


def clear_profile_view_cache() -> None:
    load_profile_inventory.clear()
    clear_publish_cache()


def render_profile_lifecycle_guide() -> None:
    st.markdown(
        """
<style id="hm-profile-lifecycle-guide-v1">
.hm-profile-lifecycle{border:1px solid #E3C98E;background:linear-gradient(135deg,#FFFDF8,#FFF7E7);border-radius:17px;padding:.78rem .86rem;margin:.40rem 0 .86rem;box-shadow:0 8px 20px rgba(15,23,42,.045)}
.hm-profile-lifecycle-title{color:#064E3B;font-size:.92rem;font-weight:950;margin:0 0 .50rem}
.hm-profile-lifecycle-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:.55rem}
.hm-profile-life-card{border:1px solid rgba(216,168,78,.55);background:#fff;border-radius:13px;padding:.58rem .62rem;color:#475569;font-size:.76rem;line-height:1.38;font-weight:680}
.hm-profile-life-card b{display:block;color:#064E3B;font-size:.82rem;font-weight:950;margin-bottom:.18rem}
.hm-profile-life-card strong{color:#7A4F00}
@media(max-width:900px){.hm-profile-lifecycle-grid{grid-template-columns:1fr 1fr}}
@media(max-width:560px){.hm-profile-lifecycle-grid{grid-template-columns:1fr}}
</style>
<div class="hm-profile-lifecycle">
  <div class="hm-profile-lifecycle-title">Recommendation Profile lifecycle</div>
  <div class="hm-profile-lifecycle-grid">
    <div class="hm-profile-life-card"><b>Preview</b>Reviews the profile currently loaded in the Builder. It may include unsaved on-screen edits. Preview does not save or change profile status.</div>
    <div class="hm-profile-life-card"><b>Publish</b>Admin/Super Admin activates a <strong>saved Draft</strong> that has a member and recommendation rows. The member's previous Active profile becomes Replaced.</div>
    <div class="hm-profile-life-card"><b>Active</b>Read-only check of the member's current live consumption contract. Existing Builder module saves to an Active Profile ID update that live profile in place.</div>
    <div class="hm-profile-life-card"><b>View Profiles</b>Read-only inventory of Draft, Active, Replaced and Archived profiles. Editing and activation remain inside the Builder.</div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )


def _inventory_rows(rows: List[dict]) -> List[Dict[str, Any]]:
    output: List[Dict[str, Any]] = []
    for row in rows:
        status = _clean(row.get("status"), "draft").lower()
        output.append(
            {
                "Profile": row.get("profile_name") or "Untitled",
                "Status": STATUS_LABELS.get(status, status.title() or "Unknown"),
                "Member": row.get("assigned_member_label") or "Unallocated",
                "Start Date": row.get("start_date") or "NA",
                "Updated": str(row.get("updated_at") or "")[:19] or "NA",
                "Created By": row.get("created_by_email") or "NA",
            }
        )
    return output


def _profile_label(row: dict) -> str:
    status = STATUS_LABELS.get(_clean(row.get("status")).lower(), _clean(row.get("status"), "Unknown").title())
    member = _clean(row.get("assigned_member_label"), "Unallocated")
    updated = str(row.get("updated_at") or "")[:16]
    return f"{_clean(row.get('profile_name'), 'Untitled')} · {status} · {member} · {updated}"


def render_view_profiles() -> None:
    render_profile_lifecycle_guide()

    refresh_col, builder_col = st.columns([1, 1], gap="medium")
    if refresh_col.button("Refresh Profiles", use_container_width=True):
        clear_profile_view_cache()
        st.rerun()
    if builder_col.button("Open Recommendation Profile Builder", use_container_width=True):
        st.switch_page("pages/38_Admin_Recommendation_Profile_Builder.py")

    ok, profiles, message = load_profile_inventory()
    if not ok:
        st.error(message)
        return
    st.caption(message)

    status_col, member_col, search_col = st.columns([0.25, 0.35, 0.40], gap="medium")
    status_filter = status_col.selectbox(
        "Status",
        ["All"] + [STATUS_LABELS[value] for value in PROFILE_STATUSES],
        key="view_profiles_status",
    )
    member_values = sorted(
        {
            _clean(row.get("assigned_member_label"), "Unallocated")
            for row in profiles
        }
    )
    member_filter = member_col.selectbox(
        "Member",
        ["All"] + member_values,
        key="view_profiles_member",
    )
    search_text = search_col.text_input(
        "Search profile or member",
        key="view_profiles_search",
        placeholder="Profile name or member",
    ).strip().lower()

    filtered: List[dict] = []
    for row in profiles:
        row_status = _clean(row.get("status"), "draft").lower()
        row_status_label = STATUS_LABELS.get(row_status, row_status.title())
        member_label = _clean(row.get("assigned_member_label"), "Unallocated")
        haystack = f"{row.get('profile_name', '')} {member_label}".lower()
        if status_filter != "All" and row_status_label != status_filter:
            continue
        if member_filter != "All" and member_label != member_filter:
            continue
        if search_text and search_text not in haystack:
            continue
        filtered.append(row)

    counts = {
        status: len([row for row in profiles if _clean(row.get("status")).lower() == status])
        for status in PROFILE_STATUSES
    }
    st.markdown(
        f"""
<div class="hm-count-grid">
  <div class="hm-count-card"><b>{counts['draft']}</b><span>Draft</span></div>
  <div class="hm-count-card"><b>{counts['active']}</b><span>Active</span></div>
  <div class="hm-count-card"><b>{counts['replaced']}</b><span>Replaced</span></div>
  <div class="hm-count-card"><b>{counts['archived']}</b><span>Archived</span></div>
</div>
""",
        unsafe_allow_html=True,
    )

    st.markdown("<div class='hm-title'>Profile Inventory</div>", unsafe_allow_html=True)
    _safe_table(_inventory_rows(filtered), "No profiles match the selected filters.")
    if not filtered:
        return

    by_id = {_clean(row.get("id")): row for row in filtered if _clean(row.get("id"))}
    profile_ids = list(by_id.keys())
    selected_id = st.selectbox(
        "View Profile Detail",
        profile_ids,
        format_func=lambda value: _profile_label(by_id[value]),
        key="view_profiles_detail",
    )
    detail_ok, profile, items, detail_message = load_profile_detail(selected_id)
    if not detail_ok:
        st.error(detail_message)
        return

    status = STATUS_LABELS.get(_clean(profile.get("status")).lower(), _clean(profile.get("status"), "Unknown").title())
    st.markdown(
        f"""
<div class="hm-preview">
<b>Selected Profile</b><br>
<b>Profile ID:</b> {_safe(profile.get('id'))}<br>
<b>Profile:</b> {_safe(profile.get('profile_name'))}<br>
<b>Status:</b> {_safe(status)}<br>
<b>Member:</b> {_safe(profile.get('assigned_member_label'), 'Unallocated')}<br>
<b>Start Date:</b> {_safe(profile.get('start_date'))}<br>
<b>Cycle:</b> {_safe(profile.get('cycle_rule'))}<br>
<b>Profile Note:</b> {_safe(profile.get('profile_note'))}<br>
<b>Change Note:</b> {_safe(profile.get('change_note'))}
</div>
""",
        unsafe_allow_html=True,
    )

    meal_count = len([row for row in items if row.get("item_type") == "meal"])
    exercise_count = len([row for row in items if row.get("item_type") == "exercise"])
    supplement_count = len([row for row in items if row.get("item_type") == "supplement"])
    st.markdown(
        f"""
<div class="hm-count-grid">
  <div class="hm-count-card"><b>{meal_count}</b><span>Meal rows</span></div>
  <div class="hm-count-card"><b>{exercise_count}</b><span>Exercise rows</span></div>
  <div class="hm-count-card"><b>{supplement_count}</b><span>Supplement rows</span></div>
  <div class="hm-count-card"><b>{len(items)}</b><span>Total rows</span></div>
</div>
""",
        unsafe_allow_html=True,
    )

    day = st.selectbox("Profile Day", list(range(1, 8)), key="view_profiles_day")
    day_items = [row for row in items if int(row.get("day_number") or 0) == day]
    _safe_table(_review_rows(day_items), f"No recommendation rows found for Day {day}.")
