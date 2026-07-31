from datetime import date

import streamlit as st

from components.assessment_instances import (
    get_current_assessment_instance,
    submit_current_assessment_instance_once,
)
from components.db import (
    get_profile_with_laf_fallback,
    recalculate_member_nsp_system_scores,
)
from components.flash import render_system_message, set_system_message
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


CONSENT_VERSION_PREFIX = "hm_member_consent_version_"


def _instance_scope(instance: dict) -> str:
    return str(
        instance.get("instance_id")
        or f"legacy_{instance.get('instance_number', 'current')}"
    )


def _consent_version(instance_scope: str) -> int:
    key = f"{CONSENT_VERSION_PREFIX}{instance_scope}"
    return max(int(st.session_state.get(key, 1) or 1), 1)


def _advance_consent_version(instance_scope: str) -> None:
    key = f"{CONSENT_VERSION_PREFIX}{instance_scope}"
    st.session_state[key] = _consent_version(instance_scope) + 1


def task_title_v96_2(task_key):
    return {
        "nsp1": "NSP Page 1",
        "nsp2": "NSP Page 2",
        "body_mind": "Body-Mind Connection",
    }.get(str(task_key), str(task_key))


def task_done_v96_2(instance, task_key):
    if task_key == "nsp1":
        return bool(instance.get("nsp1_completed"))
    if task_key == "nsp2":
        return bool(instance.get("nsp2_completed"))
    if task_key == "body_mind":
        return bool(instance.get("body_mind_completed"))
    return True


st.set_page_config(
    page_title="Consent & Submit",
    page_icon="💚",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_global_styles()
apply_luxe_theme()
require_member()
utility_logout_bar()

user_id = st.session_state["user_id"]
instance = get_current_assessment_instance(user_id)
profile = get_profile_with_laf_fallback(user_id)
instance_scope = _instance_scope(instance)
consent_version = _consent_version(instance_scope)

accepted_key = f"hm_member_consent_accept_{user_id}_{instance_scope}_{consent_version}"
name_key = f"hm_member_consent_name_{user_id}_{instance_scope}_{consent_version}"
date_key = f"hm_member_consent_date_{user_id}_{instance_scope}_{consent_version}"
submit_key = f"hm_member_consent_submit_{user_id}_{instance_scope}_{consent_version}"

topbar(
    "Consent & Submit",
    f"{instance.get('instance_type')} — Instance {instance.get('instance_number')}",
    "NSP submission",
)
render_system_message()

card_start()
stat_grid(
    [
        {
            "label": "Instance",
            "value": instance.get("instance_number"),
            "note": instance.get("instance_type"),
        },
        {
            "label": "Requested Tasks",
            "value": ", ".join(
                [task_title_v96_2(page) for page in instance.get("requested_pages", [])]
            ),
            "note": "Nutritionist request",
        },
        {
            "label": "Status",
            "value": instance.get("status", "").replace("_", " ").title(),
            "note": "Current state",
        },
        {
            "label": "Due Date",
            "value": instance.get("due_date") or "-",
            "note": "If set by admin",
        },
    ]
)
card_end()

card_start()
st.subheader("Client Statement")
st.markdown(
    """
    <div class='warning-banner'>
      I understand and acknowledge that the services provided are at all times restricted to consultation on the subject of health matters intended for general well-being and are not meant for the purposes of medical diagnosis, treatment or prescribing of medicine for any disease, or any licensed or controlled act which may constitute the practice of medicine. This statement is being accepted voluntarily.
      <br><br>
      Thank you for your cooperation. All information contained on this form will be kept strictly confidential.
    </div>
    """,
    unsafe_allow_html=True,
)

accepted = st.checkbox(
    "I accept the client statement",
    value=False,
    key=accepted_key,
)
name = st.text_input(
    "Name / Signature",
    value=profile.get("full_name", ""),
    key=name_key,
)
consent_date = st.date_input(
    "Date",
    value=date.today(),
    key=date_key,
)

left, right = st.columns(2)
with left:
    pass  # v102.0 legacy direct navigation removed; use canonical footer
with right:
    if st.button(
        "Submit Assessment for Admin Review",
        type="primary",
        use_container_width=True,
        key=submit_key,
    ):
        incomplete_tasks = [
            task_title_v96_2(page)
            for page in instance.get("requested_pages", [])
            if not task_done_v96_2(instance, page)
        ]
        if incomplete_tasks:
            set_system_message(
                "Please complete the requested task(s) before submitting: "
                + ", ".join(incomplete_tasks),
                "error",
            )
            st.rerun()
        elif not accepted:
            set_system_message("Please tick I accept before submitting.", "error")
            st.rerun()
        elif not name.strip():
            set_system_message(
                "Please enter your name/signature before submitting.",
                "error",
            )
            st.rerun()
        else:
            try:
                recalculate_member_nsp_system_scores(user_id, actor_id=user_id)
                first_submission = submit_current_assessment_instance_once(
                    user_id,
                    {
                        "accepted": True,
                        "accepted_date": consent_date.isoformat(),
                        "name_signature": name.strip(),
                        "instance_id": instance.get("instance_id"),
                    },
                )
            except Exception:
                st.error(
                    "Unable to submit the assessment right now. Your consent, name and "
                    "date remain available so you can try again."
                )
            else:
                if first_submission:
                    _advance_consent_version(instance_scope)
                    set_system_message(
                        "Assessment submitted successfully. Admin review is now required.",
                        "success",
                        celebrate=True,
                    )
                else:
                    set_system_message(
                        "This assessment was already submitted. Admin review is already pending.",
                        "info",
                    )
                st.switch_page("pages/06_Submit_Status.py")
card_end()

render_page_nav(
    "NSP Submit",
    back_page="pages/02_Member_Home.py",
    dashboard_page="pages/02_Member_Home.py",
    show_evaluation=False,
    show_dashboard=True,
    location="bottom",
)
render_back_to_top()
