import streamlit as st

from components.current_member_plan_view import render_current_member_plan_view
from components.guards import require_member
from components.ui_common import (
    apply_luxe_theme,
    inject_global_styles,
    render_back_to_top,
    render_page_nav,
    topbar,
    utility_logout_bar,
)

st.set_page_config(
    page_title="Current Member Plan",
    page_icon="💚",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_global_styles()
apply_luxe_theme()
require_member()
utility_logout_bar()
topbar(
    "Current Member Plan",
    "Your current meals, exercises and supplements in one read-only view.",
    "Member plan",
)

render_current_member_plan_view()

render_page_nav(
    "Current Member Plan",
    back_page="pages/02_Member_Home.py",
    dashboard_page="pages/02_Member_Home.py",
    show_evaluation=False,
    show_dashboard=True,
    location="bottom",
)
render_back_to_top()
