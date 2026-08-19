-- HealthyMe consultation reminder delivery ledger.
--
-- Schedules remain owned by healthyme_app_state. This table records only
-- reminder stages and delivery outcomes so the background worker never needs
-- to rewrite the full application-state JSON blob.

create extension if not exists supabase_vault with schema vault;

create table if not exists public.hm_consultation_reminder_events (
    id uuid primary key default gen_random_uuid(),
    schedule_id text not null,
    member_id text not null default '',
    member_email text not null default '',
    stage text not null check (stage in ('72h_action', '24h_action', '24h_info')),
    scheduled_start_at_utc timestamptz not null,
    subject text not null,
    message text not null,
    details jsonb not null default '{}'::jsonb,
    email_to text not null default '',
    email_status text not null default 'pending'
        check (email_status in (
            'pending', 'sending', 'sent', 'failed', 'suppressed', 'configuration_missing'
        )),
    email_attempt_count integer not null default 0 check (email_attempt_count >= 0),
    email_attempted_at timestamptz,
    email_sent_at timestamptz,
    email_provider text not null default 'Resend',
    email_provider_id text not null default '',
    email_error text not null default '',
    archived_at timestamptz,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (schedule_id, stage)
);

create index if not exists hm_consultation_reminder_events_due_idx
    on public.hm_consultation_reminder_events (email_status, scheduled_start_at_utc);

create index if not exists hm_consultation_reminder_events_member_idx
    on public.hm_consultation_reminder_events (member_id, scheduled_start_at_utc desc);

alter table public.hm_consultation_reminder_events enable row level security;

-- This is an internal service table. The member-facing application reads it
-- only from trusted server code using the backend secret key.
revoke all on table public.hm_consultation_reminder_events from anon, authenticated;
grant select, insert, update on table public.hm_consultation_reminder_events to service_role;

comment on table public.hm_consultation_reminder_events is
    'Idempotent 72h/24h consultation reminder stages and email delivery audit.';

-- Cron invokes the Edge Function with an opaque value stored in Supabase Vault.
-- The Edge Function uses its server-side secret key to call this verifier before
-- doing any work. PUBLIC execution is explicitly removed because this function
-- reads a decrypted Vault value.
create or replace function public.hm_verify_consultation_cron_secret(p_secret text)
returns boolean
language sql
stable
security definer
set search_path = ''
as $$
    select coalesce(
        exists (
            select 1
            from vault.decrypted_secrets
            where name = 'healthyme_consultation_cron_secret'
              and decrypted_secret = coalesce(p_secret, '')
        ),
        false
    );
$$;

revoke all on function public.hm_verify_consultation_cron_secret(text) from public, anon, authenticated;
grant execute on function public.hm_verify_consultation_cron_secret(text) to service_role;

comment on function public.hm_verify_consultation_cron_secret(text) is
    'Internal verifier for the consultation-reminder cron invocation secret.';
