"""HealthyMe shared components package."""

from components.login_expiry_recovery import install_login_expiry_recovery
from components.package_hardening_bootstrap import install_package_hardening
from components.member_email_bootstrap import install_member_email_notifications
from components.member_email_followups import install_member_email_followups
from components.member_email_legacy_reminders import (
    install_legacy_schedule_reminder_delivery,
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
