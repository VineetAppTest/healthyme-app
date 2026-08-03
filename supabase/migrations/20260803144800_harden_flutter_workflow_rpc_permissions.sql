-- HealthyMe Users/Workflow Batch 2B, Gate 1
-- Harden the Flutter member identity helper and NSP Workflow helper before
-- any broader User or Workflow authority cutover.
--
-- Runtime compatibility:
-- - Public Flutter RPC signatures are unchanged.
-- - Existing LAF/NSP shared-state projection is unchanged.
-- - Authenticated members continue using the outer Flutter RPCs.
-- - No User, Workflow, assessment or session row is migrated or deleted.

create or replace function public.hm_flutter_current_member_id()
returns text
language plpgsql
security definer
set search_path = ''
as $function$
declare
  v_auth_user_id uuid := auth.uid();
  v_email text := lower(coalesce(auth.jwt() ->> 'email', ''));
  v_member_id text;
  v_count integer;
begin
  if v_auth_user_id is null then
    raise exception using
      errcode = '28000',
      message = 'No Supabase Auth user was found in the current request.';
  end if;

  select count(*)
    into v_count
  from public.hm_users u
  where lower(coalesce(u.role, '')) = 'member'
    and u.is_active is true
    and (
      u.auth_user_id = v_auth_user_id
      or (
        u.auth_user_id is null
        and v_email <> ''
        and lower(u.email) = v_email
      )
    );

  if v_count = 0 then
    raise exception using
      errcode = '42501',
      message = 'Current login is not linked to an active HealthyMe member profile.';
  end if;

  if v_count > 1 then
    raise exception using
      errcode = '21000',
      message = 'More than one active HealthyMe member profile matches this login. Admin must resolve duplicates before mobile access.';
  end if;

  select u.id::text
    into v_member_id
  from public.hm_users u
  where lower(coalesce(u.role, '')) = 'member'
    and u.is_active is true
    and (
      u.auth_user_id = v_auth_user_id
      or (
        u.auth_user_id is null
        and v_email <> ''
        and lower(u.email) = v_email
      )
    )
  order by case when u.auth_user_id = v_auth_user_id then 0 else 1 end
  limit 1;

  return v_member_id;
end;
$function$;

comment on function public.hm_flutter_current_member_id() is
  'Resolves only the active HealthyMe member linked to the current authenticated Supabase identity.';

create or replace function public.hm_flutter_upsert_nsp_workflow(
  p_member_id text,
  p_nsp1_completed boolean default null,
  p_nsp2_completed boolean default null,
  p_submitted_for_review boolean default null
)
returns void
language plpgsql
security definer
set search_path = ''
as $function$
declare
  v_authenticated_member_id text;
  v_existing public.hm_workflow%rowtype;
  v_laf_completed boolean := false;
  v_nsp1_completed boolean := false;
  v_nsp2_completed boolean := false;
  v_submitted_for_review boolean := false;
  v_admin_completed boolean := false;
  v_final_report_ready boolean := false;
  v_status text;
begin
  v_authenticated_member_id := public.hm_flutter_current_member_id();

  if nullif(btrim(p_member_id), '') is null
     or p_member_id <> v_authenticated_member_id then
    raise exception using
      errcode = '42501',
      message = 'Workflow updates are limited to the current authenticated HealthyMe member.';
  end if;

  select *
    into v_existing
  from public.hm_workflow
  where user_id = v_authenticated_member_id
  limit 1;

  v_laf_completed := coalesce(v_existing.laf_completed, false);
  v_nsp1_completed := coalesce(p_nsp1_completed, v_existing.nsp1_completed, false);
  v_nsp2_completed := coalesce(p_nsp2_completed, v_existing.nsp2_completed, false);
  v_submitted_for_review := coalesce(p_submitted_for_review, v_existing.submitted_for_review, false);
  v_admin_completed := coalesce(v_existing.admin_completed, false);
  v_final_report_ready := coalesce(v_existing.final_report_ready, false);

  v_status := public.hm_flutter_nsp_workflow_status(
    v_laf_completed,
    v_nsp1_completed,
    v_nsp2_completed,
    v_submitted_for_review,
    v_admin_completed,
    v_final_report_ready
  );

  insert into public.hm_workflow (
    user_id,
    laf_completed,
    nsp1_completed,
    nsp2_completed,
    submitted_for_review,
    admin_completed,
    final_report_ready,
    workflow_status,
    updated_at
  ) values (
    v_authenticated_member_id,
    v_laf_completed,
    v_nsp1_completed,
    v_nsp2_completed,
    v_submitted_for_review,
    v_admin_completed,
    v_final_report_ready,
    v_status,
    now()
  )
  on conflict (user_id) do update set
    nsp1_completed = excluded.nsp1_completed,
    nsp2_completed = excluded.nsp2_completed,
    submitted_for_review = excluded.submitted_for_review,
    workflow_status = excluded.workflow_status,
    updated_at = now();
end;
$function$;

comment on function public.hm_flutter_upsert_nsp_workflow(text, boolean, boolean, boolean) is
  'Internal Flutter Workflow helper. Verifies that the supplied member ID is the current authenticated member before writing.';

-- Supabase functions are executable by PUBLIC by default. Remove public and
-- client-role execution explicitly, then expose only the identity helper that
-- is safe for authenticated self-resolution. Outer authenticated Flutter RPCs
-- continue to call the internal Workflow helper as their function owner.
revoke all on function public.hm_flutter_current_member_id() from PUBLIC;
revoke all on function public.hm_flutter_current_member_id() from anon;
revoke all on function public.hm_flutter_current_member_id() from authenticated;
grant execute on function public.hm_flutter_current_member_id() to authenticated;

revoke all on function public.hm_flutter_upsert_nsp_workflow(text, boolean, boolean, boolean) from PUBLIC;
revoke all on function public.hm_flutter_upsert_nsp_workflow(text, boolean, boolean, boolean) from anon;
revoke all on function public.hm_flutter_upsert_nsp_workflow(text, boolean, boolean, boolean) from authenticated;
