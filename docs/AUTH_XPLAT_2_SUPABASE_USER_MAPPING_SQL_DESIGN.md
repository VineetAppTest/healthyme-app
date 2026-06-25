# AUTH-XPLAT-2 — Supabase Auth User Mapping and Migration SQL Design

Status: Stage 2 design only
Scope: Documentation and SQL design only
Date: 2026-06-25

## 1. Purpose

This document defines the Supabase Auth identity mapping design for HealthyMe across:

1. Flutter Member App
2. Streamlit Web App / Full Admin
3. Future Practitioner Lite

This stage does not change live login behavior and does not execute any database migration.

## 2. Stage 2 scope

Included:

- Inspect current Supabase table structure at a schema level.
- Confirm current `hm_users`, `hm_workflow`, and `healthyme_app_state` status.
- Design safe user/auth mapping fields.
- Draft SQL migration and rollback SQL.
- Define pilot mapping process for one admin and one member.

Not included:

- No Supabase schema change executed.
- No Streamlit code change.
- No Flutter code change.
- No Auth0 removal.
- No Streamlit `AUTH_MODE` feature flag yet.
- No production user migration.
- No RLS policy replacement yet.

## 3. Current Supabase table inspection summary

Read-only inspection confirmed these tables exist:

```text
public.healthyme_app_state
public.hm_users
public.hm_workflow
auth.users
```

Current row counts at inspection time:

```text
hm_users: 11
hm_workflow: 11
healthyme_app_state: 1
auth.users: 8
```

Current `hm_users` columns:

```text
id text primary key
name text not null default ''
email text not null unique
password_hash text not null default ''
role text not null
must_reset_password boolean not null default false
is_active boolean not null default true
auth_provider text not null default 'oidc'
created_at timestamptz not null default now()
updated_at timestamptz not null default now()
```

Current `hm_workflow` columns:

```text
user_id text primary key references hm_users(id)
laf_completed boolean not null default false
nsp1_completed boolean not null default false
nsp2_completed boolean not null default false
submitted_for_review boolean not null default false
admin_completed boolean not null default false
final_report_ready boolean not null default false
workflow_status text not null default 'not_started'
created_at timestamptz not null default now()
updated_at timestamptz not null default now()
```

Current `healthyme_app_state` columns:

```text
id text primary key
data jsonb not null default '{}'
created_at timestamptz not null default now()
updated_at timestamptz not null default now()
```

## 4. Current role/provider state

At inspection time, `hm_users` has a mix of active/inactive admin/member rows and current `auth_provider` values:

```text
admin / oidc / inactive: 1
admin / oidc / active: 2
member / local_or_oidc / active: 1
member / oidc / inactive: 3
member / oidc / active: 4
```

Interpretation:

- `hm_users` is already the correct app-level access-control table.
- Login identity provider is still transitional and not fully normalized to Supabase Auth.
- Existing business/user IDs must remain stable.

## 5. Current RLS state

RLS is enabled on:

```text
public.healthyme_app_state
public.hm_users
public.hm_workflow
```

Current member-safe policies exist for Flutter-style authenticated access:

- `hm_users`: member can read own active row by matching `lower(email)` to JWT email.
- `hm_workflow`: member can read own workflow by joining through `hm_users` and matching JWT email.

Interpretation:

- Current RLS already supports basic member read-by-email behavior.
- Stage 2 should not replace RLS yet.
- Once `supabase_auth_id` is populated, later stages can strengthen policies to prefer `auth.uid()` while retaining email fallback during transition.

## 6. Identity design decision

Do not replace `hm_users.id` with `auth.users.id`.

`hm_users.id` remains the HealthyMe business/app user ID because it is already referenced by profiles, workflow, LAF, NSP, reports, admin assessment, and assessment instances.

Add Supabase Auth identity as a mapping field.

Target model:

```text
hm_users.id                 = HealthyMe app/business user ID
hm_users.email              = login email and current bridge key
hm_users.role               = admin/member/future practitioner_lite
hm_users.is_active          = HealthyMe access control
hm_users.auth_provider      = oidc/auth0/local_or_oidc/supabase transition marker
hm_users.supabase_auth_id   = Supabase auth.users.id
hm_users.auth_migrated_at   = when user row was linked to Supabase Auth
hm_users.auth_last_login_at = optional future tracking field
```

## 7. Stage 2 migration SQL draft — do not run yet

This SQL is a design draft. It must not be run until explicitly approved.

```sql
begin;

alter table public.hm_users
  add column if not exists supabase_auth_id uuid null,
  add column if not exists auth_migrated_at timestamptz null,
  add column if not exists auth_last_login_at timestamptz null;

create unique index if not exists hm_users_supabase_auth_id_unique
  on public.hm_users (supabase_auth_id)
  where supabase_auth_id is not null;

create index if not exists hm_users_lower_email_idx
  on public.hm_users (lower(email));

comment on column public.hm_users.supabase_auth_id is
  'Supabase auth.users.id mapped to the existing HealthyMe app/business user ID. Do not replace hm_users.id.';

comment on column public.hm_users.auth_migrated_at is
  'Timestamp when this HealthyMe user was linked to Supabase Auth.';

comment on column public.hm_users.auth_last_login_at is
  'Optional future tracking for last successful Supabase Auth login.';

commit;
```

### Why no foreign key to `auth.users` yet?

A foreign key to `auth.users(id)` can be considered later, but it is intentionally not included in this first draft because:

- auth schema behavior is platform-managed;
- Stage 2 should be low-risk;
- rollback is cleaner without a cross-schema dependency;
- email-based bridge still exists during transition.

## 8. Pilot mapping SQL draft — do not run yet

After the Stage 2 schema migration is approved and two pilot Supabase Auth users exist, map only those two pilot users first.

Use placeholder emails only until the actual pilot emails are confirmed.

```sql
begin;

update public.hm_users u
set
  supabase_auth_id = au.id,
  auth_provider = 'supabase',
  auth_migrated_at = now(),
  updated_at = now()
from auth.users au
where lower(au.email) = lower(u.email)
  and u.supabase_auth_id is null
  and lower(u.email) in (
    lower('PILOT_ADMIN_EMAIL_HERE'),
    lower('PILOT_MEMBER_EMAIL_HERE')
  );

commit;
```

Pilot validation query:

```sql
select
  id,
  email,
  role,
  is_active,
  auth_provider,
  supabase_auth_id is not null as linked_to_supabase_auth,
  auth_migrated_at
from public.hm_users
where lower(email) in (
  lower('PILOT_ADMIN_EMAIL_HERE'),
  lower('PILOT_MEMBER_EMAIL_HERE')
)
order by role, email;
```

## 9. Full migration mapping SQL draft — not for pilot

This is for a later rollout only, after pilot passes.

```sql
begin;

update public.hm_users u
set
  supabase_auth_id = au.id,
  auth_provider = 'supabase',
  auth_migrated_at = coalesce(u.auth_migrated_at, now()),
  updated_at = now()
from auth.users au
where lower(au.email) = lower(u.email)
  and u.supabase_auth_id is null
  and u.is_active = true;

commit;
```

Do not run this during pilot.

## 10. Rollback SQL draft

Preferred rollback is non-destructive: keep the columns but unlink Supabase mappings.

Pilot rollback:

```sql
begin;

update public.hm_users
set
  supabase_auth_id = null,
  auth_provider = 'oidc',
  auth_migrated_at = null,
  auth_last_login_at = null,
  updated_at = now()
where lower(email) in (
  lower('PILOT_ADMIN_EMAIL_HERE'),
  lower('PILOT_MEMBER_EMAIL_HERE')
);

commit;
```

Full rollback, only if needed:

```sql
begin;

update public.hm_users
set
  supabase_auth_id = null,
  auth_provider = 'oidc',
  auth_migrated_at = null,
  auth_last_login_at = null,
  updated_at = now()
where auth_provider = 'supabase';

commit;
```

Do not drop columns during normal rollback. Dropping columns is cleanup, not rollback.

## 11. RLS direction for later stage

Current policies use JWT email. That is acceptable for transition, but the stronger final model should use `auth.uid()` once `supabase_auth_id` is populated.

Future member read policy direction:

```sql
-- design direction only, not to run yet
-- Member can read own hm_users row when hm_users.supabase_auth_id = auth.uid()
-- Transitional fallback may continue matching lower(email) = lower(auth.jwt() ->> 'email') until rollout is complete.
```

RLS updates should be a separate stage after identity mapping is proven.

## 12. Required app logic later

### Flutter

Flutter should resolve the HealthyMe app user record after Supabase login using either:

1. `supabase_auth_id = auth.uid()` once available, or
2. email fallback during transition.

Flutter must not write LAF/NSP real data until identity resolution and member isolation are formally closed.

### Streamlit

Streamlit should continue resolving role/access through `hm_users`.

For Stage 3 dual-auth, Streamlit should support:

```text
AUTH_MODE = auth0 | dual | supabase
```

No dual-auth code is added in Stage 2.

## 13. Stage 2 acceptance criteria

Stage 2 is complete when:

1. The current Supabase table structure is documented.
2. Current counts and RLS state are documented without exposing member PII.
3. The mapping strategy preserves existing `hm_users.id`.
4. Draft migration SQL is documented but not executed.
5. Draft pilot mapping SQL is documented but not executed.
6. Draft rollback SQL is documented.
7. Stage 3 prerequisites are clear.

## 14. Stage 3 recommended next task

Next task:

```text
AUTH-XPLAT-3 — Streamlit Dual-Auth Mode Scaffold
```

Stage 3 should introduce a safe feature flag:

```text
AUTH_MODE = auth0 | dual | supabase
```

Stage 3 must default to current Auth0 behavior until Supabase login is tested.
