-- HealthyMe Supabase PostgreSQL setup
-- Run this once in Supabase Dashboard > SQL Editor.

create table if not exists public.healthyme_app_state (
    id text primary key,
    data jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create or replace function public.set_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

drop trigger if exists set_healthyme_app_state_updated_at on public.healthyme_app_state;

create trigger set_healthyme_app_state_updated_at
before update on public.healthyme_app_state
for each row
execute function public.set_updated_at();

-- Recommended for this MVP:
-- Keep Row Level Security enabled and use SUPABASE_SERVICE_ROLE_KEY in Streamlit Secrets.
alter table public.healthyme_app_state enable row level security;

-- No public policies are created intentionally.
-- Server-side app access should use the service role key from Streamlit Secrets.

-- Optional future performance table for normalized sessions.
-- The current optimized MVP keeps app state in healthyme_app_state JSONB with per-session cache.
-- In a future enterprise version, these tables can be used to reduce JSONB read/write size further.
create table if not exists public.healthyme_login_sessions (
    token text primary key,
    user_id text not null,
    active boolean not null default true,
    created_at timestamptz not null default now(),
    last_seen_at timestamptz
);

create index if not exists idx_healthyme_login_sessions_user_id
on public.healthyme_login_sessions(user_id);

create table if not exists public.healthyme_audit_events (
    id bigserial primary key,
    event_ts timestamptz not null default now(),
    actor_user_id text,
    member_user_id text,
    event_type text not null,
    payload jsonb not null default '{}'::jsonb
);

create index if not exists idx_healthyme_audit_events_member
on public.healthyme_audit_events(member_user_id, event_ts desc);
