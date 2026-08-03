-- HealthyMe Users/Workflow Batch 2B, Gate 3
-- Cut shared-state User writers over to the canonical transactional User contract
-- while preserving the complete application-state compatibility projection.
--
-- Workflow remains on its existing synchronization path. Sessions, password
-- retirement, default-Admin redesign and shared User retirement are excluded.

alter table public.hm_domain_write_requests
  drop constraint if exists hm_domain_write_requests_operation_check;
alter table public.hm_domain_write_requests
  add constraint hm_domain_write_requests_operation_check
  check (operation in ('user_upsert', 'workflow_upsert', 'user_state_commit'));

create or replace function public.hm_admin_commit_users_and_state(
  p_request_id text,
  p_state_id text,
  p_state_data jsonb,
  p_users jsonb,
  p_actor_id text default null,
  p_actor_email text default null,
  p_source text default 'streamlit_user_cutover',
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
  v_metadata jsonb := coalesce(p_metadata, '{}'::jsonb);
  v_replay_operation text;
  v_replay_entity_id text;
  v_replay_response jsonb;
  v_item jsonb;
  v_user_id text;
  v_patch jsonb;
  v_user_response jsonb;
  v_results jsonb := '[]'::jsonb;
  v_changed_count integer := 0;
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
  if jsonb_typeof(v_metadata) <> 'object' then
    raise exception using errcode = '22023', message = 'metadata must be a JSON object.';
  end if;

  perform pg_catalog.pg_advisory_xact_lock(
    pg_catalog.hashtextextended('hm_admin_commit_users_and_state:' || v_request_id, 0)
  );

  select operation, entity_id, response_payload
    into v_replay_operation, v_replay_entity_id, v_replay_response
  from public.hm_domain_write_requests
  where request_id = v_request_id;

  if found then
    if v_replay_operation <> 'user_state_commit' or v_replay_entity_id <> v_state_id then
      raise exception using
        errcode = '22023',
        message = 'request_id has already been used for a different operation or entity.';
    end if;
    return jsonb_set(v_replay_response, '{idempotent_replay}', 'true'::jsonb, true);
  end if;

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

    v_user_response := public.hm_admin_upsert_user(
      v_request_id || ':user:' || v_user_id,
      v_user_id,
      v_patch,
      p_actor_id,
      p_actor_email,
      p_source,
      v_metadata || jsonb_build_object('parent_request_id', v_request_id)
    );
    if coalesce((v_user_response->>'changed')::boolean, false) then
      v_changed_count := v_changed_count + 1;
    end if;
    v_results := v_results || jsonb_build_array(v_user_response);
  end loop;

  insert into public.healthyme_app_state(id, data, updated_at)
  values (v_state_id, v_state_data, now())
  on conflict (id) do update
    set data = excluded.data,
        updated_at = now();

  v_response := jsonb_build_object(
    'ok', true,
    'operation', 'user_state_commit',
    'request_id', v_request_id,
    'state_id', v_state_id,
    'changed_user_count', v_changed_count,
    'user_results', v_results,
    'idempotent_replay', false
  );

  insert into public.hm_domain_write_requests(request_id, operation, entity_id, response_payload)
  values (v_request_id, 'user_state_commit', v_state_id, v_response);

  return v_response;
end;
$function$;

revoke all on function public.hm_admin_commit_users_and_state(text, text, jsonb, jsonb, text, text, text, jsonb)
  from public, anon, authenticated;
grant execute on function public.hm_admin_commit_users_and_state(text, text, jsonb, jsonb, text, text, text, jsonb)
  to service_role;

comment on function public.hm_admin_commit_users_and_state(text, text, jsonb, jsonb, text, text, text, jsonb) is
  'Atomically commits changed canonical Users and the complete HealthyMe compatibility state.';

create or replace function public.hm_capture_direct_user_event()
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
  -- Contract writes run as the function owner and already append their own event.
  -- This trigger captures remaining direct service-role provisioning/linkage writes.
  if current_user <> 'service_role' then
    return new;
  end if;

  v_before := case when tg_op = 'INSERT' then null else to_jsonb(old) - 'password_hash' end;
  v_after := to_jsonb(new) - 'password_hash';

  if tg_op = 'INSERT' then
    select coalesce(array_agg(key order by key), '{}'::text[])
      into v_changed_fields
    from jsonb_object_keys(to_jsonb(new) - 'created_at' - 'updated_at') as key;
  else
    select coalesce(array_agg(key order by key), '{}'::text[])
      into v_changed_fields
    from jsonb_object_keys(to_jsonb(new) - 'created_at' - 'updated_at') as key
    where (to_jsonb(old) -> key) is distinct from (to_jsonb(new) -> key);
  end if;

  if coalesce(cardinality(v_changed_fields), 0) = 0 then
    return new;
  end if;

  v_request_id := 'direct-user:' || pg_catalog.gen_random_uuid()::text;
  insert into public.hm_user_events(
    request_id, user_id, event_type, source, changed_fields,
    before_snapshot, after_snapshot, metadata
  ) values (
    v_request_id,
    new.id,
    case when tg_op = 'INSERT' then 'created' else 'updated' end,
    'service_role_direct',
    v_changed_fields,
    v_before,
    v_after,
    jsonb_build_object('cutover_gate', 3, 'direct_write_captured', true)
  );

  return new;
end;
$function$;

revoke all on function public.hm_capture_direct_user_event() from public, anon, authenticated;
grant execute on function public.hm_capture_direct_user_event() to service_role;

drop trigger if exists hm_users_capture_direct_event on public.hm_users;
create trigger hm_users_capture_direct_event
after insert or update on public.hm_users
for each row execute function public.hm_capture_direct_user_event();
