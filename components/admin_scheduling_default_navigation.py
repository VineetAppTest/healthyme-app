from __future__ import annotations

import streamlit as st

from components.admin_scheduling_timezone_selector import (
    _TIMEZONE_SELECTION_READY_KEY,
)


def install_default_scheduling_navigation(schedule_timezone_ui) -> None:
    """Keep the Admin Dashboard return control visible before timezone selection."""

    if getattr(
        schedule_timezone_ui,
        "_hm_default_scheduling_navigation_installed",
        False,
    ):
        return
    schedule_timezone_ui._hm_default_scheduling_navigation_installed = True
    base_radio = schedule_timezone_ui.st.radio

    def radio_with_default_back_navigation(label, options, *args, **kwargs):
        if (
            label == "Enter the schedule in"
            and not st.session_state.get(_TIMEZONE_SELECTION_READY_KEY, False)
        ):
            st.info(
                "Search by city, country or timezone and confirm a city-based timezone to continue."
            )
            schedule_timezone_ui.render_page_nav(
                "Scheduling",
                back_page="pages/10_Admin_Dashboard.py",
                dashboard_page="pages/10_Admin_Dashboard.py",
                show_evaluation=False,
                show_dashboard=True,
                location="bottom",
            )
            schedule_timezone_ui.render_back_to_top()
            st.stop()
        return base_radio(label, options, *args, **kwargs)

    st.radio = radio_with_default_back_navigation
    schedule_timezone_ui.st.radio = radio_with_default_back_navigation
