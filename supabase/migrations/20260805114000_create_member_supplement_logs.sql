begin;

create table if not exists public.hm_member_supplement_logs (
  id uuid primary key default gen_random_uuid(),
  member_id text not null,
  log_date date not null,
  allocation_id text not null,
  source_id text,
  supplement_name text not null,
  dosage text,
  timing text not null,
  status text not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint hm_member_supplement_logs_status_check
    check (status in ('Taken', 'Not Taken')),
  constraint hm_member_supplement_logs_member_day_allocation_timing_key
    unique (member_id, log_date, allocation_id, timing)
);

comment on table public.hm_member_supplement_logs is
  'Member-entered Taken/Not Taken journal records for allocated supplement timings.';

create index if not exists hm_member_supplement_logs_member_date_idx
  on public.hm_member_supplement_logs (member_id, log_date desc);

alter table public.hm_member_supplement_logs enable row level security;

drop policy if exists hm_member_supplement_logs_member_select_self
  on public.hm_member_supplement_logs;
create policy hm_member_supplement_logs_member_select_self
  on public.hm_member_supplement_logs
  for select
  to authenticated
  using (
    exists (
      select 1
      from public.hm_users as member
      where member.id = hm_member_supplement_logs.member_id
        and member.role = 'member'
        and member.is_active is true
        and member.auth_user_id = (select auth.uid())
    )
  );

drop policy if exists hm_member_supplement_logs_member_insert_self
  on public.hm_member_supplement_logs;
create policy hm_member_supplement_logs_member_insert_self
  on public.hm_member_supplement_logs
  for insert
  to authenticated
  with check (
    exists (
      select 1
      from public.hm_users as member
      where member.id = hm_member_supplement_logs.member_id
        and member.role = 'member'
        and member.is_active is true
        and member.auth_user_id = (select auth.uid())
    )
  );

drop policy if exists hm_member_supplement_logs_member_update_self
  on public.hm_member_supplement_logs;
create policy hm_member_supplement_logs_member_update_self
  on public.hm_member_supplement_logs
  for update
  to authenticated
  using (
    exists (
      select 1
      from public.hm_users as member
      where member.id = hm_member_supplement_logs.member_id
        and member.role = 'member'
        and member.is_active is true
        and member.auth_user_id = (select auth.uid())
    )
  )
  with check (
    exists (
      select 1
      from public.hm_users as member
      where member.id = hm_member_supplement_logs.member_id
        and member.role = 'member'
        and member.is_active is true
        and member.auth_user_id = (select auth.uid())
    )
  );

revoke all on table public.hm_member_supplement_logs from anon, authenticated;
grant select, insert, update on table public.hm_member_supplement_logs
  to authenticated, service_role;

commit;
