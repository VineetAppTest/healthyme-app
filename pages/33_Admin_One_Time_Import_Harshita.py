import streamlit as st

from components.guards import require_admin
from components.ui_common import inject_global_styles, apply_luxe_theme, utility_logout_bar, render_back_to_top, card_start, card_end
from scripts.import_harshita_laf_backend import run_import, MEMBER_NAME, MEMBER_EMAIL, LAF_FORM_DATE, LAF_SIGNED_DATE

st.set_page_config(page_title="One-Time Import - Harshita LAF", page_icon="🌿", layout="wide", initial_sidebar_state="collapsed")
inject_global_styles(); apply_luxe_theme(); require_admin(); utility_logout_bar(); render_back_to_top()

st.title("One-Time Backend Import")
st.caption("Admin-only import for offline LAF PDF received for Harshita Sajjanhar.")

card_start()
st.subheader(MEMBER_NAME)
st.write(f"Temporary email/login authorization: **{MEMBER_EMAIL}**")
st.write(f"LAF form date: **{LAF_FORM_DATE}**")
st.write(f"LAF signed/client statement date: **{LAF_SIGNED_DATE}**")
st.info("This import is idempotent. Running it again will update the same member record and refresh only the imported LAF/profile/workflow data for this member.")
st.warning("This import does not create the Auth0 user. Create/update Auth0 manually. Replace the temporary email later when the real email is available.")

if st.button("Run one-time LAF import for Harshita Sajjanhar", type="primary", use_container_width=True):
    with st.spinner("Importing member and LAF into backend..."):
        try:
            result = run_import()
            st.success("LAF import completed successfully.")
            st.json(result)
        except Exception as exc:
            st.error(f"Import failed: {exc}")
            st.exception(exc)
card_end()
