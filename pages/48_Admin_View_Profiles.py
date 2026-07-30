import streamlit as st

from components.performance_diagnostics import begin_page_measurement, finish_and_render_page_diagnostics
from components.profile_builder_access import (
    current_profile_builder_role,
    profile_builder_role_utility_bar,
    require_profile_builder_access,
)
from components.recommendation_profile_viewer import render_view_profiles
from components.ui_common import (
    apply_luxe_theme,
    inject_global_styles,
    render_back_to_top,
    render_page_nav,
    topbar,
)


st.set_page_config(
    page_title="View Recommendation Profiles",
    page_icon="💚",
    layout="wide",
    initial_sidebar_state="collapsed",
)
begin_page_measurement("View Recommendation Profiles")
inject_global_styles()
apply_luxe_theme()
require_profile_builder_access()
profile_builder_role_utility_bar()

topbar(
    "View Profiles",
    "Read-only inventory of Draft, Active, Replaced and Archived recommendation profiles.",
    "Recommendation profiles",
)

render_view_profiles()

if current_profile_builder_role() in {"admin", "super_admin"}:
    render_page_nav(
        "View Profiles",
        back_page="pages/10_Admin_Dashboard.py",
        dashboard_page="pages/10_Admin_Dashboard.py",
        show_evaluation=False,
        show_dashboard=True,
        location="bottom",
    )
render_back_to_top()
finish_and_render_page_diagnostics("View Recommendation Profiles")
