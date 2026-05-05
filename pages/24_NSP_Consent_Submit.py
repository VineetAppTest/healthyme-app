import streamlit as st
from datetime import date
from components.guards import require_member
from components.ui_common import inject_global_styles, apply_luxe_theme, topbar, card_start, card_end, utility_logout_bar, stat_grid
from components.db import get_profile_with_laf_fallback
from components.assessment_instances import get_current_assessment_instance, submit_current_assessment_instance_once
from components.flash import set_system_message, render_system_message

st.set_page_config(page_title="Consent & Submit", page_icon="💚", layout="wide", initial_sidebar_state="collapsed")
inject_global_styles(); apply_luxe_theme(); require_member(); utility_logout_bar()

user_id = st.session_state["user_id"]
inst = get_current_assessment_instance(user_id)
profile = get_profile_with_laf_fallback(user_id)

topbar(
    "Consent & Submit",
    f"{inst.get('instance_type')} — Instance {inst.get('instance_number')}",
    "NSP submission"
)
render_system_message()

card_start()
stat_grid([
    {"label": "Instance", "value": inst.get("instance_number"), "note": inst.get("instance_type")},
    {"label": "Requested Pages", "value": ", ".join(["NSP1" if p=="nsp1" else "NSP2" for p in inst.get("requested_pages", [])]), "note": "Admin request"},
    {"label": "Status", "value": inst.get("status", "").replace("_", " ").title(), "note": "Current state"},
    {"label": "Due Date", "value": inst.get("due_date") or "-", "note": "If set by admin"},
])
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

accepted = st.checkbox("I accept the client statement", value=False)
name = st.text_input("Name / Signature", value=profile.get("full_name", ""))
consent_date = st.date_input("Date", value=date.today())

c1, c2 = st.columns(2)
with c1:
    if st.button("Back", use_container_width=True):
        pages = inst.get("requested_pages", [])
        if "nsp2" in pages:
            st.switch_page("pages/05_NSP_Page2.py")
        elif "nsp1" in pages:
            st.switch_page("pages/04_NSP_Page1.py")
        else:
            st.switch_page("pages/02_Member_Home.py")
with c2:
    if st.button("Submit Assessment for Admin Review", type="primary", use_container_width=True):
        if not accepted:
            set_system_message("Please tick I accept before submitting.", "error")
            st.rerun()
        elif not name.strip():
            set_system_message("Please enter your name/signature before submitting.", "error")
            st.rerun()
        else:
            first = submit_current_assessment_instance_once(user_id, {
                "accepted": True,
                "accepted_date": consent_date.isoformat(),
                "name_signature": name.strip(),
                "instance_id": inst.get("instance_id"),
            })
            if first:
                set_system_message("Assessment submitted successfully. Admin review is now required.", "success", celebrate=True)
            else:
                set_system_message("This assessment was already submitted. Admin review is already pending.", "info")
            st.switch_page("pages/06_Submit_Status.py")
card_end()