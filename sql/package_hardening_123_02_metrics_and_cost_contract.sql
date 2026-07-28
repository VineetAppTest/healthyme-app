-- Package Hardening 1, 2 and 3: canonical package/session metrics.
-- Consumption rule shared by Streamlit and Flutter:
--   consumed when schedule.status = completed OR schedule.session_counted = true.
-- Open scheduled/acknowledged rows reserve capacity before another session is created.

create or replace function public.hm_package_schedule_subscription_id(p_schedule jsonb)
returns text
language plpgsql
stable
security definer
set search_path = public
as $$
declare
  v_direct text := trim(coalesce(p_schedule ->> 'member_package_id', ''));
  v_member_id text := trim(coalesce(p_schedule ->> 'member_id', ''));
  v_member_email text := lower(trim(coalesce(p_schedule ->> 'member_email', p_schedule ->> 'email', '')));
  v_package_id text := trim(coalesce(p_schedule ->> 'package_id', ''));
  v_event_at timestamptz;
  v_subscription_id text;
begin
  if v_direct <> '' and exists (
    select 1 from public.hm_member_package_subscriptions s where s.id = v_direct
  ) then
    return v_direct;
  end if;

  begin
    v_event_at := nullif(p_schedule ->> 'start_at_utc', '')::timestamptz;
  exception when others then
    v_event_at := null;
  end;
  if v_event_at is null then
    begin
      v_event_at := nullif(p_schedule ->> 'schedule_date', '')::date::timestamptz;
    exception when others then
      v_event_at := null;
    end;
  end if;
  if v_event_at is null then
    begin
      v_event_at := nullif(p_schedule ->> 'created_at', '')::timestamptz;
    exception when others then
      v_event_at := now();
    end;
  end if;

  select s.id
    into v_subscription_id
  from public.hm_member_package_subscriptions s
  where (
      (v_member_id <> '' and s.member_id = v_member_id)
      or (v_member_email <> '' and lower(s.member_email) = v_member_email)
    )
    and (v_package_id = '' or s.package_id = v_package_id)
    and s.subscribed_at <= v_event_at + interval '1 day'
    and (s.ended_at is null or s.ended_at >= v_event_at - interval '1 day')
  order by
    case when v_package_id <> '' and s.package_id = v_package_id then 0 else 1 end,
    s.subscribed_at desc
  limit 1;

  return v_subscription_id;
end;
$$;

create or replace function public.hm_package_schedule_cost(p_schedule jsonb)
returns numeric
language plpgsql
stable
security definer
set search_path = public
as $$
declare
  v_stored numeric := 0;
  v_subscription_id text;
  v_historical numeric := 0;
begin
  begin
    v_stored := coalesce(nullif(p_schedule ->> 'session_cost', '')::numeric, 0);
  exception when others then
    v_stored := 0;
  end;
  if v_stored > 0 then
    return v_stored;
  end if;

  v_subscription_id := public.hm_package_schedule_subscription_id(p_schedule);
  if coalesce(v_subscription_id, '') <> '' then
    select coalesce(s.cost_per_session, 0)
      into v_historical
    from public.hm_member_package_subscriptions s
    where s.id = v_subscription_id;
  end if;
  return coalesce(v_historical, 0);
end;
$$;

create or replace function public.hm_package_subscription_metrics(p_subscription_id text)
returns jsonb
language plpgsql
stable
security definer
set search_path = public
as $$
declare
  v_subscription public.hm_member_package_subscriptions%rowtype;
  v_state jsonb := '{}'::jsonb;
  v_schedules jsonb := '[]'::jsonb;
  v_base_allowance integer := 0;
  v_allowance_adjustment integer := 0;
  v_manual_consumption integer := 0;
  v_consumed integer := 0;
  v_reserved integer := 0;
  v_allowance integer := 0;
  v_remaining integer := 0;
  v_available integer := 0;
  v_overbooked integer := 0;
  v_consumed_value numeric := 0;
begin
  select * into v_subscription
  from public.hm_member_package_subscriptions
  where id = p_subscription_id;

  if not found then
    return jsonb_build_object(
      'subscription_id', coalesce(p_subscription_id, ''),
      'found', false,
      'package_sessions', 0,
      'sessions_consumed', 0,
      'sessions_reserved', 0,
      'sessions_remaining', 0,
      'sessions_available_to_schedule', 0,
      'overbooked_sessions', 0,
      'consumed_value', 0
    );
  end if;

  v_base_allowance := greatest(coalesce(v_subscription.session_count, 0), 0);

  select
    coalesce(sum(allowance_delta), 0)::integer,
    coalesce(sum(consumption_delta), 0)::integer
  into v_allowance_adjustment, v_manual_consumption
  from public.hm_package_usage_events
  where subscription_id = p_subscription_id
    and event_type in (
      'complimentary_added',
      'manual_allowance_adjustment',
      'manual_consumption_adjustment',
      'carry_forward_in',
      'carry_forward_out'
    );

  select coalesce(data, '{}'::jsonb)
    into v_state
  from public.healthyme_app_state
  where id = 'healthyme_app_state_v1';

  v_schedules := case jsonb_typeof(v_state -> 'schedules')
    when 'array' then coalesce(v_state -> 'schedules', '[]'::jsonb)
    when 'object' then coalesce(jsonb_path_query_array(v_state -> 'schedules', '$.*'), '[]'::jsonb)
    else '[]'::jsonb
  end;

  select
    count(*) filter (
      where lower(coalesce(value ->> 'status', '')) = 'completed'
         or lower(coalesce(value ->> 'session_counted', 'false')) = 'true'
    )::integer,
    count(*) filter (
      where lower(coalesce(value ->> 'status', '')) in ('scheduled','acknowledged')
        and lower(coalesce(value ->> 'session_counted', 'false')) <> 'true'
    )::integer,
    coalesce(sum(
      case
        when lower(coalesce(value ->> 'status', '')) = 'completed'
          or lower(coalesce(value ->> 'session_counted', 'false')) = 'true'
        then public.hm_package_schedule_cost(value)
        else 0
      end
    ), 0)
  into v_consumed, v_reserved, v_consumed_value
  from jsonb_array_elements(v_schedules) value
  where public.hm_package_schedule_subscription_id(value) = p_subscription_id;

  v_consumed := greatest(v_consumed + v_manual_consumption, 0);
  v_consumed_value := greatest(
    v_consumed_value + (v_manual_consumption * coalesce(v_subscription.cost_per_session, 0)),
    0
  );
  v_allowance := greatest(v_base_allowance + v_allowance_adjustment, 0);
  v_remaining := greatest(v_allowance - v_consumed, 0);
  v_available := greatest(v_allowance - v_consumed - v_reserved, 0);
  v_overbooked := greatest(v_consumed + v_reserved - v_allowance, 0);

  return jsonb_build_object(
    'subscription_id', v_subscription.id,
    'found', true,
    'member_id', v_subscription.member_id,
    'package_id', coalesce(v_subscription.package_id, ''),
    'package_name', v_subscription.package_name,
    'package_sessions', v_allowance,
    'base_package_sessions', v_base_allowance,
    'allowance_adjustment', v_allowance_adjustment,
    'sessions_consumed', v_consumed,
    'sessions_reserved', v_reserved,
    'sessions_remaining', v_remaining,
    'sessions_available_to_schedule', v_available,
    'overbooked_sessions', v_overbooked,
    'cost_per_session', v_subscription.cost_per_session,
    'currency', v_subscription.currency,
    'consumed_value', v_consumed_value
  );
end;
$$;

create or replace function public.hm_package_member_summary(p_member_id text)
returns jsonb
language plpgsql
stable
security definer
set search_path = public
as $$
declare
  v_subscription public.hm_member_package_subscriptions%rowtype;
  v_metrics jsonb;
begin
  select * into v_subscription
  from public.hm_member_package_subscriptions
  where member_id = p_member_id
    and status in ('active','paused')
  order by subscribed_at desc
  limit 1;

  if not found then
    return jsonb_build_object(
      'member_id', coalesce(p_member_id, ''),
      'has_current_package', false,
      'package', '{}'::jsonb,
      'metrics', jsonb_build_object(
        'package_sessions', 0,
        'sessions_consumed', 0,
        'sessions_reserved', 0,
        'sessions_remaining', 0,
        'sessions_available_to_schedule', 0,
        'overbooked_sessions', 0,
        'consumed_value', 0
      )
    );
  end if;

  v_metrics := public.hm_package_subscription_metrics(v_subscription.id);
  return jsonb_build_object(
    'member_id', p_member_id,
    'has_current_package', true,
    'package', to_jsonb(v_subscription),
    'metrics', v_metrics
  );
end;
$$;

revoke all on function public.hm_package_schedule_subscription_id(jsonb) from public;
revoke all on function public.hm_package_schedule_cost(jsonb) from public;
revoke all on function public.hm_package_subscription_metrics(text) from public;
revoke all on function public.hm_package_member_summary(text) from public;
grant execute on function public.hm_package_schedule_subscription_id(jsonb) to service_role;
grant execute on function public.hm_package_schedule_cost(jsonb) to service_role;
grant execute on function public.hm_package_subscription_metrics(text) to service_role;
grant execute on function public.hm_package_member_summary(text) to service_role;

comment on function public.hm_package_schedule_subscription_id(jsonb) is
  'Resolves a schedule to its saved historical member-package subscription. It never substitutes the latest active package.';
comment on function public.hm_package_schedule_cost(jsonb) is
  'Returns stored schedule cost, otherwise the matched historical subscription snapshot cost; never current Package Library price.';
comment on function public.hm_package_subscription_metrics(text) is
  'Canonical package usage contract. Completed/session_counted schedules consume; scheduled/acknowledged schedules reserve capacity.';
