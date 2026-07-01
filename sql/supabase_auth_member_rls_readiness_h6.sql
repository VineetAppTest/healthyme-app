-- HealthyMe H6 Supabase Auth member RLS readiness review
-- Review before running. Do not apply blindly in production.
-- Goal: authenticated members can read only their own active member profile/workflow.
-- Admin/service_role access remains unaffected by RLS.

-- 1) Inspect current RLS state
select
  schemaname,
  tablename,
  rowsecurity
from pg_tables
where schemaname = 'public'
  and tablename in ('hm_users', 'hm_workflow')
order by tablename;

-- 2) Inspect existing policies before deciding whether to replace anything
select
  schemaname,
  tablename,
  policyname,
  permissive,
  roles,
  cmd,
  qual,
  with_check
from pg_policies
where schemaname = 'public'
  and tablename in ('hm_users', 'hm_workflow')
order by tablename, policyname;

-- 3) Optional member read-only policies.
-- Run only after confirming these do not conflict with existing policies.
-- alter table public.hm_users enable row level security;
-- alter table public.hm_workflow enable row level security;

-- drop policy if exists hm_users_member_select_self_h6 on public.hm_users;
-- create policy hm_users_member_select_self_h6
-- on public.hm_users
-- for select
-- to authenticated
-- using (
--   role = 'member'
--   and is_active = true
--   and lower(email) = lower(coalesce(auth.jwt() ->> 'email', ''))
-- );

-- drop policy if exists hm_workflow_member_select_self_h6 on public.hm_workflow;
-- create policy hm_workflow_member_select_self_h6
-- on public.hm_workflow
-- for select
-- to authenticated
-- using (
--   exists (
--     select 1
--     from public.hm_users u
--     where u.id = hm_workflow.user_id
--       and u.role = 'member'
--       and u.is_active = true
--       and lower(u.email) = lower(coalesce(auth.jwt() ->> 'email', ''))
--   )
-- );

-- 4) Optional post-check after policies are applied
-- select * from pg_policies
-- where schemaname = 'public'
--   and tablename in ('hm_users', 'hm_workflow')
-- order by tablename, policyname;
