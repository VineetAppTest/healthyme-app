import streamlit as st

from components.current_member_plan_view import render_todays_current_plan_view
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
    page_title="Today's Plan",
    page_icon="💚",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_global_styles()
apply_luxe_theme()
require_member()
utility_logout_bar()
topbar(
    "Today's Plan",
    "Today's meals plus your current Exercise and Supplement allocations.",
    "Member plan",
)

render_todays_current_plan_view()

render_page_nav(
    "Today's Plan",
    back_page="pages/02_Member_Home.py",
    dashboard_page="pages/02_Member_Home.py",
    show_evaluation=False,
    show_dashboard=True,
    location="bottom",
)
render_back_to_top()
