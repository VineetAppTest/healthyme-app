import streamlit as st

from components.guards import require_admin
from components.performance_diagnostics import (
    clear_measurement_history,
    measurement_enabled,
    render_history_workspace,
    set_measurement_enabled,
)
from components.ui_common import (
    apply_luxe_theme,
    inject_global_styles,
    render_page_nav,
    topbar,
    utility_logout_bar,
)


st.set_page_config(
    page_title="Performance Diagnostics",
    page_icon="⏱️",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_global_styles()
apply_luxe_theme()
require_admin()
utility_logout_bar()

topbar(
    "Performance Diagnostics",
    "Temporary measurement workspace for page render, state access and Supabase timing.",
    "Measurement-only build",
)

st.warning(
    "This workspace measures timing and record counts only. It does not capture passwords, "
    "health responses, message text, notes or email content. Measurements are retained only "
    "inside this browser session and disappear when the session is cleared."
)

left, middle, right = st.columns(3, gap="medium")
with left:
    if st.button(
        "Start measurement",
        type="primary" if not measurement_enabled() else "secondary",
        use_container_width=True,
        key="hm_perf_enable",
    ):
        set_measurement_enabled(True)
        st.success("Measurement is enabled for this browser session.")
        st.rerun()
with middle:
    if st.button(
        "Pause measurement",
        use_container_width=True,
        key="hm_perf_disable",
    ):
        set_measurement_enabled(False)
        st.info("Measurement is paused. Existing measurements remain available.")
        st.rerun()
with right:
    if st.button(
        "Clear measurements",
        use_container_width=True,
        key="hm_perf_clear",
    ):
        clear_measurement_history()
        st.success("Measurement history cleared.")
        st.rerun()

if measurement_enabled():
    st.success(
        "Measurement is active. Open the target HealthyMe pages in this same browser tab/session, "
        "perform the guided journey and return here to compare the runs."
    )
else:
    st.info(
        "Measurement is paused. Select Start measurement before beginning the recorded journey."
    )

with st.expander("How to use this temporary build", expanded=True):
    st.markdown(
        """
1. Select **Start measurement**.
2. Open Admin Dashboard, Scheduling, Packages, Recommendation Profile Builder, Messages and Daily Logs.
3. Change one selector or workspace control at a time and wait until the page becomes usable.
4. Return here after the journey.
5. Review the page table, inspect slow runs and download the JSON file for analysis.
6. For the Member journey, append `?perf=1` to the Member Home URL once. The measurement flag then remains active in that browser session.

A high `load_db` count can indicate repeated full application-state access. A high Supabase-read count or a slow package RPC highlights backend work. A large page-render time with little backend time usually points to excessive UI construction, records rendered or full-page reruns.
"""
    )

render_history_workspace()

render_page_nav(
    "Performance Diagnostics",
    back_page="pages/10_Admin_Dashboard.py",
    dashboard_page="pages/10_Admin_Dashboard.py",
    show_evaluation=False,
    show_dashboard=True,
    location="bottom",
)
