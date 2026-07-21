import streamlit as st


st.set_page_config(
    page_title="HealthyMe Logout",
    page_icon="🌿",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# This compatibility route now follows the same native lifecycle as the protected
# page Logout buttons. Streamlit removes the identity cookie and starts a new session.
if st.user.is_logged_in:
    st.logout()

st.switch_page("pages/01_Login.py")
