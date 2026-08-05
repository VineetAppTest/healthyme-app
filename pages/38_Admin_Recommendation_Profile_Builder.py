import functools

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


_HIDDEN_BUILD_LABEL = "Full Admin integration build:"
_BUILD_LABEL_SUPPRESSION_MARKER = "_hm_profile_builder_build_label_suppressed"


def _install_build_label_suppression() -> None:
    """Hide the obsolete technical build caption without removing measurement."""

    def should_hide(value: object) -> bool:
        return _HIDDEN_BUILD_LABEL in str(value or "")

    for attribute in ("caption", "markdown", "write"):
        original = getattr(st, attribute, None)
        if not callable(original) or getattr(original, _BUILD_LABEL_SUPPRESSION_MARKER, False):
            continue

        @functools.wraps(original)
        def without_build_label(*args, __original=original, **kwargs):
            body = args[0] if args else kwargs.get("body", kwargs.get("value", ""))
            if should_hide(body):
                return None
            return __original(*args, **kwargs)

        setattr(without_build_label, _BUILD_LABEL_SUPPRESSION_MARKER, True)
        setattr(st, attribute, without_build_label)


# Keep the stable route. Install the meals-only write boundary before importing
# the rebuilt Member Plan Builder so Exercise and Supplement writes remain in
# their independent allocation stores.
install_profile_builder_performance()
install_meal_profile_builder_write_boundary()
from components.profile_builder_modular import render_modular_profile_builder


st.set_page_config(
    page_title="Member Plan Builder",
    page_icon="💚",
    layout="wide",
    initial_sidebar_state="collapsed",
)
begin_page_measurement("Recommendation Profile Builder")
_install_build_label_suppression()
inject_global_styles()
apply_luxe_theme()
require_profile_builder_access()
profile_builder_role_utility_bar()

with admin_profile_builder_render_scope():
    render_modular_profile_builder()

if current_profile_builder_role() in {"admin", "super_admin"}:
    render_page_nav(
        "Member Plan Builder",
        back_page="pages/10_Admin_Dashboard.py",
        dashboard_page="pages/10_Admin_Dashboard.py",
        show_evaluation=False,
        show_dashboard=True,
        location="bottom",
    )
render_back_to_top()
finish_and_render_page_diagnostics("Recommendation Profile Builder")
