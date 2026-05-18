import streamlit as st
from components.guards import require_admin
from components.ui_common import inject_global_styles, apply_luxe_theme, topbar, card_start, card_end, utility_logout_bar, render_build_text_v15, render_page_nav, stat_grid
from components.db import list_members, get_workflow, set_body_mind_visibility, load_db, get_admin_assessment
from components.flash import set_system_message, render_system_message

st.set_page_config(page_title="Body-Mind Access Control", page_icon="💚", layout="wide", initial_sidebar_state="collapsed")
inject_global_styles(); apply_luxe_theme(); require_admin(); utility_logout_bar()
render_build_text_v15()
render_page_nav("Body-Mind Access", back_page="pages/10_Admin_Dashboard.py", show_evaluation=False, location="top")

topbar(
    "Body-Mind Access Control",
    "Activate Body-Mind after the five admin pages/final admin assessment are completed, or explicitly disable it if required.",
    "Admin control"
)
render_system_message()

members = list_members()
if not members:
    st.info("No members available.")
    st.stop()

selected = st.selectbox("Select member", [f"{m['id']} — {m['name']} — {m['email']}" for m in members])
member_id = selected.split(" — ")[0]
member = next(m for m in members if m["id"] == member_id)
wf = get_workflow(member_id)
db = load_db()
body_response = db.get("body_mind_responses", {}).get(member_id, {})
admin_assessment = get_admin_assessment(member_id)

admin_assessment_saved = bool(admin_assessment) or bool(wf.get("admin_completed"))
admin_final_completed = bool(wf.get("admin_completed")) or bool(wf.get("final_report_ready"))

card_start()
st.subheader(member["name"])
st.caption(member["email"])
stat_grid([
    {"label": "Visibility", "value": "Visible" if wf.get("body_mind_unlocked") else "Hidden", "note": "Member access"},
    {"label": "Admin Assessment", "value": "Saved" if admin_assessment_saved else "Not saved", "note": "Unlock prerequisite"},
    {"label": "Body-Mind", "value": "Completed" if wf.get("body_mind_completed") else "Not completed", "note": "Member progress"},
    {"label": "Responses", "value": "Available" if body_response else "No responses", "note": "Stored data"},
])
if not admin_final_completed:
    st.warning("Complete the five admin pages / final admin assessment before enabling Body-Mind Connection.")
card_end()

card_start()
st.subheader("Set visibility")
st.caption("v22 note: Body-Mind activates only after admin completion and admin selection. Use this page to activate, verify, or explicitly disable.")

if not admin_final_completed and not wf.get("body_mind_unlocked"):
    st.checkbox(
        "Make Body-Mind Connection page visible to this member",
        value=False,
        disabled=True,
        help="Admin assessment must be saved first."
    )
    st.button("Save Body-Mind Visibility", disabled=True, use_container_width=True)
else:
    old_visibility = bool(wf.get("body_mind_unlocked"))

    if old_visibility:
        st.info("Body-Mind Connection is already activated for this member.")
        if st.button("Keep Activated", disabled=True, use_container_width=True):
            pass
        st.caption("To avoid accidental duplicate activation, this page will not re-activate an already active Body-Mind connection.")
        allow_disable = st.checkbox("I need to disable Body-Mind visibility for this member")
        if allow_disable:
            if st.button("Disable Body-Mind Visibility", type="primary", use_container_width=True):
                set_body_mind_visibility(member_id, False)
                set_system_message("Body-Mind Connection page disabled for this member.", "warning")
                st.rerun()
    else:
        unlock = st.checkbox(
            "Make Body-Mind Connection page visible to this member",
            value=False,
            help="Enable Body-Mind Connection for this member."
        )
        if st.button("Save Body-Mind Visibility", type="primary", use_container_width=True):
            set_body_mind_visibility(member_id, unlock)
            if unlock:
                set_system_message("Body-Mind Connection page enabled for this member.", "success", celebrate=True)
            else:
                set_system_message("No visibility change was needed.", "info")
            st.rerun()

card_end()

render_page_nav("Body-Mind Access", back_page="pages/10_Admin_Dashboard.py", show_evaluation=False, location="bottom")