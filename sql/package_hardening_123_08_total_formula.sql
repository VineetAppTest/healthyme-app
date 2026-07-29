-- Package Hardening follow-up: package master total is always derived.
-- Existing member subscription snapshots are intentionally not changed.

update public.hm_packages
set total_value = session_count * cost_per_session,
    updated_at = now(),
    updated_by = 'package_total_formula_hardening'
where total_value is distinct from session_count * cost_per_session;

create or replace function public.hm_packages_calculate_total()
returns trigger
language plpgsql
set search_path = public
as $$
begin
  new.total_value := new.session_count * new.cost_per_session;
  return new;
end;
$$;

drop trigger if exists hm_packages_calculate_total_before_write
  on public.hm_packages;

create trigger hm_packages_calculate_total_before_write
before insert or update of session_count, cost_per_session, total_value
on public.hm_packages
for each row
execute function public.hm_packages_calculate_total();

do $$
begin
  if not exists (
    select 1
    from pg_constraint
    where conname = 'hm_packages_total_formula_check'
      and conrelid = 'public.hm_packages'::regclass
  ) then
    alter table public.hm_packages
      add constraint hm_packages_total_formula_check
      check (total_value = session_count * cost_per_session);
  end if;
end;
$$;

revoke all on function public.hm_packages_calculate_total()
  from public, anon, authenticated;

comment on function public.hm_packages_calculate_total() is
  'Forces Package Library total_value to equal session_count multiplied by cost_per_session. Member subscription snapshots remain unchanged.';
