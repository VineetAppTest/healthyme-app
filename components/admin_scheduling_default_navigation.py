from __future__ import annotations

import streamlit as st

from components.admin_scheduling_timezone_selector import (
    _TIMEZONE_SELECTION_READY_KEY,
)


def install_default_scheduling_navigation(schedule_timezone_ui) -> None:
    """Keep Back and Admin Dashboard controls visible before all page gates."""

    if getattr(
        schedule_timezone_ui,
        "_hm_default_scheduling_navigation_installed",
        False,
    ):
        return
    schedule_timezone_ui._hm_default_scheduling_navigation_installed = True

    base_topbar = schedule_timezone_ui.topbar
    base_radio = schedule_timezone_ui.st.radio

    def topbar_with_visible_navigation(*args, **kwargs):
        result = base_topbar(*args, **kwargs)
        schedule_timezone_ui.render_page_nav(
            "Scheduling",
            back_page="pages/10_Admin_Dashboard.py",
            dashboard_page="pages/10_Admin_Dashboard.py",
            show_evaluation=False,
            show_dashboard=True,
            location="top",
        )
        return result

    def radio_with_default_back_navigation(label, options, *args, **kwargs):
        if (
            label == "Enter the schedule in"
            and not st.session_state.get(_TIMEZONE_SELECTION_READY_KEY, False)
        ):
            st.info(
                "Select a practitioner timezone to continue with scheduling."
            )
            st.stop()
        return base_radio(label, options, *args, **kwargs)

    schedule_timezone_ui.topbar = topbar_with_visible_navigation
    st.radio = radio_with_default_back_navigation
    schedule_timezone_ui.st.radio = radio_with_default_back_navigation
