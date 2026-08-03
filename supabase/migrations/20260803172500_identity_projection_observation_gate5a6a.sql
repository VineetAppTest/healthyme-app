-- HealthyMe Users/Workflow Gate 5A + 6A
-- Canonical read observation and explicit compatibility-projection repair.
--
-- Canonical hm_users and hm_workflow remain the authority. The shared JSON
-- projection is observed and may be repaired only through an explicit,
-- service-role-only contract. Nothing in this migration retires the projection.

create table if not exists public.hm_identity_projection_observations (
  observation_id bigint generated always as identity primary key,
  request_id text not null unique,
  observed_at timestamptz not null default now(),
  source text not null default 'identity_projection_observation',
  actor_id text,
  actor_email text,
  apply_repair boolean not null default false,
  repair_applied boolean not null default false,
  healthy_before boolean not null,
  healthy_after boolean,
  snapshot_before jsonb not null,
  snapshot_after jsonb,
  response_payload jsonb not null,
  metadata jsonb not null default '{}'::jsonb
);

alter table public.hm_identity_projection_observations enable row level security;
revoke all on table public.hm_identity_projection_observations from public, anon, authenticated;
grant select, insert on table public.hm_identity_projection_observations to service_role;
grant usage, select on sequence public.hm_identity_projection_observations_observation_id_seq to service_role;

create or replace function public.hm_identity_projection_snapshot()
returns jsonb
language sql
stable
security definer
set search_path = ''
as $function$
with state as (
  select coalesce(data, '{}'::jsonb) as data
  from public.healthyme_app_state
  where id = 'healthyme_app_state_v1'
), shared_users as (
  select
    value as row_data,
    btrim(coalesce(value->>'id', '')) as user_id
  from state,
  lateral jsonb_array_elements(
    case when jsonb_typeof(data->'users') = 'array' then data->'users' else '[]'::jsonb end
  )
), shared_workflow as (
  select key as user_id, value as row_data
  from state,
  lateral jsonb_each(
    case when jsonb_typeof(data->'workflow') = 'object' then data->'workflow' else '{}'::jsonb end
  )
), missing_shared_users as (
  select coalesce(jsonb_agg(c.id order by c.id), '[]'::jsonb) as ids
  from public.hm_users c
  left join shared_users s on s.user_id = c.id
  where s.user_id is null
), orphan_shared_users as (
  select coalesce(jsonb_agg(s.user_id order by s.user_id), '[]'::jsonb) as ids
  from shared_users s
  left join public.hm_users c on c.id = s.user_id
  where c.id is null or s.user_id = ''
), duplicate_shared_users as (
  select coalesce(jsonb_agg(user_id order by user_id), '[]'::jsonb) as ids
  from (
    select user_id
    from shared_users
    where user_id <> ''
    group by user_id
    having count(*) > 1
  ) d
), user_mismatches as (
  select coalesce(
    jsonb_agg(
      jsonb_build_object(
        'user_id', c.id,
        'fields', to_jsonb(array_remove(array[
          case when coalesce(c.name, '') is distinct from coalesce(s.row_data->>'name', '') then 'name' end,
          case when lower(coalesce(c.email, '')) is distinct from lower(coalesce(s.row_data->>'email', '')) then 'email' end,
          case when coalesce(c.password_hash, '') is distinct from coalesce(s.row_data->>'password_hash', '') then 'password_hash' end,
          case when lower(coalesce(c.role, 'member')) is distinct from lower(coalesce(s.row_data->>'role', 'member')) then 'role' end,
          case when c.must_reset_password is distinct from coalesce((s.row_data->>'must_reset_password')::boolean, false) then 'must_reset_password' end,
          case when c.is_active is distinct from coalesce((s.row_data->>'is_active')::boolean, true) then 'is_active' end,
          case when lower(coalesce(c.auth_provider, 'oidc')) is distinct from lower(coalesce(s.row_data->>'auth_provider', 'oidc')) then 'auth_provider' end
        ], null))
      ) order by c.id
    ),
    '[]'::jsonb
  ) as rows
  from public.hm_users c
  join shared_users s on s.user_id = c.id
  where coalesce(c.name, '') is distinct from coalesce(s.row_data->>'name', '')
     or lower(coalesce(c.email, '')) is distinct from lower(coalesce(s.row_data->>'email', ''))
     or coalesce(c.password_hash, '') is distinct from coalesce(s.row_data->>'password_hash', '')
     or lower(coalesce(c.role, 'member')) is distinct from lower(coalesce(s.row_data->>'role', 'member'))
     or c.must_reset_password is distinct from coalesce((s.row_data->>'must_reset_password')::boolean, false)
     or c.is_active is distinct from coalesce((s.row_data->>'is_active')::boolean, true)
     or lower(coalesce(c.auth_provider, 'oidc')) is distinct from lower(coalesce(s.row_data->>'auth_provider', 'oidc'))
), missing_shared_workflow as (
  select coalesce(jsonb_agg(c.user_id order by c.user_id), '[]'::jsonb) as ids
  from public.hm_workflow c
  left join shared_workflow s on s.user_id = c.user_id
  where s.user_id is null
), orphan_shared_workflow as (
  select coalesce(jsonb_agg(s.user_id order by s.user_id), '[]'::jsonb) as ids
  from shared_workflow s
  left join public.hm_workflow c on c.user_id = s.user_id
  where c.user_id is null
), workflow_mismatches as (
  select coalesce(
    jsonb_agg(
      jsonb_build_object(
        'user_id', c.user_id,
        'fields', to_jsonb(array_remove(array[
          case when c.laf_completed is distinct from coalesce((s.row_data->>'laf_completed')::boolean, false) then 'laf_completed' end,
          case when c.nsp1_completed is distinct from coalesce((s.row_data->>'nsp1_completed')::boolean, false) then 'nsp1_completed' end,
          case when c.nsp2_completed is distinct from coalesce((s.row_data->>'nsp2_completed')::boolean, false) then 'nsp2_completed' end,
          case when c.submitted_for_review is distinct from coalesce((s.row_data->>'submitted_for_review')::boolean, false) then 'submitted_for_review' end,
          case when c.admin_completed is distinct from coalesce((s.row_data->>'admin_completed')::boolean, false) then 'admin_completed' end,
          case when c.final_report_ready is distinct from coalesce((s.row_data->>'final_report_ready')::boolean, false) then 'final_report_ready' end,
          case when c.workflow_status is distinct from coalesce(s.row_data->>'workflow_status', 'not_started') then 'workflow_status' end
        ], null))
      ) order by c.user_id
    ),
    '[]'::jsonb
  ) as rows
  from public.hm_workflow c
  join shared_workflow s on s.user_id = c.user_id
  where c.laf_completed is distinct from coalesce((s.row_data->>'laf_completed')::boolean, false)
     or c.nsp1_completed is distinct from coalesce((s.row_data->>'nsp1_completed')::boolean, false)
     or c.nsp2_completed is distinct from coalesce((s.row_data->>'nsp2_completed')::boolean, false)
     or c.submitted_for_review is distinct from coalesce((s.row_data->>'submitted_for_review')::boolean, false)
     or c.admin_completed is distinct from coalesce((s.row_data->>'admin_completed')::boolean, false)
     or c.final_report_ready is distinct from coalesce((s.row_data->>'final_report_ready')::boolean, false)
     or c.workflow_status is distinct from coalesce(s.row_data->>'workflow_status', 'not_started')
), payload as (
  select jsonb_build_object(
    'canonical_user_count', (select count(*) from public.hm_users),
    'shared_user_count', (select count(*) from shared_users),
    'canonical_workflow_count', (select count(*) from public.hm_workflow),
    'shared_workflow_count', (select count(*) from shared_workflow),
    'missing_shared_user_ids', (select ids from missing_shared_users),
    'orphan_shared_user_ids', (select ids from orphan_shared_users),
    'duplicate_shared_user_ids', (select ids from duplicate_shared_users),
    'user_mismatches', (select rows from user_mismatches),
    'missing_shared_workflow_ids', (select ids from missing_shared_workflow),
    'orphan_shared_workflow_ids', (select ids from orphan_shared_workflow),
    'workflow_mismatches', (select rows from workflow_mismatches)
  ) as snapshot
)
select snapshot || jsonb_build_object(
  'healthy',
    jsonb_array_length(snapshot->'missing_shared_user_ids') = 0
    and jsonb_array_length(snapshot->'orphan_shared_user_ids') = 0
    and jsonb_array_length(snapshot->'duplicate_shared_user_ids') = 0
    and jsonb_array_length(snapshot->'user_mismatches') = 0
    and jsonb_array_length(snapshot->'missing_shared_workflow_ids') = 0
    and jsonb_array_length(snapshot->'orphan_shared_workflow_ids') = 0
    and jsonb_array_length(snapshot->'workflow_mismatches') = 0,
  'observed_at', now()
)
from payload;
$function$;

revoke all on function public.hm_identity_projection_snapshot() from public, anon, authenticated;
grant execute on function public.hm_identity_projection_snapshot() to service_role;

create or replace function public.hm_admin_observe_identity_projection(
  p_request_id text,
  p_apply_repair boolean default false,
  p_actor_id text default null,
  p_actor_email text default null,
  p_source text default 'identity_projection_observation',
  p_metadata jsonb default '{}'::jsonb
)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $function$
declare
  v_request_id text := btrim(coalesce(p_request_id, ''));
  v_source text := coalesce(nullif(btrim(coalesce(p_source, '')), ''), 'identity_projection_observation');
  v_metadata jsonb := coalesce(p_metadata, '{}'::jsonb);
  v_existing jsonb;
  v_before jsonb;
  v_after jsonb;
  v_state jsonb;
  v_projected_users jsonb;
  v_projected_workflow jsonb;
  v_repair_applied boolean := false;
  v_response jsonb;
begin
  if v_request_id = '' then
    raise exception using errcode = '22023', message = 'request_id is required.';
  end if;
  if jsonb_typeof(v_metadata) <> 'object' then
    raise exception using errcode = '22023', message = 'metadata must be a JSON object.';
  end if;

  perform pg_catalog.pg_advisory_xact_lock(
    pg_catalog.hashtextextended('hm_admin_observe_identity_projection:' || v_request_id, 0)
  );

  select response_payload into v_existing
  from public.hm_identity_projection_observations
  where request_id = v_request_id;
  if found then
    return jsonb_set(v_existing, '{idempotent_replay}', 'true'::jsonb, true);
  end if;

  v_before := public.hm_identity_projection_snapshot();

  if p_apply_repair and not coalesce((v_before->>'healthy')::boolean, false) then
    select coalesce(data, '{}'::jsonb)
      into v_state
    from public.healthyme_app_state
    where id = 'healthyme_app_state_v1'
    for update;

    if v_state is null then
      raise exception using errcode = 'P0002', message = 'HealthyMe application state is missing.';
    end if;

    with shared_users as (
      select value as row_data, btrim(coalesce(value->>'id', '')) as user_id
      from jsonb_array_elements(
        case when jsonb_typeof(v_state->'users') = 'array' then v_state->'users' else '[]'::jsonb end
      )
    )
    select coalesce(
      jsonb_agg(
        coalesce(s.row_data, '{}'::jsonb)
        || jsonb_build_object(
          'id', c.id,
          'name', coalesce(c.name, ''),
          'email', lower(coalesce(c.email, '')),
          'password_hash', coalesce(c.password_hash, ''),
          'role', lower(coalesce(c.role, 'member')),
          'must_reset_password', c.must_reset_password,
          'is_active', c.is_active,
          'auth_provider', lower(coalesce(c.auth_provider, 'oidc'))
        )
        order by c.id
      ),
      '[]'::jsonb
    ) into v_projected_users
    from public.hm_users c
    left join shared_users s on s.user_id = c.id;

    select coalesce(
      jsonb_object_agg(
        c.user_id,
        coalesce(v_state #> array['workflow', c.user_id], '{}'::jsonb)
        || jsonb_build_object(
          'laf_completed', c.laf_completed,
          'nsp1_completed', c.nsp1_completed,
          'nsp2_completed', c.nsp2_completed,
          'submitted_for_review', c.submitted_for_review,
          'admin_completed', c.admin_completed,
          'final_report_ready', c.final_report_ready,
          'workflow_status', c.workflow_status
        )
        order by c.user_id
      ),
      '{}'::jsonb
    ) into v_projected_workflow
    from public.hm_workflow c;

    v_state := jsonb_set(v_state, '{users}', v_projected_users, true);
    v_state := jsonb_set(v_state, '{workflow}', v_projected_workflow, true);

    update public.healthyme_app_state
       set data = v_state,
           updated_at = now()
     where id = 'healthyme_app_state_v1';

    v_repair_applied := true;
  end if;

  v_after := public.hm_identity_projection_snapshot();
  v_response := jsonb_build_object(
    'ok', true,
    'request_id', v_request_id,
    'apply_repair', p_apply_repair,
    'repair_applied', v_repair_applied,
    'healthy_before', coalesce((v_before->>'healthy')::boolean, false),
    'healthy_after', coalesce((v_after->>'healthy')::boolean, false),
    'snapshot_before', v_before,
    'snapshot_after', v_after,
    'idempotent_replay', false
  );

  insert into public.hm_identity_projection_observations(
    request_id, source, actor_id, actor_email, apply_repair, repair_applied,
    healthy_before, healthy_after, snapshot_before, snapshot_after,
    response_payload, metadata
  ) values (
    v_request_id,
    v_source,
    nullif(btrim(coalesce(p_actor_id, '')), ''),
    nullif(lower(btrim(coalesce(p_actor_email, ''))), ''),
    p_apply_repair,
    v_repair_applied,
    coalesce((v_before->>'healthy')::boolean, false),
    coalesce((v_after->>'healthy')::boolean, false),
    v_before,
    v_after,
    v_response,
    v_metadata
  );

  return v_response;
end;
$function$;

revoke all on function public.hm_admin_observe_identity_projection(text, boolean, text, text, text, jsonb)
  from public, anon, authenticated;
grant execute on function public.hm_admin_observe_identity_projection(text, boolean, text, text, text, jsonb)
  to service_role;

comment on function public.hm_identity_projection_snapshot() is
  'Read-only canonical-versus-shared Users and Workflow projection drift snapshot.';
comment on function public.hm_admin_observe_identity_projection(text, boolean, text, text, text, jsonb) is
  'Service-role-only idempotent identity projection observation with optional explicit canonical repair.';
