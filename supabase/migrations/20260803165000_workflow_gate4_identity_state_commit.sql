-- HealthyMe Users/Workflow Batch 2B, Gate 4
-- Cut Streamlit/shared-state Workflow writers over to the canonical transactional
-- Workflow contract while keeping combined User + Workflow operations atomic.
--
-- The complete compatibility state is written in the same transaction so
-- notifications, assessment instances, final-report data and shared-only
-- Workflow fields remain aligned with canonical identity state.

alter table public.hm_domain_write_requests
  drop constraint if exists hm_domain_write_requests_operation_check;
alter table public.hm_domain_write_requests
  add constraint hm_domain_write_requests_operation_check
  check (operation in (
    'user_upsert',
    'workflow_upsert',
    'user_state_commit',
    'identity_state_commit'
  ));

create or replace function public.hm_admin_commit_identity_and_state(
  p_request_id text,
  p_state_id text,
  p_state_data jsonb,
  p_users jsonb,
  p_workflows jsonb,
  p_actor_id text default null,
  p_actor_email text default null,
  p_source text default 'streamlit_identity_cutover',
  p_metadata jsonb default '{}'::jsonb
)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $function$
declare
  v_request_id text := btrim(coalesce(p_request_id, ''));
  v_state_id text := btrim(coalesce(p_state_id, ''));
  v_state_data jsonb := coalesce(p_state_data, '{}'::jsonb);
  v_users jsonb := coalesce(p_users, '[]'::jsonb);
  v_workflows jsonb := coalesce(p_workflows, '[]'::jsonb);
  v_metadata jsonb := coalesce(p_metadata, '{}'::jsonb);
  v_replay_operation text;
  v_replay_entity_id text;
  v_replay_response jsonb;
  v_item jsonb;
  v_user_id text;
  v_patch jsonb;
  v_child_response jsonb;
  v_user_results jsonb := '[]'::jsonb;
  v_workflow_results jsonb := '[]'::jsonb;
  v_changed_user_count integer := 0;
  v_changed_workflow_count integer := 0;
  v_response jsonb;
begin
  if v_request_id = '' then
    raise exception using errcode = '22023', message = 'request_id is required.';
  end if;
  if v_state_id = '' then
    raise exception using errcode = '22023', message = 'state_id is required.';
  end if;
  if jsonb_typeof(v_state_data) <> 'object' then
    raise exception using errcode = '22023', message = 'state_data must be a JSON object.';
  end if;
  if jsonb_typeof(v_users) <> 'array' then
    raise exception using errcode = '22023', message = 'users must be a JSON array.';
  end if;
  if jsonb_typeof(v_workflows) <> 'array' then
    raise exception using errcode = '22023', message = 'workflows must be a JSON array.';
  end if;
  if jsonb_typeof(v_metadata) <> 'object' then
    raise exception using errcode = '22023', message = 'metadata must be a JSON object.';
  end if;

  perform pg_catalog.pg_advisory_xact_lock(
    pg_catalog.hashtextextended('hm_admin_commit_identity_and_state:' || v_request_id, 0)
  );

  select operation, entity_id, response_payload
    into v_replay_operation, v_replay_entity_id, v_replay_response
  from public.hm_domain_write_requests
  where request_id = v_request_id;

  if found then
    if v_replay_operation <> 'identity_state_commit' or v_replay_entity_id <> v_state_id then
      raise exception using
        errcode = '22023',
        message = 'request_id has already been used for a different operation or entity.';
    end if;
    return jsonb_set(v_replay_response, '{idempotent_replay}', 'true'::jsonb, true);
  end if;

  -- Users are committed first so new-member Workflow rows satisfy the canonical
  -- hm_workflow -> hm_users dependency in the same transaction.
  for v_item in select value from jsonb_array_elements(v_users)
  loop
    if jsonb_typeof(v_item) <> 'object' then
      raise exception using errcode = '22023', message = 'Each users entry must be an object.';
    end if;
    v_user_id := btrim(coalesce(v_item->>'user_id', ''));
    v_patch := coalesce(v_item->'patch', '{}'::jsonb);
    if v_user_id = '' then
      raise exception using errcode = '22023', message = 'Each users entry requires user_id.';
    end if;
    if jsonb_typeof(v_patch) <> 'object' then
      raise exception using errcode = '22023', message = 'Each users entry patch must be an object.';
    end if;

    v_child_response := public.hm_admin_upsert_user(
      v_request_id || ':user:' || v_user_id,
      v_user_id,
      v_patch,
      p_actor_id,
      p_actor_email,
      p_source,
      v_metadata || jsonb_build_object('parent_request_id', v_request_id, 'cutover_gate', 4)
    );
    if coalesce((v_child_response->>'changed')::boolean, false) then
      v_changed_user_count := v_changed_user_count + 1;
    end if;
    v_user_results := v_user_results || jsonb_build_array(v_child_response);
  end loop;

  for v_item in select value from jsonb_array_elements(v_workflows)
  loop
    if jsonb_typeof(v_item) <> 'object' then
      raise exception using errcode = '22023', message = 'Each workflows entry must be an object.';
    end if;
    v_user_id := btrim(coalesce(v_item->>'user_id', ''));
    v_patch := coalesce(v_item->'patch', '{}'::jsonb);
    if v_user_id = '' then
      raise exception using errcode = '22023', message = 'Each workflows entry requires user_id.';
    end if;
    if jsonb_typeof(v_patch) <> 'object' then
      raise exception using errcode = '22023', message = 'Each workflows entry patch must be an object.';
    end if;

    v_child_response := public.hm_admin_upsert_workflow(
      v_request_id || ':workflow:' || v_user_id,
      v_user_id,
      v_patch,
      p_actor_id,
      p_actor_email,
      p_source,
      v_metadata || jsonb_build_object('parent_request_id', v_request_id, 'cutover_gate', 4)
    );
    if coalesce((v_child_response->>'changed')::boolean, false) then
      v_changed_workflow_count := v_changed_workflow_count + 1;
    end if;
    v_workflow_results := v_workflow_results || jsonb_build_array(v_child_response);
  end loop;

  insert into public.healthyme_app_state(id, data, updated_at)
  values (v_state_id, v_state_data, now())
  on conflict (id) do update
    set data = excluded.data,
        updated_at = now();

  v_response := jsonb_build_object(
    'ok', true,
    'operation', 'identity_state_commit',
    'request_id', v_request_id,
    'state_id', v_state_id,
    'changed_user_count', v_changed_user_count,
    'changed_workflow_count', v_changed_workflow_count,
    'user_results', v_user_results,
    'workflow_results', v_workflow_results,
    'idempotent_replay', false
  );

  insert into public.hm_domain_write_requests(request_id, operation, entity_id, response_payload)
  values (v_request_id, 'identity_state_commit', v_state_id, v_response);

  return v_response;
end;
$function$;

revoke all on function public.hm_admin_commit_identity_and_state(
  text, text, jsonb, jsonb, jsonb, text, text, text, jsonb
) from public, anon, authenticated;
grant execute on function public.hm_admin_commit_identity_and_state(
  text, text, jsonb, jsonb, jsonb, text, text, text, jsonb
) to service_role;

comment on function public.hm_admin_commit_identity_and_state(
  text, text, jsonb, jsonb, jsonb, text, text, text, jsonb
) is 'Atomically commits changed canonical Users, canonical Workflow and the complete HealthyMe compatibility state.';

create or replace function public.hm_capture_direct_workflow_event()
returns trigger
language plpgsql
security invoker
set search_path = ''
as $function$
declare
  v_before jsonb;
  v_after jsonb;
  v_changed_fields text[] := '{}'::text[];
  v_request_id text;
begin
  -- Security-definer contract writes run as the function owner and already append
  -- their own event. Capture only residual direct service-role table writes.
  if current_user <> 'service_role' then
    return new;
  end if;

  v_before := case when tg_op = 'INSERT' then null else to_jsonb(old) end;
  v_after := to_jsonb(new);

  if tg_op = 'INSERT' then
    select coalesce(array_agg(key order by key), '{}'::text[])
      into v_changed_fields
    from jsonb_object_keys(to_jsonb(new) - 'created_at' - 'updated_at' - 'user_id') as key;
  else
    select coalesce(array_agg(key order by key), '{}'::text[])
      into v_changed_fields
    from jsonb_object_keys(to_jsonb(new) - 'created_at' - 'updated_at' - 'user_id') as key
    where (to_jsonb(old) -> key) is distinct from (to_jsonb(new) -> key);
  end if;

  if coalesce(cardinality(v_changed_fields), 0) = 0 then
    return new;
  end if;

  v_request_id := 'direct-workflow:' || pg_catalog.gen_random_uuid()::text;
  insert into public.hm_workflow_events(
    request_id, user_id, event_type, source, changed_fields,
    before_snapshot, after_snapshot, metadata
  ) values (
    v_request_id,
    new.user_id,
    case when tg_op = 'INSERT' then 'created' else 'updated' end,
    'service_role_direct',
    v_changed_fields,
    v_before,
    v_after,
    jsonb_build_object('cutover_gate', 4, 'direct_write_captured', true)
  );

  return new;
end;
$function$;

revoke all on function public.hm_capture_direct_workflow_event() from public, anon, authenticated;
grant execute on function public.hm_capture_direct_workflow_event() to service_role;

drop trigger if exists hm_workflow_capture_direct_event on public.hm_workflow;
create trigger hm_workflow_capture_direct_event
after insert or update on public.hm_workflow
for each row execute function public.hm_capture_direct_workflow_event();
