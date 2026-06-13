import streamlit as st
from components.guards import require_member
from components.ui_common import inject_global_styles, apply_luxe_theme, topbar, card_start, card_end, utility_logout_bar, stat_grid, render_build_text_v12, render_back_to_top
from components.db import get_workflow
from components.assessment_instances import get_assessment_instances, get_current_assessment_instance
from components.flash import render_system_message

st.set_page_config(page_title="Submit Status", page_icon="💚", layout="wide", initial_sidebar_state="collapsed")
inject_global_styles(); apply_luxe_theme(); require_member(); utility_logout_bar(); render_back_to_top()

user_id = st.session_state["user_id"]
wf = get_workflow(user_id)
instances = get_assessment_instances(user_id)
current = get_current_assessment_instance(user_id)


def task_title_v96_2(task_key):
    return {
        "nsp1": "NSP Page 1",
        "nsp2": "NSP Page 2",
        "body_mind": "Body-Mind Connection",
    }.get(str(task_key), str(task_key))

topbar("Submission Status", "Track your assessment and reassessment submissions.", "Member status")
render_system_message()

stat_grid([
    {"label": "Current Instance", "value": current.get("instance_number"), "note": current.get("instance_type")},
    {"label": "Current Status", "value": current.get("status", "").replace("_", " ").title(), "note": "Latest assessment"},
    {"label": "LAF", "value": "Completed" if wf.get("laf_completed") else "Pending", "note": "Initial only; not repeated for task requests"},
    {"label": "Body-Mind Status", "value": "Completed" if wf.get("body_mind_completed") or inst.get("body_mind_completed") else "Pending", "note": "Shown until completed"},
    {"label": "Admin Review", "value": "Pending" if current.get("submitted_for_review") else "Not Submitted", "note": "Review status"},
])

card_start()
st.subheader("Assessment history")
for inst in sorted(instances, key=lambda x: x.get("instance_number", 0)):
    st.markdown(
        f"""
        **Instance {inst.get('instance_number')} — {inst.get('instance_type')}**  
        Task allocation date: {inst.get('created_date') or '-'}  
Requested: {', '.join([task_title_v96_2(p) for p in inst.get('requested_pages', [])])}  
        Status: `{inst.get('status')}` | Submitted: `{inst.get('submitted_date') or '-'}`
        """
    )
card_end()

if st.button("Back to Home"):
    st.switch_page("pages/02_Member_Home.py")