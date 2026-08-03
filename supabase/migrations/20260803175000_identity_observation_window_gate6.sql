-- HealthyMe Users/Workflow Gate 6
-- Read-only observation-window and automated retirement-precondition evidence.
--
-- This migration does not retire or rewrite the shared Users/Workflow projection.
-- It summarizes retained observations, current parity, Auth-link coverage and the
-- remaining Flutter shared-Workflow fallback so later retirement decisions are
-- explicit and evidence based.

create or replace function public.hm_identity_observation_window_status(
  p_window_start timestamptz default (now() - interval '24 hours'),
  p_min_observations integer default 3,
  p_min_span_minutes integer default 60
)
returns jsonb
language sql
stable
security definer
set search_path = ''
as $function$
with params as (
  select
    coalesce(p_window_start, now() - interval '24 hours') as window_start,
    greatest(coalesce(p_min_observations, 3), 1) as min_observations,
    greatest(coalesce(p_min_span_minutes, 60), 0) as min_span_minutes
), current_snapshot as (
  select public.hm_identity_projection_snapshot() as snapshot
), observations as (
  select o.*
  from public.hm_identity_projection_observations o, params p
  where o.observed_at >= p.window_start
), observation_summary as (
  select
    count(*)::integer as observation_count,
    count(*) filter (
      where healthy_before and coalesce(healthy_after, healthy_before)
    )::integer as healthy_observation_count,
    count(*) filter (where repair_applied)::integer as repair_count,
    min(observed_at) as first_observed_at,
    max(observed_at) as latest_observed_at,
    coalesce(
      extract(epoch from (max(observed_at) - min(observed_at))) / 60.0,
      0
    ) as span_minutes
  from observations
), member_coverage as (
  select
    count(*) filter (where role = 'member' and is_active)::integer as active_member_count,
    count(*) filter (
      where role = 'member' and is_active and auth_user_id is not null
    )::integer as active_members_with_auth_user_id,
    count(*) filter (
      where role = 'member' and is_active and auth_user_id is null
    )::integer as active_members_using_email_fallback,
    count(*) filter (
      where role = 'member'
        and is_active
        and not exists (
          select 1
          from public.hm_workflow w
          where w.user_id = hm_users.id
        )
    )::integer as active_members_missing_workflow
  from public.hm_users
), flutter_contract as (
  select
    coalesce(
      jsonb_agg(p.proname order by p.proname) filter (
        where position(
          '#> array[''workflow''' in lower(pg_catalog.pg_get_functiondef(p.oid))
        ) > 0
      ),
      '[]'::jsonb
    ) as shared_workflow_fallback_functions,
    count(*) filter (
      where has_function_privilege('anon', p.oid, 'EXECUTE')
    )::integer as anon_executable_function_count,
    count(*) filter (
      where not has_function_privilege('authenticated', p.oid, 'EXECUTE')
    )::integer as authenticated_missing_function_count,
    count(*)::integer as checked_function_count
  from pg_catalog.pg_proc p
  join pg_catalog.pg_namespace n on n.oid = p.pronamespace
  where n.nspname = 'public'
    and p.proname in (
      'hm_flutter_current_member_id',
      'hm_flutter_get_laf',
      'hm_flutter_save_laf_draft',
      'hm_flutter_submit_laf',
      'hm_flutter_get_nsp',
      'hm_flutter_save_nsp1_draft',
      'hm_flutter_submit_nsp1',
      'hm_flutter_save_nsp2_draft',
      'hm_flutter_submit_nsp2',
      'hm_flutter_submit_assessment_review'
    )
), evidence as (
  select
    p.*,
    c.snapshot,
    o.*,
    m.*,
    f.*,
    coalesce((c.snapshot->>'healthy')::boolean, false) as current_projection_healthy,
    (
      coalesce((c.snapshot->>'healthy')::boolean, false)
      and o.observation_count >= p.min_observations
      and o.healthy_observation_count = o.observation_count
      and o.repair_count = 0
      and o.span_minutes >= p.min_span_minutes
    ) as database_observation_ready
  from params p
  cross join current_snapshot c
  cross join observation_summary o
  cross join member_coverage m
  cross join flutter_contract f
)
select jsonb_build_object(
  'window_start', window_start,
  'minimum_observations', min_observations,
  'minimum_span_minutes', min_span_minutes,
  'observation_count', observation_count,
  'healthy_observation_count', healthy_observation_count,
  'repair_count', repair_count,
  'first_observed_at', first_observed_at,
  'latest_observed_at', latest_observed_at,
  'span_minutes', span_minutes,
  'current_snapshot', snapshot,
  'current_projection_healthy', current_projection_healthy,
  'database_observation_ready', database_observation_ready,
  'active_member_count', active_member_count,
  'active_members_with_auth_user_id', active_members_with_auth_user_id,
  'active_members_using_email_fallback', active_members_using_email_fallback,
  'active_members_missing_workflow', active_members_missing_workflow,
  'flutter_checked_function_count', checked_function_count,
  'flutter_anon_executable_function_count', anon_executable_function_count,
  'flutter_authenticated_missing_function_count', authenticated_missing_function_count,
  'flutter_shared_workflow_fallback_functions', shared_workflow_fallback_functions,
  'automated_retirement_preconditions_ready',
    database_observation_ready
    and active_members_using_email_fallback = 0
    and active_members_missing_workflow = 0
    and anon_executable_function_count = 0
    and authenticated_missing_function_count = 0
    and jsonb_array_length(shared_workflow_fallback_functions) = 0,
  'blockers', to_jsonb(array_remove(array[
    case when not current_projection_healthy then 'current_projection_unhealthy' end,
    case when observation_count < min_observations then 'insufficient_observation_count' end,
    case when healthy_observation_count <> observation_count then 'unhealthy_observation_in_window' end,
    case when repair_count > 0 then 'repair_present_in_window' end,
    case when span_minutes < min_span_minutes then 'insufficient_observation_span' end,
    case when active_members_using_email_fallback > 0 then 'active_member_auth_email_fallback_remains' end,
    case when active_members_missing_workflow > 0 then 'active_member_missing_canonical_workflow' end,
    case when anon_executable_function_count > 0 then 'flutter_rpc_anon_execution_remains' end,
    case when authenticated_missing_function_count > 0 then 'flutter_authenticated_rpc_access_missing' end,
    case when jsonb_array_length(shared_workflow_fallback_functions) > 0 then 'flutter_shared_workflow_fallback_remains' end
  ], null))
)
from evidence;
$function$;

revoke all on function public.hm_identity_observation_window_status(timestamptz, integer, integer)
  from public, anon, authenticated;
grant execute on function public.hm_identity_observation_window_status(timestamptz, integer, integer)
  to service_role;

comment on function public.hm_identity_observation_window_status(timestamptz, integer, integer) is
  'Read-only Gate 6 observation-window, Auth-link coverage and Flutter Workflow fallback readiness summary.';
