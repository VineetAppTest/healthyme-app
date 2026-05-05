-- HealthyMe Normalized Tables Foundation - Users + Workflow
-- Run this once in Supabase SQL Editor.
-- This is additive and does not remove the existing healthyme_app_state JSONB table.

create table if not exists public.hm_users (
    id text primary key,
    name text not null default '',
    email text not null unique,
    password_hash text not null default '',
    role text not null check (role in ('admin', 'member')),
    must_reset_password boolean not null default false,
    is_active boolean not null default true,
    auth_provider text not null default 'oidc',
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index if not exists idx_hm_users_email on public.hm_users(lower(email));
create index if not exists idx_hm_users_role_active on public.hm_users(role, is_active);

create table if not exists public.hm_workflow (
    user_id text primary key references public.hm_users(id) on delete cascade,
    laf_completed boolean not null default false,
    nsp1_completed boolean not null default false,
    nsp2_completed boolean not null default false,
    submitted_for_review boolean not null default false,
    admin_completed boolean not null default false,
    final_report_ready boolean not null default false,
    workflow_status text not null default 'not_started',
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index if not exists idx_hm_workflow_status on public.hm_workflow(workflow_status);
create index if not exists idx_hm_workflow_review on public.hm_workflow(submitted_for_review, admin_completed, final_report_ready);

create or replace function public.hm_set_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

drop trigger if exists set_hm_users_updated_at on public.hm_users;
create trigger set_hm_users_updated_at
before update on public.hm_users
for each row execute function public.hm_set_updated_at();

drop trigger if exists set_hm_workflow_updated_at on public.hm_workflow;
create trigger set_hm_workflow_updated_at
before update on public.hm_workflow
for each row execute function public.hm_set_updated_at();

-- RLS remains enabled. The Streamlit backend should use the service role key.
alter table public.hm_users enable row level security;
alter table public.hm_workflow enable row level security;

-- No public policies are intentionally created.
-- Access should be through Streamlit server-side app using SUPABASE_SERVICE_ROLE_KEY.