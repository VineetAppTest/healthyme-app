-- Keep the reminder delivery ledger aligned with the zero-cost Gmail transport
-- used by the deployed consultation-reminders Edge Function.

alter table public.hm_consultation_reminder_events
  alter column email_provider set default 'Gmail SMTP';
