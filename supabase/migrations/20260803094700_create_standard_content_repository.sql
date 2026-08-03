-- HealthyMe standard Content Repository persistence foundation.
--
-- This migration creates one canonical Supabase-backed persistence model for
-- Recipe, Exercise and Supplement definitions. It does not backfill data and it
-- does not switch any production page. Controlled backfill and cutover happen in
-- later phases of issue #347.

create table if not exists public.hm_content_repository_items (
    id uuid primary key default gen_random_uuid(),
    repository_type text not null
        check (repository_type in ('recipe', 'exercise', 'supplement')),
    source_id text not null
        check (btrim(source_id) <> ''),
    display_name text not null
        check (btrim(display_name) <> ''),
    status text not null default 'active'
        check (status in ('active', 'inactive')),
    payload jsonb not null default '{}'::jsonb
        check (jsonb_typeof(payload) = 'object'),
    content_version integer not null default 1
        check (content_version > 0),
    source_system text not null default 'healthyme',
    legacy_reference text,
    created_at timestamptz not null default now(),
    created_by text,
    updated_at timestamptz not null default now(),
    updated_by text,
    constraint hm_content_repository_identity_unique
        unique (repository_type, source_id)
);

create index if not exists hm_content_repository_type_status_idx
    on public.hm_content_repository_items (repository_type, status);

create index if not exists hm_content_repository_display_name_idx
    on public.hm_content_repository_items (repository_type, lower(display_name));

create table if not exists public.hm_content_repository_events (
    id uuid primary key default gen_random_uuid(),
    repository_item_id uuid not null
        references public.hm_content_repository_items(id) on delete restrict,
    repository_type text not null
        check (repository_type in ('recipe', 'exercise', 'supplement')),
    source_id text not null,
    event_type text not null
        check (event_type in ('created', 'updated', 'deactivated', 'reactivated')),
    before_record jsonb,
    after_record jsonb not null,
    actor_id text,
    created_at timestamptz not null default now()
);

create index if not exists hm_content_repository_events_item_idx
    on public.hm_content_repository_events (repository_item_id, created_at desc);

create index if not exists hm_content_repository_events_source_idx
    on public.hm_content_repository_events
        (repository_type, source_id, created_at desc);

create or replace function public.hm_set_content_repository_updated_at()
returns trigger
language plpgsql
set search_path = public, pg_temp
as $$
begin
    if new.repository_type <> old.repository_type
       or new.source_id <> old.source_id then
        raise exception 'Content Repository identity cannot be changed';
    end if;

    new.created_at := old.created_at;
    new.created_by := old.created_by;
    new.updated_at := now();
    new.content_version := old.content_version + 1;
    return new;
end;
$$;

create or replace function public.hm_capture_content_repository_event()
returns trigger
language plpgsql
set search_path = public, pg_temp
as $$
declare
    next_event_type text;
begin
    if tg_op = 'INSERT' then
        next_event_type := 'created';
    elsif old.status = 'active' and new.status = 'inactive' then
        next_event_type := 'deactivated';
    elsif old.status = 'inactive' and new.status = 'active' then
        next_event_type := 'reactivated';
    else
        next_event_type := 'updated';
    end if;

    insert into public.hm_content_repository_events (
        repository_item_id,
        repository_type,
        source_id,
        event_type,
        before_record,
        after_record,
        actor_id
    ) values (
        new.id,
        new.repository_type,
        new.source_id,
        next_event_type,
        case when tg_op = 'INSERT' then null else to_jsonb(old) end,
        to_jsonb(new),
        coalesce(new.updated_by, new.created_by)
    );

    return new;
end;
$$;

drop trigger if exists hm_content_repository_touch
    on public.hm_content_repository_items;
create trigger hm_content_repository_touch
before update on public.hm_content_repository_items
for each row execute function public.hm_set_content_repository_updated_at();

drop trigger if exists hm_content_repository_audit
    on public.hm_content_repository_items;
create trigger hm_content_repository_audit
after insert or update on public.hm_content_repository_items
for each row execute function public.hm_capture_content_repository_event();

alter table public.hm_content_repository_items enable row level security;
alter table public.hm_content_repository_events enable row level security;

-- These tables are server-managed. The Streamlit backend uses the service role;
-- Member and browser clients do not receive direct table access.
revoke all on table public.hm_content_repository_items from public, anon, authenticated;
revoke all on table public.hm_content_repository_events from public, anon, authenticated;
revoke all on function public.hm_set_content_repository_updated_at() from public, anon, authenticated;
revoke all on function public.hm_capture_content_repository_event() from public, anon, authenticated;

grant select, insert, update on table public.hm_content_repository_items to service_role;
grant select, insert on table public.hm_content_repository_events to service_role;
grant execute on function public.hm_set_content_repository_updated_at() to service_role;
grant execute on function public.hm_capture_content_repository_event() to service_role;

comment on table public.hm_content_repository_items is
    'Canonical Recipe, Exercise and Supplement definitions keyed by repository_type and source_id.';
comment on table public.hm_content_repository_events is
    'Append-only audit history for canonical Content Repository mutations.';
comment on column public.hm_content_repository_items.payload is
    'Type-specific repository fields; identity, status and audit metadata remain in common columns.';
comment on column public.hm_content_repository_items.source_id is
    'Stable external ID retained from the legacy authority. Never renumbered or derived from display_name.';
