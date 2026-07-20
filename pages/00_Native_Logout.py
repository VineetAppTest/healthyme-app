import streamlit as st


st.set_page_config(
    page_title="HealthyMe Logout",
    page_icon="🌿",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# Execute native logout at the top level, outside page guards and button callbacks.
# Streamlit deletes its identity cookie and starts a new session.
if st.user.is_logged_in:
    st.logout()

# Direct visits after logout should land on the PoC login page.
st.switch_page("pages/01_Login.py")
