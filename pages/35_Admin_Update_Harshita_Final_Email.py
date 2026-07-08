import streamlit as st

from components.guards import require_admin
from components.ui_common import inject_global_styles, apply_luxe_theme, utility_logout_bar, render_back_to_top, card_start, card_end
from scripts.import_harshita_laf_backend_final_email import run_import, MEMBER_NAME, MEMBER_EMAIL, LAF_FORM_DATE, LAF_SIGNED_DATE

EXPECTED_EMAIL = "harshita.sajjanhar@gmail.com"

st.set_page_config(page_title="Harshita Final Email Update", page_icon="🌿", layout="wide", initial_sidebar_state="collapsed")
inject_global_styles(); apply_luxe_theme(); require_admin(); utility_logout_bar(); render_back_to_top()

st.title("Harshita Final Email Update + LAF Refresh")
st.caption("Admin-only import for offline LAF PDF received for Harshita Sajjanhar. This route uses a new page and new script name to update the final email and refresh Harshita's LAF safely.")

card_start()
st.subheader(MEMBER_NAME)
st.write(f"Expected email/login authorization: **{EXPECTED_EMAIL}**")
st.write(f"Script email/login authorization: **{MEMBER_EMAIL}**")
st.write(f"LAF form date: **{LAF_FORM_DATE}**")
st.write(f"LAF signed/client statement date: **{LAF_SIGNED_DATE}**")

if MEMBER_EMAIL.strip().lower() != EXPECTED_EMAIL:
    st.error("Safety stop: loaded script is not the email-fix version. Do not run this import.")
else:
    st.info("This import is idempotent. Running it again will update the same member record and refresh only Harshita's imported LAF/profile/workflow data.")
    st.warning("This import does not create the Auth0 user. Auth0 should be created/updated manually with harshita.sajjanhar@gmail.com.")
    if st.button("Run Harshita final email update + LAF refresh", type="primary", use_container_width=True):
        with st.spinner("Updating Harshita final member email and refreshing LAF into backend..."):
            try:
                result = run_import()
                st.success("Harshita final email update and LAF refresh completed successfully.")
                st.json(result)
            except Exception as exc:
                st.error(f"Import failed: {exc}")
                st.exception(exc)
card_end()
