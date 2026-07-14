-- H9A.11 Member Exercise Journal
-- Creates version-linked completion tracking for exercises prescribed through
-- the active Recommendation Profile Builder contract.

create table if not exists public.hm_member_exercise_logs (
  id uuid primary key default gen_random_uuid(),
  member_id text not null,
  log_date date not null,
  profile_id uuid not null,
  profile_name text,
  day_number integer not null check (day_number between 1 and 7),
  item_order integer not null default 0,
  exercise_name text not null,
  scheduled_time text,
  difficulty text,
  duration_or_reps text,
  equipment text,
  benefits text,
  instruction text,
  image_reference text,
  status text not null default 'Not Started'
    check (status in ('Not Started', 'In Progress', 'Completed', 'Skipped')),
  completion_time time,
  member_notes text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (member_id, log_date, profile_id, day_number, item_order)
);

create index if not exists hm_member_exercise_logs_member_date_idx
  on public.hm_member_exercise_logs (member_id, log_date desc);

alter table public.hm_member_exercise_logs enable row level security;

-- The current Streamlit application may use service_role for controlled writes.
-- These policies keep the contract Flutter-ready for direct authenticated access.
drop policy if exists hm_member_exercise_logs_member_select_self on public.hm_member_exercise_logs;
create policy hm_member_exercise_logs_member_select_self
on public.hm_member_exercise_logs
for select
to authenticated
using (
  exists (
    select 1
    from public.hm_users u
    where u.id::text = hm_member_exercise_logs.member_id
      and u.role = 'member'
      and u.is_active = true
      and lower(u.email) = lower(coalesce(auth.jwt() ->> 'email', ''))
  )
);

drop policy if exists hm_member_exercise_logs_member_insert_self on public.hm_member_exercise_logs;
create policy hm_member_exercise_logs_member_insert_self
on public.hm_member_exercise_logs
for insert
to authenticated
with check (
  exists (
    select 1
    from public.hm_users u
    where u.id::text = hm_member_exercise_logs.member_id
      and u.role = 'member'
      and u.is_active = true
      and lower(u.email) = lower(coalesce(auth.jwt() ->> 'email', ''))
  )
);

drop policy if exists hm_member_exercise_logs_member_update_self on public.hm_member_exercise_logs;
create policy hm_member_exercise_logs_member_update_self
on public.hm_member_exercise_logs
for update
to authenticated
using (
  exists (
    select 1
    from public.hm_users u
    where u.id::text = hm_member_exercise_logs.member_id
      and lower(u.email) = lower(coalesce(auth.jwt() ->> 'email', ''))
  )
)
with check (
  exists (
    select 1
    from public.hm_users u
    where u.id::text = hm_member_exercise_logs.member_id
      and lower(u.email) = lower(coalesce(auth.jwt() ->> 'email', ''))
  )
);
