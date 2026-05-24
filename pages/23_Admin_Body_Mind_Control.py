import streamlit as st
from components.guards import require_admin
from components.ui_common import inject_global_styles, apply_luxe_theme, topbar, card_start, card_end, utility_logout_bar, render_build_text_v15, render_page_nav, stat_grid, render_back_to_top, compact_topbar
from components.db import list_members, get_workflow, set_body_mind_visibility, load_db, get_admin_assessment, sync_body_mind_after_admin_completion, request_body_mind_activation, clear_body_mind_activation, sync_body_mind_after_admin_completion, request_body_mind_activation, clear_body_mind_activation, manually_unlock_body_mind_after_finalization, sync_member_finalization_state, has_explicit_body_mind_access
from components.flash import set_system_message, render_system_message

st.set_page_config(page_title="Body-Mind Access Control", page_icon="💚", layout="wide", initial_sidebar_state="collapsed")
inject_global_styles(); apply_luxe_theme(); require_admin(); utility_logout_bar(); render_back_to_top()
render_build_text_v15()
render_page_nav("Body-Mind Access", back_page="pages/10_Admin_Dashboard.py", show_evaluation=False, location="top")

compact_topbar(
    "Body-Mind Access Control",
    "Manually activate Body-Mind after final admin completion, or explicitly disable access if required.",
    "Admin control"
)
render_system_message()

members = list_members()
if not members:
    st.info("No members available.")
    st.stop()

card_start()
st.markdown("### 👤 Body-Mind Control Context")
st.caption("This member selection controls whose Body-Mind access status is visible and changed below.")
selected = st.selectbox("👤 Member", [f"{m['id']} — {m['name']} — {m['email']}" for m in members])
member_id = selected.split(" — ")[0]
st.markdown(f"<div class='hm-date-emphasis'>👤 Managing Body-Mind access for: {selected}</div>", unsafe_allow_html=True)
card_end()
member = next(m for m in members if m["id"] == member_id)
wf = get_workflow(member_id)
explicit_body_mind_access = has_explicit_body_mind_access(member_id)
if explicit_body_mind_access:
    wf["body_mind_unlocked"] = True

# v31: repair stale review/instance status for finalized records without auto-unlocking Body-Mind.
if wf.get("admin_completed") or wf.get("final_report_ready") or wf.get("workflow_status") == "finalized":
    wf = sync_member_finalization_state(member_id, body_mind_unlock=None)
explicit_body_mind_access = has_explicit_body_mind_access(member_id)
if explicit_body_mind_access:
    wf["body_mind_unlocked"] = True

db = load_db()
body_response = db.get("body_mind_responses", {}).get(member_id, {})
admin_assessment = get_admin_assessment(member_id)

admin_assessment_saved = bool(admin_assessment) or bool(wf.get("admin_completed"))
admin_final_completed = bool(wf.get("admin_completed")) or bool(wf.get("final_report_ready"))

card_start()
st.subheader(member["name"])
st.caption(member["email"])
stat_grid([
    {"label": "Visibility", "value": "Visible" if (wf.get("body_mind_unlocked") or explicit_body_mind_access) else "Hidden", "note": "Member access"},
    {"label": "Activation", "value": "Activated" if (wf.get("body_mind_unlocked") or explicit_body_mind_access) else ("Requested" if wf.get("body_mind_activation_requested") else "Not requested"), "note": "Admin selection"},
    {"label": "Admin Assessment", "value": "Saved" if admin_assessment_saved else "Not saved", "note": "Unlock prerequisite"},
    {"label": "Body-Mind", "value": "Completed" if wf.get("body_mind_completed") else "Not completed", "note": "Member progress"},
    {"label": "Responses", "value": "Available" if body_response else "No responses", "note": "Stored data"},
])
card_end()

card_start()
st.subheader("Set visibility")

body_mind_active = bool(wf.get("body_mind_unlocked")) or explicit_body_mind_access

if body_mind_active:
    st.success("Body-Mind Connection is active for this member.")

    allow_disable = st.checkbox("I need to disable Body-Mind visibility for this member")
    if allow_disable:
        if st.button("Disable Body-Mind Visibility", type="primary", use_container_width=True):
            clear_body_mind_activation(member_id)
            set_system_message("Body-Mind Connection page disabled for this member.", "warning")
            st.rerun()
else:
    if admin_final_completed:
        st.warning("Final admin work is complete, but Body-Mind is not active for this member.")
        if st.button("Activate Body-Mind Connection", type="primary", use_container_width=True):
            ok, msg = manually_unlock_body_mind_after_finalization(member_id)
            if ok:
                set_system_message(msg, "success", celebrate=True)
            else:
                set_system_message(msg, "error")
            st.rerun()
    else:
        st.warning("Complete the five admin pages / final admin assessment before enabling Body-Mind Connection.")
        st.button("Activate Body-Mind Connection", use_container_width=True, disabled=True)

card_end()
render_page_nav("Body-Mind Access", back_page="pages/10_Admin_Dashboard.py", show_evaluation=False, location="bottom")