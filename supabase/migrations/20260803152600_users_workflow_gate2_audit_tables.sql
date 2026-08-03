-- HealthyMe Users/Workflow Batch 2B, Gate 2
-- Append-only idempotency and audit foundation.
--
-- No historical events are backfilled. Existing User and Workflow rows remain
-- untouched. These tables are service-side only and are not exposed to anon or
-- authenticated clients.

create table if not exists public.hm_domain_write_requests (
  request_id text primary key,
  operation text not null,
  entity_id text not null,
  response_payload jsonb not null,
  created_at timestamptz not null default now(),
  constraint hm_domain_write_requests_request_id_not_blank
    check (btrim(request_id) <> ''),
  constraint hm_domain_write_requests_operation_check
    check (operation in ('user_upsert', 'workflow_upsert'))
);

create table if not exists public.hm_user_events (
  event_id bigint generated always as identity primary key,
  request_id text not null unique,
  user_id text not null,
  event_type text not null,
  actor_id text,
  actor_email text,
  source text not null default 'server_contract',
  changed_fields text[] not null default '{}'::text[],
  before_snapshot jsonb,
  after_snapshot jsonb not null,
  metadata jsonb not null default '{}'::jsonb,
  occurred_at timestamptz not null default now(),
  constraint hm_user_events_event_type_check
    check (event_type in ('created', 'updated'))
);

create table if not exists public.hm_workflow_events (
  event_id bigint generated always as identity primary key,
  request_id text not null unique,
  user_id text not null,
  event_type text not null,
  actor_id text,
  actor_email text,
  source text not null default 'server_contract',
  changed_fields text[] not null default '{}'::text[],
  before_snapshot jsonb,
  after_snapshot jsonb not null,
  metadata jsonb not null default '{}'::jsonb,
  occurred_at timestamptz not null default now(),
  constraint hm_workflow_events_event_type_check
    check (event_type in ('created', 'updated'))
);

create index if not exists hm_user_events_user_time_idx
  on public.hm_user_events(user_id, occurred_at desc);
create index if not exists hm_workflow_events_user_time_idx
  on public.hm_workflow_events(user_id, occurred_at desc);

alter table public.hm_domain_write_requests enable row level security;
alter table public.hm_domain_write_requests force row level security;
alter table public.hm_user_events enable row level security;
alter table public.hm_user_events force row level security;
alter table public.hm_workflow_events enable row level security;
alter table public.hm_workflow_events force row level security;

revoke all on table public.hm_domain_write_requests from public, anon, authenticated;
revoke all on table public.hm_user_events from public, anon, authenticated;
revoke all on table public.hm_workflow_events from public, anon, authenticated;

grant select on table public.hm_domain_write_requests to service_role;
grant select on table public.hm_user_events to service_role;
grant select on table public.hm_workflow_events to service_role;

create or replace function public.hm_reject_append_only_mutation()
returns trigger
language plpgsql
security invoker
set search_path = ''
as $function$
begin
  raise exception using
    errcode = '42501',
    message = format('%I is append-only; UPDATE and DELETE are not permitted.', tg_table_name);
end;
$function$;

revoke all on function public.hm_reject_append_only_mutation()
  from public, anon, authenticated;
grant execute on function public.hm_reject_append_only_mutation()
  to service_role;

drop trigger if exists hm_domain_write_requests_append_only on public.hm_domain_write_requests;
create trigger hm_domain_write_requests_append_only
before update or delete on public.hm_domain_write_requests
for each row execute function public.hm_reject_append_only_mutation();

drop trigger if exists hm_user_events_append_only on public.hm_user_events;
create trigger hm_user_events_append_only
before update or delete on public.hm_user_events
for each row execute function public.hm_reject_append_only_mutation();

drop trigger if exists hm_workflow_events_append_only on public.hm_workflow_events;
create trigger hm_workflow_events_append_only
before update or delete on public.hm_workflow_events
for each row execute function public.hm_reject_append_only_mutation();
