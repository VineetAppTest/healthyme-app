import streamlit as st

from components.assessment_instances import (
    get_assessment_instances,
    get_current_assessment_instance,
    submit_current_assessment_instance_once,
    task_progress_summary_v99,
)
from components.db import get_workflow
from components.flash import render_system_message
from components.guards import require_member
from components.ui_common import (
    apply_luxe_theme,
    card_end,
    card_start,
    inject_global_styles,
    render_back_to_top,
    render_page_nav,
    stat_grid,
    topbar,
    utility_logout_bar,
)


SUBMIT_VERSION_PREFIX = "hm_member_submit_status_version_"


def _instance_scope(instance: dict) -> str:
    return str(
        instance.get("instance_id")
        or f"legacy_{instance.get('instance_number', 'current')}"
    )


def _submit_version(instance_scope: str) -> int:
    key = f"{SUBMIT_VERSION_PREFIX}{instance_scope}"
    return max(int(st.session_state.get(key, 1) or 1), 1)


def _advance_submit_version(instance_scope: str) -> None:
    key = f"{SUBMIT_VERSION_PREFIX}{instance_scope}"
    st.session_state[key] = _submit_version(instance_scope) + 1


def task_title_v96_2(task_key):
    return {
        "nsp1": "NSP Page 1",
        "nsp2": "NSP Page 2",
        "body_mind": "Body-Mind Connection",
    }.get(str(task_key), str(task_key))


st.set_page_config(
    page_title="Submit Status",
    page_icon="💚",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_global_styles()
apply_luxe_theme()
require_member()
utility_logout_bar()

user_id = st.session_state["user_id"]
workflow = get_workflow(user_id)
instances = get_assessment_instances(user_id)
current = get_current_assessment_instance(user_id)
instance_scope = _instance_scope(current)
submit_version = _submit_version(instance_scope)
confirmation_key = (
    f"hm_member_submit_confirm_{user_id}_{instance_scope}_{submit_version}"
)
submit_button_key = (
    f"hm_member_submit_button_{user_id}_{instance_scope}_{submit_version}"
)

topbar(
    "Submission Status",
    "Track your assessment and reassessment submissions.",
    "Member status",
)
render_system_message()

progress = task_progress_summary_v99(current)
body_mind_done = bool(workflow.get("body_mind_completed")) or bool(
    current.get("body_mind_completed")
)
review_label = (
    "Submitted"
    if current.get("submitted_for_review")
    else ("Ready" if progress.get("is_complete") else "Not Ready")
)

stat_grid(
    [
        {
            "label": "Current Instance",
            "value": current.get("instance_number"),
            "note": current.get("instance_type"),
        },
        {
            "label": "Current Status",
            "value": current.get("status", "").replace("_", " ").title(),
            "note": "Latest assessment",
        },
        {
            "label": "LAF",
            "value": "Completed" if workflow.get("laf_completed") else "Pending",
            "note": "Initial only; not repeated for task requests",
        },
        {
            "label": "Body-Mind Status",
            "value": "Completed" if body_mind_done else "Pending",
            "note": "Shown until completed",
        },
        {
            "label": "Admin Review",
            "value": review_label,
            "note": "Review status",
        },
    ]
)

card_start()
st.subheader("Submit for admin review")
if current.get("submitted_for_review"):
    st.success(
        f"Instance {current.get('instance_number')} has already been submitted for admin review."
    )
elif progress.get("is_complete"):
    st.info("All requested tasks are complete. Submit this instance so Admin can review it.")
    confirm_submit = st.checkbox(
        "I confirm this task set is complete and ready for admin review.",
        key=confirmation_key,
    )
    if st.button(
        "Submit to Admin Review",
        type="primary",
        use_container_width=True,
        disabled=not confirm_submit,
        key=submit_button_key,
    ):
        try:
            first_submission = submit_current_assessment_instance_once(
                user_id,
                {
                    "accepted": True,
                    "source": "submit_status_v100",
                    "instance_id": current.get("instance_id"),
                },
            )
        except Exception:
            st.error(
                "Unable to submit this assessment right now. The confirmation remains "
                "selected so you can try again."
            )
        else:
            if first_submission:
                _advance_submit_version(instance_scope)
                st.success("Submitted to Admin Review.")
            else:
                st.info("This instance was already submitted earlier.")
            st.rerun()
else:
    st.warning(
        "Complete all requested tasks before submission. "
        f"Progress: {progress.get('done', 0)} of {progress.get('total', 0)} completed."
    )
card_end()

card_start()
st.subheader("Assessment history")
for instance in sorted(instances, key=lambda item: item.get("instance_number", 0)):
    instance_progress = task_progress_summary_v99(instance)
    st.markdown(
        f"""
        **Instance {instance.get('instance_number')} — {instance.get('instance_type')}**  
        Task allocation date: {instance.get('created_date') or '-'}  
        Requested: {', '.join([task_title_v96_2(page) for page in instance.get('requested_pages', [])])}  
        Progress: `{instance_progress.get('done', 0)} of {instance_progress.get('total', 0)}`  
        Status: `{instance.get('status')}` | Submitted: `{instance.get('submitted_date') or '-'}`
        """
    )
card_end()

render_page_nav(
    "Submit Status",
    back_page="pages/02_Member_Home.py",
    dashboard_page="pages/02_Member_Home.py",
    show_evaluation=False,
    show_dashboard=True,
    location="bottom",
)
render_back_to_top()
