-- Enforce the Member Plan invariant at the database boundary:
-- one and only one Active Meal Profile may exist for a member at a time.
--
-- The application publish path already replaces the member's previous Active
-- profile before activating the selected Draft. This partial unique index is
-- the final safeguard against simultaneous or alternate writes bypassing that
-- sequence.

do $$
begin
    if exists (
        select 1
        from public.hm_recommendation_profiles
        where status = 'active'
          and nullif(btrim(assigned_member_id), '') is not null
        group by assigned_member_id
        having count(*) > 1
    ) then
        raise exception
            'Cannot enforce one Active Meal Profile per member: duplicate Active profiles exist.';
    end if;
end
$$;

create unique index if not exists
    hm_recommendation_profiles_one_active_per_member_idx
on public.hm_recommendation_profiles (assigned_member_id)
where status = 'active'
  and nullif(btrim(assigned_member_id), '') is not null;

comment on index public.hm_recommendation_profiles_one_active_per_member_idx is
    'Prevents more than one Active Meal Profile for the same assigned member.';
