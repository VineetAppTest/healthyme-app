# AUTH-XPLAT-4 Supabase Auth Pilot Readiness

## Purpose

AUTH-XPLAT-4 prepares HealthyMe for controlled Supabase Auth pilot validation with one pilot admin and one pilot member.

This stage is a readiness and verification stage only. It does not migrate users, switch production login behavior, execute SQL, or create Supabase Auth users.

## Prerequisites

- PR #8 merged.
- PR #10 merged.
- PR #9 closed or ignored as superseded.
- Streamlit app tested with default auth mode.
- Default mode shows Auth0 only.
- Supabase login form does not appear by default.
- Admin Auth0 login works.
- Logout works.
- Work starts from latest `main`.

## What This Stage Does

- Adds an admin-only Streamlit readiness page at `pages/33_Admin_Supabase_Auth_Pilot_Readiness.py`.
- Shows current `AUTH_MODE` using the existing auth mode helper.
- Shows whether Auth0 and Supabase pilot login are enabled.
- Shows Yes/No configuration status for Supabase URL, anon key, and service role key without displaying values.
- Performs read-only readiness checks for `hm_users` counts when server-side Supabase access is available.
- Performs read-only Supabase Auth user count and email-match checks only when service-role server-side access is safely available.
- Allows an admin to check one pilot admin email and one pilot member email.
- Provides manual Supabase Dashboard checklist steps.
- Provides dual-mode pilot test steps and rollback instructions.

## What This Stage Does Not Do

- Does not remove Auth0.
- Does not disable Auth0.
- Does not change default `AUTH_MODE`.
- Does not add or change Streamlit secrets.
- Does not change Supabase Auth settings.
- Does not execute migration SQL.
- Does not add automatic user migration.
- Does not add batch provisioning.
- Does not add public signup.
- Does not create Supabase Auth users.
- Does not update `hm_users`.
- Does not change Flutter code.
- Does not change LAF, NSP, workflow, reports, or admin evaluation behavior.
- Does not touch deployment files or GitHub Actions.
- Does not expose `SUPABASE_SERVICE_ROLE_KEY` to member/browser flows.

## Admin Readiness Page Usage

1. Sign in to the Streamlit app as an admin.
2. Open `Admin Supabase Auth Pilot Readiness`.
3. Confirm the Stage 4 warning is visible.
4. Confirm the current auth mode is shown.
5. Confirm Supabase config status shows only Yes/No values.
6. Review user mapping counts.
7. Enter the pilot admin email and pilot member email.
8. Click `Check Pilot Readiness`.
9. Confirm:
   - pilot admin exists in `hm_users`
   - pilot admin role is `admin`
   - pilot admin is active
   - pilot member exists in `hm_users`
   - pilot member role is `member`
   - pilot member is active
   - Supabase Auth users are confirmed by the page or manually in Supabase Dashboard

The page is read-only. It must not be used as a migration or provisioning tool.

## Default AUTH_MODE Behavior

Default behavior remains unchanged:

```text
AUTH_MODE unset or AUTH_MODE = "auth0" => existing Auth0 login only
```

Expected default smoke result:

- Login page shows Auth0 only.
- Supabase login form does not appear.
- Existing Auth0 admin login works.
- Logout works.

## Dual Mode Test Steps

Only after the default Auth0 smoke test passes, set Streamlit secret:

```text
AUTH_MODE = "dual"
```

Then test:

1. Auth0 admin login still works.
2. Supabase admin pilot login works.
3. Supabase member pilot login works.
4. Unauthorized Supabase user is blocked.
5. Logout works.

Do not change Supabase Auth settings, redirect URLs, schema, or secrets during this stage unless separately approved.

## Rollback Steps

Fast rollback:

```text
Remove AUTH_MODE or set AUTH_MODE = "auth0"
```

Code rollback branch:

```text
backup/pre-auth-xplat-current-streamlit-20260625-clean
```

After rollback, confirm:

- Login page shows Auth0 only.
- Supabase login form does not appear.
- Existing Auth0 admin login works.
- Logout works.

## Stage 5 Recommendation

After AUTH-XPLAT-4 is reviewed and the pilot readiness page confirms the pilot admin/member mapping, proceed to Stage 5 as a separate approved sprint.

Recommended Stage 5 scope:

- Controlled pilot validation in `AUTH_MODE = "dual"`.
- Document pilot results for admin, member, unauthorized user, and logout flows.
- Decide whether Supabase Auth migration SQL should remain draft, be revised, or be executed in a separately approved migration sprint.

Stage 5 should still avoid public signup, automatic migration, and production auth behavior changes unless explicitly approved by Vineet and reviewed by Victor.
