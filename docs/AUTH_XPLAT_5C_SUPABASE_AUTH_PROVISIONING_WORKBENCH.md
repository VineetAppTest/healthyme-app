# AUTH-XPLAT-5C Supabase Auth Provisioning Workbench

## Purpose

AUTH-XPLAT-5C adds an admin-only supervised provisioning workbench for Supabase Auth pilot operations.

The workbench is designed for exactly one email at a time. It is not a bulk migration tool and must not be used for batch provisioning.

## Scope

The page added in this stage is:

```text
pages/34_Admin_Supabase_Auth_Provisioning_Workbench.py
```

It supports:

- admin-only access
- one email input
- readiness / dry-run check
- `hm_users` mapping lookup
- Supabase Auth user existence lookup when service-role access is available
- recommended next action
- optional one-user Supabase Auth invite after explicit confirmation
- optional one-user recovery/reset email after explicit confirmation
- rollback and safety guidance

## Guardrails

This stage does not:

- batch provision users
- upload CSV files
- loop through all users for actions
- execute SQL
- alter Supabase schema
- update `hm_users`
- delete users
- change user roles
- change passwords directly
- display secret values
- change `AUTH_MODE`
- remove Auth0
- enable public signup
- touch Flutter
- change LAF, NSP, workflow, reports, or admin evaluation behavior
- touch deployment files or GitHub Actions

The page may read:

- one `hm_users` mapping by email
- Supabase Auth user list for existence matching, if service-role access is available

The page may perform only these one-user actions after confirmation:

- send Supabase Auth invite for one missing active HealthyMe user
- send Supabase recovery/reset email for one existing Supabase Auth user

## Admin Flow

1. Admin opens the Supabase Auth Provisioning Workbench.
2. Page restores an existing app session where available.
3. Page blocks logged-out users.
4. Page blocks non-admin users.
5. Admin enters exactly one email.
6. Admin selects an action. Default action is `Dry-run only`.
7. Admin clicks `Check Readiness / Dry Run`.
8. Page shows mapping status and recommended action.
9. If invite or recovery/reset is selected, action executes only after explicit confirmation.

## Dry-run Behavior

Dry-run is the default.

Dry-run performs no mutation. It checks and displays:

- normalized email checked
- whether the email exists in `hm_users`
- role in `hm_users`
- active status in `hm_users`
- whether the email exists in Supabase Auth, if safely available
- recommended next action

If service-role access is missing, the page may still attempt available app lookup for HealthyMe mapping, but invite/recovery actions remain blocked.

## Invite Behavior

Invite action is allowed only when all conditions are true:

- active `hm_users` record exists
- role is `admin` or `member`
- Supabase Auth user is confirmed missing
- service-role server-side client is available
- admin checks the confirmation checkbox
- admin types `PROVISION` exactly

The page prefers:

```python
client.auth.admin.invite_user_by_email(email)
```

If the installed Supabase client does not expose that method, the page shows a controlled manual-dashboard message and does not crash.

## Recovery / Reset Behavior

Recovery/reset action is allowed only when all conditions are true:

- active `hm_users` record exists
- role is `admin` or `member`
- Supabase Auth user is confirmed existing
- service-role server-side client is available
- admin checks the confirmation checkbox
- admin types `PROVISION` exactly

The page prefers:

```python
client.auth.reset_password_for_email(email)
```

If the installed Supabase client does not expose that method, the page shows a controlled manual-dashboard message and does not crash.

## Rollback

Fast auth-mode rollback:

```text
Remove AUTH_MODE or set AUTH_MODE = "auth0"
```

Code rollback branch:

```text
backup/pre-auth-xplat-current-streamlit-20260625-clean
```

If an invite or recovery/reset email is sent in error, review the user manually in Supabase Dashboard > Authentication > Users. This stage does not include delete, disable, role change, password edit, or schema rollback functions.

## Acceptance Criteria

- Admin-only provisioning workbench is added.
- Direct page access works for authenticated admin.
- Non-admin is blocked.
- Logged-out user is blocked.
- Email readiness/dry-run works.
- Page shows `hm_users` mapping status.
- Page shows Supabase Auth existence status when service-role access is available.
- Dry-run performs no mutation.
- Invite action requires explicit confirmation.
- Recovery/reset action requires explicit confirmation.
- No batch provisioning is added.
- No SQL is executed.
- Supabase schema is unchanged.
- Streamlit secrets are unchanged.
- Auth0 settings are unchanged.
- Auth0 is not removed.
- Flutter is untouched.
- LAF/NSP/workflow/report/admin evaluation files are untouched.
- Deployment and GitHub Actions files are untouched.
- Secret values are never displayed.

## Next Stage Recommendation

After Stage 5C is reviewed and tested, the next stage should be a controlled operational validation sprint.

Recommended next stage:

- test one admin invite path if needed
- test one member invite path if needed
- test recovery/reset for one existing Supabase Auth user
- record results in documentation
- decide whether provisioning should remain manual, move to a more formal admin workflow, or stay limited to Supabase Dashboard operations

Any future expansion beyond one-email-at-a-time provisioning should require explicit approval from Vineet and Victor.
