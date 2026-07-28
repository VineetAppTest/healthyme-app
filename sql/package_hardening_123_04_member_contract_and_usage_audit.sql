-- Package Hardening 1, 2 and 3: member read contract and immutable usage audit.

with app as (
  select data
  from public.healthyme_app_state
  where id = 'healthyme_app_state_v1'
),
schedules as (
  select value
  from app,
  lateral jsonb_array_elements(
    case jsonb_typeof(data -> 'schedules')
      when 'array' then coalesce(data -> 'schedules', '[]'::jsonb)
      when 'object' then coalesce(jsonb_path_query_array(data -> 'schedules', '$.*'), '[]'::jsonb)
      else '[]'::jsonb
    end
  ) value
),
consumed as (
  select
    value,
    public.hm_package_schedule_subscription_id(value) as subscription_id
  from schedules
  where lower(coalesce(value ->> 'status', '')) = 'completed'
     or lower(coalesce(value ->> 'session_counted', 'false')) = 'true'
)
insert into public.hm_package_usage_events (
  subscription_id, member_id, schedule_id, event_type,
  allowance_delta, consumption_delta, reason, source,
  dedupe_key, metadata, created_by
)
select
  c.subscription_id,
  s.member_id,
  coalesce(c.value ->> 'id', ''),
  'schedule_consumed',
  0,
  0,
  'Historical consumed schedule audit backfill.',
  'legacy_schedule_backfill',
  'schedule_consumed|' || coalesce(c.value ->> 'id', md5(c.value::text)),
  jsonb_build_object(
    'status', c.value ->> 'status',
    'session_counted', c.value ->> 'session_counted',
    'historical_cost', public.hm_package_schedule_cost(c.value)
  ),
  'legacy_migration'
from consumed c
join public.hm_member_package_subscriptions s on s.id = c.subscription_id
where c.subscription_id is not null
on conflict (dedupe_key) where dedupe_key is not null and dedupe_key <> '' do nothing;

create or replace function public.hm_member_schedule_contract()
returns jsonb
language plpgsql
security definer
set search_path = public
as $$
declare
  v_email text := lower(trim(coalesce(auth.jwt() ->> 'email', '')));
  v_member_id text;
  v_state jsonb := '{}'::jsonb;
  v_schedules jsonb := '[]'::jsonb;
  v_subscription public.hm_member_package_subscriptions%rowtype;
  v_metrics jsonb := jsonb_build_object(
    'package_sessions', 0,
    'sessions_consumed', 0,
    'sessions_reserved', 0,
    'sessions_remaining', 0,
    'sessions_available_to_schedule', 0,
    'overbooked_sessions', 0,
    'consumed_value', 0
  );
  v_package jsonb := '{}'::jsonb;
  v_upcoming jsonb := '[]'::jsonb;
  v_ledger jsonb := '[]'::jsonb;
  v_history jsonb := '[]'::jsonb;
begin
  if v_email = '' then
    return jsonb_build_object('error', 'Authenticated email is missing.');
  end if;

  select u.id
    into v_member_id
  from public.hm_users u
  where lower(trim(u.email)) = v_email
    and lower(coalesce(u.role, '')) = 'member'
    and coalesce(u.is_active, true) = true
  limit 1;

  if coalesce(v_member_id, '') = '' then
    return jsonb_build_object(
      'error', 'No active HealthyMe member mapping was found for the authenticated email.',
      'resolved_email', v_email
    );
  end if;

  select coalesce(data, '{}'::jsonb)
    into v_state
  from public.healthyme_app_state
  where id = 'healthyme_app_state_v1';

  v_schedules := case jsonb_typeof(v_state -> 'schedules')
    when 'array' then coalesce(v_state -> 'schedules', '[]'::jsonb)
    when 'object' then coalesce(jsonb_path_query_array(v_state -> 'schedules', '$.*'), '[]'::jsonb)
    else '[]'::jsonb
  end;

  select * into v_subscription
  from public.hm_member_package_subscriptions
  where member_id = v_member_id
    and status in ('active','paused')
  order by subscribed_at desc
  limit 1;

  if found then
    v_metrics := public.hm_package_subscription_metrics(v_subscription.id);
    v_package := jsonb_build_object(
      'id', v_subscription.id,
      'subscription_id', v_subscription.id,
      'package_id', coalesce(v_subscription.package_id, ''),
      'package_name', v_subscription.package_name,
      'session_count', coalesce((v_metrics ->> 'package_sessions')::integer, v_subscription.session_count),
      'base_session_count', v_subscription.session_count,
      'cost_per_session', v_subscription.cost_per_session,
      'total_value', v_subscription.total_value,
      'currency', v_subscription.currency,
      'inclusions', v_subscription.inclusions,
      'inclusions_informational_only', true,
      'inclusions_note', 'Package inclusions are informational only and do not control HealthyMe module access.',
      'number_of_people', 1,
      'start_date', v_subscription.start_date,
      'expiry_date', v_subscription.expiry_date,
      'status', v_subscription.status,
      'payment_status', v_subscription.payment_status,
      'amount_paid', v_subscription.amount_paid,
      'outstanding_amount', v_subscription.outstanding_amount,
      'payment_date', v_subscription.payment_date,
      'payment_reference', v_subscription.payment_reference,
      'subscribed_at', v_subscription.subscribed_at,
      'assigned_by', v_subscription.assigned_by,
      'updated_at', v_subscription.updated_at,
      'updated_by', v_subscription.updated_by
    );
  end if;

  select coalesce(jsonb_agg(item order by sort_date, sort_time), '[]'::jsonb)
    into v_upcoming
  from (
    select
      coalesce(value ->> 'schedule_date', '') as sort_date,
      coalesce(value ->> 'start_time', '') as sort_time,
      jsonb_build_object(
        'id', coalesce(value ->> 'id', ''),
        'title', coalesce(nullif(value ->> 'title', ''), nullif(value ->> 'schedule_type', ''), 'Scheduled session'),
        'schedule_type', coalesce(value ->> 'schedule_type', ''),
        'schedule_date', coalesce(value ->> 'schedule_date', ''),
        'start_time', coalesce(value ->> 'start_time', ''),
        'end_time', coalesce(value ->> 'end_time', ''),
        'start_at_utc', coalesce(value ->> 'start_at_utc', ''),
        'end_at_utc', coalesce(value ->> 'end_at_utc', ''),
        'member_timezone_name', coalesce(value ->> 'member_timezone_name', ''),
        'practitioner_timezone_name', coalesce(value ->> 'practitioner_timezone_name', ''),
        'mode', coalesce(value ->> 'mode', ''),
        'location_or_link', coalesce(value ->> 'location_or_link', ''),
        'member_package_id', coalesce(x.subscription_id, ''),
        'package_name', coalesce(sub.package_name, ''),
        'session_cost', public.hm_package_schedule_cost(value),
        'currency', coalesce(sub.currency, 'INR'),
        'status', coalesce(value ->> 'status', ''),
        'stage', case
          when lower(coalesce(value ->> 'reschedule_request_status', '')) = 'pending' then 'Reschedule pending'
          when lower(coalesce(value ->> 'status', '')) = 'acknowledged'
            or coalesce(value ->> 'acknowledged_at', '') <> '' then 'Acknowledged'
          else 'Open'
        end,
        'acknowledged_at', coalesce(value ->> 'acknowledged_at', ''),
        'reschedule_request_status', coalesce(value ->> 'reschedule_request_status', ''),
        'can_acknowledge', lower(coalesce(value ->> 'status', '')) = 'scheduled'
          and coalesce(value ->> 'acknowledged_at', '') = '',
        'can_reschedule', lower(coalesce(value ->> 'status', '')) in ('scheduled','acknowledged')
          and lower(coalesce(value ->> 'reschedule_request_status', '')) <> 'pending'
      ) as item
    from jsonb_array_elements(v_schedules) value
    cross join lateral (
      select public.hm_package_schedule_subscription_id(value) as subscription_id
    ) x
    left join public.hm_member_package_subscriptions sub on sub.id = x.subscription_id
    where (
        trim(coalesce(value ->> 'member_id', '')) = v_member_id
        or lower(trim(coalesce(value ->> 'member_email', value ->> 'email', ''))) = v_email
      )
      and lower(coalesce(value ->> 'status', '')) in ('scheduled','acknowledged')
      and coalesce(value ->> 'schedule_date', '') ~ '^\d{4}-\d{2}-\d{2}$'
      and (value ->> 'schedule_date')::date >= current_date
  ) q;

  select coalesce(jsonb_agg(item order by sort_date desc, sort_time desc), '[]'::jsonb)
    into v_ledger
  from (
    select
      coalesce(value ->> 'schedule_date', '') as sort_date,
      coalesce(value ->> 'start_time', '') as sort_time,
      jsonb_build_object(
        'id', coalesce(value ->> 'id', ''),
        'title', coalesce(nullif(value ->> 'title', ''), nullif(value ->> 'schedule_type', ''), 'Scheduled session'),
        'schedule_type', coalesce(value ->> 'schedule_type', ''),
        'schedule_date', coalesce(value ->> 'schedule_date', ''),
        'start_time', coalesce(value ->> 'start_time', ''),
        'end_time', coalesce(value ->> 'end_time', ''),
        'start_at_utc', coalesce(value ->> 'start_at_utc', ''),
        'end_at_utc', coalesce(value ->> 'end_at_utc', ''),
        'mode', coalesce(value ->> 'mode', ''),
        'location_or_link', '',
        'member_package_id', coalesce(x.subscription_id, ''),
        'package_name', coalesce(sub.package_name, ''),
        'session_cost', public.hm_package_schedule_cost(value),
        'currency', coalesce(sub.currency, 'INR'),
        'status', coalesce(value ->> 'status', ''),
        'stage', case
          when lower(coalesce(value ->> 'status', '')) = 'completed'
            or lower(coalesce(value ->> 'session_counted', 'false')) = 'true' then 'Consumed'
          when lower(coalesce(value ->> 'status', '')) = 'cancelled' then 'Cancelled'
          when lower(coalesce(value ->> 'status', '')) = 'rescheduled' then 'Rescheduled — not consumed'
          when lower(coalesce(value ->> 'status', '')) = 'acknowledged' then 'Open'
          else 'Open'
        end,
        'consumed', lower(coalesce(value ->> 'status', '')) = 'completed'
          or lower(coalesce(value ->> 'session_counted', 'false')) = 'true',
        'acknowledged_at', coalesce(value ->> 'acknowledged_at', ''),
        'reschedule_request_status', coalesce(value ->> 'reschedule_request_status', ''),
        'can_acknowledge', false,
        'can_reschedule', false
      ) as item
    from jsonb_array_elements(v_schedules) value
    cross join lateral (
      select public.hm_package_schedule_subscription_id(value) as subscription_id
    ) x
    left join public.hm_member_package_subscriptions sub on sub.id = x.subscription_id
    where (
      trim(coalesce(value ->> 'member_id', '')) = v_member_id
      or lower(trim(coalesce(value ->> 'member_email', value ->> 'email', ''))) = v_email
    )
  ) q;

  select coalesce(jsonb_agg(
    jsonb_build_object(
      'id', s.id,
      'package_id', coalesce(s.package_id, ''),
      'package_name', s.package_name,
      'status', s.status,
      'start_date', s.start_date,
      'expiry_date', s.expiry_date,
      'session_count', s.session_count,
      'cost_per_session', s.cost_per_session,
      'total_value', s.total_value,
      'currency', s.currency,
      'payment_status', s.payment_status,
      'amount_paid', s.amount_paid,
      'outstanding_amount', s.outstanding_amount,
      'subscribed_at', s.subscribed_at,
      'ended_at', s.ended_at,
      'end_reason', s.end_reason,
      'replacement_reason', s.replacement_reason,
      'unused_sessions_decision', s.unused_sessions_decision,
      'unused_sessions_at_end', s.unused_sessions_at_end,
      'carry_forward_sessions', s.carry_forward_sessions,
      'metrics', public.hm_package_subscription_metrics(s.id),
      'inclusions', s.inclusions,
      'inclusions_informational_only', true
    ) order by s.subscribed_at desc
  ), '[]'::jsonb)
    into v_history
  from public.hm_member_package_subscriptions s
  where s.member_id = v_member_id;

  return jsonb_build_object(
    'package', v_package,
    'package_metrics', v_metrics,
    'package_sessions', coalesce((v_metrics ->> 'package_sessions')::integer, 0),
    'sessions_consumed', coalesce((v_metrics ->> 'sessions_consumed')::integer, 0),
    'sessions_reserved', coalesce((v_metrics ->> 'sessions_reserved')::integer, 0),
    'sessions_remaining', coalesce((v_metrics ->> 'sessions_remaining')::integer, 0),
    'sessions_available_to_schedule', coalesce((v_metrics ->> 'sessions_available_to_schedule')::integer, 0),
    'overbooked_sessions', coalesce((v_metrics ->> 'overbooked_sessions')::integer, 0),
    'consumed_value', coalesce((v_metrics ->> 'consumed_value')::numeric, 0),
    'upcoming_sessions', v_upcoming,
    'session_ledger', v_ledger,
    'package_history', v_history,
    'inclusions_informational_only', true,
    'resolved_email', v_email,
    'resolved_member_id', v_member_id,
    'matched_package', v_subscription.id is not null,
    'matched_schedule_count', jsonb_array_length(v_ledger),
    'contract_version', 'package-hardening-123-v1'
  );
end;
$$;

revoke all on table public.hm_packages from anon, authenticated;
revoke all on table public.hm_member_package_subscriptions from anon, authenticated;
revoke all on table public.hm_package_usage_events from anon, authenticated;
revoke all on table public.hm_package_payments from anon, authenticated;
revoke all on table public.hm_package_subscription_events from anon, authenticated;
revoke all on function public.hm_member_schedule_contract() from public;
grant execute on function public.hm_member_schedule_contract() to authenticated;
grant execute on function public.hm_member_schedule_contract() to service_role;

comment on function public.hm_member_schedule_contract() is
  'Package Hardening 1/2/3 member contract: normalized subscription snapshot, canonical usage, historical session cost and informational inclusions.';
