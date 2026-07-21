import streamlit as st


st.set_page_config(
    page_title="HealthyMe Logout",
    page_icon="🌿",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# Keep the signed-out marker in the URL while Streamlit deletes the identity cookie
# and starts a fresh browser session.
try:
    st.query_params["logout"] = "1"
except Exception:
    pass

if st.user.is_logged_in:
    st.logout()

# After st.logout() starts the fresh session, continue to Login in the same tab.
try:
    st.query_params["logout"] = "1"
except Exception:
    pass
st.switch_page("pages/01_Login.py")
