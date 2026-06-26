# AUTH-XPLAT-5E Small Pilot Wave Readiness and Go/No-Go

## 1. Purpose

AUTH-XPLAT-5E validates whether HealthyMe can safely run a very small Supabase Auth pilot wave while Auth0 remains available as fallback.

This is a controlled pilot-readiness sprint, not a production cutover.

The goal is to answer:

Can one admin and one member use Supabase Auth safely in dual mode without breaking role routing, data visibility, logout, fallback, or existing Auth0 access?

This document does not migrate users in bulk, does not create application functionality, does not remove Auth0, and does not change production authentication behavior.

## 2. Current Baseline

The current AUTH-XPLAT baseline is:

- AUTH-XPLAT-5B migration/provisioning plan is merged.
- AUTH-XPLAT-5C admin-only Supabase Auth provisioning workbench is merged.
- AUTH-XPLAT-5C-A readiness/email-action safety polish is merged.
- AUTH-XPLAT-5D controlled operational validation is merged.
- Auth0 admin path candidate-passed in controlled validation.
- Supabase admin path candidate-passed in controlled validation.
- Supabase member path candidate-passed in controlled validation.
- Workbench readiness checks passed.
- Unauthorized Supabase Auth-only user without HealthyMe `hm_users` mapping was blocked from HealthyMe access.
- Temporary unauthorized test user has been deleted or disabled.
- Auth0 remains available.
- Supabase Auth works for at least one admin and one member in controlled testing.
- `AUTH_MODE = "auth0"` should remain the default unless actively testing dual mode.
- Dual mode is used only for controlled testing.

## 3. Pilot Scope

Pilot wave size:

- Pilot Admin 1
- Pilot Member 1

Do not commit real passwords, temporary passwords, OTPs, tokens, auth IDs, service role keys, or secrets into this document or repository.

Preferred pilot user tracking table:

| Pilot Role | User Label | HealthyMe Mapping Verified | Supabase Auth Exists | Status |
| ---------- | ---------- | -------------------------- | -------------------- | ------ |
| Admin | Pilot Admin 1 | Pending | Pending | Pending |
| Member | Pilot Member 1 | Pending | Pending | Pending |

Do not include passwords in the repository.

## 4. Preconditions

Before the 5E pilot wave starts, confirm:

- Streamlit app is deployed after latest merged `main`.
- Admin can access HealthyMe using Auth0.
- Supabase Auth admin and member pilot users exist.
- Pilot admin and pilot member have active `hm_users` records.
- Pilot admin role is correctly `admin`.
- Pilot member role is correctly `member`.
- `SUPABASE_URL` is configured.
- `SUPABASE_ANON_KEY` is configured.
- `SUPABASE_SERVICE_ROLE_KEY` is configured only for admin workbench readiness/actions.
- Public signup remains disabled.
- `AUTH_MODE = "auth0"` when not testing.
- `AUTH_MODE = "dual"` only during pilot testing.
- Auth0 remains fallback.
- No SQL/schema change is part of this sprint.
- No batch provisioning is part of this sprint.

## 5. Pilot User Selection Rules

Pilot users must be:

- Low-risk test or pilot users.
- Already present in `hm_users`.
- Active in `hm_users`.
- Already present in Supabase Auth, or provisioned separately through the approved manual/admin-only process before UAT.
- Able to complete login/logout tests.
- Not using shared credentials.
- Not production-critical users unless explicitly approved.

Do not:

- Select unknown or unmapped users.
- Add users directly to `hm_users` for convenience.
- Enable public signup.
- Use batch provisioning.
- Store passwords or temporary passwords in the document.

## 6. Pilot Readiness Checklist

| Check | Pilot Admin 1 | Pilot Member 1 | Notes |
| ----- | ------------- | -------------- | ----- |
| Exists in `hm_users` | Pending | Pending | |
| `hm_users.is_active = true` | Pending | Pending | |
| Correct role | Pending | Pending | Admin/member |
| Exists in Supabase Auth | Pending | Pending | |
| Workbench readiness result reviewed | Pending | Pending | Readiness only |
| Auth0 fallback still available | Pending | Pending | |
| Supabase login credential available to tester | Pending | Pending | Do not record password |
| Logout path understood | Pending | Pending | Complete secure logout if switching identity |

## 7. Pilot UAT Test Cases

### 5E-T1 - Auth0 fallback baseline

Steps:

1. Set or confirm `AUTH_MODE = "auth0"`.
2. Login as admin using Auth0.
3. Confirm Admin Dashboard opens.
4. Logout.

Expected:

- Auth0 admin login works.
- Admin Dashboard opens.
- Logout works.

### 5E-T2 - Enable dual mode for controlled test

Steps:

1. Set `AUTH_MODE = "dual"`.
2. Open login page.
3. Confirm Auth0 and Supabase login paths are available.

Expected:

- Dual login options are available.
- No secret values are visible.
- App does not break in dual mode.

### 5E-T3 - Pilot admin Supabase login

Steps:

1. Use Complete secure logout if switching from Auth0.
2. Login through Supabase using Pilot Admin 1.
3. Confirm Admin Dashboard opens.
4. Confirm admin role is respected.
5. Logout.

Expected:

- Pilot Admin 1 reaches Admin Dashboard.
- Pilot Admin 1 does not land on Member Home.
- Logout works.

### 5E-T4 - Pilot member Supabase login

Steps:

1. Logout completely.
2. Login through Supabase using Pilot Member 1.
3. Confirm Member Home opens.
4. Confirm member role is respected.
5. Logout.

Expected:

- Pilot Member 1 reaches Member Home.
- Pilot Member 1 does not reach Admin Dashboard.
- Logout works.

### 5E-T5 - Role switching / session isolation

Steps:

1. Login as Auth0 admin.
2. Complete secure logout.
3. Login as Supabase member.
4. Complete logout.
5. Login as Supabase admin.
6. Complete logout.

Expected:

- No stale session routes member to admin.
- No stale session routes admin to member.
- Complete secure logout clears the expected session state.

### 5E-T6 - Pilot member data visibility

Steps:

1. Login as Pilot Member 1 via Supabase.
2. Open member home/dashboard.
3. Confirm expected member-level data appears.
4. Confirm no admin-only navigation/action appears.

Expected:

- Member sees only member-appropriate content.
- No admin functions are visible.

### 5E-T7 - Pilot admin data visibility

Steps:

1. Login as Pilot Admin 1 via Supabase.
2. Open Admin Dashboard.
3. Open one non-destructive admin page.
4. Confirm admin data loads.

Expected:

- Admin can access Admin Dashboard.
- Admin role routing is correct.
- No destructive action is performed.

### 5E-T8 - Workbench readiness confirmation

Steps:

1. Login as admin.
2. Open Supabase Auth Provisioning Workbench.
3. Run readiness check only for Pilot Admin 1.
4. Run readiness check only for Pilot Member 1.

Expected:

- Pilot Admin 1 shows mapped, active, role admin, Supabase Auth user exists.
- Pilot Member 1 shows mapped, active, role member, Supabase Auth user exists.
- No email action is triggered.

### 5E-T9 - Rollback to Auth0

Steps:

1. Set `AUTH_MODE = "auth0"`.
2. Open login page.
3. Confirm Supabase login path is no longer active/visible.
4. Login as admin using Auth0.

Expected:

- Auth0-only mode works.
- Admin can still access app.
- Rollback path is operational.

## 8. Result Recording Table

| Test ID | Scenario | Tester | Date | Result | Evidence / screenshot | Notes | Follow-up needed |
| ------- | -------- | ------ | ---- | ------ | --------------------- | ----- | ---------------- |
| 5E-T1 | Auth0 fallback baseline | Vineet | TBD | Pending | TBD | | |
| 5E-T2 | Dual mode available | Vineet | TBD | Pending | TBD | | |
| 5E-T3 | Pilot admin Supabase login | Vineet | TBD | Pending | TBD | | |
| 5E-T4 | Pilot member Supabase login | Vineet | TBD | Pending | TBD | | |
| 5E-T5 | Role switching / session isolation | Vineet | TBD | Pending | TBD | | |
| 5E-T6 | Pilot member data visibility | Vineet | TBD | Pending | TBD | | |
| 5E-T7 | Pilot admin data visibility | Vineet | TBD | Pending | TBD | | |
| 5E-T8 | Workbench readiness confirmation | Vineet | TBD | Pending | TBD | | |
| 5E-T9 | Rollback to Auth0 | Vineet | TBD | Pending | TBD | | |

## 9. Go Criteria

5E can be marked Go if:

- Auth0 fallback works.
- Dual mode works.
- Pilot admin can login using Supabase.
- Pilot member can login using Supabase.
- Admin reaches only admin route.
- Member reaches only member route.
- Member does not reach Admin Dashboard.
- Session switching does not leak prior identity.
- Workbench readiness confirms both pilot users.
- No email action is accidentally triggered.
- Rollback to Auth0 works.
- No SQL/schema/secrets/Auth0 settings/code changes were made in this sprint.

## 10. No-Go Criteria

5E is No-Go if any of the following occur:

- Auth0 fallback login fails.
- Dual mode does not load or hides the required pilot login paths.
- Pilot admin cannot login through Supabase.
- Pilot member cannot login through Supabase.
- Pilot admin is routed to Member Home.
- Pilot member reaches Admin Dashboard or sees admin-only controls.
- Session switching leaks a prior identity or routes to the wrong role.
- Logout does not clear the expected session state.
- Workbench readiness does not confirm mapped, active pilot users with the expected roles.
- Any email action is accidentally triggered during readiness-only checks.
- Rollback to `AUTH_MODE = "auth0"` fails.
- Any SQL/schema/secrets/Auth0 settings/code change is required to complete 5E.
- Any service-role key, password, OTP, token, or credential is exposed.

## 11. Rollback Plan

Fast rollback:

1. Stop pilot testing.
2. Set `AUTH_MODE = "auth0"`.
3. Confirm Supabase login path is no longer active/visible.
4. Login as admin through Auth0.
5. Confirm Admin Dashboard opens.
6. Record the rollback result in the 5E result table.

Code rollback:

- Use the latest known-good merged `main` if a future code issue is discovered.
- Do not use 5E to change code; this sprint is documentation-only.
- If a blocker appears, open a separate follow-up issue or sprint packet.

Operational rollback:

- Do not delete production users as part of 5E.
- Do not change Auth0 settings as part of 5E rollback.
- Do not change Supabase Auth settings unless separately approved.

## 12. Operational Notes

- Keep `AUTH_MODE = "auth0"` as the default outside active pilot testing.
- Use `AUTH_MODE = "dual"` only during the controlled pilot test window.
- Use Complete secure logout when switching identities, especially from Auth0 admin to Supabase member testing.
- Use the provisioning workbench for readiness checks only unless a separately approved action is being performed.
- Do not trigger email actions during the 5E readiness test unless explicitly approved outside this document.
- Do not store pilot credentials in GitHub, Streamlit secrets comments, screenshots, PR comments, or this document.
- Capture evidence with screenshots or notes that do not reveal credentials, tokens, or private user data.
- Keep pilot users limited to the 1 admin and 1 member scope.
- Record all test outcomes before making a Go/No-Go decision.

## 13. Decision Gate After 5E

After all 5E tests are recorded, Vineet and Victor should decide one of the following:

- Go: proceed to the next controlled Supabase Auth pilot stage with the same guardrails.
- Conditional Go: proceed only after listed follow-up fixes are completed and reviewed.
- No-Go: keep `AUTH_MODE = "auth0"`, pause Supabase Auth pilot expansion, and create a remediation sprint.

Recommended Stage 6 direction, only after 5E is Go:

- Expand pilot size cautiously.
- Keep Auth0 fallback available.
- Keep public signup disabled.
- Continue using branch and PR review for every change.
- Do not perform bulk migration until pilot evidence supports it.

## 14. Strict Guardrails

This 5E sprint does not and must not:

- Migrate users in bulk.
- Create users automatically.
- Create public signup.
- Remove Auth0.
- Change default `AUTH_MODE`.
- Change Streamlit secrets.
- Change Auth0 settings.
- Change Supabase Auth settings.
- Execute SQL.
- Change Supabase schema.
- Change RLS policies.
- Touch service-role keys, credentials, tokens, OTPs, or passwords.
- Touch Flutter repo/files.
- Touch LAF/NSP files.
- Touch workflow/report/admin evaluation files.
- Touch recommendation modules.
- Touch GitHub Actions/deployment files.
- Trigger emails or provisioning actions.
- Perform destructive admin actions.

Files changed in this sprint should remain limited to:

- `docs/AUTH_XPLAT_5E_SMALL_PILOT_WAVE_READINESS_GO_NO_GO.md`
