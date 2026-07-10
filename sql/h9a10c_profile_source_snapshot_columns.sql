-- HealthyMe H9A.10C - Profile Builder source snapshot columns
-- Run once in Supabase SQL Editor before validating source snapshot persistence.
-- This is additive and backward-compatible.

alter table public.hm_recommendation_profile_items
  add column if not exists source_type text,
  add column if not exists source_id text,
  add column if not exists source_label text,
  add column if not exists source_snapshot jsonb default '{}'::jsonb,
  add column if not exists source_image_url text,
  add column if not exists source_image_bucket text,
  add column if not exists source_image_path text,
  add column if not exists source_image_access_type text;

create index if not exists hm_recommendation_profile_items_source_idx
  on public.hm_recommendation_profile_items (profile_id, item_type, source_type, source_id);

comment on column public.hm_recommendation_profile_items.source_type is
  'H9A.10C source family, for example recipe_repository, exercise_repository, active_supplement_regimen.';
comment on column public.hm_recommendation_profile_items.source_id is
  'H9A.10C source identifier from repository/regimen at selection time.';
comment on column public.hm_recommendation_profile_items.source_label is
  'H9A.10C clean source title/name, kept separate from admin override display label.';
comment on column public.hm_recommendation_profile_items.source_snapshot is
  'H9A.10C immutable source detail snapshot preserved at draft/publish time.';
comment on column public.hm_recommendation_profile_items.source_image_url is
  'H9A.10C optional image URL reference only; image is not loaded in normal admin editing.';
comment on column public.hm_recommendation_profile_items.source_image_bucket is
  'H9A.10C optional Supabase storage bucket reference.';
comment on column public.hm_recommendation_profile_items.source_image_path is
  'H9A.10C optional Supabase storage path reference.';
comment on column public.hm_recommendation_profile_items.source_image_access_type is
  'H9A.10C optional image access type reference.';
