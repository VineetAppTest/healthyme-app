# AUTH-XPLAT-2 — Supabase Auth User Mapping and Migration SQL Design

Status: Stage 2 design
Scope: Documentation only
Date: 2026-06-25

## 1. Purpose

This document defines the Supabase Auth user-mapping design for HealthyMe.

The goal is to connect Supabase Auth identities to the existing HealthyMe business user records without breaking existing app data, workflow data, Streamlit admin behavior, Flutter member login, reports, or rollback.

This stage does not switch Streamlit login behavior.

## 2. Current inspected Supabase state

Read-only inspection confirmed the following Supabase objects exist:

```text
public.healthyme_app_state
public.hm_users
public.hm_workflow
auth.users
```

Current row counts from read-only inspection:

```text
public.hm_users             11 rows
public.hm_workflow          11 rows
public.healthyme_app_state   1 row
auth.users                   8 rows
```

Current active user/auth alignment:

```text
active hm_users                         7
auth.users with email                   8
active hm_users matched to auth.users   7
active hm_users without auth user        0
auth users without active hm_user        1
```

Interpretation:

- The active HealthyMe users already appear to have matching Supabase Auth users by email.
- There is one Supabase Auth user that does not currently match an active HealthyMe app user.
- Email-based bridging is currently viable, but a stable `supabase_auth_id` mapping is still required before deeper Flutter persistence or final Streamlit Supabase Auth migration.

## 3. Current table structure

### 3.1 public.hm_users

Current columns:

```text
id                   text, primary key
name                 text
email                text, unique
password_hash        text
role                 text
must_reset_password  boolean
is_active            boolean
auth_provider        text
created_at           timestamptz
updated_at           timestamptz
```

Current relevant indexes/constraints:

```text
hm_users_pkey             primary key on id
hm_users_email_key        unique index on email
idx_hm_users_email        index on lower(email)
idx_hm_users_role_active  index on role, is_active
hm_users_role_check       role check constraint
```

### 3.2 public.hm_workflow

Current columns:

```text
user_id                text, primary key / foreign key to hm_users.id
laf_completed          boolean
nsp1_completed         boolean
nsp2_completed         boolean
submitted_for_review   boolean
admin_completed        boolean
final_report_ready     boolean
workflow_status        text
created_at             timestamptz
updated_at             timestamptz
```

Current relevant indexes/constraints:

```text
hm_workflow_pkey          primary key on user_id
hm_workflow_user_id_fkey  foreign key to hm_users.id
idx_hm_workflow_review    index on review status flags
idx_hm_workflow_status    index on workflow_status
```

### 3.3 public.healthyme_app_state

Current columns:

```text
id          text, primary key
data        jsonb
created_at  timestamptz
updated_at  timestamptz
```

## 4. Current RLS state

Read-only inspection confirmed RLS is enabled on:

```text
public.healthyme_app_state
public.hm_users
public.hm_workflow
```

Existing member-safe policies:

```text
hm_users:
- authenticated users can SELECT their own active member row by matching JWT email to hm_users.email

hm_workflow:
- authenticated users can SELECT their own workflow by joining hm_workflow.user_id to hm_users.id and matching JWT email
```

Existing app-state policies:

```text
healthyme_app_state:
- healthme_app_user role can select/insert/update/delete the JSONB app state
```

Interpretation:

- Flutter member read policies already depend on email matching.
- Final identity mapping should add Supabase Auth UID mapping while preserving the email policies during transition.
- Streamlit server-side access can continue to use server-side secrets while migration is controlled.

## 5. Target identity model

Do not replace the existing HealthyMe business user ID.

The existing app-level user ID remains the stable business key across:

- profiles
- workflow
- LAF responses
- NSP responses
- admin assessments
- reports
- notifications
- assessment instances
- Streamlit admin operations

Add Supabase Auth identity fields to `hm_users`.

Target mapping:

```text
hm_users.id                 Existing HealthyMe business/app user ID
hm_users.email              Login email and compatibility bridge
hm_users.role               member/admin/practitioner_lite_future
hm_users.is_active          HealthyMe authorization gate
hm_users.supabase_auth_id   Supabase auth.users.id
hm_users.auth_provider      auth0 / oidc / supabase during transition
hm_users.auth_migrated_at   timestamp when mapping was established
hm_users.updated_at         standard update timestamp
```

## 6. Proposed migration SQL — draft only, do not execute yet

The SQL below is a draft for Stage 3/controlled migration. It is not to be executed in Stage 2 without explicit approval.

```sql
-- AUTH-XPLAT-2 DRAFT ONLY
-- Purpose: Add Supabase Auth mapping fields to public.hm_users.

alter table public.hm_users
  add column if not exists supabase_auth_id uuid,
  add column if not exists auth_migrated_at timestamptz;

create index if not exists idx_hm_users_supabase_auth_id
  on public.hm_users (supabase_auth_id);

-- Optional uniqueness after backfill is clean.
-- Keep partial unique to allow unmigrated/null rows during transition.
create unique index if not exists uq_hm_users_supabase_auth_id_not_null
  on public.hm_users (supabase_auth_id)
  where supabase_auth_id is not null;
```

## 7. Proposed backfill SQL — draft only, do not execute yet

Because active users currently match by email, the first controlled backfill can map `hm_users.email` to `auth.users.email`.

```sql
-- AUTH-XPLAT-2 DRAFT ONLY
-- Purpose: Backfill Supabase Auth ID for existing HealthyMe users by email.

update public.hm_users u
set
  supabase_auth_id = au.id,
  auth_provider = 'supabase',
  auth_migrated_at = now(),
  updated_at = now()
from auth.users au
where lower(u.email) = lower(au.email)
  and u.supabase_auth_id is null;
```

Important:

- This maps all matching users, not only members.
- This should be run only after confirming admin/member pilot users are correct.
- Do not run this until Stage 3 is explicitly approved.

## 8. Verification SQL — safe read-only checks

These checks are safe to run before and after backfill.

```sql
-- Count app users vs Supabase Auth users.
select
  (select count(*) from public.hm_users) as hm_users_count,
  (select count(*) from auth.users) as auth_users_count;

-- Check active users that match by email.
with hm as (
  select lower(email) as email from public.hm_users where is_active = true
), au as (
  select lower(email) as email from auth.users where email is not null
)
select
  (select count(*) from hm) as active_hm_users,
  (select count(*) from au) as auth_users_with_email,
  (select count(*) from hm join au using(email)) as email_matches,
  (select count(*) from hm where email not in (select email from au)) as active_hm_without_auth_user,
  (select count(*) from au where email not in (select email from hm)) as auth_user_without_active_hm_user;

-- Check mapped users after migration.
select
  count(*) filter (where supabase_auth_id is not null) as mapped_users,
  count(*) filter (where supabase_auth_id is null) as unmapped_users
from public.hm_users;
```

## 9. Rollback SQL — draft only

If the mapping fields are added but the migration is abandoned, the safest rollback is first to stop using the fields, not immediately drop them.

Soft rollback:

```sql
-- AUTH-XPLAT-2 DRAFT ONLY
-- Soft rollback: remove active mappings but keep columns.

update public.hm_users
set
  supabase_auth_id = null,
  auth_migrated_at = null,
  auth_provider = 'oidc',
  updated_at = now()
where supabase_auth_id is not null;
```

Hard rollback, only if explicitly approved:

```sql
-- AUTH-XPLAT-2 DRAFT ONLY
-- Hard rollback: remove columns/indexes.

DROP INDEX IF EXISTS public.uq_hm_users_supabase_auth_id_not_null;
DROP INDEX IF EXISTS public.idx_hm_users_supabase_auth_id;

alter table public.hm_users
  drop column if exists auth_migrated_at,
  drop column if exists supabase_auth_id;
```

Recommendation:

Use soft rollback first. Avoid hard rollback unless the app is fully stable without the mapping fields.

## 10. Required app behavior after mapping

### 10.1 Flutter

Flutter should continue to authenticate with Supabase Auth.

Before any real LAF/NSP persistence is connected, Flutter must resolve:

```text
Supabase Auth user -> hm_users row -> HealthyMe business user ID
```

Preferred lookup order after mapping exists:

```text
1. supabase_auth_id = auth.uid()
2. fallback during transition: lower(email) = lower(auth.jwt()->>'email')
```

Do not let Flutter write member data until member-safe RLS/RPC design is approved.

### 10.2 Streamlit

Streamlit should continue Auth0/OIDC until dual-auth mode is implemented.

When Supabase Auth is added to Streamlit later:

```text
Supabase Auth session -> auth user ID/email -> hm_users row -> role -> app user ID -> route
```

Unauthorized Supabase Auth users must be blocked if no active `hm_users` record exists.

## 11. Role handling

Current roles should continue to be stored in `hm_users.role`.

Expected role values:

```text
admin
member
```

Future-ready role value:

```text
practitioner_lite
```

Do not introduce Practitioner Lite behavior in this stage.

## 12. Stage 2 acceptance criteria

Stage 2 is complete when:

1. Existing Supabase schema has been inspected read-only.
2. `hm_users`, `hm_workflow`, and `healthyme_app_state` current structure is documented.
3. Current counts and RLS state are documented without exposing member PII.
4. Target `supabase_auth_id` mapping model is documented.
5. Draft migration SQL is documented but not executed.
6. Draft rollback SQL is documented but not executed.
7. No runtime app code is changed.
8. No Supabase schema is changed.
9. No secrets/config/deployment/auth settings are changed.
10. Stage 3 requirements are clear.

## 13. Stage 3 recommended next task

Next task:

```text
AUTH-XPLAT-3 — Streamlit Dual-Auth Mode Foundation
```

Stage 3 should introduce a controlled feature flag:

```text
AUTH_MODE = auth0 | dual | supabase
```

Stage 3 should not remove Auth0. It should only create the safe dual-auth foundation for pilot testing.
