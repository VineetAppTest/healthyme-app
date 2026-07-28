"""HealthyMe shared components package."""

from components.member_email_bootstrap import install_member_email_notifications
from components.member_email_followups import install_member_email_followups
from components.member_email_legacy_reminders import (
    install_legacy_schedule_reminder_delivery,
)


install_member_email_notifications()
install_member_email_followups()
install_legacy_schedule_reminder_delivery()
