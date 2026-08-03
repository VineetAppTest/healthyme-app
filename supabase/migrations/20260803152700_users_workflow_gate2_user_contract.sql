-- HealthyMe Users/Workflow Batch 2B, Gate 2
-- Transactional, idempotent, service-role-only User write contract.
--
-- Password hashes may still be written for compatibility, but they are never
-- returned in the contract response or stored in audit snapshots.

create or replace function public.hm_admin_upsert_user(
  p_request_id text,
  p_user_id text,
  p_patch jsonb,
  p_actor_id text default null,
  p_actor_email text default null,
  p_source text default 'streamlit_admin',
  p_metadata jsonb default '{}'::jsonb
)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $function$
declare
  v_request_id text := btrim(coalesce(p_request_id, ''));
  v_user_id text := btrim(coalesce(p_user_id, ''));
  v_patch jsonb := coalesce(p_patch, '{}'::jsonb);
  v_metadata jsonb := coalesce(p_metadata, '{}'::jsonb);
  v_existing public.hm_users%rowtype;
  v_saved public.hm_users%rowtype;
  v_exists boolean := false;
  v_replay_operation text;
  v_replay_entity_id text;
  v_replay_response jsonb;
  v_unknown_keys text[];
  v_before_full jsonb;
  v_after_full jsonb;
  v_before_public jsonb;
  v_after_public jsonb;
  v_changed_fields text[] := '{}'::text[];
  v_event_id bigint;
  v_event_type text;
  v_response jsonb;
  v_target_name text;
  v_target_email text;
  v_target_password_hash text;
  v_target_role text;
  v_target_must_reset_password boolean;
  v_target_is_active boolean;
  v_target_auth_provider text;
  v_target_auth_user_id uuid;
  v_target_auth_migrated_at timestamptz;
begin
  if v_request_id = '' then
    raise exception using errcode = '22023', message = 'request_id is required.';
  end if;
  if v_user_id = '' then
    raise exception using errcode = '22023', message = 'user_id is required.';
  end if;
  if jsonb_typeof(v_patch) <> 'object' then
    raise exception using errcode = '22023', message = 'patch must be a JSON object.';
  end if;
  if jsonb_typeof(v_metadata) <> 'object' then
    raise exception using errcode = '22023', message = 'metadata must be a JSON object.';
  end if;

  perform pg_catalog.pg_advisory_xact_lock(
    pg_catalog.hashtextextended('hm_admin_upsert_user:' || v_request_id, 0)
  );

  select operation, entity_id, response_payload
    into v_replay_operation, v_replay_entity_id, v_replay_response
  from public.hm_domain_write_requests
  where request_id = v_request_id;

  if found then
    if v_replay_operation <> 'user_upsert' or v_replay_entity_id <> v_user_id then
      raise exception using
        errcode = '22023',
        message = 'request_id has already been used for a different operation or entity.';
    end if;
    return jsonb_set(v_replay_response, '{idempotent_replay}', 'true'::jsonb, true);
  end if;

  select array_agg(key order by key)
    into v_unknown_keys
  from jsonb_object_keys(v_patch) as key
  where key not in (
    'name', 'email', 'password_hash', 'role', 'must_reset_password',
    'is_active', 'auth_provider', 'auth_user_id', 'auth_migrated_at'
  );

  if coalesce(cardinality(v_unknown_keys), 0) > 0 then
    raise exception using
      errcode = '22023',
      message = 'Unsupported User patch keys: ' || array_to_string(v_unknown_keys, ', ');
  end if;

  select * into v_existing
  from public.hm_users
  where id = v_user_id
  for update;

  v_exists := found;
  if v_exists then
    v_before_full := to_jsonb(v_existing);
    v_target_name := case when v_patch ? 'name' then coalesce(v_patch->>'name', '') else v_existing.name end;
    v_target_email := case when v_patch ? 'email' then lower(btrim(coalesce(v_patch->>'email', ''))) else v_existing.email end;
    v_target_password_hash := case when v_patch ? 'password_hash' then coalesce(v_patch->>'password_hash', '') else v_existing.password_hash end;
    v_target_role := case when v_patch ? 'role' then lower(btrim(coalesce(v_patch->>'role', ''))) else v_existing.role end;
    v_target_must_reset_password := case when v_patch ? 'must_reset_password' then (v_patch->>'must_reset_password')::boolean else v_existing.must_reset_password end;
    v_target_is_active := case when v_patch ? 'is_active' then (v_patch->>'is_active')::boolean else v_existing.is_active end;
    v_target_auth_provider := case when v_patch ? 'auth_provider' then lower(btrim(coalesce(v_patch->>'auth_provider', ''))) else v_existing.auth_provider end;
    v_target_auth_user_id := case when v_patch ? 'auth_user_id' then nullif(v_patch->>'auth_user_id', '')::uuid else v_existing.auth_user_id end;
    v_target_auth_migrated_at := case when v_patch ? 'auth_migrated_at' then nullif(v_patch->>'auth_migrated_at', '')::timestamptz else v_existing.auth_migrated_at end;
    v_event_type := 'updated';

    if v_target_email = '' then
      raise exception using errcode = '22023', message = 'email cannot be blank.';
    end if;
    if v_target_role = '' then
      raise exception using errcode = '22023', message = 'role cannot be blank.';
    end if;
    if v_target_auth_provider = '' then
      raise exception using errcode = '22023', message = 'auth_provider cannot be blank.';
    end if;

    if row(
      v_existing.name, v_existing.email, v_existing.password_hash, v_existing.role,
      v_existing.must_reset_password, v_existing.is_active, v_existing.auth_provider,
      v_existing.auth_user_id, v_existing.auth_migrated_at
    ) is distinct from row(
      v_target_name, v_target_email, v_target_password_hash, v_target_role,
      v_target_must_reset_password, v_target_is_active, v_target_auth_provider,
      v_target_auth_user_id, v_target_auth_migrated_at
    ) then
      update public.hm_users
         set name = v_target_name,
             email = v_target_email,
             password_hash = v_target_password_hash,
             role = v_target_role,
             must_reset_password = v_target_must_reset_password,
             is_active = v_target_is_active,
             auth_provider = v_target_auth_provider,
             auth_user_id = v_target_auth_user_id,
             auth_migrated_at = v_target_auth_migrated_at
       where id = v_user_id
       returning * into v_saved;
    else
      v_saved := v_existing;
    end if;
  else
    v_target_name := coalesce(v_patch->>'name', '');
    v_target_email := lower(btrim(coalesce(v_patch->>'email', '')));
    v_target_password_hash := coalesce(v_patch->>'password_hash', '');
    v_target_role := lower(btrim(coalesce(v_patch->>'role', '')));
    v_target_must_reset_password := coalesce((v_patch->>'must_reset_password')::boolean, false);
    v_target_is_active := coalesce((v_patch->>'is_active')::boolean, true);
    v_target_auth_provider := coalesce(nullif(lower(btrim(v_patch->>'auth_provider')), ''), 'oidc');
    v_target_auth_user_id := nullif(v_patch->>'auth_user_id', '')::uuid;
    v_target_auth_migrated_at := nullif(v_patch->>'auth_migrated_at', '')::timestamptz;
    v_event_type := 'created';

    if v_target_email = '' then
      raise exception using errcode = '22023', message = 'email is required when creating a User.';
    end if;
    if v_target_role = '' then
      raise exception using errcode = '22023', message = 'role is required when creating a User.';
    end if;

    insert into public.hm_users (
      id, name, email, password_hash, role, must_reset_password,
      is_active, auth_provider, auth_user_id, auth_migrated_at
    ) values (
      v_user_id, v_target_name, v_target_email, v_target_password_hash,
      v_target_role, v_target_must_reset_password, v_target_is_active,
      v_target_auth_provider, v_target_auth_user_id, v_target_auth_migrated_at
    ) returning * into v_saved;
  end if;

  v_after_full := to_jsonb(v_saved);
  v_before_public := case when v_before_full is null then null else v_before_full - 'password_hash' end;
  v_after_public := v_after_full - 'password_hash';

  if v_before_full is null then
    select coalesce(array_agg(key order by key), '{}'::text[])
      into v_changed_fields
    from jsonb_object_keys(v_after_full - 'created_at' - 'updated_at') as key;
  else
    select coalesce(array_agg(key order by key), '{}'::text[])
      into v_changed_fields
    from jsonb_object_keys(v_after_full - 'created_at' - 'updated_at') as key
    where (v_before_full -> key) is distinct from (v_after_full -> key);
  end if;

  if coalesce(cardinality(v_changed_fields), 0) > 0 then
    insert into public.hm_user_events (
      request_id, user_id, event_type, actor_id, actor_email, source,
      changed_fields, before_snapshot, after_snapshot, metadata
    ) values (
      v_request_id, v_user_id, v_event_type,
      nullif(btrim(coalesce(p_actor_id, '')), ''),
      nullif(lower(btrim(coalesce(p_actor_email, ''))), ''),
      coalesce(nullif(btrim(coalesce(p_source, '')), ''), 'streamlit_admin'),
      v_changed_fields, v_before_public, v_after_public, v_metadata
    ) returning event_id into v_event_id;
  end if;

  v_response := jsonb_build_object(
    'ok', true,
    'operation', 'user_upsert',
    'request_id', v_request_id,
    'user_id', v_user_id,
    'changed', coalesce(cardinality(v_changed_fields), 0) > 0,
    'changed_fields', to_jsonb(v_changed_fields),
    'event_id', v_event_id,
    'record', v_after_public,
    'idempotent_replay', false
  );

  insert into public.hm_domain_write_requests (
    request_id, operation, entity_id, response_payload
  ) values (
    v_request_id, 'user_upsert', v_user_id, v_response
  );

  return v_response;
end;
$function$;

revoke all on function public.hm_admin_upsert_user(text, text, jsonb, text, text, text, jsonb)
  from public, anon, authenticated;
grant execute on function public.hm_admin_upsert_user(text, text, jsonb, text, text, text, jsonb)
  to service_role;

comment on function public.hm_admin_upsert_user(text, text, jsonb, text, text, text, jsonb) is
  'Transactional idempotent service-side User write contract with append-only audit.';
