-- Package Hardening 1, 2 and 3: controlled Admin/Super Admin write contracts.

create or replace function public.hm_package_require_admin(p_actor_id text)
returns void
language plpgsql
stable
security definer
set search_path = public
as $$
begin
  if not exists (
    select 1
    from public.hm_users u
    where u.id = trim(coalesce(p_actor_id, ''))
      and lower(coalesce(u.role, '')) in ('admin','super_admin')
      and coalesce(u.is_active, true) = true
  ) then
    raise exception 'Admin or Super Admin authorization is required.';
  end if;
end;
$$;

create or replace function public.hm_admin_save_package(
  p_package_id text,
  p_package_name text,
  p_session_count integer,
  p_cost_per_session numeric,
  p_total_value numeric,
  p_currency text,
  p_inclusions jsonb,
  p_status text,
  p_actor_id text
)
returns jsonb
language plpgsql
security definer
set search_path = public
as $$
declare
  v_id text := trim(coalesce(p_package_id, ''));
  v_name text := trim(coalesce(p_package_name, ''));
  v_sessions integer := greatest(coalesce(p_session_count, 1), 1);
  v_cost numeric := greatest(coalesce(p_cost_per_session, 0), 0);
  v_total numeric;
  v_status text := lower(trim(coalesce(p_status, 'active')));
  v_row public.hm_packages%rowtype;
begin
  perform public.hm_package_require_admin(p_actor_id);
  if v_name = '' then
    raise exception 'Package name is required.';
  end if;
  if v_status not in ('active','inactive') then
    raise exception 'Package status must be active or inactive.';
  end if;
  v_total := greatest(coalesce(p_total_value, v_sessions * v_cost), 0);

  if v_id = '' then
    v_id := substr(replace(gen_random_uuid()::text, '-', ''), 1, 8);
    insert into public.hm_packages (
      id, package_name, session_count, cost_per_session, total_value,
      currency, inclusions, inclusions_informational_only, status,
      created_by, updated_by
    ) values (
      v_id, v_name, v_sessions, v_cost, v_total,
      coalesce(nullif(trim(p_currency), ''), 'INR'),
      coalesce(p_inclusions, '{}'::jsonb), true, v_status,
      p_actor_id, p_actor_id
    ) returning * into v_row;
  else
    update public.hm_packages
    set package_name = v_name,
        session_count = v_sessions,
        cost_per_session = v_cost,
        total_value = v_total,
        currency = coalesce(nullif(trim(p_currency), ''), 'INR'),
        inclusions = coalesce(p_inclusions, '{}'::jsonb),
        inclusions_informational_only = true,
        status = v_status,
        updated_at = now(),
        updated_by = p_actor_id
    where id = v_id
    returning * into v_row;
    if not found then
      raise exception 'Selected package was not found.';
    end if;
  end if;

  return to_jsonb(v_row) || jsonb_build_object(
    'commercial_snapshot_note',
    'Package Library changes apply to future subscriptions only. Existing subscriptions retain their saved commercial snapshot.',
    'inclusions_rule',
    'Package inclusions are informational only and do not control HealthyMe module access.'
  );
end;
$$;

create or replace function public.hm_admin_assign_member_package(
  p_member_id text,
  p_package_id text,
  p_start_date date,
  p_expiry_date date,
  p_payment_status text,
  p_amount_paid numeric,
  p_payment_date date,
  p_payment_reference text,
  p_assignment_type text,
  p_unused_sessions_decision text,
  p_replacement_reason text,
  p_manual_adjustment_sessions integer,
  p_actor_id text
)
returns jsonb
language plpgsql
security definer
set search_path = public
as $$
declare
  v_package public.hm_packages%rowtype;
  v_member public.hm_users%rowtype;
  v_current public.hm_member_package_subscriptions%rowtype;
  v_new public.hm_member_package_subscriptions%rowtype;
  v_metrics jsonb := '{}'::jsonb;
  v_available integer := 0;
  v_remaining integer := 0;
  v_reserved integer := 0;
  v_carry integer := 0;
  v_decision text := lower(trim(coalesce(p_unused_sessions_decision, '')));
  v_reason text := trim(coalesce(p_replacement_reason, ''));
  v_assignment_type text := lower(trim(coalesce(p_assignment_type, 'replacement')));
  v_payment_status text := lower(trim(coalesce(p_payment_status, 'not_recorded')));
  v_amount_paid numeric := greatest(coalesce(p_amount_paid, 0), 0);
  v_outstanding numeric := 0;
  v_new_id text := substr(replace(gen_random_uuid()::text, '-', ''), 1, 8);
  v_now timestamptz := now();
begin
  perform public.hm_package_require_admin(p_actor_id);

  select * into v_member
  from public.hm_users
  where id = trim(coalesce(p_member_id, ''))
    and lower(coalesce(role, '')) = 'member'
    and coalesce(is_active, true) = true;
  if not found then
    raise exception 'Selected active member was not found.';
  end if;

  select * into v_package
  from public.hm_packages
  where id = trim(coalesce(p_package_id, ''))
    and status = 'active';
  if not found then
    raise exception 'Selected active package was not found.';
  end if;

  if p_expiry_date is not null and p_expiry_date < coalesce(p_start_date, current_date) then
    raise exception 'Expiry date cannot be earlier than the start date.';
  end if;
  if v_payment_status not in ('not_recorded','unpaid','partially_paid','paid','complimentary','refunded') then
    raise exception 'Select a valid payment status.';
  end if;
  if v_assignment_type not in ('replacement','renewal') then
    raise exception 'Assignment type must be replacement or renewal.';
  end if;

  select * into v_current
  from public.hm_member_package_subscriptions
  where member_id = v_member.id
    and status in ('active','paused')
  order by subscribed_at desc
  limit 1
  for update;

  if found then
    v_metrics := public.hm_package_subscription_metrics(v_current.id);
    v_available := coalesce((v_metrics ->> 'sessions_available_to_schedule')::integer, 0);
    v_remaining := coalesce((v_metrics ->> 'sessions_remaining')::integer, 0);
    v_reserved := coalesce((v_metrics ->> 'sessions_reserved')::integer, 0);

    if v_reason = '' then
      raise exception 'A replacement or renewal reason is required.';
    end if;
    if v_decision not in ('expire_unused','carry_forward','retain_until_exhausted','manual_adjustment') then
      raise exception 'Select how unused sessions should be handled.';
    end if;

    if v_decision = 'retain_until_exhausted' and v_remaining > 0 then
      return jsonb_build_object(
        'status', 'retained',
        'assigned', false,
        'message', 'The current package remains active until its remaining sessions are exhausted.',
        'current_subscription', to_jsonb(v_current),
        'current_metrics', v_metrics
      );
    end if;

    if v_decision = 'carry_forward' then
      v_carry := v_available;
    elsif v_decision = 'manual_adjustment' then
      if p_manual_adjustment_sessions is null or p_manual_adjustment_sessions < 0 then
        raise exception 'Manual adjustment sessions must be zero or greater.';
      end if;
      v_carry := p_manual_adjustment_sessions;
    else
      v_carry := 0;
    end if;

    update public.hm_member_package_subscriptions
    set status = 'replaced',
        ended_at = v_now,
        end_reason = case when v_assignment_type = 'renewal' then 'renewed' else 'replaced' end,
        replacement_reason = v_reason,
        unused_sessions_decision = v_decision,
        unused_sessions_at_end = v_available,
        carry_forward_sessions = v_carry,
        replaced_by_subscription_id = v_new_id,
        updated_at = v_now,
        updated_by = p_actor_id
    where id = v_current.id;
  else
    v_current.id := null;
    v_decision := '';
    v_reason := '';
    v_carry := 0;
  end if;

  v_outstanding := case
    when v_payment_status in ('complimentary','refunded') then 0
    else greatest(v_package.total_value - v_amount_paid, 0)
  end;

  insert into public.hm_member_package_subscriptions (
    id, member_id, member_name, member_email,
    package_id, package_name, session_count, cost_per_session, total_value,
    currency, inclusions, inclusions_informational_only,
    start_date, expiry_date, status,
    payment_status, amount_paid, outstanding_amount, payment_date, payment_reference,
    subscribed_at, renewed_from_subscription_id,
    created_by, assigned_by, updated_by
  ) values (
    v_new_id, v_member.id, v_member.name, v_member.email,
    v_package.id, v_package.package_name, v_package.session_count,
    v_package.cost_per_session, v_package.total_value,
    v_package.currency, v_package.inclusions, true,
    coalesce(p_start_date, current_date), p_expiry_date, 'active',
    v_payment_status, v_amount_paid, v_outstanding, p_payment_date,
    trim(coalesce(p_payment_reference, '')),
    v_now,
    case when v_assignment_type = 'renewal' then v_current.id else null end,
    p_actor_id, p_actor_id, p_actor_id
  ) returning * into v_new;

  if v_carry > 0 then
    insert into public.hm_package_usage_events (
      subscription_id, member_id, event_type, allowance_delta,
      reason, source, dedupe_key, metadata, created_by
    ) values (
      v_new.id, v_new.member_id, 'carry_forward_in', v_carry,
      v_reason, 'package_assignment',
      'carry_forward_in|' || v_new.id,
      jsonb_build_object(
        'from_subscription_id', coalesce(v_current.id, ''),
        'unused_sessions_decision', v_decision
      ),
      p_actor_id
    );
  end if;

  if v_current.id is not null then
    insert into public.hm_package_subscription_events (
      subscription_id, member_id, event_type, reason, metadata, created_by
    ) values (
      v_current.id, v_current.member_id,
      case when v_assignment_type = 'renewal' then 'renewed' else 'replaced' end,
      v_reason,
      jsonb_build_object(
        'new_subscription_id', v_new.id,
        'unused_sessions_decision', v_decision,
        'sessions_remaining', v_remaining,
        'sessions_reserved', v_reserved,
        'sessions_available_to_schedule', v_available,
        'sessions_carried_or_adjusted', v_carry
      ),
      p_actor_id
    );
  end if;

  insert into public.hm_package_subscription_events (
    subscription_id, member_id, event_type, reason, metadata, created_by
  ) values (
    v_new.id, v_new.member_id,
    case when v_assignment_type = 'renewal' then 'renewal_assigned' else 'package_assigned' end,
    v_reason,
    jsonb_build_object(
      'prior_subscription_id', coalesce(v_current.id, ''),
      'commercial_snapshot', true,
      'inclusions_informational_only', true
    ),
    p_actor_id
  );

  if v_amount_paid > 0 or trim(coalesce(p_payment_reference, '')) <> '' then
    insert into public.hm_package_payments (
      subscription_id, member_id, payment_type, amount, currency,
      payment_status, payment_date, reference, note, created_by
    ) values (
      v_new.id, v_new.member_id, 'payment', v_amount_paid, v_new.currency,
      case when v_payment_status = 'paid' then 'confirmed' else 'recorded' end,
      p_payment_date, trim(coalesce(p_payment_reference, '')),
      'Recorded during package assignment.', p_actor_id
    );
  end if;

  return jsonb_build_object(
    'status', 'assigned',
    'assigned', true,
    'subscription', to_jsonb(v_new),
    'metrics', public.hm_package_subscription_metrics(v_new.id),
    'prior_subscription_id', coalesce(v_current.id, ''),
    'inclusions_rule', 'Package inclusions are informational only.'
  );
end;
$$;

create or replace function public.hm_admin_adjust_package_sessions(
  p_subscription_id text,
  p_adjustment_type text,
  p_session_delta integer,
  p_reason text,
  p_actor_id text
)
returns jsonb
language plpgsql
security definer
set search_path = public
as $$
declare
  v_subscription public.hm_member_package_subscriptions%rowtype;
  v_type text := lower(trim(coalesce(p_adjustment_type, '')));
  v_event_type text;
  v_allowance_delta integer := 0;
  v_consumption_delta integer := 0;
  v_reason text := trim(coalesce(p_reason, ''));
begin
  perform public.hm_package_require_admin(p_actor_id);
  if v_reason = '' then
    raise exception 'An adjustment reason is required.';
  end if;
  if coalesce(p_session_delta, 0) = 0 then
    raise exception 'Adjustment sessions cannot be zero.';
  end if;

  select * into v_subscription
  from public.hm_member_package_subscriptions
  where id = trim(coalesce(p_subscription_id, ''));
  if not found then
    raise exception 'Selected subscription was not found.';
  end if;

  if v_type = 'complimentary' then
    if p_session_delta < 1 then
      raise exception 'Complimentary sessions must be greater than zero.';
    end if;
    v_event_type := 'complimentary_added';
    v_allowance_delta := p_session_delta;
  elsif v_type = 'manual_allowance' then
    v_event_type := 'manual_allowance_adjustment';
    v_allowance_delta := p_session_delta;
  elsif v_type = 'manual_consumption' then
    v_event_type := 'manual_consumption_adjustment';
    v_consumption_delta := p_session_delta;
  else
    raise exception 'Select complimentary, manual allowance or manual consumption.';
  end if;

  insert into public.hm_package_usage_events (
    subscription_id, member_id, event_type,
    allowance_delta, consumption_delta, reason, source, metadata, created_by
  ) values (
    v_subscription.id, v_subscription.member_id, v_event_type,
    v_allowance_delta, v_consumption_delta, v_reason,
    'admin_adjustment',
    jsonb_build_object('package_name', v_subscription.package_name),
    p_actor_id
  );

  update public.hm_member_package_subscriptions
  set updated_at = now(), updated_by = p_actor_id
  where id = v_subscription.id;

  return jsonb_build_object(
    'subscription_id', v_subscription.id,
    'event_type', v_event_type,
    'metrics', public.hm_package_subscription_metrics(v_subscription.id)
  );
end;
$$;

create or replace function public.hm_admin_update_package_subscription(
  p_subscription_id text,
  p_action text,
  p_reason text,
  p_expiry_date date,
  p_payment_status text,
  p_amount numeric,
  p_payment_date date,
  p_reference text,
  p_actor_id text
)
returns jsonb
language plpgsql
security definer
set search_path = public
as $$
declare
  v_subscription public.hm_member_package_subscriptions%rowtype;
  v_action text := lower(trim(coalesce(p_action, '')));
  v_reason text := trim(coalesce(p_reason, ''));
  v_payment_status text := lower(trim(coalesce(p_payment_status, '')));
  v_amount numeric := greatest(coalesce(p_amount, 0), 0);
  v_event_type text;
  v_now timestamptz := now();
begin
  perform public.hm_package_require_admin(p_actor_id);
  select * into v_subscription
  from public.hm_member_package_subscriptions
  where id = trim(coalesce(p_subscription_id, ''))
  for update;
  if not found then
    raise exception 'Selected subscription was not found.';
  end if;

  if v_action = 'payment_update' then
    if v_payment_status not in ('not_recorded','unpaid','partially_paid','paid','complimentary','refunded') then
      raise exception 'Select a valid payment status.';
    end if;
    update public.hm_member_package_subscriptions
    set payment_status = v_payment_status,
        amount_paid = case when v_payment_status = 'complimentary' then 0 else v_amount end,
        outstanding_amount = case
          when v_payment_status in ('complimentary','refunded') then 0
          else greatest(total_value - v_amount, 0)
        end,
        payment_date = p_payment_date,
        payment_reference = trim(coalesce(p_reference, '')),
        updated_at = v_now,
        updated_by = p_actor_id
    where id = v_subscription.id;
    if v_amount > 0 or trim(coalesce(p_reference, '')) <> '' then
      insert into public.hm_package_payments (
        subscription_id, member_id, payment_type, amount, currency,
        payment_status, payment_date, reference, note, created_by
      ) values (
        v_subscription.id, v_subscription.member_id, 'payment', v_amount,
        v_subscription.currency,
        case when v_payment_status = 'paid' then 'confirmed' else 'recorded' end,
        p_payment_date, trim(coalesce(p_reference, '')), v_reason, p_actor_id
      );
    end if;
    v_event_type := 'payment_updated';

  elsif v_action = 'extend' then
    if p_expiry_date is null or p_expiry_date < v_subscription.start_date then
      raise exception 'Select a valid new expiry date.';
    end if;
    if v_reason = '' then raise exception 'An extension reason is required.'; end if;
    update public.hm_member_package_subscriptions
    set expiry_date = p_expiry_date, updated_at = v_now, updated_by = p_actor_id
    where id = v_subscription.id;
    v_event_type := 'extended';

  elsif v_action = 'pause' then
    if v_reason = '' then raise exception 'A pause reason is required.'; end if;
    if v_subscription.status <> 'active' then raise exception 'Only an active subscription can be paused.'; end if;
    update public.hm_member_package_subscriptions
    set status = 'paused', paused_at = v_now, updated_at = v_now, updated_by = p_actor_id
    where id = v_subscription.id;
    v_event_type := 'paused';

  elsif v_action = 'resume' then
    if v_reason = '' then raise exception 'A resume reason is required.'; end if;
    if v_subscription.status <> 'paused' then raise exception 'Only a paused subscription can be resumed.'; end if;
    update public.hm_member_package_subscriptions
    set status = 'active', resumed_at = v_now, updated_at = v_now, updated_by = p_actor_id
    where id = v_subscription.id;
    v_event_type := 'resumed';

  elsif v_action in ('cancel','complete') then
    if v_reason = '' then raise exception 'An end reason is required.'; end if;
    update public.hm_member_package_subscriptions
    set status = case when v_action = 'cancel' then 'cancelled' else 'completed' end,
        ended_at = v_now,
        cancelled_at = case when v_action = 'cancel' then v_now else cancelled_at end,
        completed_at = case when v_action = 'complete' then v_now else completed_at end,
        end_reason = v_reason,
        updated_at = v_now,
        updated_by = p_actor_id
    where id = v_subscription.id;
    v_event_type := case when v_action = 'cancel' then 'cancelled' else 'completed' end;

  elsif v_action = 'refund' then
    if v_reason = '' then raise exception 'A refund reason is required.'; end if;
    update public.hm_member_package_subscriptions
    set status = 'refunded',
        payment_status = 'refunded',
        refund_amount = v_amount,
        refund_date = p_payment_date,
        refund_reference = trim(coalesce(p_reference, '')),
        outstanding_amount = 0,
        ended_at = v_now,
        end_reason = v_reason,
        updated_at = v_now,
        updated_by = p_actor_id
    where id = v_subscription.id;
    insert into public.hm_package_payments (
      subscription_id, member_id, payment_type, amount, currency,
      payment_status, payment_date, reference, note, created_by
    ) values (
      v_subscription.id, v_subscription.member_id, 'refund', v_amount,
      v_subscription.currency, 'confirmed', p_payment_date,
      trim(coalesce(p_reference, '')), v_reason, p_actor_id
    );
    v_event_type := 'refunded';
  else
    raise exception 'Unsupported subscription action.';
  end if;

  insert into public.hm_package_subscription_events (
    subscription_id, member_id, event_type, reason, metadata, created_by
  ) values (
    v_subscription.id, v_subscription.member_id, v_event_type, v_reason,
    jsonb_build_object(
      'expiry_date', p_expiry_date,
      'payment_status', v_payment_status,
      'amount', v_amount,
      'reference', trim(coalesce(p_reference, ''))
    ),
    p_actor_id
  );

  select * into v_subscription
  from public.hm_member_package_subscriptions
  where id = v_subscription.id;

  return jsonb_build_object(
    'subscription', to_jsonb(v_subscription),
    'metrics', public.hm_package_subscription_metrics(v_subscription.id),
    'event_type', v_event_type
  );
end;
$$;

create or replace function public.hm_admin_record_schedule_limit_override(
  p_member_id text,
  p_schedule_id text,
  p_reason text,
  p_actor_id text
)
returns jsonb
language plpgsql
security definer
set search_path = public
as $$
declare
  v_summary jsonb;
  v_subscription_id text;
  v_reason text := trim(coalesce(p_reason, ''));
  v_event_id uuid;
begin
  perform public.hm_package_require_admin(p_actor_id);
  if v_reason = '' then
    raise exception 'A schedule-limit override reason is required.';
  end if;
  v_summary := public.hm_package_member_summary(p_member_id);
  v_subscription_id := nullif(v_summary #>> '{package,id}', '');

  insert into public.hm_package_usage_events (
    subscription_id, member_id, schedule_id, event_type,
    allowance_delta, consumption_delta, reason, source,
    dedupe_key, metadata, created_by
  ) values (
    v_subscription_id, p_member_id, trim(coalesce(p_schedule_id, '')),
    'schedule_limit_override', 0, 0, v_reason, 'admin_scheduling',
    case when trim(coalesce(p_schedule_id, '')) <> ''
      then 'schedule_limit_override|' || trim(p_schedule_id)
      else null
    end,
    jsonb_build_object('summary_before_override', v_summary),
    p_actor_id
  )
  returning id into v_event_id;

  return jsonb_build_object(
    'override_event_id', v_event_id,
    'member_id', p_member_id,
    'subscription_id', coalesce(v_subscription_id, ''),
    'schedule_id', trim(coalesce(p_schedule_id, '')),
    'reason', v_reason
  );
end;
$$;

revoke all on function public.hm_package_require_admin(text) from public;
revoke all on function public.hm_admin_save_package(text,text,integer,numeric,numeric,text,jsonb,text,text) from public;
revoke all on function public.hm_admin_assign_member_package(text,text,date,date,text,numeric,date,text,text,text,text,integer,text) from public;
revoke all on function public.hm_admin_adjust_package_sessions(text,text,integer,text,text) from public;
revoke all on function public.hm_admin_update_package_subscription(text,text,text,date,text,numeric,date,text,text) from public;
revoke all on function public.hm_admin_record_schedule_limit_override(text,text,text,text) from public;

grant execute on function public.hm_package_require_admin(text) to service_role;
grant execute on function public.hm_admin_save_package(text,text,integer,numeric,numeric,text,jsonb,text,text) to service_role;
grant execute on function public.hm_admin_assign_member_package(text,text,date,date,text,numeric,date,text,text,text,text,integer,text) to service_role;
grant execute on function public.hm_admin_adjust_package_sessions(text,text,integer,text,text) to service_role;
grant execute on function public.hm_admin_update_package_subscription(text,text,text,date,text,numeric,date,text,text) to service_role;
grant execute on function public.hm_admin_record_schedule_limit_override(text,text,text,text) to service_role;

comment on function public.hm_admin_save_package(text,text,integer,numeric,numeric,text,jsonb,text,text) is
  'Creates/updates Package Library masters for future subscriptions. Existing member subscription commercial snapshots are not modified.';
comment on function public.hm_admin_assign_member_package(text,text,date,date,text,numeric,date,text,text,text,text,integer,text) is
  'Atomically assigns/replaces/renews one member package with mandatory unused-session decision and replacement reason.';
