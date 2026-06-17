import json
import streamlit as st

from components.guards import require_admin
from components.ui_common import inject_global_styles, apply_luxe_theme, utility_logout_bar, render_back_to_top, card_start, card_end
from scripts.import_shweta_mishra_backend import run_import, MEMBER_NAME, MEMBER_EMAIL, NSP_ASSESSMENT_DATE

st.set_page_config(page_title="One-Time Import - Shweta Mishra", page_icon="🌿", layout="wide", initial_sidebar_state="collapsed")
inject_global_styles(); apply_luxe_theme(); require_admin(); utility_logout_bar(); render_back_to_top()

st.title("One-Time Backend Import")
st.caption("Admin-only import for offline LAF PDF + NSP Excel received for Shweta Mishra.")

card_start()
st.subheader(MEMBER_NAME)
st.write(f"Email/login authorization: **{MEMBER_EMAIL}**")
st.write(f"NSP assessment date: **{NSP_ASSESSMENT_DATE}**")
st.info("This import is idempotent. Running it again will update the same member record and refresh the imported assessment data.")

if st.button("Run one-time import for Shweta Mishra", type="primary", use_container_width=True):
    with st.spinner("Importing member, LAF, NSP and admin subforms into backend..."):
        try:
            result = run_import()
            st.success("Import completed successfully.")
            st.json(result)
        except Exception as exc:
            st.error(f"Import failed: {exc}")
            st.exception(exc)
card_end()
