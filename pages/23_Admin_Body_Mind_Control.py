import streamlit as st
from components.guards import require_admin
from components.ui_common import inject_global_styles, apply_luxe_theme, topbar, card_start, card_end, utility_logout_bar
from components.db import list_members, get_workflow, set_body_mind_visibility, load_db, get_admin_assessment
from components.flash import set_system_message, render_system_message

st.set_page_config(page_title="Body-Mind Access Control", page_icon="💚", layout="wide")
inject_global_styles(); apply_luxe_theme(); require_admin(); utility_logout_bar()

topbar(
    "Body-Mind Access Control",
    "Enable or disable the Body-Mind Connection page after the admin assessment has been saved.",
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

card_start()
st.subheader(member["name"])
st.caption(member["email"])
st.write(f"Current visibility: **{'Visible to member' if wf.get('body_mind_unlocked') else 'Hidden from member'}**")
st.write(f"Admin assessment: **{'Saved/Completed' if admin_assessment_saved else 'Not saved yet'}**")
st.write(f"Body-Mind completion: **{'Completed' if wf.get('body_mind_completed') else 'Not completed'}**")

if body_response:
    st.success("Body-Mind responses exist for this member.")
else:
    st.info("No Body-Mind responses yet.")

if not admin_assessment_saved:
    st.warning("Complete and save Admin Assessment before enabling Body-Mind Connection.")
card_end()

card_start()
st.subheader("Set visibility")

if not admin_assessment_saved and not wf.get("body_mind_unlocked"):
    st.checkbox(
        "Make Body-Mind Connection page visible to this member",
        value=False,
        disabled=True,
        help="Admin assessment must be saved first."
    )
    st.button("Save Body-Mind Visibility", disabled=True, use_container_width=True)
else:
    unlock = st.checkbox(
        "Make Body-Mind Connection page visible to this member",
        value=bool(wf.get("body_mind_unlocked")),
        help="You can disable visibility later if needed."
    )
    if st.button("Save Body-Mind Visibility", type="primary", use_container_width=True):
        old_visibility = bool(wf.get("body_mind_unlocked"))
        set_body_mind_visibility(member_id, unlock)
        if unlock and not old_visibility:
            set_system_message("Body-Mind Connection page enabled for this member.", "success", celebrate=True)
        elif not unlock and old_visibility:
            set_system_message("Body-Mind Connection page disabled for this member.", "warning")
        else:
            set_system_message("No visibility change was needed.", "info")
        st.rerun()

card_end()

if st.button("Back to Dashboard"):
    st.switch_page("pages/10_Admin_Dashboard.py")