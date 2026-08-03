-- HealthyMe Users/Workflow Batch 2B, Gate 2
-- Transactional, idempotent, service-role-only Workflow write contract.
--
-- workflow_status is not accepted from callers. The canonical table trigger
-- derives it from the six lifecycle booleans before each insert or update.

create or replace function public.hm_admin_upsert_workflow(
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
  v_existing public.hm_workflow%rowtype;
  v_saved public.hm_workflow%rowtype;
  v_exists boolean := false;
  v_replay_operation text;
  v_replay_entity_id text;
  v_replay_response jsonb;
  v_unknown_keys text[];
  v_before jsonb;
  v_after jsonb;
  v_changed_fields text[] := '{}'::text[];
  v_event_id bigint;
  v_event_type text;
  v_response jsonb;
  v_target_laf_completed boolean;
  v_target_nsp1_completed boolean;
  v_target_nsp2_completed boolean;
  v_target_submitted_for_review boolean;
  v_target_admin_completed boolean;
  v_target_final_report_ready boolean;
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
    pg_catalog.hashtextextended('hm_admin_upsert_workflow:' || v_request_id, 0)
  );

  select operation, entity_id, response_payload
    into v_replay_operation, v_replay_entity_id, v_replay_response
  from public.hm_domain_write_requests
  where request_id = v_request_id;

  if found then
    if v_replay_operation <> 'workflow_upsert' or v_replay_entity_id <> v_user_id then
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
    'laf_completed', 'nsp1_completed', 'nsp2_completed',
    'submitted_for_review', 'admin_completed', 'final_report_ready'
  );

  if coalesce(cardinality(v_unknown_keys), 0) > 0 then
    raise exception using
      errcode = '22023',
      message = 'Unsupported Workflow patch keys: ' || array_to_string(v_unknown_keys, ', ');
  end if;

  if not exists (select 1 from public.hm_users where id = v_user_id) then
    raise exception using errcode = '23503', message = 'Workflow User does not exist.';
  end if;

  select * into v_existing
  from public.hm_workflow
  where user_id = v_user_id
  for update;

  v_exists := found;
  if v_exists then
    v_before := to_jsonb(v_existing);
    v_target_laf_completed := case when v_patch ? 'laf_completed' then (v_patch->>'laf_completed')::boolean else v_existing.laf_completed end;
    v_target_nsp1_completed := case when v_patch ? 'nsp1_completed' then (v_patch->>'nsp1_completed')::boolean else v_existing.nsp1_completed end;
    v_target_nsp2_completed := case when v_patch ? 'nsp2_completed' then (v_patch->>'nsp2_completed')::boolean else v_existing.nsp2_completed end;
    v_target_submitted_for_review := case when v_patch ? 'submitted_for_review' then (v_patch->>'submitted_for_review')::boolean else v_existing.submitted_for_review end;
    v_target_admin_completed := case when v_patch ? 'admin_completed' then (v_patch->>'admin_completed')::boolean else v_existing.admin_completed end;
    v_target_final_report_ready := case when v_patch ? 'final_report_ready' then (v_patch->>'final_report_ready')::boolean else v_existing.final_report_ready end;
    v_event_type := 'updated';

    if row(
      v_existing.laf_completed, v_existing.nsp1_completed, v_existing.nsp2_completed,
      v_existing.submitted_for_review, v_existing.admin_completed, v_existing.final_report_ready
    ) is distinct from row(
      v_target_laf_completed, v_target_nsp1_completed, v_target_nsp2_completed,
      v_target_submitted_for_review, v_target_admin_completed, v_target_final_report_ready
    ) then
      update public.hm_workflow
         set laf_completed = v_target_laf_completed,
             nsp1_completed = v_target_nsp1_completed,
             nsp2_completed = v_target_nsp2_completed,
             submitted_for_review = v_target_submitted_for_review,
             admin_completed = v_target_admin_completed,
             final_report_ready = v_target_final_report_ready
       where user_id = v_user_id
       returning * into v_saved;
    else
      v_saved := v_existing;
    end if;
  else
    v_target_laf_completed := coalesce((v_patch->>'laf_completed')::boolean, false);
    v_target_nsp1_completed := coalesce((v_patch->>'nsp1_completed')::boolean, false);
    v_target_nsp2_completed := coalesce((v_patch->>'nsp2_completed')::boolean, false);
    v_target_submitted_for_review := coalesce((v_patch->>'submitted_for_review')::boolean, false);
    v_target_admin_completed := coalesce((v_patch->>'admin_completed')::boolean, false);
    v_target_final_report_ready := coalesce((v_patch->>'final_report_ready')::boolean, false);
    v_event_type := 'created';

    insert into public.hm_workflow (
      user_id, laf_completed, nsp1_completed, nsp2_completed,
      submitted_for_review, admin_completed, final_report_ready
    ) values (
      v_user_id, v_target_laf_completed, v_target_nsp1_completed,
      v_target_nsp2_completed, v_target_submitted_for_review,
      v_target_admin_completed, v_target_final_report_ready
    ) returning * into v_saved;
  end if;

  v_after := to_jsonb(v_saved);

  if v_before is null then
    select coalesce(array_agg(key order by key), '{}'::text[])
      into v_changed_fields
    from jsonb_object_keys(v_after - 'created_at' - 'updated_at' - 'user_id') as key;
  else
    select coalesce(array_agg(key order by key), '{}'::text[])
      into v_changed_fields
    from jsonb_object_keys(v_after - 'created_at' - 'updated_at' - 'user_id') as key
    where (v_before -> key) is distinct from (v_after -> key);
  end if;

  if coalesce(cardinality(v_changed_fields), 0) > 0 then
    insert into public.hm_workflow_events (
      request_id, user_id, event_type, actor_id, actor_email, source,
      changed_fields, before_snapshot, after_snapshot, metadata
    ) values (
      v_request_id, v_user_id, v_event_type,
      nullif(btrim(coalesce(p_actor_id, '')), ''),
      nullif(lower(btrim(coalesce(p_actor_email, ''))), ''),
      coalesce(nullif(btrim(coalesce(p_source, '')), ''), 'streamlit_admin'),
      v_changed_fields, v_before, v_after, v_metadata
    ) returning event_id into v_event_id;
  end if;

  v_response := jsonb_build_object(
    'ok', true,
    'operation', 'workflow_upsert',
    'request_id', v_request_id,
    'user_id', v_user_id,
    'changed', coalesce(cardinality(v_changed_fields), 0) > 0,
    'changed_fields', to_jsonb(v_changed_fields),
    'event_id', v_event_id,
    'record', v_after,
    'idempotent_replay', false
  );

  insert into public.hm_domain_write_requests (
    request_id, operation, entity_id, response_payload
  ) values (
    v_request_id, 'workflow_upsert', v_user_id, v_response
  );

  return v_response;
end;
$function$;

revoke all on function public.hm_admin_upsert_workflow(text, text, jsonb, text, text, text, jsonb)
  from public, anon, authenticated;
grant execute on function public.hm_admin_upsert_workflow(text, text, jsonb, text, text, text, jsonb)
  to service_role;

comment on function public.hm_admin_upsert_workflow(text, text, jsonb, text, text, text, jsonb) is
  'Transactional idempotent service-side Workflow write contract with canonical status and append-only audit.';
