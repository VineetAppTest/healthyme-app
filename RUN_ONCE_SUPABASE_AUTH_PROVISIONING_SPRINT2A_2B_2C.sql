-- HealthyMe Streamlit Admin - Supabase Auth Provisioning Sprint 2A + 2B + 2C
-- Run once in Supabase SQL Editor before using the Streamlit provisioning page.
-- Purpose:
-- 1) Ensure hm_users has a durable auth_user_id link to auth.users.id.
-- 2) Add migration metadata columns used by admin provisioning.
-- 3) Create a server-side provisioning audit table.
-- 4) Keep this compatible with the Flutter Sprint 1B + 1C auth_user_id model.
--
-- Safety:
-- - This does not remove Auth0.
-- - This does not change Streamlit admin login.
-- - This does not expose service_role access to Flutter.
-- - Provisioning actions must be executed only from trusted Streamlit/admin/server-side code.

alter table public.hm_users
add column if not exists auth_user_id uuid references auth.users(id) on delete set null;

alter table public.hm_users
add column if not exists auth_migrated_at timestamptz;

alter table public.hm_users
add column if not exists auth_provider text;

create unique index if not exists hm_users_auth_user_id_unique_idx
on public.hm_users(auth_user_id)
where auth_user_id is not null;

create index if not exists hm_users_lower_email_idx
on public.hm_users(lower(email));

create table if not exists public.hm_supabase_auth_provisioning_audit (
  id bigserial primary key,
  created_at timestamptz not null default now(),
  action text not null,
  status text not null,
  member_id text,
  member_email text,
  auth_user_id uuid,
  actor_email text,
  message text,
  metadata jsonb not null default '{}'::jsonb
);

create index if not exists idx_hm_supabase_auth_provisioning_audit_created_at
on public.hm_supabase_auth_provisioning_audit(created_at desc);

create index if not exists idx_hm_supabase_auth_provisioning_audit_member_email
on public.hm_supabase_auth_provisioning_audit(lower(member_email));

create index if not exists idx_hm_supabase_auth_provisioning_audit_action_status
on public.hm_supabase_auth_provisioning_audit(action, status);

alter table public.hm_supabase_auth_provisioning_audit enable row level security;

-- Client-side users should not read audit history. Streamlit service_role bypasses RLS.
do $$
begin
  if not exists (
    select 1
    from pg_policies
    where schemaname = 'public'
      and tablename = 'hm_supabase_auth_provisioning_audit'
      and policyname = 'hm_supabase_auth_provisioning_audit_no_client_access'
  ) then
    create policy hm_supabase_auth_provisioning_audit_no_client_access
    on public.hm_supabase_auth_provisioning_audit
    for all
    to authenticated
    using (false)
    with check (false);
  end if;
end $$;

-- Optional compatibility backfill: link existing hm_users rows to existing Supabase Auth users by exact lower(email).
-- This is safe to re-run and only fills blank auth_user_id.
update public.hm_users u
set auth_user_id = au.id,
    auth_provider = coalesce(nullif(u.auth_provider, ''), 'supabase'),
    auth_migrated_at = coalesce(u.auth_migrated_at, now())
from auth.users au
where lower(u.email) = lower(au.email)
  and u.auth_user_id is null
  and u.is_active = true
  and lower(coalesce(u.role, '')) = 'member';

-- Verification summary after run.
select
  (select count(*) from public.hm_users where lower(coalesce(role, '')) = 'member') as member_rows,
  (select count(*) from public.hm_users where lower(coalesce(role, '')) = 'member' and is_active = true) as active_member_rows,
  (select count(*) from public.hm_users where lower(coalesce(role, '')) = 'member' and auth_user_id is not null) as linked_member_rows,
  (select count(*) from public.hm_supabase_auth_provisioning_audit) as provisioning_audit_rows;
