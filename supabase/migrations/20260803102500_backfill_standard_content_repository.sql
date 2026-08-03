-- Controlled backfill for HealthyMe standard Content Repository.
--
-- This migration inserts the frozen 2 Recipe, 3 Exercise and 5 Supplement
-- definitions into the canonical repository without switching any live page.
--
-- Corrected canonical checksums (legacy_reference included for all sources):
--   Recipe:     a61af93dec4052ed2b3c8160657be594e5bab68a8e63b554fbd6eb745edce48f
--   Exercise:   585764b996d1952226405966efada936b87eae4cfa0f2a6120433f5f560e4716
--   Supplement: 4bb7bcb320b0cb1c83981d38531f14db9c020b0a61b1d74b3765f0b09865bf96
--   Total:      52ac68b76032cfdacba2686cf85c7d3b4d954f8d54589ba67890a0af11c40f5e
--
-- Frozen raw app-state hashes:
--   Exercise:   fdd4b6945284c46dadcf60b4000a02f2e75daf31efd10b55358cfa4813fa65e0
--   Supplement: dd25cd82f88ad07afdea2e91cfc80f9ccaca60598566fcc34d9697036408790c
--
-- No legacy source row is updated or deleted.

do $backfill_precheck$
declare
    current_exercises jsonb;
    current_supplements jsonb;
    destination_items integer;
    destination_events integer;
    exercise_hash text;
    supplement_hash text;
begin
    select count(*) into destination_items
      from public.hm_content_repository_items;
    select count(*) into destination_events
      from public.hm_content_repository_events;

    if destination_items <> 0 or destination_events <> 0 then
        raise exception
            'Content Repository backfill refused: destination is not empty (items %, events %).',
            destination_items,
            destination_events;
    end if;

    select
        data -> 'exercises',
        data -> 'supplement_repository'
      into
        current_exercises,
        current_supplements
      from public.healthyme_app_state
     where id = 'healthyme_app_state_v1'
       for share;

    if current_exercises is null or current_supplements is null then
        raise exception
            'Content Repository backfill refused: legacy app-state sources are missing.';
    end if;

    if jsonb_array_length(current_exercises) <> 3
       or jsonb_array_length(current_supplements) <> 5 then
        raise exception
            'Content Repository backfill refused: source counts changed after inventory.';
    end if;

    exercise_hash := encode(
        digest(convert_to(current_exercises::text, 'UTF8'), 'sha256'),
        'hex'
    );
    supplement_hash := encode(
        digest(convert_to(current_supplements::text, 'UTF8'), 'sha256'),
        'hex'
    );

    if exercise_hash <> 'fdd4b6945284c46dadcf60b4000a02f2e75daf31efd10b55358cfa4813fa65e0' then
        raise exception
            'Content Repository backfill refused: Exercise source changed after inventory.';
    end if;

    if supplement_hash <> 'dd25cd82f88ad07afdea2e91cfc80f9ccaca60598566fcc34d9697036408790c' then
        raise exception
            'Content Repository backfill refused: Supplement source changed after inventory.';
    end if;
end;
$backfill_precheck$;

create temporary table hm_content_repository_backfill_expected (
    repository_type text not null,
    source_id text not null,
    display_name text not null,
    status text not null,
    payload jsonb not null,
    source_system text not null,
    legacy_reference text not null,
    created_at timestamptz not null,
    created_by text not null,
    updated_at timestamptz not null,
    updated_by text not null,
    primary key (repository_type, source_id)
) on commit drop;

-- Recipe remains file-backed at this point, so its two frozen rows are explicit.
insert into hm_content_repository_backfill_expected (
    repository_type,
    source_id,
    display_name,
    status,
    payload,
    source_system,
    legacy_reference,
    created_at,
    created_by,
    updated_at,
    updated_by
) values
(
    'recipe',
    '0',
    'Moong Chilla',
    'active',
    $recipe_0${
        "title":"Moong Chilla",
        "description":"High-protein Indian breakfast",
        "meal_type":"Breakfast",
        "diet_type":"Vegetarian",
        "goal_tags":"weight_loss;general",
        "condition_tags":"general",
        "prep_time":"15",
        "calories":"",
        "servings":"",
        "portion_size":"",
        "image_url":"",
        "image_bucket":"",
        "image_path":"",
        "image_access_type":"public",
        "ingredients":"Moong dal batter, spices",
        "steps":"Cook batter on tawa",
        "nutrition":""
    }$recipe_0$::jsonb,
    'recipe_csv',
    'data/recipes.csv:0',
    clock_timestamp(),
    'system:content_repository_backfill',
    clock_timestamp(),
    'system:content_repository_backfill'
),
(
    'recipe',
    '1',
    'Paneer Salad',
    'active',
    $recipe_1${
        "title":"Paneer Salad",
        "description":"Quick protein lunch",
        "meal_type":"Lunch",
        "diet_type":"Vegetarian",
        "goal_tags":"muscle_gain;general",
        "condition_tags":"general",
        "prep_time":"10",
        "calories":"",
        "servings":"",
        "portion_size":"",
        "image_url":"",
        "image_bucket":"",
        "image_path":"",
        "image_access_type":"public",
        "ingredients":"Paneer, veggies",
        "steps":"Mix and serve",
        "nutrition":""
    }$recipe_1$::jsonb,
    'recipe_csv',
    'data/recipes.csv:1',
    clock_timestamp(),
    'system:content_repository_backfill',
    clock_timestamp(),
    'system:content_repository_backfill'
);

-- Exercise is transformed directly from the locked, hash-verified app-state source.
with source_rows as (
    select source_row, ordinal_position
      from public.healthyme_app_state state
      cross join lateral jsonb_array_elements(state.data -> 'exercises')
          with ordinality as rows(source_row, ordinal_position)
     where state.id = 'healthyme_app_state_v1'
)
insert into hm_content_repository_backfill_expected (
    repository_type,
    source_id,
    display_name,
    status,
    payload,
    source_system,
    legacy_reference,
    created_at,
    created_by,
    updated_at,
    updated_by
)
select
    'exercise',
    coalesce(
        nullif(btrim(source_row ->> 'source_id'), ''),
        nullif(btrim(source_row ->> 'id'), '')
    ),
    coalesce(
        nullif(btrim(source_row ->> 'title'), ''),
        nullif(btrim(source_row ->> 'name'), '')
    ),
    case lower(coalesce(nullif(btrim(source_row ->> 'status'), ''), 'active'))
        when 'inactive' then 'inactive'
        when 'stopped' then 'inactive'
        when 'archived' then 'inactive'
        when 'disabled' then 'inactive'
        else 'active'
    end,
    source_row - array[
        'id',
        'source_id',
        'resource_type',
        'status',
        'source',
        'source_system',
        'legacy_reference',
        'created_at',
        'created_by',
        'updated_at',
        'updated_by',
        'content_version'
    ]::text[],
    coalesce(
        nullif(btrim(source_row ->> 'source'), ''),
        'healthyme_app_state:exercises'
    ),
    'healthyme_app_state.data.exercises:' || (ordinal_position - 1)::text,
    case
        when nullif(btrim(source_row ->> 'created_at'), '') is null
            then clock_timestamp()
        when source_row ->> 'created_at' ~ '(Z|[+-][0-9]{2}:[0-9]{2})$'
            then (source_row ->> 'created_at')::timestamptz
        else (source_row ->> 'created_at')::timestamp at time zone 'UTC'
    end,
    coalesce(
        nullif(btrim(source_row ->> 'created_by'), ''),
        'system:content_repository_backfill'
    ),
    case
        when nullif(btrim(source_row ->> 'updated_at'), '') is null
            then clock_timestamp()
        when source_row ->> 'updated_at' ~ '(Z|[+-][0-9]{2}:[0-9]{2})$'
            then (source_row ->> 'updated_at')::timestamptz
        else (source_row ->> 'updated_at')::timestamp at time zone 'UTC'
    end,
    'system:content_repository_backfill'
from source_rows
order by ordinal_position;

-- Supplement is transformed directly from the same locked, hash-verified state.
with source_rows as (
    select source_row, ordinal_position
      from public.healthyme_app_state state
      cross join lateral jsonb_array_elements(state.data -> 'supplement_repository')
          with ordinality as rows(source_row, ordinal_position)
     where state.id = 'healthyme_app_state_v1'
)
insert into hm_content_repository_backfill_expected (
    repository_type,
    source_id,
    display_name,
    status,
    payload,
    source_system,
    legacy_reference,
    created_at,
    created_by,
    updated_at,
    updated_by
)
select
    'supplement',
    coalesce(
        nullif(btrim(source_row ->> 'source_id'), ''),
        nullif(btrim(source_row ->> 'id'), '')
    ),
    coalesce(
        nullif(btrim(source_row ->> 'supplement_name'), ''),
        nullif(btrim(source_row ->> 'title'), ''),
        nullif(btrim(source_row ->> 'name'), '')
    ),
    case lower(coalesce(nullif(btrim(source_row ->> 'status'), ''), 'active'))
        when 'inactive' then 'inactive'
        when 'stopped' then 'inactive'
        when 'archived' then 'inactive'
        when 'disabled' then 'inactive'
        else 'active'
    end,
    source_row - array[
        'id',
        'source_id',
        'resource_type',
        'status',
        'source',
        'source_system',
        'legacy_reference',
        'created_at',
        'created_by',
        'updated_at',
        'updated_by',
        'content_version'
    ]::text[],
    coalesce(
        nullif(btrim(source_row ->> 'source'), ''),
        'healthyme_app_state:supplement_repository'
    ),
    'healthyme_app_state.data.supplement_repository:'
        || (ordinal_position - 1)::text,
    case
        when nullif(btrim(source_row ->> 'created_at'), '') is null
            then clock_timestamp()
        when source_row ->> 'created_at' ~ '(Z|[+-][0-9]{2}:[0-9]{2})$'
            then (source_row ->> 'created_at')::timestamptz
        else (source_row ->> 'created_at')::timestamp at time zone 'UTC'
    end,
    coalesce(
        nullif(btrim(source_row ->> 'created_by'), ''),
        'system:content_repository_backfill'
    ),
    case
        when nullif(btrim(source_row ->> 'updated_at'), '') is null
            then clock_timestamp()
        when source_row ->> 'updated_at' ~ '(Z|[+-][0-9]{2}:[0-9]{2})$'
            then (source_row ->> 'updated_at')::timestamptz
        else (source_row ->> 'updated_at')::timestamp at time zone 'UTC'
    end,
    'system:content_repository_backfill'
from source_rows
order by ordinal_position;

insert into public.hm_content_repository_items (
    repository_type,
    source_id,
    display_name,
    status,
    payload,
    source_system,
    legacy_reference,
    created_at,
    created_by,
    updated_at,
    updated_by
)
select
    repository_type,
    source_id,
    display_name,
    status,
    payload,
    source_system,
    legacy_reference,
    created_at,
    created_by,
    updated_at,
    updated_by
from hm_content_repository_backfill_expected
order by repository_type, source_id;

do $backfill_postcheck$
declare
    mismatch_count integer;
    item_count integer;
    event_count integer;
begin
    select count(*) into item_count
      from public.hm_content_repository_items;
    select count(*) into event_count
      from public.hm_content_repository_events;

    if item_count <> 10 then
        raise exception
            'Content Repository backfill verification failed: expected 10 items, found %.',
            item_count;
    end if;

    if event_count <> 10 then
        raise exception
            'Content Repository backfill verification failed: expected 10 events, found %.',
            event_count;
    end if;

    if (select count(*) from public.hm_content_repository_items where repository_type = 'recipe') <> 2
       or (select count(*) from public.hm_content_repository_items where repository_type = 'exercise') <> 3
       or (select count(*) from public.hm_content_repository_items where repository_type = 'supplement') <> 5 then
        raise exception
            'Content Repository backfill verification failed: repository counts do not match 2/3/5.';
    end if;

    select count(*) into mismatch_count
    from (
        (
            select
                repository_type,
                source_id,
                display_name,
                status,
                payload,
                source_system,
                legacy_reference,
                created_at,
                created_by,
                updated_at,
                updated_by
            from public.hm_content_repository_items
            except
            select
                repository_type,
                source_id,
                display_name,
                status,
                payload,
                source_system,
                legacy_reference,
                created_at,
                created_by,
                updated_at,
                updated_by
            from hm_content_repository_backfill_expected
        )
        union all
        (
            select
                repository_type,
                source_id,
                display_name,
                status,
                payload,
                source_system,
                legacy_reference,
                created_at,
                created_by,
                updated_at,
                updated_by
            from hm_content_repository_backfill_expected
            except
            select
                repository_type,
                source_id,
                display_name,
                status,
                payload,
                source_system,
                legacy_reference,
                created_at,
                created_by,
                updated_at,
                updated_by
            from public.hm_content_repository_items
        )
    ) differences;

    if mismatch_count <> 0 then
        raise exception
            'Content Repository backfill verification failed: % canonical row differences.',
            mismatch_count;
    end if;

    if exists (
        select 1
          from public.hm_content_repository_items
         where content_version <> 1
    ) then
        raise exception
            'Content Repository backfill verification failed: initial content_version must be 1.';
    end if;

    if exists (
        select 1
          from public.hm_content_repository_events
         where event_type <> 'created'
            or before_record is not null
            or after_record is null
            or actor_id <> 'system:content_repository_backfill'
    ) then
        raise exception
            'Content Repository backfill verification failed: audit events are not clean created events.';
    end if;

    if (
        select count(distinct repository_item_id)
          from public.hm_content_repository_events
    ) <> 10 then
        raise exception
            'Content Repository backfill verification failed: each item requires one created event.';
    end if;

    if exists (
        select 1
          from public.hm_content_repository_events event
          join public.hm_content_repository_items item
            on item.id = event.repository_item_id
         where event.repository_type <> item.repository_type
            or event.source_id <> item.source_id
            or event.after_record ->> 'source_id' <> item.source_id
            or event.after_record ->> 'repository_type' <> item.repository_type
    ) then
        raise exception
            'Content Repository backfill verification failed: audit identity mismatch.';
    end if;
end;
$backfill_postcheck$;
