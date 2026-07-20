-- H13C: Durable Supabase-backed Streamlit refresh sessions
-- Run once in the Supabase SQL Editor before deploying the H13C Streamlit code.
-- Idempotent: safe to run again.

begin;

create extension if not exists pgcrypto;

create table if not exists public.hm_streamlit_auth_sessions (
    id uuid primary key default gen_random_uuid(),
    marker_hash text not null unique,
    user_email text not null,
    auth_user_id text,
    app_role text,
    app_user_snapshot jsonb not null default '{}'::jsonb,
    access_token text,
    refresh_token text,
    token_expires_at bigint,
    expires_at timestamptz not null,
    revoked_at timestamptz,
    role_checked_at timestamptz,
    last_seen_at timestamptz not null default now(),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    metadata jsonb not null default '{}'::jsonb,
    constraint hm_streamlit_auth_sessions_marker_hash_len
        check (length(marker_hash) = 64),
    constraint hm_streamlit_auth_sessions_active_tokens
        check (
            revoked_at is not null
            or (
                coalesce(access_token, '') <> ''
                and coalesce(refresh_token, '') <> ''
            )
        ),
    constraint hm_streamlit_auth_sessions_expiry_order
        check (expires_at > created_at)
);

comment on table public.hm_streamlit_auth_sessions is
'Server-side session registry for HealthyMe Streamlit Supabase authentication. '
'The browser stores only a random opaque marker; this table stores only its SHA-256 hash.';

comment on column public.hm_streamlit_auth_sessions.marker_hash is
'SHA-256 hash of the opaque browser marker. The raw marker is never stored in Supabase.';

alter table public.hm_streamlit_auth_sessions enable row level security;
alter table public.hm_streamlit_auth_sessions force row level security;

-- No anon/authenticated policies are created. The Streamlit server accesses this
-- table only with SUPABASE_SERVICE_ROLE_KEY.
revoke all on table public.hm_streamlit_auth_sessions from public;
revoke all on table public.hm_streamlit_auth_sessions from anon;
revoke all on table public.hm_streamlit_auth_sessions from authenticated;
grant select, insert, update, delete on table public.hm_streamlit_auth_sessions to service_role;

create index if not exists idx_hm_streamlit_auth_sessions_active_expiry
    on public.hm_streamlit_auth_sessions (expires_at)
    where revoked_at is null;

create index if not exists idx_hm_streamlit_auth_sessions_user_email
    on public.hm_streamlit_auth_sessions (lower(user_email), created_at desc);

create index if not exists idx_hm_streamlit_auth_sessions_last_seen
    on public.hm_streamlit_auth_sessions (last_seen_at);

create or replace function public.hm_set_streamlit_auth_session_updated_at()
returns trigger
language plpgsql
security invoker
set search_path = public, pg_temp
as $$
begin
    new.updated_at := now();
    return new;
end;
$$;

drop trigger if exists trg_hm_streamlit_auth_sessions_updated_at
    on public.hm_streamlit_auth_sessions;

create trigger trg_hm_streamlit_auth_sessions_updated_at
before update on public.hm_streamlit_auth_sessions
for each row
execute function public.hm_set_streamlit_auth_session_updated_at();

create or replace function public.hm_cleanup_streamlit_auth_sessions(
    p_retention_days integer default 7
)
returns bigint
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
    v_deleted bigint := 0;
    v_retention interval;
begin
    v_retention := make_interval(days => greatest(coalesce(p_retention_days, 7), 1));

    delete from public.hm_streamlit_auth_sessions
    where
        (
            revoked_at is not null
            and revoked_at < now() - v_retention
        )
        or (
            expires_at < now() - v_retention
        );

    get diagnostics v_deleted = row_count;
    return v_deleted;
end;
$$;

revoke all on function public.hm_cleanup_streamlit_auth_sessions(integer) from public;
revoke all on function public.hm_cleanup_streamlit_auth_sessions(integer) from anon;
revoke all on function public.hm_cleanup_streamlit_auth_sessions(integer) from authenticated;
grant execute on function public.hm_cleanup_streamlit_auth_sessions(integer) to service_role;

commit;

-- Verification queries (read-only; run manually after the migration if required):
--
-- select
--     count(*) as session_rows,
--     count(*) filter (where revoked_at is null and expires_at > now()) as active_rows
-- from public.hm_streamlit_auth_sessions;
--
-- select grantee, privilege_type
-- from information_schema.role_table_grants
-- where table_schema = 'public'
--   and table_name = 'hm_streamlit_auth_sessions'
-- order by grantee, privilege_type;
