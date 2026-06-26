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
- readiness check with no email action
- `hm_users` mapping lookup
- Supabase Auth user existence lookup when service-role access is available
- recommended next action
- optional one-user Supabase Auth invite after explicit confirmation
- optional one-user recovery/reset email after explicit confirmation
- rollback and safety guidance

## 5C-A UX Safety Polish

AUTH-XPLAT-5C-A separates readiness checking from real email actions.

The workbench now has two clear stages:

1. **Readiness Check Only**
   - Admin enters one email.
   - Admin clicks `Run readiness check — no email will be sent`.
   - This stage normalizes the email, checks HealthyMe mapping, checks Supabase Auth existence where safely available, shows the recommended next step, and stores the readiness result.
   - This button never sends a Supabase invite or recovery/reset email.

2. **Optional email action**
   - This section appears only after a readiness check has completed.
   - The default option is `No email action`.
   - Invite and recovery/reset actions remain one-user only and require checkbox confirmation plus typing `PROVISION` exactly.
   - Email action buttons are explicit: `Send one Supabase invite email` or `Send one Supabase recovery/reset email`.

A successful invite or recovery/reset API call means **email request submitted** to Supabase. It does not mean the email was delivered or received.

Email delivery may depend on the Supabase/email provider, spam filtering, and rate limits. Admins should verify actual receipt during supervised pilot testing.

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
5. Admin enters exactly one email in Stage 1.
6. Admin clicks `Run readiness check — no email will be sent`.
7. Page shows mapping status, Supabase Auth status where available, and recommended next action.
8. Stage 2 appears only after readiness is checked.
9. Admin keeps `No email action` selected unless a supervised invite or recovery/reset email is intentionally needed.
10. If invite or recovery/reset is selected, action executes only after explicit confirmation.

## Readiness Behavior

Readiness checking performs no mutation. It checks and displays:

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

A successful API call means the Supabase email request was submitted for this one user. It does not guarantee inbox delivery.

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

A successful API call means the Supabase email request was submitted for this one user. It does not guarantee inbox delivery.

## Rollback

Fast auth-mode rollback:

```text
Remove AUTH_MODE or set AUTH_MODE = "auth0"
```

Code rollback branch:

```text
backup/pre-auth-xplat-current-streamlit-20260625-clean
```

If an invite or recovery/reset email is requested in error, review the user manually in Supabase Dashboard > Authentication > Users. This stage does not include delete, disable, role change, password edit, or schema rollback functions.

## Acceptance Criteria

- Admin-only provisioning workbench is added.
- Direct page access works for authenticated admin.
- Non-admin is blocked.
- Logged-out user is blocked.
- Readiness check works and never sends email.
- Optional email action appears only after readiness has completed.
- Optional email action defaults to `No email action`.
- Page shows `hm_users` mapping status.
- Page shows Supabase Auth existence status when service-role access is available.
- Invite action requires explicit confirmation.
- Recovery/reset action requires explicit confirmation.
- Successful API call copy says email request submitted, not email delivered.
- Delivery caveat is visible.
- No batch provisioning is added.
- No SQL is executed.
- Supabase schema is unchanged.
- Streamlit secrets are unchanged.
- Auth0 settings are unchanged.
- Auth0 is not removed.
- Public signup is not enabled.
- Flutter is untouched.
- LAF/NSP/workflow/report/admin evaluation files are untouched.
- Deployment and GitHub Actions files are untouched.
- Secret values are never displayed.

## Next Stage Recommendation

After Stage 5C-A is reviewed and tested, the next stage should be a controlled operational validation sprint.

Recommended next stage:

- test one admin readiness-only check
- test one member readiness-only check
- test one supervised invite path only if needed
- test one supervised recovery/reset path only if needed
- confirm whether actual email receipt succeeds or is affected by provider/spam/rate limits
- record results in documentation
- decide whether provisioning should remain manual, move to a more formal admin workflow, or stay limited to Supabase Dashboard operations

Any future expansion beyond one-email-at-a-time provisioning should require explicit approval from Vineet and Victor.
