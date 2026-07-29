import streamlit as st

from components import guards, ui_common
from components.admin_scheduling_default_navigation import (
    install_default_scheduling_navigation,
)
from components.admin_scheduling_timezone_selector import (
    install_admin_scheduling_timezone_selector,
)
from components.package_hardening_schedule_ui import (
    install_package_hardening_schedule_ui,
)
import components.schedule_timezone_ui as schedule_timezone_ui


schedule_timezone_ui.require_admin = guards.require_admin
schedule_timezone_ui.require_member = guards.require_member
schedule_timezone_ui.inject_global_styles = ui_common.inject_global_styles
schedule_timezone_ui.apply_luxe_theme = ui_common.apply_luxe_theme
schedule_timezone_ui.utility_logout_bar = ui_common.utility_logout_bar
schedule_timezone_ui.render_back_to_top = ui_common.render_back_to_top
schedule_timezone_ui.topbar = ui_common.topbar
schedule_timezone_ui.render_page_nav = ui_common.render_page_nav

install_admin_scheduling_timezone_selector(schedule_timezone_ui)
install_default_scheduling_navigation(schedule_timezone_ui)
install_package_hardening_schedule_ui(schedule_timezone_ui, admin_page=True)
schedule_timezone_ui.render_admin_scheduling_page()
