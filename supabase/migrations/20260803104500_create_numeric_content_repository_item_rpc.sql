-- Atomic numeric ID allocation for canonical Content Repository items.
--
-- Exercise is the first live cutover. Recipe may reuse this function later after
-- its CSV compatibility rules are retired. Supplement retains its suprepo_* IDs.

create or replace function public.hm_create_numeric_content_repository_item(
    p_repository_type text,
    p_display_name text,
    p_payload jsonb default '{}'::jsonb,
    p_status text default 'active',
    p_actor_id text default 'admin',
    p_source_system text default 'healthyme'
)
returns setof public.hm_content_repository_items
language plpgsql
security invoker
set search_path = public, pg_temp
as $$
declare
    next_source_id text;
    inserted public.hm_content_repository_items%rowtype;
begin
    if p_repository_type not in ('recipe', 'exercise') then
        raise exception 'Numeric Content Repository IDs are not supported for %.', p_repository_type;
    end if;

    if btrim(coalesce(p_display_name, '')) = '' then
        raise exception 'Content Repository display name is required.';
    end if;

    if p_status not in ('active', 'inactive') then
        raise exception 'Unsupported Content Repository status: %.', p_status;
    end if;

    if jsonb_typeof(coalesce(p_payload, '{}'::jsonb)) <> 'object' then
        raise exception 'Content Repository payload must be a JSON object.';
    end if;

    -- Serialize ID allocation within each repository type. This prevents two
    -- concurrent admin creates from receiving the same max(source_id) + 1 value.
    perform pg_advisory_xact_lock(
        hashtextextended('hm_content_repository_numeric:' || p_repository_type, 0)
    );

    select (coalesce(max(source_id::bigint), -1) + 1)::text
      into next_source_id
      from public.hm_content_repository_items
     where repository_type = p_repository_type
       and source_id ~ '^[0-9]+$';

    insert into public.hm_content_repository_items (
        repository_type,
        source_id,
        display_name,
        status,
        payload,
        source_system,
        created_by,
        updated_by
    ) values (
        p_repository_type,
        next_source_id,
        btrim(p_display_name),
        p_status,
        coalesce(p_payload, '{}'::jsonb),
        coalesce(nullif(btrim(p_source_system), ''), 'healthyme'),
        coalesce(nullif(btrim(p_actor_id), ''), 'admin'),
        coalesce(nullif(btrim(p_actor_id), ''), 'admin')
    )
    returning * into inserted;

    return next inserted;
end;
$$;

revoke all on function public.hm_create_numeric_content_repository_item(
    text, text, jsonb, text, text, text
) from public, anon, authenticated, service_role;

grant execute on function public.hm_create_numeric_content_repository_item(
    text, text, jsonb, text, text, text
) to service_role;

comment on function public.hm_create_numeric_content_repository_item(
    text, text, jsonb, text, text, text
) is 'Atomically allocates the next numeric source_id and inserts one canonical Recipe or Exercise item.';
