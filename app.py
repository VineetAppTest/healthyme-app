import streamlit as st

from components.ui_common import inject_global_styles
from components.auth_session import restore_persistent_session, route_authenticated_user, safe_switch_page, maybe_wait_for_cookie_restore

st.set_page_config(page_title="HealthyMe", page_icon="🌿", layout="wide")
inject_global_styles()

if restore_persistent_session():
    route_authenticated_user()
else:
    maybe_wait_for_cookie_restore()
    safe_switch_page("pages/01_Login.py")
