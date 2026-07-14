import streamlit as st

from components.guards import require_admin
from components.profile_builder_modular import render_modular_profile_builder
from components.ui_common import (
    apply_luxe_theme,
    inject_global_styles,
    render_back_to_top,
    render_page_nav,
    utility_logout_bar,
)


st.set_page_config(
    page_title="Recommendation Profile Builder",
    page_icon="💚",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_global_styles()
apply_luxe_theme()
require_admin()
utility_logout_bar()

render_modular_profile_builder()

render_page_nav(
    "Recommendation Profile Builder",
    back_page="pages/10_Admin_Dashboard.py",
    dashboard_page="pages/10_Admin_Dashboard.py",
    show_evaluation=False,
    show_dashboard=True,
    location="bottom",
)
render_back_to_top()
