# AUTH-XPLAT-1 — Cross-Platform Supabase Auth Migration Audit

Status: Stage 1 audit/design
Scope: Documentation only
Date: 2026-06-25

## 1. Purpose

This document defines the safe migration path for HealthyMe authentication across both active platforms:

1. Flutter Member App: `VineetAppTest/healthyme-flutter-member`
2. Streamlit Web App / Full Admin: `VineetAppTest/healthyme-app`

The goal is to move HealthyMe toward Supabase Auth as the shared identity layer without breaking the existing Streamlit admin/member app, the current member records, workflow, assessment data, reports, or admin access.

## 2. Current platform reality

### 2.1 Flutter Member App

Current status:

- Flutter initializes Supabase directly at app startup.
- Flutter uses the Supabase publishable/anon key only.
- Flutter login already uses Supabase password auth.
- Flutter should not use Auth0.
- Flutter should never contain the Supabase service-role key.

Interpretation:

Flutter Auth is mostly aligned with the target direction already. The remaining Flutter gap is not basic login. The real gap is identity mapping from Supabase Auth user to the HealthyMe business/member record.

### 2.2 Streamlit Web App / Full Admin

Current status:

- Streamlit login currently uses Auth0/OIDC through `st.login("auth0")`.
- Streamlit resolves the authenticated email to a HealthyMe user record.
- Streamlit already uses Supabase for application state when Supabase secrets are configured.
- Streamlit also uses normalized Supabase tables such as `hm_users` and `hm_workflow` where available.
- Streamlit can still fall back to local/sample state when Supabase is unavailable.

Interpretation:

Streamlit has Supabase data storage, but Streamlit authentication is still Auth0/OIDC. Therefore, the migration is not complete until Streamlit can use Supabase Auth as the login identity provider and resolve roles safely.

## 3. Migration principle

Do not replace the existing HealthyMe app user ID immediately.

HealthyMe currently uses app-level `user_id` values across many data areas:

- users
- profiles
- workflow
- LAF responses
- NSP responses
- admin assessment
- reports
- notifications
- assessment instances
- future member/admin shared flows

A forced immediate switch to Supabase `auth.users.id` as the primary business key would create avoidable risk.

### Target identity rule

Keep the existing HealthyMe user ID as the business/app ID.

Add Supabase Auth ID as the authentication identity reference.

Recommended mapping:

```text
hm_users.id                 = existing HealthyMe app/business user ID
hm_users.email              = login email
hm_users.role               = member/admin/practitioner_lite_future
hm_users.is_active          = access control flag
hm_users.supabase_auth_id   = Supabase auth.users.id
hm_users.auth_provider      = auth0 / oidc / supabase during transition
```

## 4. Target architecture

### 4.1 Supabase Auth

Supabase Auth becomes the shared identity layer for:

- Flutter Member App
- Streamlit Web App / Full Admin
- future Practitioner Lite

### 4.2 Flutter Member App

Flutter should:

- use Supabase Auth directly
- use only the publishable/anon key
- read/write only member-safe data through approved APIs/RLS/RPCs
- never use service-role key
- never use Auth0
- map authenticated email/Auth UID to the HealthyMe member record before any real data persistence sprint

### 4.3 Streamlit Full Admin/Web App

Streamlit should:

- transition from Auth0/OIDC to Supabase Auth in controlled stages
- keep admin/reporting work in Streamlit
- use server-side secrets only
- keep service-role key server-side only, if required
- resolve role and app user ID through `hm_users`
- support rollback to Auth0 until Supabase login is proven

### 4.4 Supabase Database

Supabase should:

- retain current HealthyMe app data
- retain normalized `hm_users` and `hm_workflow`
- add auth mapping fields without breaking existing JSONB/state compatibility
- enforce member isolation before Flutter writes real data

## 5. Migration stages

### Stage 0 — Backup and rollback readiness

Completed before Stage 1.

Artifacts expected:

- Streamlit source ZIP downloaded
- Streamlit secrets backup saved securely outside GitHub and ChatGPT
- Flutter APK backup pending post-PR #18 smoke test
- Flutter source ZIP pending post-PR #18 smoke test
- GitHub rollback branches created

Rollback anchors:

```text
Flutter backup branch:
backup/pre-auth-xplat-lafux1-smoke-passed-20260625

Streamlit clean backup branch:
backup/pre-auth-xplat-current-streamlit-20260625-clean
```

### Stage 1 — Audit and design

This document.

No runtime behavior change.
No secrets change.
No Supabase config change.
No Auth0 removal.

### Stage 2 — Supabase identity mapping design

Required output:

- final `hm_users` auth mapping fields
- rules for member/admin role resolution
- rules for existing user provisioning
- migration SQL draft
- rollback SQL draft

No login behavior change yet.

### Stage 3 — Streamlit dual-auth mode

Introduce a feature flag, but do not remove Auth0.

Recommended setting:

```text
AUTH_MODE = auth0 | dual | supabase
```

Meaning:

- `auth0`: current behavior
- `dual`: Auth0 remains active, Supabase login available for controlled test users
- `supabase`: final target mode after UAT

### Stage 4 — Controlled Supabase Auth pilot

Pilot with:

- one admin user
- one member user

Validation:

- Supabase login succeeds
- HealthyMe role resolves correctly
- Admin reaches Admin Dashboard
- Member reaches Member Home
- Logout works
- Unauthorized Supabase Auth user is blocked
- Auth0 rollback remains available

### Stage 5 — Supabase-first rollout and cleanup

Only after pilot passes:

- move Streamlit `AUTH_MODE` from `dual` to `supabase`
- retain rollback window
- later remove Auth0 labels/code/secrets only after production stability

## 6. Required Supabase data changes — future Stage 2, not Stage 1

Potential SQL changes to be designed later:

```sql
alter table hm_users
add column if not exists supabase_auth_id uuid,
add column if not exists auth_provider text default 'supabase',
add column if not exists auth_migrated_at timestamptz;
```

Do not run this yet.

Stage 2 must verify actual table structure first.

## 7. User provisioning options

### Option A — Manual pilot provisioning

Use for first pilot only.

Create one admin and one member in Supabase Auth manually, then ensure their emails already exist in `hm_users`.

Pros:

- simplest
- lowest immediate risk
- good for first UAT

Cons:

- not scalable
- not final rollout solution

### Option B — Admin-only batch provisioning

Use for broader existing user migration.

Streamlit admin-only tool can create Supabase Auth users for existing active HealthyMe users.

Pros:

- controlled
- repeatable
- can log outcomes

Cons:

- requires service-role server-side
- needs careful email/password/reset handling

### Option C — Invite/password reset rollout

Use for production-friendly rollout.

Existing users receive invitation/password reset flow via Supabase Auth.

Pros:

- clean user experience
- avoids shared temporary passwords

Cons:

- needs email template/redirect testing

Recommendation:

- Stage 4: Option A for pilot.
- Stage 5: Option B or C for rollout after pilot.

## 8. What must not happen yet

Do not do any of these during Stage 1:

- remove Auth0 from Streamlit
- remove Auth0 secrets
- change Streamlit deployment auth config
- change Supabase Auth settings
- change redirect URLs
- add Supabase writes from Flutter LAF
- mark LAF completed from Flutter
- unlock NSP1 from backend
- change report generation flow
- replace existing HealthyMe user IDs with Supabase Auth IDs
- expose service-role key to Flutter

## 9. Stage 1 acceptance criteria

Stage 1 is complete when:

1. This audit/design document exists in the repo.
2. No runtime code is changed.
3. No secrets/config/platform files are changed.
4. Current Flutter/Streamlit auth reality is documented.
5. Target identity model is documented.
6. Rollback branches are documented.
7. Stage 2 requirements are clear.

## 10. Stage 2 recommended next task

Next task:

```text
AUTH-XPLAT-2 — Supabase Auth User Mapping and Migration SQL Design
```

Stage 2 should inspect or document the actual Supabase table structure and then prepare SQL and app-level mapping logic.

Stage 2 must still avoid switching login behavior.
