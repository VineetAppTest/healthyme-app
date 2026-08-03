-- HealthyMe Users/Workflow Gate 8
-- Capture genuine signed-in smoke evidence and aggregate projection-retirement readiness.

create table if not exists public.hm_identity_manual_smoke_evidence (
  evidence_id uuid primary key default gen_random_uuid(),
  request_id text not null unique,
  evidence_bundle text not null check (
    evidence_bundle in ('streamlit_admin', 'streamlit_member', 'flutter_member')
  ),
  status text not null check (status in ('pass', 'fail')),
  tested_revision text not null,
  build_reference text not null,
  environment text not null default 'production',
  checklist jsonb not null,
  notes text,
  evidence_reference text,
  tester_id text,
  tester_email text,
  tested_at timestamptz not null default now(),
  metadata jsonb not null default '{}'::jsonb,
  request_payload jsonb not null,
  created_at timestamptz not null default now(),
  constraint hm_identity_manual_smoke_checklist_object
    check (jsonb_typeof(checklist) = 'object'),
  constraint hm_identity_manual_smoke_metadata_object
    check (jsonb_typeof(metadata) = 'object'),
  constraint hm_identity_manual_smoke_request_payload_object
    check (jsonb_typeof(request_payload) = 'object'),
  constraint hm_identity_manual_smoke_revision_not_blank
    check (btrim(tested_revision) <> ''),
  constraint hm_identity_manual_smoke_build_not_blank
    check (btrim(build_reference) <> ''),
  constraint hm_identity_manual_smoke_environment_not_blank
    check (btrim(environment) <> '')
);

create index if not exists hm_identity_manual_smoke_bundle_tested_idx
  on public.hm_identity_manual_smoke_evidence (evidence_bundle, tested_at desc, created_at desc);

alter table public.hm_identity_manual_smoke_evidence enable row level security;
revoke all on table public.hm_identity_manual_smoke_evidence from public, anon, authenticated;
grant select, insert on table public.hm_identity_manual_smoke_evidence to service_role;

create or replace function public.hm_admin_record_identity_smoke_evidence(
  p_request_id text,
  p_evidence_bundle text,
  p_status text,
  p_tested_revision text,
  p_build_reference text,
  p_environment text,
  p_checklist jsonb,
  p_notes text default null,
  p_evidence_reference text default null,
  p_tester_id text default null,
  p_tester_email text default null,
  p_tested_at timestamptz default null,
  p_metadata jsonb default '{}'::jsonb
)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $function$
declare
  v_request_id text := btrim(coalesce(p_request_id, ''));
  v_bundle text := lower(btrim(coalesce(p_evidence_bundle, '')));
  v_status text := lower(btrim(coalesce(p_status, '')));
  v_revision text := btrim(coalesce(p_tested_revision, ''));
  v_build text := btrim(coalesce(p_build_reference, ''));
  v_environment text := lower(btrim(coalesce(p_environment, 'production')));
  v_checklist jsonb := coalesce(p_checklist, '{}'::jsonb);
  v_metadata jsonb := coalesce(p_metadata, '{}'::jsonb);
  v_required text[];
  v_missing_or_invalid text[];
  v_false_steps text[];
  v_tested_at timestamptz := coalesce(p_tested_at, transaction_timestamp());
  v_payload jsonb;
  v_existing public.hm_identity_manual_smoke_evidence%rowtype;
  v_saved public.hm_identity_manual_smoke_evidence%rowtype;
begin
  if v_request_id = '' then
    raise exception using errcode = '22023', message = 'request_id is required.';
  end if;
  if v_bundle not in ('streamlit_admin', 'streamlit_member', 'flutter_member') then
    raise exception using errcode = '22023', message = 'Unsupported smoke evidence bundle.';
  end if;
  if v_status not in ('pass', 'fail') then
    raise exception using errcode = '22023', message = 'Smoke evidence status must be pass or fail.';
  end if;
  if v_revision = '' then
    raise exception using errcode = '22023', message = 'tested_revision is required.';
  end if;
  if v_build = '' then
    raise exception using errcode = '22023', message = 'build_reference is required.';
  end if;
  if v_environment = '' then
    raise exception using errcode = '22023', message = 'environment is required.';
  end if;
  if jsonb_typeof(v_checklist) <> 'object' then
    raise exception using errcode = '22023', message = 'checklist must be a JSON object.';
  end if;
  if jsonb_typeof(v_metadata) <> 'object' then
    raise exception using errcode = '22023', message = 'metadata must be a JSON object.';
  end if;

  v_required := case v_bundle
    when 'streamlit_admin' then array['login', 'refresh_persistence', 'admin_protected_route', 'logout']
    when 'streamlit_member' then array['login', 'refresh_persistence', 'member_protected_route', 'logout']
    else array['login', 'dashboard', 'laf', 'nsp', 'submit_for_review']
  end;

  select coalesce(array_agg(step order by step), '{}'::text[])
    into v_missing_or_invalid
  from unnest(v_required) step
  where not (v_checklist ? step)
     or jsonb_typeof(v_checklist -> step) <> 'boolean';

  if cardinality(v_missing_or_invalid) > 0 then
    raise exception using
      errcode = '22023',
      message = 'Missing or invalid smoke checklist steps: ' || array_to_string(v_missing_or_invalid, ', ');
  end if;

  select coalesce(array_agg(step order by step), '{}'::text[])
    into v_false_steps
  from unnest(v_required) step
  where coalesce((v_checklist ->> step)::boolean, false) is false;

  if v_status = 'pass' and cardinality(v_false_steps) > 0 then
    raise exception using
      errcode = '22023',
      message = 'A passing smoke record requires every mandatory step to pass: ' || array_to_string(v_false_steps, ', ');
  end if;

  v_payload := jsonb_build_object(
    'evidence_bundle', v_bundle,
    'status', v_status,
    'tested_revision', v_revision,
    'build_reference', v_build,
    'environment', v_environment,
    'checklist', v_checklist,
    'notes', nullif(btrim(coalesce(p_notes, '')), ''),
    'evidence_reference', nullif(btrim(coalesce(p_evidence_reference, '')), ''),
    'tester_id', nullif(btrim(coalesce(p_tester_id, '')), ''),
    'tester_email', nullif(lower(btrim(coalesce(p_tester_email, ''))), ''),
    'tested_at_input', p_tested_at,
    'metadata', v_metadata
  );

  perform pg_catalog.pg_advisory_xact_lock(
    pg_catalog.hashtextextended('hm_admin_record_identity_smoke_evidence:' || v_request_id, 0)
  );

  select * into v_existing
  from public.hm_identity_manual_smoke_evidence
  where request_id = v_request_id;

  if found then
    if v_existing.request_payload is distinct from v_payload then
      raise exception using
        errcode = '22023',
        message = 'request_id has already been used with a different smoke evidence payload.';
    end if;
    return jsonb_build_object(
      'ok', true,
      'idempotent_replay', true,
      'record', to_jsonb(v_existing) - 'request_payload'
    );
  end if;

  insert into public.hm_identity_manual_smoke_evidence (
    request_id,
    evidence_bundle,
    status,
    tested_revision,
    build_reference,
    environment,
    checklist,
    notes,
    evidence_reference,
    tester_id,
    tester_email,
    tested_at,
    metadata,
    request_payload
  ) values (
    v_request_id,
    v_bundle,
    v_status,
    v_revision,
    v_build,
    v_environment,
    v_checklist,
    nullif(btrim(coalesce(p_notes, '')), ''),
    nullif(btrim(coalesce(p_evidence_reference, '')), ''),
    nullif(btrim(coalesce(p_tester_id, '')), ''),
    nullif(lower(btrim(coalesce(p_tester_email, ''))), ''),
    v_tested_at,
    v_metadata,
    v_payload
  ) returning * into v_saved;

  return jsonb_build_object(
    'ok', true,
    'idempotent_replay', false,
    'record', to_jsonb(v_saved) - 'request_payload'
  );
end;
$function$;

revoke execute on function public.hm_admin_record_identity_smoke_evidence(
  text, text, text, text, text, text, jsonb, text, text, text, text, timestamptz, jsonb
) from public, anon, authenticated;
grant execute on function public.hm_admin_record_identity_smoke_evidence(
  text, text, text, text, text, text, jsonb, text, text, text, text, timestamptz, jsonb
) to service_role;

create or replace function public.hm_identity_projection_retirement_readiness(
  p_evidence_max_age_hours integer default 72
)
returns jsonb
language sql
stable
security definer
set search_path = ''
as $function$
with parameters as (
  select greatest(coalesce(p_evidence_max_age_hours, 72), 1) as max_age_hours
), automated as (
  select public.hm_identity_observation_window_status(
    transaction_timestamp() - interval '24 hours', 3, 60
  ) as data
), closure as (
  select public.hm_identity_fallback_closure_status() as data
), required_bundles(evidence_bundle) as (
  values ('streamlit_admin'::text), ('streamlit_member'::text), ('flutter_member'::text)
), latest as (
  select distinct on (e.evidence_bundle)
    e.evidence_bundle,
    e.status,
    e.tested_revision,
    e.build_reference,
    e.environment,
    e.checklist,
    e.notes,
    e.evidence_reference,
    e.tester_id,
    e.tester_email,
    e.tested_at,
    e.created_at
  from public.hm_identity_manual_smoke_evidence e
  order by e.evidence_bundle, e.tested_at desc, e.created_at desc
), evaluated as (
  select
    r.evidence_bundle,
    l.status,
    l.tested_revision,
    l.build_reference,
    l.environment,
    l.checklist,
    l.notes,
    l.evidence_reference,
    l.tester_id,
    l.tester_email,
    l.tested_at,
    l.created_at,
    case
      when l.evidence_bundle is null then 'missing'
      when lower(coalesce(l.environment, '')) <> 'production' then 'non_production'
      when l.tested_at < transaction_timestamp() - make_interval(hours => p.max_age_hours) then 'stale'
      when l.status <> 'pass' then 'failed'
      else 'pass'
    end as readiness_status
  from required_bundles r
  cross join parameters p
  left join latest l on l.evidence_bundle = r.evidence_bundle
), smoke_summary as (
  select
    count(*) filter (where readiness_status = 'pass') as passing_bundle_count,
    jsonb_object_agg(
      evidence_bundle,
      jsonb_build_object(
        'readiness_status', readiness_status,
        'status', status,
        'tested_revision', tested_revision,
        'build_reference', build_reference,
        'environment', environment,
        'checklist', checklist,
        'notes', notes,
        'evidence_reference', evidence_reference,
        'tester_id', tester_id,
        'tester_email', tester_email,
        'tested_at', tested_at,
        'created_at', created_at
      ) order by evidence_bundle
    ) as latest_evidence,
    coalesce(
      array_agg(
        case readiness_status
          when 'missing' then evidence_bundle || '_smoke_missing'
          when 'non_production' then evidence_bundle || '_smoke_not_production'
          when 'stale' then evidence_bundle || '_smoke_stale'
          when 'failed' then evidence_bundle || '_smoke_failed'
          else null
        end
        order by evidence_bundle
      ) filter (where readiness_status <> 'pass'),
      '{}'::text[]
    ) as smoke_blockers
  from evaluated
), combined as (
  select
    automated.data as automated_data,
    closure.data as closure_data,
    smoke.passing_bundle_count,
    smoke.latest_evidence,
    smoke.smoke_blockers,
    parameters.max_age_hours,
    coalesce((automated.data->>'automated_retirement_preconditions_ready')::boolean, false) as automated_ready,
    coalesce((closure.data->>'closed')::boolean, false) as closure_ready,
    smoke.passing_bundle_count = 3 as manual_smoke_ready,
    coalesce((automated.data #>> '{current_snapshot,healthy}')::boolean, false)
      and coalesce((automated.data #>> '{current_snapshot,shared_user_count}')::integer, 0)
          = coalesce((automated.data #>> '{current_snapshot,canonical_user_count}')::integer, -1)
      and coalesce((automated.data #>> '{current_snapshot,shared_workflow_count}')::integer, 0)
          = coalesce((automated.data #>> '{current_snapshot,canonical_workflow_count}')::integer, -1)
      as rollback_projection_ready
  from automated
  cross join closure
  cross join smoke_summary smoke
  cross join parameters
)
select jsonb_build_object(
  'ready_for_retirement_decision',
    automated_ready and closure_ready and manual_smoke_ready and rollback_projection_ready,
  'projection_retirement_approved', false,
  'automated_ready', automated_ready,
  'fallback_closure_ready', closure_ready,
  'manual_smoke_ready', manual_smoke_ready,
  'rollback_projection_ready', rollback_projection_ready,
  'passing_bundle_count', passing_bundle_count,
  'required_bundle_count', 3,
  'evidence_max_age_hours', max_age_hours,
  'latest_evidence', latest_evidence,
  'automated_status', automated_data,
  'fallback_closure_status', closure_data,
  'blockers', to_jsonb(
    array_remove(array[
      case when not automated_ready then 'automated_database_readiness_incomplete' end,
      case when not closure_ready then 'identity_fallback_closure_incomplete' end,
      case when not rollback_projection_ready then 'rollback_projection_not_healthy' end
    ], null) || smoke_blockers
  ),
  'rollback_requirements', jsonb_build_array(
    'Download and retain the complete current database backup before retirement.',
    'Record the deployed HealthyMe commit and Flutter build reference used for smoke evidence.',
    'Keep the shared Users/Workflow projection unchanged until the retirement PR is merged and post-deployment checks pass.',
    'Rollback immediately if canonical identity reads, role routing, LAF, NSP or Submit-for-Review regress.'
  ),
  'checked_at', transaction_timestamp()
)
from combined;
$function$;

revoke execute on function public.hm_identity_projection_retirement_readiness(integer)
  from public, anon, authenticated;
grant execute on function public.hm_identity_projection_retirement_readiness(integer)
  to service_role;
