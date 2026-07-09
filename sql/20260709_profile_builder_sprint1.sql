-- HealthyMe Recommendation Profile Builder - Sprint 1 backend foundation
-- Run once in Supabase SQL Editor before smoke-testing draft save/load.
-- Scope: draft storage only. No publish/member-consumption policies are introduced in this sprint.

create extension if not exists pgcrypto;

create table if not exists public.hm_recommendation_profiles (
  id uuid primary key default gen_random_uuid(),
  profile_name text not null,
  status text not null default 'draft' check (status in ('draft','active','replaced','stopped','archived')),
  region text,
  age_band text,
  diet_type text,
  health_concerns text[] not null default '{}',
  profile_note text,
  change_note text,
  cycle_rule text not null default 'Weekly cyclical until replaced or stopped',
  assigned_member_id text,
  assigned_member_label text,
  start_date date,
  clone_source_profile_id uuid,
  clone_source_label text,
  version_number integer not null default 1,
  created_by_user_id text,
  created_by_email text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.hm_recommendation_profile_items (
  id uuid primary key default gen_random_uuid(),
  profile_id uuid not null references public.hm_recommendation_profiles(id) on delete cascade,
  item_type text not null check (item_type in ('meal','exercise','supplement')),
  day_number integer not null check (day_number between 1 and 7),
  slot_name text not null,
  item_order integer not null default 1,
  reference_label text,
  portion text,
  instruction text,
  scheduled_time text,
  intensity text,
  dosage_frequency text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.hm_recommendation_profile_events (
  id uuid primary key default gen_random_uuid(),
  profile_id uuid references public.hm_recommendation_profiles(id) on delete cascade,
  event_type text not null,
  event_note text,
  created_by_user_id text,
  created_by_email text,
  created_at timestamptz not null default now()
);

create table if not exists public.hm_recommendation_master_options (
  id uuid primary key default gen_random_uuid(),
  option_group text not null,
  option_value text not null,
  sort_order integer not null default 100,
  is_active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique(option_group, option_value)
);

create index if not exists hm_recommendation_profiles_status_idx
on public.hm_recommendation_profiles(status);

create index if not exists hm_recommendation_profiles_member_idx
on public.hm_recommendation_profiles(assigned_member_id, status);

create index if not exists hm_recommendation_items_profile_day_idx
on public.hm_recommendation_profile_items(profile_id, item_type, day_number, slot_name, item_order);

create index if not exists hm_recommendation_events_profile_idx
on public.hm_recommendation_profile_events(profile_id, created_at desc);

create index if not exists hm_recommendation_master_options_group_idx
on public.hm_recommendation_master_options(option_group, is_active, sort_order);

alter table public.hm_recommendation_profiles enable row level security;
alter table public.hm_recommendation_profile_items enable row level security;
alter table public.hm_recommendation_profile_events enable row level security;
alter table public.hm_recommendation_master_options enable row level security;

-- Sprint 1 Streamlit admin uses SUPABASE_SERVICE_ROLE_KEY, which bypasses RLS.
-- Member-facing read policies should be added only in the publish/member-consumption sprint.

insert into public.hm_recommendation_master_options(option_group, option_value, sort_order)
values
  ('age_band','Teen',10),
  ('age_band','18-30',20),
  ('age_band','31-45',30),
  ('age_band','46-60',40),
  ('age_band','60+',50),
  ('health_concern','Weight Management',10),
  ('health_concern','Gut Health',20),
  ('health_concern','Diabetes Support',30),
  ('health_concern','Energy',40),
  ('health_concern','Inflammation',50),
  ('health_concern','Sleep',60),
  ('health_concern','General Wellness',70),
  ('diet_type','Vegetarian',10),
  ('diet_type','Non-vegetarian',20),
  ('diet_type','Vegan',30),
  ('diet_type','Eggetarian',40),
  ('diet_type','Jain',50),
  ('diet_type','Custom',60),
  ('recipe','-- Select recipe --',0),
  ('recipe','Moong Chilla',10),
  ('recipe','Paneer Salad',20),
  ('recipe','Fruit + Nuts',30),
  ('recipe','Herbal Tea',40),
  ('exercise','-- Select exercise --',0),
  ('exercise','Brisk Walking',10),
  ('exercise','Cat-Cow Stretch',20),
  ('exercise','Breathing Exercise',30),
  ('exercise','Mobility Flow',40),
  ('supplement','-- Select supplement --',0),
  ('supplement','Magnesium',10),
  ('supplement','Vitamin D',20),
  ('supplement','Omega 3',30),
  ('supplement','Probiotic',40)
on conflict (option_group, option_value) do nothing;
