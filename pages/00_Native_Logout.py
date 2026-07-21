import streamlit as st
import streamlit.components.v1 as components


st.set_page_config(
    page_title="HealthyMe Logout",
    page_icon="🌿",
    layout="centered",
    initial_sidebar_state="collapsed",
)

LOGIN_AFTER_LOGOUT_URL = "/Login?logout=1"

# This route is opened with ?logout=1. st.logout() deletes Streamlit's identity
# cookie and creates a new session. The URL marker survives that transition and
# keeps the Login page stable while cookie deletion finishes in the browser.
if st.user.is_logged_in:
    st.logout()

st.title("Signed out")
st.success("Your HealthyMe test session has been closed.")

# Navigate the top-level app, not the component iframe. The visible link remains
# as a fallback if a browser blocks scripted navigation.
components.html(
    f"""
    <script>
      window.parent.location.replace({LOGIN_AFTER_LOGOUT_URL!r});
    </script>
    """,
    height=0,
)
st.link_button("Continue to Login", LOGIN_AFTER_LOGOUT_URL, type="primary")
