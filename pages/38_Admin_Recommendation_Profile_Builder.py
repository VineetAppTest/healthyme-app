import streamlit as st

from components.profile_builder_access import (
    current_profile_builder_role,
    profile_builder_role_utility_bar,
    require_profile_builder_access,
)
from components.profile_builder_modular import render_modular_profile_builder
from components.ui_common import (
    apply_luxe_theme,
    inject_global_styles,
    render_back_to_top,
    render_page_nav,
)


st.set_page_config(
    page_title="Recommendation Profile Builder",
    page_icon="💚",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_global_styles()
apply_luxe_theme()
require_profile_builder_access()
profile_builder_role_utility_bar()

render_modular_profile_builder()

# Nutritionists are intentionally restricted to this workflow and should not be
# given a navigation control that points to the wider Admin application.
if current_profile_builder_role() in {"admin", "super_admin"}:
    render_page_nav(
        "Recommendation Profile Builder",
        back_page="pages/10_Admin_Dashboard.py",
        dashboard_page="pages/10_Admin_Dashboard.py",
        show_evaluation=False,
        show_dashboard=True,
        location="bottom",
    )
render_back_to_top()
