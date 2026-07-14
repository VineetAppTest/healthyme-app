import streamlit as st

from components.flash import render_system_message
from components.guards import require_member
from components.member_exercise_view import render_member_exercise_journal
from components.ui_common import (
    apply_luxe_theme,
    inject_global_styles,
    render_back_to_top,
    render_page_nav,
    topbar,
    utility_logout_bar,
)


st.set_page_config(
    page_title="My Exercise",
    page_icon="💚",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_global_styles()
apply_luxe_theme()
require_member()
utility_logout_bar()
topbar(
    "My Exercise",
    "View today's prescribed exercises and record progress.",
    "Member tracker",
)
render_system_message()

render_member_exercise_journal(key_prefix="standalone_exercise")

render_page_nav(
    "My Exercise",
    back_page="pages/18_Daily_Log.py",
    dashboard_page="pages/02_Member_Home.py",
    show_evaluation=False,
    show_dashboard=True,
    location="bottom",
)
render_back_to_top()
