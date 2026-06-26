# AUTH-XPLAT-5F — Limited Pilot Expansion Plan

## Purpose

AUTH-XPLAT-5F defines the next controlled step after the successful AUTH-XPLAT-5E pilot. The goal is to expand Supabase Auth testing from one admin and one member to a small named pilot group while keeping Auth0 as the safe fallback.

This document is planning-only. It does not change code, database structure, deployment settings, Auth0 setup, Flutter behavior, or user records.

## Baseline

AUTH-XPLAT-5E has passed.

5E validated:

- Auth0 baseline login works.
- Dual mode works during controlled testing.
- Supabase admin login works.
- Supabase member login works.
- Admin/member session isolation works.
- Member data visibility is correct.
- Admin data visibility is correct.
- Workbench readiness check works.
- Rollback to Auth0 works.

Default operating mode remains Auth0. Dual mode is only for controlled pilot windows.

## Pilot Scope

Suggested 5F pilot size:

- 1 to 2 admins
- 3 to 5 members

Rules:

- Named users only.
- No public signup.
- No broad migration.
- No inactive users.
- No users with unclear role mapping.
- No users without matching HealthyMe user records.
- Auth0 remains available as fallback.

## Preconditions

Before 5F testing starts:

1. 5E must be passed.
2. Pilot users must be explicitly selected.
3. Each pilot user must pass readiness review.
4. Role mapping must be clear.
5. Expected data visibility must be known.
6. Rollback process must be understood.
7. Evidence capture must be ready.

## Readiness Review

For every pilot user, confirm:

- HealthyMe user record exists.
- User is active.
- Email match is correct.
- Role is correct.
- Supabase Auth account is available or approved for controlled setup.
- User is safe to include in the pilot.

Readiness review must be separate from any email or account action.

## 5F UAT Checklist

| Test ID | Test Name | User Email | Role | Expected Result | Actual Result | Pass/Fail | Evidence | Issue | Retest |
|---|---|---|---|---|---|---|---|---|---|
| 5F-T1 | Auth0 baseline before pilot |  | Admin | Auth0 login works |  |  |  |  |  |
| 5F-T2 | Controlled dual mode window |  | Admin | Dual mode is available |  |  |  |  |  |
| 5F-T3 | Pilot admin 1 Supabase login |  | Admin | Admin login works |  |  |  |  |  |
| 5F-T4 | Pilot admin 2 Supabase login, if selected |  | Admin | Admin login works |  |  |  |  |  |
| 5F-T5 | Pilot member 1 Supabase login |  | Member | Member login works |  |  |  |  |  |
| 5F-T6 | Pilot member 2 Supabase login |  | Member | Member login works |  |  |  |  |  |
| 5F-T7 | Pilot member 3 Supabase login |  | Member | Member login works |  |  |  |  |  |
| 5F-T8 | Additional members, if selected |  | Member | Login works |  |  |  |  |  |
| 5F-T9 | Admin/member isolation |  | Mixed | No role crossover |  |  |  |  |  |
| 5F-T10 | Member data visibility |  | Member | Member sees own data only |  |  |  |  |  |
| 5F-T11 | Admin data visibility |  | Admin | Admin sees expected data |  |  |  |  |  |
| 5F-T12 | Workbench readiness captured |  | Mixed | Readiness result recorded |  |  |  |  |  |
| 5F-T13 | Logout clarity |  | Mixed | Logout works clearly |  |  |  |  |  |
| 5F-T14 | Rollback to Auth0 |  | Admin | Rollback works |  |  |  |  |  |
| 5F-T15 | Auth0 after rollback |  | Admin | Auth0 login still works |  |  |  |  |  |

## Pilot User Evidence Table

| Pilot Wave | User Name | Email | Role | Active? | Supabase Auth Exists? | Readiness Passed? | Login Tested? | Data Visibility Tested? | Logout Tested? | Result | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 5F |  |  |  |  |  |  |  |  |  |  |  |
| 5F |  |  |  |  |  |  |  |  |  |  |  |
| 5F |  |  |  |  |  |  |  |  |  |  |  |
| 5F |  |  |  |  |  |  |  |  |  |  |  |
| 5F |  |  |  |  |  |  |  |  |  |  |  |

## Rollback Plan

Rollback is by returning the app to Auth0-only operating mode, then confirming Auth0 admin login still works in a fresh browser session. Rollback must not require SQL, schema, Flutter, Auth0 configuration, or code deployment changes.

## Go Criteria

5F can be marked Go only if:

- All selected pilot users pass readiness.
- All selected pilot users can login.
- Admin/member isolation works.
- Member data visibility is correct.
- Admin data visibility is correct.
- Logout works.
- Rollback to Auth0 works.
- No unauthorized access occurs.
- No data visibility issue occurs.

## Conditional Go Criteria

Conditional Go is allowed only for minor UX issues where there is no login failure, no role issue, no data visibility issue, and the workaround is documented.

## No-Go Criteria

5F is No-Go if there is unauthorized access, incorrect data visibility, admin/member role crossover, fallback failure, rollback failure, unintended email action, inactive user access, or unclear user mapping.

## Guardrails

- Auth0 remains fallback.
- Do not remove Auth0.
- Do not make Supabase the only path.
- Do not enable public signup.
- Do not batch migrate users yet.
- Do not change database schema.
- Do not change RLS policies.
- Do not change Streamlit runtime code.
- Do not change Flutter code.
- Do not touch LAF, NSP, workflow, reports, or recommendations.
- Do not record passwords.
- Do not leave dual mode active after the pilot unless explicitly approved.

## Decision Gate Before 5G

AUTH-XPLAT-5G may start only after:

- 5F pilot group passes.
- Evidence table is complete.
- Rollback has been tested.
- No open No-Go issue exists.
- Vineet explicitly approves moving to 5G.

Possible 5G direction: controlled Supabase Auth operating model and batch-readiness design.

Do not implement 5G in this PR.
