-- Package Hardening 1, 2 and 3
-- Normalizes package masters, member subscription snapshots, usage adjustments and payments.
-- Package inclusions are informational only and never grant, hide, block or enforce module access.

create extension if not exists pgcrypto;

create table if not exists public.hm_packages (
  id text primary key default substr(replace(gen_random_uuid()::text, '-', ''), 1, 8),
  package_name text not null,
  session_count integer not null check (session_count > 0),
  cost_per_session numeric(12,2) not null default 0 check (cost_per_session >= 0),
  total_value numeric(12,2) not null default 0 check (total_value >= 0),
  currency text not null default 'INR',
  inclusions jsonb not null default '{}'::jsonb,
  inclusions_informational_only boolean not null default true
    check (inclusions_informational_only = true),
  status text not null default 'active'
    check (status in ('active','inactive')),
  created_at timestamptz not null default now(),
  created_by text not null default 'system',
  updated_at timestamptz not null default now(),
  updated_by text not null default 'system'
);

create table if not exists public.hm_member_package_subscriptions (
  id text primary key default substr(replace(gen_random_uuid()::text, '-', ''), 1, 8),
  member_id text not null references public.hm_users(id) on update cascade on delete restrict,
  member_name text not null default '',
  member_email text not null default '',
  package_id text references public.hm_packages(id) on update cascade on delete restrict,
  package_name text not null,
  session_count integer not null check (session_count > 0),
  cost_per_session numeric(12,2) not null default 0 check (cost_per_session >= 0),
  total_value numeric(12,2) not null default 0 check (total_value >= 0),
  currency text not null default 'INR',
  inclusions jsonb not null default '{}'::jsonb,
  inclusions_informational_only boolean not null default true
    check (inclusions_informational_only = true),
  start_date date not null default current_date,
  expiry_date date,
  status text not null default 'active'
    check (status in ('active','paused','replaced','expired','cancelled','completed','refunded')),
  payment_status text not null default 'not_recorded'
    check (payment_status in ('not_recorded','unpaid','partially_paid','paid','complimentary','refunded')),
  amount_paid numeric(12,2) not null default 0 check (amount_paid >= 0),
  outstanding_amount numeric(12,2) not null default 0 check (outstanding_amount >= 0),
  payment_date date,
  payment_reference text not null default '',
  refund_amount numeric(12,2) not null default 0 check (refund_amount >= 0),
  refund_date date,
  refund_reference text not null default '',
  subscribed_at timestamptz not null default now(),
  ended_at timestamptz,
  end_reason text not null default '',
  replacement_reason text not null default '',
  unused_sessions_decision text not null default ''
    check (unused_sessions_decision in ('','expire_unused','carry_forward','retain_until_exhausted','manual_adjustment')),
  unused_sessions_at_end integer not null default 0 check (unused_sessions_at_end >= 0),
  carry_forward_sessions integer not null default 0 check (carry_forward_sessions >= 0),
  replaced_by_subscription_id text,
  renewed_from_subscription_id text,
  paused_at timestamptz,
  resumed_at timestamptz,
  cancelled_at timestamptz,
  completed_at timestamptz,
  created_at timestamptz not null default now(),
  created_by text not null default 'system',
  assigned_by text not null default 'system',
  updated_at timestamptz not null default now(),
  updated_by text not null default 'system',
  check (expiry_date is null or expiry_date >= start_date)
);

create unique index if not exists hm_member_package_one_current_idx
  on public.hm_member_package_subscriptions(member_id)
  where status in ('active','paused');

create index if not exists hm_member_package_member_idx
  on public.hm_member_package_subscriptions(member_id, subscribed_at desc);

create index if not exists hm_member_package_package_idx
  on public.hm_member_package_subscriptions(package_id, subscribed_at desc);

create table if not exists public.hm_package_usage_events (
  id uuid primary key default gen_random_uuid(),
  subscription_id text references public.hm_member_package_subscriptions(id) on update cascade on delete restrict,
  member_id text not null references public.hm_users(id) on update cascade on delete restrict,
  schedule_id text not null default '',
  event_type text not null
    check (event_type in (
      'schedule_consumed',
      'schedule_reversed',
      'complimentary_added',
      'manual_allowance_adjustment',
      'manual_consumption_adjustment',
      'carry_forward_in',
      'carry_forward_out',
      'schedule_limit_override'
    )),
  allowance_delta integer not null default 0,
  consumption_delta integer not null default 0,
  reason text not null default '',
  source text not null default 'streamlit',
  dedupe_key text,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  created_by text not null default 'system'
);

create unique index if not exists hm_package_usage_dedupe_idx
  on public.hm_package_usage_events(dedupe_key)
  where dedupe_key is not null and dedupe_key <> '';

create index if not exists hm_package_usage_subscription_idx
  on public.hm_package_usage_events(subscription_id, created_at desc);

create table if not exists public.hm_package_payments (
  id uuid primary key default gen_random_uuid(),
  subscription_id text not null references public.hm_member_package_subscriptions(id) on update cascade on delete restrict,
  member_id text not null references public.hm_users(id) on update cascade on delete restrict,
  payment_type text not null default 'payment'
    check (payment_type in ('payment','refund','credit','debit','write_off')),
  amount numeric(12,2) not null check (amount >= 0),
  currency text not null default 'INR',
  payment_status text not null default 'recorded'
    check (payment_status in ('recorded','pending','confirmed','failed','reversed')),
  payment_date date,
  reference text not null default '',
  note text not null default '',
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  created_by text not null default 'system'
);

create index if not exists hm_package_payments_subscription_idx
  on public.hm_package_payments(subscription_id, created_at desc);

create table if not exists public.hm_package_subscription_events (
  id uuid primary key default gen_random_uuid(),
  subscription_id text not null references public.hm_member_package_subscriptions(id) on update cascade on delete restrict,
  member_id text not null references public.hm_users(id) on update cascade on delete restrict,
  event_type text not null,
  reason text not null default '',
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  created_by text not null default 'system'
);

create index if not exists hm_package_subscription_events_idx
  on public.hm_package_subscription_events(subscription_id, created_at desc);

alter table public.hm_packages enable row level security;
alter table public.hm_member_package_subscriptions enable row level security;
alter table public.hm_package_usage_events enable row level security;
alter table public.hm_package_payments enable row level security;
alter table public.hm_package_subscription_events enable row level security;

-- Existing package masters are migrated once. The subscription rows remain commercial snapshots.
with app as (
  select data
  from public.healthyme_app_state
  where id = 'healthyme_app_state_v1'
),
source_rows as (
  select value
  from app,
  lateral jsonb_array_elements(
    case jsonb_typeof(data -> 'packages')
      when 'array' then coalesce(data -> 'packages', '[]'::jsonb)
      when 'object' then coalesce(jsonb_path_query_array(data -> 'packages', '$.*'), '[]'::jsonb)
      else '[]'::jsonb
    end
  ) value
)
insert into public.hm_packages (
  id, package_name, session_count, cost_per_session, total_value, currency,
  inclusions, inclusions_informational_only, status,
  created_at, created_by, updated_at, updated_by
)
select
  coalesce(nullif(value ->> 'id',''), substr(replace(gen_random_uuid()::text,'-',''),1,8)),
  coalesce(nullif(value ->> 'package_name',''), 'Package'),
  greatest(coalesce(nullif(value ->> 'session_count','')::integer, 1), 1),
  greatest(coalesce(nullif(value ->> 'cost_per_session','')::numeric, 0), 0),
  greatest(
    coalesce(
      nullif(value ->> 'total_value','')::numeric,
      coalesce(nullif(value ->> 'session_count','')::numeric, 1)
        * coalesce(nullif(value ->> 'cost_per_session','')::numeric, 0)
    ),
    0
  ),
  coalesce(nullif(value ->> 'currency',''), 'INR'),
  coalesce(value -> 'inclusions', '{}'::jsonb),
  true,
  case when lower(coalesce(value ->> 'status','active')) = 'inactive' then 'inactive' else 'active' end,
  coalesce(nullif(value ->> 'created_at','')::timestamptz, now()),
  coalesce(nullif(value ->> 'created_by',''), 'legacy_migration'),
  coalesce(nullif(value ->> 'updated_at','')::timestamptz, now()),
  coalesce(nullif(value ->> 'updated_by',''), nullif(value ->> 'created_by',''), 'legacy_migration')
from source_rows
on conflict (id) do nothing;

with app as (
  select data
  from public.healthyme_app_state
  where id = 'healthyme_app_state_v1'
),
source_rows as (
  select value
  from app,
  lateral jsonb_array_elements(
    case jsonb_typeof(data -> 'member_packages')
      when 'array' then coalesce(data -> 'member_packages', '[]'::jsonb)
      when 'object' then coalesce(jsonb_path_query_array(data -> 'member_packages', '$.*'), '[]'::jsonb)
      else '[]'::jsonb
    end
  ) value
),
ranked as (
  select
    value,
    row_number() over (
      partition by coalesce(value ->> 'member_id', lower(value ->> 'member_email'))
      order by
        case when lower(coalesce(value ->> 'status','active')) in ('active','paused') then 0 else 1 end,
        coalesce(value ->> 'updated_at', value ->> 'subscribed_at', value ->> 'created_at', '') desc
    ) as member_rank
  from source_rows
)
insert into public.hm_member_package_subscriptions (
  id, member_id, member_name, member_email, package_id, package_name,
  session_count, cost_per_session, total_value, currency,
  inclusions, inclusions_informational_only,
  start_date, expiry_date, status,
  payment_status, amount_paid, outstanding_amount, payment_date, payment_reference,
  subscribed_at, ended_at, end_reason,
  created_at, created_by, assigned_by, updated_at, updated_by
)
select
  coalesce(nullif(value ->> 'id',''), substr(replace(gen_random_uuid()::text,'-',''),1,8)),
  u.id,
  coalesce(nullif(value ->> 'member_name',''), u.name, ''),
  coalesce(nullif(value ->> 'member_email',''), u.email, ''),
  case
    when exists(select 1 from public.hm_packages p where p.id = value ->> 'package_id')
      then value ->> 'package_id'
    else null
  end,
  coalesce(nullif(value ->> 'package_name',''), 'Package'),
  greatest(coalesce(nullif(value ->> 'session_count','')::integer, 1), 1),
  greatest(coalesce(nullif(value ->> 'cost_per_session','')::numeric, 0), 0),
  greatest(
    coalesce(
      nullif(value ->> 'total_value','')::numeric,
      coalesce(nullif(value ->> 'session_count','')::numeric, 1)
        * coalesce(nullif(value ->> 'cost_per_session','')::numeric, 0)
    ),
    0
  ),
  coalesce(nullif(value ->> 'currency',''), 'INR'),
  coalesce(value -> 'inclusions', '{}'::jsonb),
  true,
  coalesce(
    nullif(value ->> 'start_date','')::date,
    nullif(left(coalesce(value ->> 'subscribed_at', value ->> 'created_at',''),10),'')::date,
    current_date
  ),
  nullif(value ->> 'expiry_date','')::date,
  case
    when lower(coalesce(value ->> 'status','active')) = 'active' and member_rank = 1 then 'active'
    when lower(coalesce(value ->> 'status','active')) = 'paused' and member_rank = 1 then 'paused'
    when lower(coalesce(value ->> 'status','active')) in ('cancelled','expired','completed','refunded') then lower(value ->> 'status')
    else 'replaced'
  end,
  case
    when lower(coalesce(value ->> 'payment_status','')) in ('unpaid','partially_paid','paid','complimentary','refunded')
      then lower(value ->> 'payment_status')
    else 'not_recorded'
  end,
  greatest(coalesce(nullif(value ->> 'amount_paid','')::numeric, 0), 0),
  greatest(
    coalesce(
      nullif(value ->> 'outstanding_amount','')::numeric,
      coalesce(
        nullif(value ->> 'total_value','')::numeric,
        coalesce(nullif(value ->> 'session_count','')::numeric, 1)
          * coalesce(nullif(value ->> 'cost_per_session','')::numeric, 0)
      ) - coalesce(nullif(value ->> 'amount_paid','')::numeric, 0)
    ),
    0
  ),
  nullif(value ->> 'payment_date','')::date,
  coalesce(value ->> 'payment_reference',''),
  coalesce(nullif(value ->> 'subscribed_at','')::timestamptz, nullif(value ->> 'created_at','')::timestamptz, now()),
  coalesce(nullif(value ->> 'ended_at','')::timestamptz, null),
  coalesce(value ->> 'end_reason',''),
  coalesce(nullif(value ->> 'created_at','')::timestamptz, nullif(value ->> 'subscribed_at','')::timestamptz, now()),
  coalesce(nullif(value ->> 'created_by',''), 'legacy_migration'),
  coalesce(nullif(value ->> 'assigned_by',''), nullif(value ->> 'created_by',''), 'legacy_migration'),
  coalesce(nullif(value ->> 'updated_at','')::timestamptz, nullif(value ->> 'subscribed_at','')::timestamptz, now()),
  coalesce(nullif(value ->> 'updated_by',''), nullif(value ->> 'created_by',''), 'legacy_migration')
from ranked
join public.hm_users u
  on u.id = value ->> 'member_id'
  or lower(u.email) = lower(coalesce(value ->> 'member_email',''))
where lower(coalesce(u.role,'')) = 'member'
on conflict (id) do nothing;
