-- HealthyMe P0 Member Authority Contract v2
-- Guarded database rollback for sql/p0_member_exercise_log_allocation_identity_v2.sql
--
-- EMERGENCY ORDER:
--   1. Revert/deploy web code to the pre-#425 main anchor first.
--   2. Prefer leaving the additive v2 schema in place; old code ignores it.
--   3. Run this SQL only if the database additions themselves must be removed.
--
-- This rollback deliberately aborts if any v2 rows have been written. That
-- prevents loss of new Exercise Journal history and prevents forcing legacy
-- Recommendation Profile identity onto allocation-linked rows.

do $$
begin
  if exists (
    select 1
    from public.hm_member_exercise_logs
    where allocation_id is not null
       or journal_entry_key is not null
       or profile_id is null
       or day_number is null
  ) then
    raise exception
      'P0 v2 rollback blocked: allocation/manual v2 rows or nullable legacy identity exist. Revert application code only and leave additive schema in place.';
  end if;
end
$$;

drop index if exists public.hm_member_exercise_logs_member_allocation_idx;

alter table public.hm_member_exercise_logs
  drop constraint if exists hm_member_exercise_logs_identity_present,
  drop constraint if exists hm_member_exercise_logs_manual_entry_unique,
  drop constraint if exists hm_member_exercise_logs_allocation_unique;

-- Safe only because the guard above confirmed no v2/null-identity rows exist.
alter table public.hm_member_exercise_logs
  alter column profile_id set not null,
  alter column day_number set not null;

alter table public.hm_member_exercise_logs
  drop column if exists journal_entry_key,
  drop column if exists source_id,
  drop column if exists allocation_id;

-- Existing legacy uniqueness and RLS policies are intentionally untouched.
