"""HealthyMe shared components package."""

from components.login_expiry_recovery import install_login_expiry_recovery
from components.package_hardening_bootstrap import install_package_hardening
from components.member_email_bootstrap import install_member_email_notifications
from components.member_email_followups import install_member_email_followups
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
from components.admin_content_form_cleanup import (
    install_admin_content_form_cleanup,
)


# Expired authorization recovery is installed before app.py captures the accepted
# authorizer callable. It changes only the dead-end expired-request presentation.
install_login_expiry_recovery()

# Package hardening must wrap the canonical package/schedule functions before the
# accepted member-email layer captures those callables.
install_package_hardening()
install_member_email_notifications()
install_member_email_followups()
install_legacy_schedule_reminder_delivery()

# Member Home presents only still-open future meeting cards. The wrapper changes
# ordering/visibility only; schedule status and package consumption remain untouched.
install_member_home_schedule_presentation()

# Daily Log and the standalone Member Exercise route share one editable table renderer.
# Member changes are written only to that day's exercise log, never to the source profile.
install_member_exercise_journal_table()

# Member Home already renders scheduling in its dedicated Upcoming Schedule area.
# Remove only the repeated scheduling cards from the generic message feed; stored
# records, audit history and email delivery remain unchanged.
install_member_message_display_cleanup()

# Measurement instrumentation is installed last so it observes the final production
# callables without changing authentication, routing or business logic. Measurements
# remain in Streamlit session state; a Member can download the sanitized JSON directly
# before logout, so no diagnostic evidence is stored in HealthyMe application data.
install_backend_measurement()
install_page_boundary_measurement()
install_performance_measurement_gate()

# The performance correction is complete. Apply the final production Member shell,
# working Other Fluid time field and remove temporary diagnostics panels.
install_member_post_optimization_cleanup()

# Replace Saved Days loading with a seven-day meal-only summary, remove the Member Home
# KPI strip and balance Messages with Upcoming Schedule without changing stored data.
install_member_saved_days_home_cleanup()

# Stabilize Admin Recipe/Exercise sections, hide legacy Feedback/Allocation surfaces and
# retain success messages while safely resetting transient content-manager form state.
install_admin_content_form_cleanup()
