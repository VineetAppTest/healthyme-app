# AUTH-XPLAT-5D Controlled Operational Validation

## Purpose

AUTH-XPLAT-5D is the controlled validation protocol for HealthyMe Supabase Auth migration readiness.

This sprint is documentation and UAT governance only. It does not add code, change auth behavior, create users, send emails, run SQL, or change schema.

## Current Baseline

The following items are already completed or candidate-passed from prior UAT:

- AUTH-XPLAT-5B provisioning and migration plan is merged.
- AUTH-XPLAT-5C admin-only provisioning workbench is merged.
- AUTH-XPLAT-5C-A UX safety polish is merged.
- Auth0 admin login path passed.
- Supabase admin login path passed.
- Supabase member login path passed.
- Logout after Supabase login passed.
- Supabase member no longer redirects to admin after the dual-session priority fix.
- Workbench readiness check passed for admin.
- Workbench readiness check passed for member.
- Admin and member test users are already present in Supabase Auth.
- Readiness and real email actions are separated.

## Preconditions

Before 5D testing:

- Streamlit app is deployed after the latest merge.
- Admin can access the Streamlit app.
- `AUTH_MODE = "dual"` is used only during controlled testing.
- `SUPABASE_URL` is configured.
- `SUPABASE_ANON_KEY` is configured for Supabase login.
- `SUPABASE_SERVICE_ROLE_KEY` is configured for admin workbench checks/actions.
- Auth0 remains available.
- Public signup remains disabled.
- No SQL or schema changes are included in this sprint.

## Test Cases

### 5D-T1 Auth0 Admin Login

Steps:

1. Keep `AUTH_MODE = "dual"` for controlled testing.
2. Open the login page.
3. Log in using Auth0 admin.
4. Confirm Admin Dashboard opens.
5. Log out.

Expected result:

- Admin Dashboard opens.
- Logout works.

### 5D-T2 Supabase Admin Login

Steps:

1. Use Complete secure logout if switching from Auth0.
2. Log in using Supabase admin credentials.
3. Confirm Admin Dashboard opens.
4. Log out.

Expected result:

- Admin Dashboard opens.
- Logout works.

### 5D-T3 Supabase Member Login

Steps:

1. Log out.
2. Log in using Supabase member credentials.
3. Confirm Member Home opens.
4. Log out.

Expected result:

- Member Home opens.
- Member does not reach Admin Dashboard.
- Logout works.

### 5D-T4 Workbench Readiness: Existing Admin

Steps:

1. Log in as admin.
2. Open the Supabase Auth Provisioning Workbench.
3. Enter the existing admin email.
4. Click `Run readiness check — no email will be sent`.

Expected result:

- HealthyMe mapping: yes.
- Role: admin.
- Active: yes.
- Supabase Auth user: yes.
- Recommended next step: Already provisioned.

### 5D-T5 Workbench Readiness: Existing Member

Steps:

1. Enter the existing member email.
2. Click `Run readiness check — no email will be sent`.

Expected result:

- HealthyMe mapping: yes.
- Role: member.
- Active: yes.
- Supabase Auth user: yes.
- Recommended next step: Already provisioned.

### 5D-T6 Supabase Auth User Without HealthyMe Mapping Is Blocked

Purpose:

Validate that Supabase Auth identity alone does not grant HealthyMe app access.

Safe method:

1. Use a temporary Supabase Auth test user whose email is not present as an active user in `hm_users`.
2. Attempt Supabase login from the HealthyMe login page.
3. Do not add this email to `hm_users`.
4. Delete or disable the temporary test user after validation if no longer needed.

Expected result:

- User is blocked.
- User does not reach Admin Dashboard.
- User does not reach Member Home.
- The app shows a controlled authorization failure message.

### 5D-T7 Optional Recovery/Reset Email Path

Only run this if needed. Do not run by default.

Expected result if run:

- Readiness is checked first.
- Stage 2 appears only after readiness.
- The app says Supabase email request submitted.
- Inbox delivery is not assumed or guaranteed.

### 5D-T8 Optional Invite Email Path

Only run this if a safe missing-user pilot case exists. Do not run by default.

Expected result if run:

- Readiness is checked first.
- Eligible missing Supabase Auth user is confirmed.
- The app says Supabase email request submitted.
- Inbox delivery is not assumed or guaranteed.

## Result Recording Table

| Test ID | Scenario | Tester | Date | Result | Evidence / screenshot | Notes | Follow-up needed |
|---|---|---|---|---|---|---|---|
| 5D-T1 | Auth0 admin login | Vineet | TBD | Candidate passed / needs 5D confirmation | TBD | Prior UAT passed | TBD |
| 5D-T2 | Supabase admin login | Vineet | TBD | Candidate passed / needs 5D confirmation | TBD | Prior UAT passed | TBD |
| 5D-T3 | Supabase member login | Vineet | TBD | Candidate passed / needs 5D confirmation | TBD | Prior UAT passed | TBD |
| 5D-T4 | Workbench admin readiness | Vineet | TBD | Candidate passed / needs 5D confirmation | TBD | Prior UAT passed | TBD |
| 5D-T5 | Workbench member readiness | Vineet | TBD | Candidate passed / needs 5D confirmation | TBD | Prior UAT passed | TBD |
| 5D-T6 | Supabase Auth user without HealthyMe mapping blocked | Vineet | TBD | Pending | TBD | Required before migration wave | TBD |
| 5D-T7 | Recovery/reset email path | Vineet | TBD | Optional / not run by default | TBD | Run only if needed | TBD |
| 5D-T8 | Invite email path | Vineet | TBD | Optional / not run by default | TBD | Run only if safe case exists | TBD |

## Pass Criteria

5D can pass when:

- Auth0 admin login still works.
- Supabase admin login works.
- Supabase member login works.
- Workbench readiness works for admin.
- Workbench readiness works for member.
- A Supabase Auth user without HealthyMe mapping is blocked.
- No accidental invite or recovery email is sent during readiness.
- No SQL, schema, secrets, Auth0 settings, or public signup changes are made.
- Rollback to Auth0-only mode remains available.

## Fail Criteria

5D fails if:

- Auth0 admin login breaks.
- Supabase admin/member routing breaks.
- Supabase member reaches Admin Dashboard.
- A Supabase Auth user without HealthyMe mapping receives app access.
- Readiness check sends an email.
- Workbench exposes secret values.
- Any SQL, schema, or auth configuration is changed in this sprint.
- Batch provisioning is introduced.

## Rollback

Fast mode rollback:

```text
AUTH_MODE = "auth0"
```

or remove `AUTH_MODE`.

Operational cleanup:

- Delete or disable the temporary unmapped Supabase Auth test user if created.
- Do not alter `hm_users` unless separately approved.

Code rollback anchor:

```text
backup/pre-auth-xplat-current-streamlit-20260625-clean
```

## Decision Gate After 5D

After 5D, choose one:

- Option A: Keep Auth0 as production default and use Supabase dual mode only for controlled testing.
- Option B: Proceed to AUTH-XPLAT-5E small pilot wave with one admin and one member.
- Option C: Pause migration and keep provisioning manual through Supabase Dashboard/workbench.
- Option D: Return to Flutter member work and defer Streamlit auth migration.

Recommended default if 5D passes:

Proceed only to a small pilot wave, not bulk migration.

## Guardrails

This PR is documentation only.

- No code files.
- No SQL.
- No Supabase schema changes.
- No Streamlit secrets changes.
- No Auth0 settings changes.
- No Auth0 removal.
- No public signup.
- No provisioning actions.
- No emails triggered.
- No Flutter changes.
- No LAF, NSP, workflow, report, or admin evaluation changes.
- No deployment or GitHub Actions changes.
