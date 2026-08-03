import streamlit as st

from components.admin_performance_optimization import (
    admin_profile_builder_render_scope,
    install_profile_builder_performance,
)
from components.meal_profile_builder_write_boundary import (
    install_meal_profile_builder_write_boundary,
)
from components.performance_diagnostics import (
    begin_page_measurement,
    finish_and_render_page_diagnostics,
)
from components.profile_builder_access import (
    current_profile_builder_role,
    profile_builder_role_utility_bar,
    require_profile_builder_access,
)
from components.ui_common import (
    apply_luxe_theme,
    inject_global_styles,
    render_back_to_top,
    render_page_nav,
)


# Keep the existing stable route while the workflow becomes meals-only. Install
# the write boundary before importing the modular renderer so its bound save
# function cannot replace legacy Exercise or Supplement rows.
install_profile_builder_performance()
install_meal_profile_builder_write_boundary()
from components.profile_builder_modular import render_modular_profile_builder


st.set_page_config(
    page_title="Meal Profile Builder",
    page_icon="💚",
    layout="wide",
    initial_sidebar_state="collapsed",
)
# Keep the established diagnostics identity because the registered route is
# unchanged; this preserves historical performance comparisons across Phase B.
begin_page_measurement("Recommendation Profile Builder")
inject_global_styles()
apply_luxe_theme()
require_profile_builder_access()
profile_builder_role_utility_bar()

with admin_profile_builder_render_scope():
    render_modular_profile_builder()

# Nutritionists are intentionally restricted to this workflow and should not be
# given a navigation control that points to the wider Admin application.
if current_profile_builder_role() in {"admin", "super_admin"}:
    render_page_nav(
        "Meal Profile Builder",
        back_page="pages/10_Admin_Dashboard.py",
        dashboard_page="pages/10_Admin_Dashboard.py",
        show_evaluation=False,
        show_dashboard=True,
        location="bottom",
    )
render_back_to_top()
finish_and_render_page_diagnostics("Recommendation Profile Builder")
