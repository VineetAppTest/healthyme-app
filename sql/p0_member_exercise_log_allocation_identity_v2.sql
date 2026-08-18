-- HealthyMe P0 Member Authority Contract v2
-- Additive Exercise Journal identity migration.
--
-- New prescribed rows link to member_exercise_allocations through allocation_id.
-- New unassigned/extra actual rows use journal_entry_key so the accepted
-- "+ Add Exercise" behaviour remains persistable without fabricating a profile.
-- Historical Recommendation Profile-linked rows remain unchanged and readable.

alter table public.hm_member_exercise_logs
  add column if not exists allocation_id text,
  add column if not exists source_id text,
  add column if not exists journal_entry_key text;

-- New v2 rows must not invent Recommendation Profile identity.
alter table public.hm_member_exercise_logs
  alter column profile_id drop not null,
  alter column day_number drop not null;

-- PostgreSQL UNIQUE permits multiple NULL values, so legacy rows with
-- allocation_id/journal_entry_key NULL remain valid while new identities can be
-- used directly by PostgREST/Supabase upsert on_conflict.
do $$
begin
  if not exists (
    select 1
    from pg_constraint
    where conname = 'hm_member_exercise_logs_allocation_unique'
      and conrelid = 'public.hm_member_exercise_logs'::regclass
  ) then
    alter table public.hm_member_exercise_logs
      add constraint hm_member_exercise_logs_allocation_unique
      unique (member_id, log_date, allocation_id);
  end if;
end
$$;

do $$
begin
  if not exists (
    select 1
    from pg_constraint
    where conname = 'hm_member_exercise_logs_manual_entry_unique'
      and conrelid = 'public.hm_member_exercise_logs'::regclass
  ) then
    alter table public.hm_member_exercise_logs
      add constraint hm_member_exercise_logs_manual_entry_unique
      unique (member_id, log_date, journal_entry_key);
  end if;
end
$$;

do $$
begin
  if not exists (
    select 1
    from pg_constraint
    where conname = 'hm_member_exercise_logs_identity_present'
      and conrelid = 'public.hm_member_exercise_logs'::regclass
  ) then
    alter table public.hm_member_exercise_logs
      add constraint hm_member_exercise_logs_identity_present
      check (
        allocation_id is not null
        or journal_entry_key is not null
        or profile_id is not null
      ) not valid;
  end if;
end
$$;

alter table public.hm_member_exercise_logs
  validate constraint hm_member_exercise_logs_identity_present;

create index if not exists hm_member_exercise_logs_member_allocation_idx
  on public.hm_member_exercise_logs (member_id, allocation_id, log_date desc)
  where allocation_id is not null;

-- Existing RLS policies are intentionally unchanged. They already scope member
-- select/insert/update access by member_id and authenticated member email.
