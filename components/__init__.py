"""HealthyMe shared components package."""

from components.streamlit_toolbar_cleanup import install_streamlit_toolbar_cleanup
from components.file_uploader_presentation import install_file_uploader_presentation
from components.login_expiry_recovery import install_login_expiry_recovery
from components.package_hardening_bootstrap import install_package_hardening
from components.member_email_bootstrap import install_member_email_notifications
from components.member_email_followups import install_member_email_followups
from components.member_allocation_notifications import (
    install_member_allocation_notifications,
)
from components.member_email_legacy_reminders import (
    install_legacy_schedule_reminder_delivery,
)
from components.member_message_display_cleanup import (
    install_member_message_display_cleanup,
)
from components.member_home_schedule_presentation import (
    install_member_home_schedule_presentation,
)
from components.member_exercise_journal_table_bootstrap import (
    install_member_exercise_journal_table,
)
from components.exercise_saved_days_readonly_runtime import (
    install_exercise_saved_days_readonly_runtime,
)
from components.performance_diagnostics import (
    install_backend_measurement,
    install_page_boundary_measurement,
)
from components.performance_measurement_gate import (
    install_performance_measurement_gate,
)
from components.member_post_optimization_cleanup import (
    install_member_post_optimization_cleanup,
)
from components.member_saved_days_home_cleanup import (
    install_member_saved_days_home_cleanup,
)
from components.member_home_side_by_side_runtime import (
    install_member_home_side_by_side_runtime,
)
from components.member_saved_days_dispatch_runtime import (
    install_member_saved_days_dispatch_runtime,
)
from components.admin_content_form_cleanup import (
    install_admin_content_form_cleanup,
)
from components.notes_supplement_form_hygiene import (
    install_notes_supplement_form_hygiene,
)
from components.repository_create_form_success import (
    install_repository_create_form_success,
)
from components.auth_provisioning_form_hygiene import (
    install_auth_provisioning_form_hygiene,
)
from components.recommendations_share_form_hygiene import (
    install_recommendations_share_form_hygiene,
)
from components.admin_exercise_repair_runtime import (
    install_admin_exercise_repair_runtime,
)
from components.member_daily_log_native_tab_persistence import (
    install_member_daily_log_native_tab_persistence,
)
from components.daily_log_widget_route_preservation import (
    install_daily_log_widget_route_preservation,
)
from components.member_home_global_header_runtime import (
    install_member_home_global_header_runtime,
)
from components.repository_layout_correction_runtime import (
    install_repository_layout_correction_runtime,
)
from components.repository_exclusive_tabs_runtime import (
    install_repository_exclusive_tabs_runtime,
)
from components.repository_disclosure_fallback_cleanup import (
    install_repository_disclosure_fallback_cleanup,
)


install_streamlit_toolbar_cleanup()
install_file_uploader_presentation()
install_login_expiry_recovery()
install_package_hardening()
install_member_email_notifications()
install_member_email_followups()
install_member_allocation_notifications()
install_legacy_schedule_reminder_delivery()
install_member_home_schedule_presentation()

# Retain the accepted Exercise Journal table and Food Journal widget corrections.
install_member_exercise_journal_table()
# Exercise history follows the Food Journal saved-days pattern: filtered, read-only
# rows below the form. Historical dates must never replace the active form date.
install_exercise_saved_days_readonly_runtime()

install_member_message_display_cleanup()
install_backend_measurement()
install_page_boundary_measurement()
install_performance_measurement_gate()
install_member_post_optimization_cleanup()
install_admin_content_form_cleanup()
install_notes_supplement_form_hygiene()
# Repository create forms clear only after a confirmed save and surface the success
# message next to the save action. Failed saves retain the entered information.
install_repository_create_form_success()
install_auth_provisioning_form_hygiene()
install_recommendations_share_form_hygiene()
install_member_saved_days_home_cleanup()
install_member_home_side_by_side_runtime()
install_member_saved_days_dispatch_runtime()

# Final page-specific repairs are deliberately outermost. Admin Exercise keeps the
# accepted hidden-section selector while receiving deterministic post-rerun success.
# Daily Log intercepts only the exact Food/Exercise pair, installs renderer gates in
# pages/18_Daily_Log.py, and executes only the selected journal. It does not call
# Streamlit tabs or rely on browser-side tab restoration.
install_admin_exercise_repair_runtime()
install_member_daily_log_native_tab_persistence()

# Streamlit widget changes rerun internally and bypass the explicit st.rerun wrapper
# in app.py. Install this last so every accepted Daily Log widget wrapper composes a
# route-preservation callback without affecting Back or Dashboard navigation.
install_daily_log_widget_route_preservation()

# Member Home has a page-specific profile control, but its row must follow the same
# compact height and hero spacing as the global header used elsewhere.
install_member_home_global_header_runtime()

# Repository presentation is page-scoped and outermost so it can override legacy
# card widths, native disclosure markers and form spacing without changing writes.
install_repository_layout_correction_runtime()

# Repository Current/Add selection must be exclusive. Install after presentation so
# the active section inherits the accepted styles while the inactive section performs
# no widget rendering and skips its repository read.
install_repository_exclusive_tabs_runtime()

# Streamlit can render its hidden material-icon ligature as keyboard_arrow text on
# mobile. Keep the accepted circular + / minus marker and suppress only that fallback.
install_repository_disclosure_fallback_cleanup()
