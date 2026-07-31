import streamlit as st

from components.db import (
    clear_body_mind_activation,
    get_admin_assessment,
    get_workflow,
    has_explicit_body_mind_access,
    list_members,
    load_db,
    manually_unlock_body_mind_after_finalization,
    sync_member_finalization_state,
)
from components.flash import render_system_message, set_system_message
from components.guards import require_admin
from components.ui_common import (
    apply_luxe_theme,
    card_end,
    card_start,
    compact_topbar,
    inject_global_styles,
    render_back_to_top,
    render_page_nav,
    stat_grid,
    utility_logout_bar,
)


SELECTED_MEMBER_KEY = "hm_body_mind_access_member_id"
DISABLE_VERSION_PREFIX = "hm_body_mind_disable_version_"


def _member_label(member: dict) -> str:
    return (
        f"{member.get('id', '')} — {member.get('name', '')} — "
        f"{member.get('email', '')}"
    )


def _disable_version(member_id: str) -> int:
    key = f"{DISABLE_VERSION_PREFIX}{member_id}"
    return max(int(st.session_state.get(key, 1) or 1), 1)


def _advance_disable_version(member_id: str) -> None:
    key = f"{DISABLE_VERSION_PREFIX}{member_id}"
    st.session_state[key] = _disable_version(member_id) + 1


st.set_page_config(
    page_title="Body-Mind Access Control",
    page_icon="💚",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_global_styles()
apply_luxe_theme()
require_admin()
utility_logout_bar()
compact_topbar(
    "Body-Mind Access Control",
    "Manually activate Body-Mind after final admin completion, or explicitly disable access if required.",
    "Admin control",
)
render_system_message()

members = list_members()
if not members:
    st.info("No members available.")
    st.stop()

member_map = {
    str(member.get("id", "")): member
    for member in members
    if member.get("id")
}
member_ids = list(member_map.keys())
if st.session_state.get(SELECTED_MEMBER_KEY) not in member_ids:
    st.session_state[SELECTED_MEMBER_KEY] = member_ids[0]

member_id = st.selectbox(
    "Select member",
    member_ids,
    format_func=lambda value: _member_label(member_map[value]),
    key=SELECTED_MEMBER_KEY,
)
member = member_map[member_id]
workflow = get_workflow(member_id)
explicit_body_mind_access = has_explicit_body_mind_access(member_id)
if explicit_body_mind_access:
    workflow["body_mind_unlocked"] = True

# Repair stale review/instance status for finalized records without auto-unlocking Body-Mind.
if (
    workflow.get("admin_completed")
    or workflow.get("final_report_ready")
    or workflow.get("workflow_status") == "finalized"
):
    workflow = sync_member_finalization_state(member_id, body_mind_unlock=None)

explicit_body_mind_access = has_explicit_body_mind_access(member_id)
if explicit_body_mind_access:
    workflow["body_mind_unlocked"] = True

database = load_db()
body_response = database.get("body_mind_responses", {}).get(member_id, {})
admin_assessment = get_admin_assessment(member_id)

admin_assessment_saved = bool(admin_assessment) or bool(workflow.get("admin_completed"))
admin_final_completed = bool(workflow.get("admin_completed")) or bool(
    workflow.get("final_report_ready")
)

card_start()
st.subheader(member["name"])
st.caption(member["email"])
stat_grid(
    [
        {
            "label": "Visibility",
            "value": "Visible"
            if (workflow.get("body_mind_unlocked") or explicit_body_mind_access)
            else "Hidden",
            "note": "Member access",
        },
        {
            "label": "Activation",
            "value": "Activated"
            if (workflow.get("body_mind_unlocked") or explicit_body_mind_access)
            else (
                "Requested"
                if workflow.get("body_mind_activation_requested")
                else "Not requested"
            ),
            "note": "Admin selection",
        },
        {
            "label": "Admin Assessment",
            "value": "Saved" if admin_assessment_saved else "Not saved",
            "note": "Unlock prerequisite",
        },
        {
            "label": "Body-Mind",
            "value": "Completed"
            if workflow.get("body_mind_completed")
            else "Not completed",
            "note": "Member progress",
        },
        {
            "label": "Responses",
            "value": "Available" if body_response else "No responses",
            "note": "Stored data",
        },
    ]
)
card_end()

card_start()
st.subheader("Set visibility")

body_mind_active = bool(workflow.get("body_mind_unlocked")) or explicit_body_mind_access

if body_mind_active:
    st.success("Body-Mind Connection is active for this member.")

    disable_version = _disable_version(member_id)
    disable_confirmation_key = (
        f"hm_body_mind_disable_confirm_{member_id}_{disable_version}"
    )
    allow_disable = st.checkbox(
        "I need to disable Body-Mind visibility for this member",
        key=disable_confirmation_key,
    )
    if allow_disable:
        if st.button(
            "Disable Body-Mind Visibility",
            type="primary",
            use_container_width=True,
            key=f"hm_body_mind_disable_button_{member_id}_{disable_version}",
        ):
            try:
                clear_body_mind_activation(member_id)
            except Exception:
                st.error(
                    "Unable to disable Body-Mind visibility. No changes were made; "
                    "the confirmation remains selected so you can try again."
                )
            else:
                _advance_disable_version(member_id)
                set_system_message(
                    "Body-Mind Connection page disabled for this member.",
                    "warning",
                )
                st.rerun()
else:
    if admin_final_completed:
        st.warning(
            "Final admin work is complete, but Body-Mind is not active for this member."
        )
        if st.button(
            "Activate Body-Mind Connection",
            type="primary",
            use_container_width=True,
            key=f"hm_body_mind_activate_{member_id}",
        ):
            ok, message = manually_unlock_body_mind_after_finalization(member_id)
            if ok:
                set_system_message(message, "success", celebrate=True)
            else:
                set_system_message(message, "error")
            st.rerun()
    else:
        st.warning(
            "Complete the five admin pages / final admin assessment before enabling "
            "Body-Mind Connection."
        )
        st.button(
            "Activate Body-Mind Connection",
            use_container_width=True,
            disabled=True,
            key=f"hm_body_mind_activate_disabled_{member_id}",
        )

card_end()

render_page_nav(
    "Body-Mind Access",
    back_page="pages/10_Admin_Dashboard.py",
    dashboard_page="pages/10_Admin_Dashboard.py",
    show_evaluation=False,
    show_dashboard=True,
    location="bottom",
)
render_back_to_top()
