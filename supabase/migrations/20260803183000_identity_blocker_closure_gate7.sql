-- HealthyMe Users/Workflow Gate 7
-- Close active-member Auth email fallback, remove shared Workflow read fallback,
-- and harden direct Flutter identity table access.

-- Link the sole active member without auth_user_id only when the Auth match is
-- exact, unique and conflict-free. The existing Gate 4 contract commits the
-- canonical User and shared rollback projection atomically and records events.
do $block$
declare
  v_missing_count integer;
  v_match_count integer;
  v_conflict_count integer;
  v_shared_count integer;
  v_member_id text;
  v_auth_user_id uuid;
  v_migrated_at timestamptz := transaction_timestamp();
  v_state jsonb;
  v_projected_users jsonb;
  v_response jsonb;
begin
  select count(*) into v_missing_count
  from public.hm_users
  where role = 'member' and is_active and auth_user_id is null;

  if v_missing_count > 1 then
    raise exception 'Gate 7 requires at most one active member without auth_user_id; found %.', v_missing_count;
  elsif v_missing_count = 1 then
    select count(*) into v_match_count
    from public.hm_users u
    join auth.users a on lower(btrim(a.email)) = lower(btrim(u.email))
    where u.role = 'member' and u.is_active and u.auth_user_id is null;

    if v_match_count <> 1 then
      raise exception 'Gate 7 requires one exact unique Auth email match; found %.', v_match_count;
    end if;

    select u.id, a.id into v_member_id, v_auth_user_id
    from public.hm_users u
    join auth.users a on lower(btrim(a.email)) = lower(btrim(u.email))
    where u.role = 'member' and u.is_active and u.auth_user_id is null
    limit 1;

    select count(*) into v_conflict_count
    from public.hm_users
    where auth_user_id = v_auth_user_id and id <> v_member_id;

    if v_conflict_count <> 0 then
      raise exception 'Gate 7 Auth user is already linked to a different HealthyMe user.';
    end if;

    select data into v_state
    from public.healthyme_app_state
    where id = 'healthyme_app_state_v1';

    select count(*) into v_shared_count
    from jsonb_array_elements(coalesce(v_state->'users', '[]'::jsonb)) item
    where item->>'id' = v_member_id;

    if v_shared_count <> 1 then
      raise exception 'Gate 7 requires exactly one shared User projection for the candidate; found %.', v_shared_count;
    end if;

    select jsonb_agg(
      case when item->>'id' = v_member_id then
        item || jsonb_build_object(
          'auth_provider', 'supabase',
          'auth_user_id', v_auth_user_id::text,
          'auth_migrated_at', v_migrated_at::text
        )
      else item end
      order by ordinality
    ) into v_projected_users
    from jsonb_array_elements(coalesce(v_state->'users', '[]'::jsonb))
      with ordinality as x(item, ordinality);

    v_state := jsonb_set(v_state, '{users}', v_projected_users, true);

    v_response := public.hm_admin_commit_identity_and_state(
      'identity-gate7-auth-link',
      'healthyme_app_state_v1',
      v_state,
      jsonb_build_array(jsonb_build_object(
        'user_id', v_member_id,
        'patch', jsonb_build_object(
          'auth_provider', 'supabase',
          'auth_user_id', v_auth_user_id::text,
          'auth_migrated_at', v_migrated_at::text
        )
      )),
      '[]'::jsonb,
      null,
      null,
      'identity_gate7_auth_link',
      jsonb_build_object('gate', 7, 'exact_unique_auth_match', true)
    );

    if not coalesce((v_response->>'ok')::boolean, false) then
      raise exception 'Gate 7 canonical identity commit failed.';
    end if;
  end if;
end;
$block$;

-- Authenticated Flutter identity resolution is now auth_user_id-only.
create or replace function public.hm_flutter_current_member_id()
returns text
language plpgsql
security definer
set search_path = ''
as $function$
declare
  v_auth_user_id uuid := auth.uid();
  v_member_id text;
begin
  if v_auth_user_id is null then
    raise exception using
      errcode = '28000',
      message = 'No Supabase Auth user was found in the current request.';
  end if;

  select u.id::text
    into v_member_id
  from public.hm_users u
  where lower(coalesce(u.role, '')) = 'member'
    and u.is_active is true
    and u.auth_user_id = v_auth_user_id
  limit 1;

  if v_member_id is null then
    raise exception using
      errcode = '42501',
      message = 'Current login is not linked by Auth user ID to an active HealthyMe member profile.';
  end if;

  return v_member_id;
end;
$function$;

-- LAF responses remain in shared state, but Workflow must exist canonically.
create or replace function public.hm_flutter_get_laf()
returns jsonb
language plpgsql
security definer
set search_path = ''
as $function$
declare
  v_user_id text := public.hm_flutter_current_member_id();
  v_state jsonb;
  v_responses jsonb;
  v_workflow jsonb;
begin
  select data into v_state
  from public.healthyme_app_state
  where id = 'healthyme_app_state_v1';

  v_state := coalesce(v_state, '{}'::jsonb);
  v_responses := coalesce(v_state #> array['laf_responses', v_user_id], '{}'::jsonb);

  select jsonb_build_object(
    'laf_completed', coalesce(w.laf_completed, false),
    'nsp1_completed', coalesce(w.nsp1_completed, false),
    'nsp2_completed', coalesce(w.nsp2_completed, false),
    'submitted_for_review', coalesce(w.submitted_for_review, false),
    'admin_completed', coalesce(w.admin_completed, false),
    'final_report_ready', coalesce(w.final_report_ready, false),
    'workflow_status', coalesce(w.workflow_status, 'not_started')
  ) into v_workflow
  from public.hm_workflow w
  where w.user_id = v_user_id;

  if v_workflow is null then
    raise exception using
      errcode = 'P0002',
      message = 'Canonical Workflow is missing for the current HealthyMe member.';
  end if;

  return jsonb_build_object(
    'member_id', v_user_id,
    'responses', v_responses,
    'workflow', v_workflow
  );
end;
$function$;

-- NSP responses remain in shared state, but all lifecycle fields come from
-- canonical hm_workflow with no shared Workflow fallback.
create or replace function public.hm_flutter_get_nsp()
returns jsonb
language plpgsql
security definer
set search_path = ''
as $function$
declare
  v_member_id text := public.hm_flutter_current_member_id();
  v_data jsonb;
  v_workflow public.hm_workflow%rowtype;
begin
  select public.hm_flutter_ensure_app_state_shape(s.data)
    into v_data
  from public.healthyme_app_state s
  where s.id = 'healthyme_app_state_v1';

  if v_data is null then
    v_data := public.hm_flutter_ensure_app_state_shape('{}'::jsonb);
  end if;

  select w.* into v_workflow
  from public.hm_workflow w
  where w.user_id = v_member_id
  limit 1;

  if not found then
    raise exception using
      errcode = 'P0002',
      message = 'Canonical Workflow is missing for the current HealthyMe member.';
  end if;

  return jsonb_build_object(
    'member_id', v_member_id,
    'nsp1_responses', coalesce(v_data #> array['nsp1_responses', v_member_id], '{}'::jsonb),
    'nsp2_responses', coalesce(v_data #> array['nsp2_responses', v_member_id], '{}'::jsonb),
    'workflow', jsonb_build_object(
      'laf_completed', coalesce(v_workflow.laf_completed, false),
      'nsp1_completed', coalesce(v_workflow.nsp1_completed, false),
      'nsp2_completed', coalesce(v_workflow.nsp2_completed, false),
      'submitted_for_review', coalesce(v_workflow.submitted_for_review, false),
      'admin_completed', coalesce(v_workflow.admin_completed, false),
      'final_report_ready', coalesce(v_workflow.final_report_ready, false),
      'workflow_status', coalesce(v_workflow.workflow_status, 'not_started')
    ),
    'can_open_nsp1', coalesce(v_workflow.laf_completed, false),
    'can_open_nsp2', coalesce(v_workflow.laf_completed, false)
      and coalesce(v_workflow.nsp1_completed, false),
    'can_submit_review', coalesce(v_workflow.laf_completed, false)
      and coalesce(v_workflow.nsp1_completed, false)
      and coalesce(v_workflow.nsp2_completed, false)
  );
end;
$function$;

revoke execute on function public.hm_flutter_current_member_id() from public, anon;
revoke execute on function public.hm_flutter_get_laf() from public, anon;
revoke execute on function public.hm_flutter_get_nsp() from public, anon;
grant execute on function public.hm_flutter_current_member_id() to authenticated, service_role;
grant execute on function public.hm_flutter_get_laf() to authenticated, service_role;
grant execute on function public.hm_flutter_get_nsp() to authenticated, service_role;

-- Consolidate three email-based User read policies into one Auth-ID policy.
drop policy if exists flutter_member_read_own_hm_users on public.hm_users;
drop policy if exists hm_users_member_select_self on public.hm_users;
drop policy if exists hm_users_member_select_self_auth_id_or_email on public.hm_users;
create policy hm_users_member_select_self_auth_user_id
on public.hm_users
for select
to authenticated
using (
  lower(coalesce(role, '')) = 'member'
  and is_active is true
  and auth_user_id = (select auth.uid())
);

-- Consolidate Workflow read policies and retire obsolete direct client writes.
drop policy if exists flutter_member_read_own_hm_workflow on public.hm_workflow;
drop policy if exists hm_workflow_member_select_self on public.hm_workflow;
drop policy if exists hm_workflow_member_select_self_auth_id_or_email on public.hm_workflow;
drop policy if exists flutter_member_insert_own_hm_workflow on public.hm_workflow;
drop policy if exists flutter_member_update_own_hm_workflow on public.hm_workflow;
create policy hm_workflow_member_select_self_auth_user_id
on public.hm_workflow
for select
to authenticated
using (
  exists (
    select 1 from public.hm_users u
    where u.id = hm_workflow.user_id
      and lower(coalesce(u.role, '')) = 'member'
      and u.is_active is true
      and u.auth_user_id = (select auth.uid())
  )
);

revoke all on table public.hm_users, public.hm_workflow from anon;
revoke insert, update, delete, truncate, references, trigger
  on table public.hm_users, public.hm_workflow from authenticated;
grant select on table public.hm_users, public.hm_workflow to authenticated;

-- Permanent read-only closure report. It does not substitute for signed-in UI
-- or device smoke evidence.
create or replace function public.hm_identity_fallback_closure_status()
returns jsonb
language sql
stable
security definer
set search_path = ''
as $function$
with definitions as (
  select
    lower(pg_get_functiondef('public.hm_flutter_current_member_id()'::regprocedure)) as member_id_def,
    lower(pg_get_functiondef('public.hm_flutter_get_laf()'::regprocedure)) as laf_def,
    lower(pg_get_functiondef('public.hm_flutter_get_nsp()'::regprocedure)) as nsp_def
), policy_metrics as (
  select
    coalesce(jsonb_agg(policyname order by policyname) filter (
      where lower(coalesce(qual, '')) like '%auth.jwt%'
         or lower(coalesce(with_check, '')) like '%auth.jwt%'
         or lower(coalesce(qual, '')) like '%email%'
         or lower(coalesce(with_check, '')) like '%email%'
    ), '[]'::jsonb) as email_fallback_policies,
    coalesce(jsonb_agg(policyname order by policyname) filter (
      where tablename = 'hm_workflow' and cmd in ('INSERT', 'UPDATE', 'DELETE')
    ), '[]'::jsonb) as direct_workflow_write_policies
  from pg_policies
  where schemaname = 'public' and tablename in ('hm_users', 'hm_workflow')
), privilege_metrics as (
  select
    count(*) filter (where grantee = 'anon') as anon_privilege_count,
    count(*) filter (
      where grantee = 'authenticated' and privilege_type <> 'SELECT'
    ) as authenticated_nonselect_privilege_count
  from information_schema.role_table_grants
  where table_schema = 'public'
    and table_name in ('hm_users', 'hm_workflow')
    and grantee in ('anon', 'authenticated')
), data_metrics as (
  select
    count(*) filter (where role = 'member' and is_active) as active_member_count,
    count(*) filter (
      where role = 'member' and is_active and auth_user_id is null
    ) as active_members_missing_auth_user_id,
    count(*) filter (
      where role = 'member' and is_active and not exists (
        select 1 from public.hm_workflow w where w.user_id = u.id
      )
    ) as active_members_missing_workflow
  from public.hm_users u
), metrics as (
  select
    d.active_member_count,
    d.active_members_missing_auth_user_id,
    d.active_members_missing_workflow,
    (
      definitions.member_id_def like '%auth.jwt%'
      or definitions.member_id_def like '%email%'
    ) as current_member_id_uses_email_fallback,
    to_jsonb(array_remove(array[
      case when definitions.laf_def like '%#> array[''workflow''%' then 'hm_flutter_get_laf' end,
      case when definitions.nsp_def like '%#> array[''workflow''%' then 'hm_flutter_get_nsp' end
    ], null)) as flutter_shared_workflow_fallback_functions,
    policies.email_fallback_policies,
    policies.direct_workflow_write_policies,
    privileges.anon_privilege_count,
    privileges.authenticated_nonselect_privilege_count
  from data_metrics d
  cross join definitions
  cross join policy_metrics policies
  cross join privilege_metrics privileges
)
select jsonb_build_object(
  'closed',
    active_members_missing_auth_user_id = 0
    and active_members_missing_workflow = 0
    and not current_member_id_uses_email_fallback
    and jsonb_array_length(flutter_shared_workflow_fallback_functions) = 0
    and jsonb_array_length(email_fallback_policies) = 0
    and jsonb_array_length(direct_workflow_write_policies) = 0
    and anon_privilege_count = 0
    and authenticated_nonselect_privilege_count = 0,
  'active_member_count', active_member_count,
  'active_members_missing_auth_user_id', active_members_missing_auth_user_id,
  'active_members_missing_workflow', active_members_missing_workflow,
  'current_member_id_uses_email_fallback', current_member_id_uses_email_fallback,
  'flutter_shared_workflow_fallback_functions', flutter_shared_workflow_fallback_functions,
  'email_fallback_policies', email_fallback_policies,
  'direct_workflow_write_policies', direct_workflow_write_policies,
  'anon_privilege_count', anon_privilege_count,
  'authenticated_nonselect_privilege_count', authenticated_nonselect_privilege_count,
  'blockers', to_jsonb(array_remove(array[
    case when active_members_missing_auth_user_id > 0 then 'active_member_auth_link_missing' end,
    case when active_members_missing_workflow > 0 then 'active_member_workflow_missing' end,
    case when current_member_id_uses_email_fallback then 'current_member_id_email_fallback_remains' end,
    case when jsonb_array_length(flutter_shared_workflow_fallback_functions) > 0 then 'flutter_shared_workflow_fallback_remains' end,
    case when jsonb_array_length(email_fallback_policies) > 0 then 'identity_email_fallback_policy_remains' end,
    case when jsonb_array_length(direct_workflow_write_policies) > 0 then 'direct_workflow_write_policy_remains' end,
    case when anon_privilege_count > 0 then 'anonymous_identity_table_privilege_remains' end,
    case when authenticated_nonselect_privilege_count > 0 then 'authenticated_identity_table_write_privilege_remains' end
  ], null)),
  'checked_at', now()
)
from metrics;
$function$;

revoke execute on function public.hm_identity_fallback_closure_status()
  from public, anon, authenticated;
grant execute on function public.hm_identity_fallback_closure_status()
  to service_role;

-- Retain one genuine healthy post-closure observation. This is not a repair.
select public.hm_admin_observe_identity_projection(
  'identity-gate7-post-closure-observation',
  false,
  null,
  null,
  'identity_gate7_post_closure',
  jsonb_build_object('gate', 7, 'fallback_closure', true)
);

comment on function public.hm_identity_fallback_closure_status() is
  'Read-only Gate 7 report for Auth-ID, Workflow fallback, RLS and privilege closure.';
