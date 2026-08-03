import streamlit as st

from components.profile_builder_access import require_profile_builder_access


st.set_page_config(
    page_title="Member Plan Builder",
    page_icon="💚",
    layout="wide",
    initial_sidebar_state="collapsed",
)
require_profile_builder_access()
st.session_state["pbm_section"] = "View Member Plan"
st.switch_page("pages/38_Admin_Recommendation_Profile_Builder.py")
