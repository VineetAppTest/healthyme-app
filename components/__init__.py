"""HealthyMe shared components package."""

from components.streamlit_toolbar_cleanup import install_streamlit_toolbar_cleanup
from components.file_uploader_presentation import install_file_uploader_presentation
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
from components.auth_provisioning_form_hygiene import (
    install_auth_provisioning_form_hygiene,
)


# Install first so every route, including the root OAuth callback, receives the
# presentation-only toolbar cleanup immediately after its own page configuration.
install_streamlit_toolbar_cleanup()

# Restore Streamlit's Material upload icon after HealthyMe's global font rules while
# preserving the original uploader values, callbacks and file objects.
install_file_uploader_presentation()

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

# Measurement instrumentation observes the final production callables without changing
# authentication, routing or business logic.
install_backend_measurement()
install_page_boundary_measurement()
install_performance_measurement_gate()

# Apply the final production Member shell and retire temporary diagnostics panels.
install_member_post_optimization_cleanup()

# Install Admin isolation before the final Member page-specific wrappers. This keeps
# inactive Admin sections silent while allowing Member wrappers to see the true page
# caller rather than an intermediate Admin wrapper frame.
install_admin_content_form_cleanup()

# Nutritionist Notes and Supplement Add use success-versioned form identities. Failed
# validation/save attempts retain work; confirmed creates start a clean transaction while
# preserving the selected member. No write, auth or routing function is replaced.
install_notes_supplement_form_hygiene()

# Supabase provisioning forms retain dry-run and failed/partial entries. Only a confirmed
# live completion advances the relevant form identity and redisplays its existing result.
# The wrapped provisioning functions retain their original arguments, result and writes.
install_auth_provisioning_form_hygiene()

# Keep Saved Days filters visible, show meal-only history without loading the form and
# suppress only the Member Home KPI strip.
install_member_saved_days_home_cleanup()

# Route Member Home messages and schedule into real Streamlit columns rather than CSS
# floats so both sections remain adjacent on desktop and stack safely on mobile.
install_member_home_side_by_side_runtime()

# Keep the Saved Days button/heading dispatch outermost so its page frame remains visible
# after the Member Home and Admin Streamlit wrappers are installed.
install_member_saved_days_dispatch_runtime()
