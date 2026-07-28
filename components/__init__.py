"""HealthyMe shared components package."""

from components.package_hardening_bootstrap import install_package_hardening
from components.member_email_bootstrap import install_member_email_notifications
from components.member_email_followups import install_member_email_followups
from components.member_email_legacy_reminders import (
    install_legacy_schedule_reminder_delivery,
)


# Package hardening must wrap the canonical package/schedule functions before the
# accepted member-email layer captures those callables. Authentication and routing
# are intentionally untouched.
install_package_hardening()
install_member_email_notifications()
install_member_email_followups()
install_legacy_schedule_reminder_delivery()
