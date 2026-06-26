# AUTH-XPLAT-5B Supabase Auth User Provisioning & Migration Plan

## Purpose

AUTH-XPLAT-5B defines the controlled plan for moving HealthyMe users from Auth0-only access toward Supabase Auth, without changing production auth behavior yet.

This is a planning and governance stage. It does not create users, execute SQL, change Streamlit secrets, change Auth0 settings, or change Supabase schema.

## Current Validated Baseline

The following pilot flows have been validated in controlled `AUTH_MODE = "dual"` testing:

- Auth0 admin login works.
- Supabase admin login works.
- Supabase member login works.
- Logout works after Supabase login.
- Dual-mode routing no longer sends Supabase member back to an active Auth0 admin session after AUTH-XPLAT-5A.

The pilot used existing HealthyMe admin/member records that already existed in both `hm_users` and Supabase Auth. No separate fake pilot users were required.

## Source of Truth Rules

### Authentication Identity

Supabase Auth is the target authentication provider for Flutter and the eventual Streamlit migration.

Supabase Auth confirms who the user is through email/password or future supported Supabase Auth methods.

### HealthyMe Authorization

`hm_users` remains the HealthyMe authorization source of truth during migration.

A Supabase Auth user must still map to an active `hm_users.email` record.

HealthyMe role routing continues to come from `hm_users.role`, not directly from Supabase Auth metadata.

### App User ID

The existing `hm_users.id` remains the business/app user ID for current Streamlit app workflows and reporting.

A future approved schema migration may add or backfill `hm_users.supabase_auth_id` for stronger identity linkage, but this stage does not execute that migration.

## User Inventory Categories

Each HealthyMe user should fall into one of these categories before broad migration:

| Category | Meaning | Action |
|---|---|---|
| A | Active `hm_users` user and matching Supabase Auth user exists | Ready for dual-mode pilot / migration wave |
| B | Active `hm_users` user exists, but Supabase Auth user missing | Needs Supabase Auth provisioning |
| C | Supabase Auth user exists, but no active `hm_users` record | Should remain blocked unless intentionally mapped |
| D | Inactive `hm_users` user | Do not provision unless reactivated by admin |
| E | Duplicate/ambiguous email | Resolve manually before provisioning |

## Provisioning Principles

1. No public signup.
2. No automatic broad migration without review.
3. No password migration from Auth0.
4. No exposure of service-role key outside server-side admin logic.
5. No member-side user creation.
6. No role assignment from Supabase Auth alone.
7. Existing `hm_users` role and active status must govern access.
8. Every provisioning wave must be reversible operationally by disabling/deleting Supabase Auth users or switching `AUTH_MODE` back to `auth0`.

## Approved Provisioning Options

### Option 1 — Supabase Dashboard Manual Provisioning

Best for first few pilot users.

Steps:

1. Open Supabase Dashboard.
2. Go to Authentication > Users.
3. Add user or invite user by email.
4. Ensure the email exactly matches `hm_users.email` in lowercase/trimmed form.
5. Use a reset-password or invite flow where practical.
6. Test login through HealthyMe dual mode.

Pros:

- Lowest code risk.
- Easy to supervise manually.
- Good for first pilot/admin/member tests.

Cons:

- Not scalable for all users.
- Manual errors possible.

### Option 2 — Admin-Only One-User Provisioning Page

Best next technical step after this plan is accepted.

A new admin-only Streamlit page can provision or invite one Supabase Auth user at a time after checking `hm_users` mapping.

Required controls:

- Admin-only access.
- Server-side service-role use only.
- No secret display.
- One email at a time.
- Must check active `hm_users` record first.
- Must display role and active status before provisioning.
- Must refuse inactive or unmapped users.
- Must log/result-message every action clearly.
- Must not change `hm_users` role.
- Must not alter Supabase schema.

Recommended first implementation mode:

- Dry-run first.
- Then invite/reset-link mode.
- Avoid temporary password bulk provisioning until explicitly approved.

### Option 3 — Batch Provisioning Script/Page

Best only after one-user provisioning is tested.

Required controls:

- Preview list before execution.
- CSV/downloadable report of intended actions.
- Explicit admin confirmation.
- Skip inactive users.
- Skip users already in Supabase Auth.
- Skip duplicate or ambiguous emails.
- No public signup.
- No schema change in the same sprint.

This option is not approved for immediate execution in 5B.

## Recommended Migration Waves

### Wave 0 — Already Validated Pilot

Status: Passed.

Users:

- Existing admin user already mapped in `hm_users` and Supabase Auth.
- Existing member user already mapped in `hm_users` and Supabase Auth.

Purpose:

- Validate dual-mode login behavior.
- Validate routing.
- Validate logout.

### Wave 1 — Internal Admin + One Member

Purpose:

- Validate controlled provisioning and reset/invite experience.

Users:

- One admin.
- One member.

Entry criteria:

- `AUTH_MODE = "dual"` works.
- Readiness page opens.
- User exists in `hm_users` and is active.
- Email is confirmed and exact.
- Supabase Auth user does not already exist, or existing user is verified.

Exit criteria:

- Auth0 still works.
- Supabase admin login works.
- Supabase member login works.
- Wrong/unmapped Supabase user remains blocked.
- Logout works.

### Wave 2 — Small Known Member Set

Purpose:

- Validate member communication and reset/invite process with a small set.

Recommended size:

- 3 to 5 users.

Exit criteria:

- No role-routing confusion.
- No member data visibility issues.
- No login support blockers.

### Wave 3 — All Active Members

Purpose:

- Broader migration only after Wave 1 and Wave 2 pass.

Prerequisites:

- User communication approved.
- Rollback path confirmed.
- Admin support path ready.
- Read-only migration report reviewed.

## Required Readiness Checks Before Provisioning

For every email:

- Email is non-empty.
- Email is normalized to lowercase and trimmed.
- Active `hm_users` record exists.
- `hm_users.role` is known and valid.
- No duplicate active `hm_users` record for the same email.
- Supabase Auth user existence checked.
- Existing Supabase Auth user is not accidentally linked to the wrong email.
- User status and role are reviewed before sending invite/reset.

## Unauthorized User Test

The controlled migration is not complete until unauthorized-user blocking is tested.

Expected result:

- A Supabase Auth user who is not active in `hm_users` must not access HealthyMe.
- The app should show an authorization failure and not route to Admin Dashboard or Member Home.

Recommended safe method:

1. Create a temporary Supabase Auth test user with an email not present in `hm_users`.
2. Attempt login in `AUTH_MODE = "dual"`.
3. Confirm access is blocked.
4. Delete or disable that test Supabase Auth user after testing.

This test should be done manually or through a later approved admin-only provisioning/test page.

## Password and Invite Policy

Do not migrate passwords from Auth0.

Recommended approach:

- Use Supabase invite or password reset flow where possible.
- If a temporary password is used for controlled internal testing, force the user to reset it operationally.
- Do not email plaintext passwords broadly.
- Do not store Supabase Auth passwords in `hm_users`.

## Communication Plan

Before broader member migration, prepare a short user-facing note covering:

- Login method is changing.
- Email remains the same.
- They may receive a password reset/invite link.
- Existing health data remains in HealthyMe.
- They should not create a new account with a different email.
- Support contact/process if login fails.

## Rollback Plan

Fast rollback:

```text
AUTH_MODE = "auth0"
```

or remove `AUTH_MODE`.

This keeps Streamlit on Auth0-only behavior.

Operational rollback for a provisioned Supabase Auth user:

- Disable/delete the Supabase Auth user if needed.
- Leave `hm_users` unchanged unless a separate admin decision is made.
- Do not run schema rollback unless a later schema migration has actually been executed.

Code rollback anchor:

```text
backup/pre-auth-xplat-current-streamlit-20260625-clean
```

## What AUTH-XPLAT-5B Does Not Do

- Does not execute SQL.
- Does not create Supabase Auth users.
- Does not send invites.
- Does not change `AUTH_MODE`.
- Does not change Streamlit secrets.
- Does not change Supabase schema.
- Does not change Auth0 settings.
- Does not remove Auth0.
- Does not enable public signup.
- Does not change Flutter.
- Does not change LAF, NSP, workflow, reports, or admin evaluation.
- Does not touch deployment files or GitHub Actions.

## Recommended AUTH-XPLAT-5C Scope

Create an admin-only Supabase Auth provisioning workbench with these modes:

1. Readiness check by email.
2. Dry-run result.
3. Optional one-user invite/reset provisioning after explicit confirmation.
4. Unauthorized-user test checklist.

AUTH-XPLAT-5C should still avoid batch provisioning and schema migration unless separately approved.

## Acceptance Criteria for 5B

- Migration/provisioning plan documented.
- Source-of-truth rules documented.
- User categories documented.
- Provisioning options documented.
- Migration waves documented.
- Unauthorized-user test documented.
- Rollback documented.
- Stage 5C recommendation documented.
- No runtime behavior changed.
- No SQL/schema/user creation/secrets changes.
