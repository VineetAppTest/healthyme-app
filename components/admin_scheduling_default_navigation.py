from __future__ import annotations

import streamlit as st


_SELECTION_READY_KEY = "hm_tz_practitioner_timezone_selection_ready"


def install_admin_scheduling_default_navigation(schedule_timezone_ui) -> None:
    """Render the Scheduling page navigation before the required-timezone stop."""

    if getattr(st, "_hm_admin_scheduling_default_navigation_installed", False):
        return
    st._hm_admin_scheduling_default_navigation_installed = True

    base_radio = st.radio

    def radio_with_default_navigation(label, options, *args, **kwargs):
        if (
            str(label or "") == "Enter the schedule in"
            and not st.session_state.get(_SELECTION_READY_KEY, False)
        ):
            schedule_timezone_ui.render_page_nav(
                "Scheduling",
                back_page="pages/10_Admin_Dashboard.py",
                dashboard_page="pages/10_Admin_Dashboard.py",
                show_evaluation=False,
                show_dashboard=True,
                location="bottom",
            )
        return base_radio(label, options, *args, **kwargs)

    st.radio = radio_with_default_navigation
    schedule_timezone_ui.st.radio = radio_with_default_navigation
