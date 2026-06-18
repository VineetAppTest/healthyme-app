from components.ui_common import render_page_nav, render_back_to_top
# v100.1 Submit Status NameError hotfix
import streamlit as st
from components.guards import require_member
from components.ui_common import inject_global_styles, apply_luxe_theme, topbar, card_start, card_end, utility_logout_bar, stat_grid, render_build_text_v12, render_back_to_top
from components.db import get_workflow
from components.assessment_instances import get_assessment_instances, get_current_assessment_instance, task_progress_summary_v99, submit_current_assessment_instance_once
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

progress_v100 = task_progress_summary_v99(current)
body_mind_done_v100 = bool(wf.get("body_mind_completed")) or bool(current.get("body_mind_completed"))
review_label_v100 = "Submitted" if current.get("submitted_for_review") else ("Ready" if progress_v100.get("is_complete") else "Not Ready")

stat_grid([
    {"label": "Current Instance", "value": current.get("instance_number"), "note": current.get("instance_type")},
    {"label": "Current Status", "value": current.get("status", "").replace("_", " ").title(), "note": "Latest assessment"},
    {"label": "LAF", "value": "Completed" if wf.get("laf_completed") else "Pending", "note": "Initial only; not repeated for task requests"},
    {"label": "Body-Mind Status", "value": "Completed" if body_mind_done_v100 else "Pending", "note": "Shown until completed"},
    {"label": "Admin Review", "value": review_label_v100, "note": "Review status"},
])


card_start()
st.subheader("Submit for admin review")
if current.get("submitted_for_review"):
    st.success(f"Instance {current.get('instance_number')} has already been submitted for admin review.")
elif progress_v100.get("is_complete"):
    st.info("All requested tasks are complete. Submit this instance so Admin can review it.")
    confirm_submit_v100 = st.checkbox("I confirm this task set is complete and ready for admin review.", key="v100_submit_confirm")
    if st.button("Submit to Admin Review", type="primary", use_container_width=True, disabled=not confirm_submit_v100):
        first_submit_v100 = submit_current_assessment_instance_once(user_id, {"accepted": True, "source": "submit_status_v100"})
        if first_submit_v100:
            st.success("Submitted to Admin Review.")
        else:
            st.info("This instance was already submitted earlier.")
        st.rerun()
else:
    st.warning(f"Complete all requested tasks before submission. Progress: {progress_v100.get('done', 0)} of {progress_v100.get('total', 0)} completed.")
card_end()

card_start()
st.subheader("Assessment history")
for inst in sorted(instances, key=lambda x: x.get("instance_number", 0)):
    st.markdown(
        f"""
        **Instance {inst.get('instance_number')} — {inst.get('instance_type')}**  
        Task allocation date: {inst.get('created_date') or '-'}  
Requested: {', '.join([task_title_v96_2(p) for p in inst.get('requested_pages', [])])}  
        Progress: `{task_progress_summary_v99(inst).get('done', 0)} of {task_progress_summary_v99(inst).get('total', 0)}`  
        Status: `{inst.get('status')}` | Submitted: `{inst.get('submitted_date') or '-'}`
        """
    )
card_end()

if st.button("Back to Home"):
    st.switch_page("pages/02_Member_Home.py")