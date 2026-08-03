-- HealthyMe Users/Workflow Batch 2B, Gate 2
-- Canonical Workflow status foundation only.
--
-- This migration centralises Workflow status derivation, prevents stored status
-- drift, and rewires existing internal Flutter status helpers without changing
-- public Flutter RPC signatures or payloads.

create or replace function public.hm_derive_workflow_status(
  p_laf_completed boolean,
  p_nsp1_completed boolean,
  p_nsp2_completed boolean,
  p_submitted_for_review boolean,
  p_admin_completed boolean,
  p_final_report_ready boolean
)
returns text
language sql
immutable
security invoker
set search_path = ''
as $function$
  select case
    when coalesce(p_final_report_ready, false) then 'finalized'
    when coalesce(p_admin_completed, false) then 'admin_completed'
    when coalesce(p_submitted_for_review, false) then 'submitted'
    when coalesce(p_laf_completed, false)
      or coalesce(p_nsp1_completed, false)
      or coalesce(p_nsp2_completed, false) then 'in_progress'
    else 'not_started'
  end;
$function$;

comment on function public.hm_derive_workflow_status(boolean, boolean, boolean, boolean, boolean, boolean) is
  'Canonical database-owned HealthyMe Workflow status derivation.';

revoke all on function public.hm_derive_workflow_status(boolean, boolean, boolean, boolean, boolean, boolean)
  from public, anon, authenticated;
grant execute on function public.hm_derive_workflow_status(boolean, boolean, boolean, boolean, boolean, boolean)
  to service_role;

create or replace function public.hm_flutter_nsp_workflow_status(
  p_laf_completed boolean,
  p_nsp1_completed boolean,
  p_nsp2_completed boolean,
  p_submitted_for_review boolean,
  p_admin_completed boolean,
  p_final_report_ready boolean
)
returns text
language sql
immutable
security invoker
set search_path = ''
as $function$
  select public.hm_derive_workflow_status(
    p_laf_completed,
    p_nsp1_completed,
    p_nsp2_completed,
    p_submitted_for_review,
    p_admin_completed,
    p_final_report_ready
  );
$function$;

revoke all on function public.hm_flutter_nsp_workflow_status(boolean, boolean, boolean, boolean, boolean, boolean)
  from public, anon, authenticated;
grant execute on function public.hm_flutter_nsp_workflow_status(boolean, boolean, boolean, boolean, boolean, boolean)
  to service_role;

create or replace function public.hm_flutter_workflow_status(p_workflow jsonb)
returns text
language sql
immutable
security invoker
set search_path = ''
as $function$
  select public.hm_derive_workflow_status(
    coalesce(nullif(p_workflow->>'laf_completed', '')::boolean, false),
    coalesce(nullif(p_workflow->>'nsp1_completed', '')::boolean, false),
    coalesce(nullif(p_workflow->>'nsp2_completed', '')::boolean, false),
    coalesce(nullif(p_workflow->>'submitted_for_review', '')::boolean, false),
    coalesce(nullif(p_workflow->>'admin_completed', '')::boolean, false),
    coalesce(nullif(p_workflow->>'final_report_ready', '')::boolean, false)
  );
$function$;

revoke all on function public.hm_flutter_workflow_status(jsonb)
  from public, anon, authenticated;
grant execute on function public.hm_flutter_workflow_status(jsonb)
  to service_role;

create or replace function public.hm_flutter_update_state_workflow(
  p_data jsonb,
  p_member_id text,
  p_nsp1_completed boolean default null,
  p_nsp2_completed boolean default null,
  p_submitted_for_review boolean default null
)
returns jsonb
language plpgsql
immutable
security invoker
set search_path = ''
as $function$
declare
  v_data jsonb := public.hm_flutter_ensure_app_state_shape(p_data);
  v_workflow jsonb := coalesce(v_data #> array['workflow', p_member_id], '{}'::jsonb);
  v_laf_completed boolean := coalesce(nullif(v_workflow->>'laf_completed', '')::boolean, false);
  v_admin_completed boolean := coalesce(nullif(v_workflow->>'admin_completed', '')::boolean, false);
  v_final_report_ready boolean := coalesce(nullif(v_workflow->>'final_report_ready', '')::boolean, false);
  v_nsp1_completed boolean := coalesce(p_nsp1_completed, nullif(v_workflow->>'nsp1_completed', '')::boolean, false);
  v_nsp2_completed boolean := coalesce(p_nsp2_completed, nullif(v_workflow->>'nsp2_completed', '')::boolean, false);
  v_submitted_for_review boolean := coalesce(p_submitted_for_review, nullif(v_workflow->>'submitted_for_review', '')::boolean, false);
  v_status text;
begin
  v_status := public.hm_derive_workflow_status(
    v_laf_completed,
    v_nsp1_completed,
    v_nsp2_completed,
    v_submitted_for_review,
    v_admin_completed,
    v_final_report_ready
  );

  v_workflow := v_workflow || jsonb_build_object(
    'laf_completed', v_laf_completed,
    'nsp1_completed', v_nsp1_completed,
    'nsp2_completed', v_nsp2_completed,
    'submitted_for_review', v_submitted_for_review,
    'admin_completed', v_admin_completed,
    'final_report_ready', v_final_report_ready,
    'workflow_status', v_status
  );

  return jsonb_set(v_data, array['workflow', p_member_id], v_workflow, true);
end;
$function$;

revoke all on function public.hm_flutter_update_state_workflow(jsonb, text, boolean, boolean, boolean)
  from public, anon, authenticated;
grant execute on function public.hm_flutter_update_state_workflow(jsonb, text, boolean, boolean, boolean)
  to service_role;

create or replace function public.hm_workflow_apply_canonical_status()
returns trigger
language plpgsql
security invoker
set search_path = ''
as $function$
begin
  new.workflow_status := public.hm_derive_workflow_status(
    new.laf_completed,
    new.nsp1_completed,
    new.nsp2_completed,
    new.submitted_for_review,
    new.admin_completed,
    new.final_report_ready
  );
  return new;
end;
$function$;

revoke all on function public.hm_workflow_apply_canonical_status()
  from public, anon, authenticated;
grant execute on function public.hm_workflow_apply_canonical_status()
  to service_role;

drop trigger if exists hm_workflow_canonical_status_insert on public.hm_workflow;
create trigger hm_workflow_canonical_status_insert
before insert on public.hm_workflow
for each row execute function public.hm_workflow_apply_canonical_status();

drop trigger if exists hm_workflow_canonical_status_update on public.hm_workflow;
create trigger hm_workflow_canonical_status_update
before update of laf_completed, nsp1_completed, nsp2_completed, submitted_for_review, admin_completed, final_report_ready, workflow_status
on public.hm_workflow
for each row execute function public.hm_workflow_apply_canonical_status();
