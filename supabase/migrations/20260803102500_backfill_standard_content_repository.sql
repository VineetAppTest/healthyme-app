-- Controlled backfill for HealthyMe standard Content Repository.
--
-- Preconditions:
--   * the canonical destination is empty;
--   * the live Exercise and Supplement JSON authorities exactly match the
--     revalidated source snapshot;
--   * Recipe source checksum remains
--     a61af93dec4052ed2b3c8160657be594e5bab68a8e63b554fbd6eb745edce48f.
--
-- Corrected canonical checksums (legacy_reference included for all sources):
--   Recipe:     a61af93dec4052ed2b3c8160657be594e5bab68a8e63b554fbd6eb745edce48f
--   Exercise:   585764b996d1952226405966efada936b87eae4cfa0f2a6120433f5f560e4716
--   Supplement: 4bb7bcb320b0cb1c83981d38531f14db9c020b0a61b1d74b3765f0b09865bf96
--   Total:      52ac68b76032cfdacba2686cf85c7d3b4d954f8d54589ba67890a0af11c40f5e
--
-- No legacy source row is updated or deleted by this migration.

do $backfill_precheck$
declare
    current_exercises jsonb;
    current_supplements jsonb;
    expected_exercises constant jsonb :=
        $exercise_source$[{"id":"0","title":"Brisk Walking","source":"exercise_repository","status":"active","benefits":"","category":"Cardio","equipment":"","goal_tags":"general","image_url":"","source_id":"0","created_at":"","created_by":"","difficulty":"Beginner","image_path":"","updated_at":"","updated_by":"","description":"Easy cardio starter","image_bucket":"","instructions":"Walk at brisk pace","resource_type":"exercises","condition_tags":"general","duration_or_reps":"20 min","image_access_type":"public","hidden_calories_v96":""},{"id":"1","title":"Cat-Cow Stretch","source":"exercise_repository","status":"active","benefits":"","category":"Mobility","equipment":"","goal_tags":"general","image_url":"","source_id":"1","created_at":"","created_by":"","difficulty":"Beginner","image_path":"","updated_at":"","updated_by":"","description":"Gentle spine mobility","image_bucket":"","instructions":"Move slowly with breath","resource_type":"exercises","condition_tags":"general","duration_or_reps":"10 reps","image_access_type":"public","hidden_calories_v96":""},{"id":"2","title":"Stretches","source":"exercise_repository","status":"active","benefits":"","category":"","equipment":"NA","goal_tags":"","image_url":"","source_id":"2","created_at":"2026-08-02T13:30:35.827878+00:00","created_by":"admin_vineet","difficulty":"","image_path":"","updated_at":"2026-08-02T13:30:35.827878+00:00","updated_by":"admin_vineet","description":"","image_bucket":"","instructions":"","resource_type":"exercises","condition_tags":"","duration_or_reps":"Morning","image_access_type":"public","hidden_calories_v96":""}]$exercise_source$::jsonb;
    expected_supplements constant jsonb :=
        $supplement_source$[{"id":"suprepo_4b3c1e53","title":"Sodium","dosage":"200","source":"legacy_member_regimen_backfill","status":"Active","timing":"Morning, Evening","frequency":"Twice","source_id":"suprepo_4b3c1e53","created_at":"2026-08-01T19:13:24","created_by":"system","updated_at":"2026-08-01T19:13:24","updated_by":"system","admin_notes":"","instructions":"","supplement_name":"Sodium","legacy_source_id":"b49d1267"},{"id":"suprepo_2ceffd32","title":"Omega-3","dosage":"1000-1700mg","source":"legacy_member_regimen_backfill","status":"Active","timing":"Morning","frequency":"Once","source_id":"suprepo_2ceffd32","created_at":"2026-08-01T19:13:24","created_by":"system","updated_at":"2026-08-01T19:13:24","updated_by":"system","admin_notes":"","instructions":"","supplement_name":"Omega-3","legacy_source_id":"a130bcda"},{"id":"suprepo_e36aa236","title":"Magnesium","dosage":"400","source":"legacy_member_regimen_backfill","status":"Active","timing":"Morning","frequency":"Once","source_id":"suprepo_e36aa236","created_at":"2026-08-01T19:13:24","created_by":"system","updated_at":"2026-08-01T19:13:24","updated_by":"system","admin_notes":"","instructions":"Test","supplement_name":"Magnesium","legacy_source_id":"5e8182e8"},{"id":"suprepo_c88d2def","title":"Magnesium Test","dosage":"400","source":"legacy_member_regimen_backfill","status":"Active","timing":"Morning","frequency":"once","source_id":"suprepo_c88d2def","created_at":"2026-08-01T19:13:24","created_by":"system","updated_at":"2026-08-01T19:13:24","updated_by":"system","admin_notes":"Test","instructions":"Test","supplement_name":"Magnesium Test","legacy_source_id":"d1575c71"},{"id":"suprepo_f687a40a","title":"Potassium","dosage":"100","source":"legacy_member_regimen_backfill","status":"Active","timing":"Morning, Evening, Before Bed, None","frequency":"thrice","source_id":"suprepo_f687a40a","created_at":"2026-08-01T19:13:24","created_by":"system","updated_at":"2026-08-01T19:13:24","updated_by":"system","admin_notes":"","instructions":"Test","supplement_name":"Potassium","legacy_source_id":"9afc6016"}]$supplement_source$::jsonb;
    destination_items integer;
    destination_events integer;
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

    select data -> 'exercises',
           data -> 'supplement_repository'
      into current_exercises,
           current_supplements
      from public.healthyme_app_state
     where id = 'healthyme_app_state_v1';

    if current_exercises is distinct from expected_exercises then
        raise exception
            'Content Repository backfill refused: Exercise source changed after inventory.';
    end if;

    if current_supplements is distinct from expected_supplements then
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
    ('recipe', '0', 'Moong Chilla', 'active', $json_recipe_0${"title":"Moong Chilla","description":"High-protein Indian breakfast","meal_type":"Breakfast","diet_type":"Vegetarian","goal_tags":"weight_loss;general","condition_tags":"general","prep_time":"15","calories":"","servings":"","portion_size":"","image_url":"","image_bucket":"","image_path":"","image_access_type":"public","ingredients":"Moong dal batter, spices","steps":"Cook batter on tawa","nutrition":""}$json_recipe_0$::jsonb, 'recipe_csv', 'data/recipes.csv:0', clock_timestamp(), 'system:content_repository_backfill', clock_timestamp(), 'system:content_repository_backfill'),
    ('recipe', '1', 'Paneer Salad', 'active', $json_recipe_1${"title":"Paneer Salad","description":"Quick protein lunch","meal_type":"Lunch","diet_type":"Vegetarian","goal_tags":"muscle_gain;general","condition_tags":"general","prep_time":"10","calories":"","servings":"","portion_size":"","image_url":"","image_bucket":"","image_path":"","image_access_type":"public","ingredients":"Paneer, veggies","steps":"Mix and serve","nutrition":""}$json_recipe_1$::jsonb, 'recipe_csv', 'data/recipes.csv:1', clock_timestamp(), 'system:content_repository_backfill', clock_timestamp(), 'system:content_repository_backfill'),
    ('exercise', '0', 'Brisk Walking', 'active', $json_exercise_0${"title":"Brisk Walking","benefits":"","category":"Cardio","equipment":"","goal_tags":"general","image_url":"","difficulty":"Beginner","image_path":"","description":"Easy cardio starter","image_bucket":"","instructions":"Walk at brisk pace","condition_tags":"general","duration_or_reps":"20 min","image_access_type":"public","hidden_calories_v96":""}$json_exercise_0$::jsonb, 'exercise_repository', 'healthyme_app_state.data.exercises:0', clock_timestamp(), 'system:content_repository_backfill', clock_timestamp(), 'system:content_repository_backfill'),
    ('exercise', '1', 'Cat-Cow Stretch', 'active', $json_exercise_1${"title":"Cat-Cow Stretch","benefits":"","category":"Mobility","equipment":"","goal_tags":"general","image_url":"","difficulty":"Beginner","image_path":"","description":"Gentle spine mobility","image_bucket":"","instructions":"Move slowly with breath","condition_tags":"general","duration_or_reps":"10 reps","image_access_type":"public","hidden_calories_v96":""}$json_exercise_1$::jsonb, 'exercise_repository', 'healthyme_app_state.data.exercises:1', clock_timestamp(), 'system:content_repository_backfill', clock_timestamp(), 'system:content_repository_backfill'),
    ('exercise', '2', 'Stretches', 'active', $json_exercise_2${"title":"Stretches","benefits":"","category":"","equipment":"NA","goal_tags":"","image_url":"","difficulty":"","image_path":"","description":"","image_bucket":"","instructions":"","condition_tags":"","duration_or_reps":"Morning","image_access_type":"public","hidden_calories_v96":""}$json_exercise_2$::jsonb, 'exercise_repository', 'healthyme_app_state.data.exercises:2', '2026-08-02T13:30:35.827878+00:00'::timestamptz, 'admin_vineet', '2026-08-02T13:30:35.827878+00:00'::timestamptz, 'system:content_repository_backfill'),
    ('supplement', 'suprepo_4b3c1e53', 'Sodium', 'active', $json_supplement_suprepo_4b3c1e53${"title":"Sodium","dosage":"200","timing":"Morning, Evening","frequency":"Twice","admin_notes":"","instructions":"","supplement_name":"Sodium","legacy_source_id":"b49d1267"}$json_supplement_suprepo_4b3c1e53$::jsonb, 'legacy_member_regimen_backfill', 'healthyme_app_state.data.supplement_repository:0', '2026-08-01T19:13:24+00:00'::timestamptz, 'system', '2026-08-01T19:13:24+00:00'::timestamptz, 'system:content_repository_backfill'),
    ('supplement', 'suprepo_2ceffd32', 'Omega-3', 'active', $json_supplement_suprepo_2ceffd32${"title":"Omega-3","dosage":"1000-1700mg","timing":"Morning","frequency":"Once","admin_notes":"","instructions":"","supplement_name":"Omega-3","legacy_source_id":"a130bcda"}$json_supplement_suprepo_2ceffd32$::jsonb, 'legacy_member_regimen_backfill', 'healthyme_app_state.data.supplement_repository:1', '2026-08-01T19:13:24+00:00'::timestamptz, 'system', '2026-08-01T19:13:24+00:00'::timestamptz, 'system:content_repository_backfill'),
    ('supplement', 'suprepo_e36aa236', 'Magnesium', 'active', $json_supplement_suprepo_e36aa236${"title":"Magnesium","dosage":"400","timing":"Morning","frequency":"Once","admin_notes":"","instructions":"Test","supplement_name":"Magnesium","legacy_source_id":"5e8182e8"}$json_supplement_suprepo_e36aa236$::jsonb, 'legacy_member_regimen_backfill', 'healthyme_app_state.data.supplement_repository:2', '2026-08-01T19:13:24+00:00'::timestamptz, 'system', '2026-08-01T19:13:24+00:00'::timestamptz, 'system:content_repository_backfill'),
    ('supplement', 'suprepo_c88d2def', 'Magnesium Test', 'active', $json_supplement_suprepo_c88d2def${"title":"Magnesium Test","dosage":"400","timing":"Morning","frequency":"once","admin_notes":"Test","instructions":"Test","supplement_name":"Magnesium Test","legacy_source_id":"d1575c71"}$json_supplement_suprepo_c88d2def$::jsonb, 'legacy_member_regimen_backfill', 'healthyme_app_state.data.supplement_repository:3', '2026-08-01T19:13:24+00:00'::timestamptz, 'system', '2026-08-01T19:13:24+00:00'::timestamptz, 'system:content_repository_backfill'),
    ('supplement', 'suprepo_f687a40a', 'Potassium', 'active', $json_supplement_suprepo_f687a40a${"title":"Potassium","dosage":"100","timing":"Morning, Evening, Before Bed, None","frequency":"thrice","admin_notes":"","instructions":"Test","supplement_name":"Potassium","legacy_source_id":"9afc6016"}$json_supplement_suprepo_f687a40a$::jsonb, 'legacy_member_regimen_backfill', 'healthyme_app_state.data.supplement_repository:4', '2026-08-01T19:13:24+00:00'::timestamptz, 'system', '2026-08-01T19:13:24+00:00'::timestamptz, 'system:content_repository_backfill');

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
end;
$backfill_postcheck$;
