# AUTH-XPLAT-5G Controlled Supabase Auth Operating Model & Batch Readiness Design

## 1. Purpose

AUTH-XPLAT-5G defines the controlled operating model for continuing the Supabase Auth migration after the AUTH-XPLAT-5F-A limited pilot smoke test.

This is a documentation and design step only. It does not change application behavior, database schema, Streamlit runtime code, Flutter code, secrets, provisioning state, or Auth0 configuration.

## 2. Current Decision Baseline

| Item | Status |
| --- | --- |
| AUTH-XPLAT-5E | Passed |
| AUTH-XPLAT-5F | Merged |
| AUTH-XPLAT-5F-A | Conditional Go |
| Default production mode | `AUTH_MODE = "auth0"` |
| Controlled pilot mode | `AUTH_MODE = "dual"` only during planned pilot windows |
| Auth0 fallback | Must remain available |
| Public signup | Not allowed |
| Wider rollout | Not approved in this step |

## 3. 5F-A Findings Carried Into 5G

### Passed

- Auth0 baseline worked.
- Workbench readiness passed.
- Controlled pilot mode was available.
- Supabase admin login worked.
- Supabase member login worked.
- Role and session isolation passed.
- Unauthorized-user blocking is carried forward from the earlier 5D evidence.
- Rollback to Auth0 passed.

### Conditions

| Finding | Classification | 5G decision |
| --- | --- | --- |
| Complete Secure Logout response is silent | Auth/session UX and operator confidence risk | Must be fixed before wider rollout |
| NSP second-instance values show first-instance data | Assessment data-instance issue | Track separately outside Auth-XPLAT |

The NSP second-instance issue is not an authentication migration blocker, but it must not be ignored. It should be handled in a separate assessment-flow sprint.

## 4. Scope of 5G

5G may define:

- Controlled operating rules for Auth0, dual mode, and Supabase login.
- Pilot-wave readiness gates.
- Batch-readiness design for mapped active users.
- Operator checklist for pilot windows.
- Rollback expectations.
- Go / Conditional Go / No-Go criteria for the next step.

5G must not implement runtime changes.

## 5. Non-Scope and Guardrails

This PR must not:

- Remove Auth0.
- Change default `AUTH_MODE`.
- Change Streamlit runtime code.
- Change Flutter code.
- Change database schema.
- Change RLS policies.
- Execute SQL.
- Provision users.
- Trigger invite, recovery, or reset email actions.
- Enable public signup.
- Batch migrate users.
- Migrate inactive users.
- Touch LAF, NSP, workflow, reports, recommendations, recipes, exercises, or supplements.
- Store or expose credentials.

## 6. Controlled Operating Model

### Default Mode

Production/default operation remains:

```text
AUTH_MODE = "auth0"
```

This means Auth0 remains the safe fallback and normal operating path unless a planned pilot window is active.

### Pilot Mode

Controlled pilot operation uses:

```text
AUTH_MODE = "dual"
```

Dual mode is allowed only for named pilot windows. After testing, the operator must return the app to Auth0 mode unless Vineet explicitly approves otherwise.

### Operator Rules

For each planned pilot window:

1. Confirm Auth0 admin login works before switching mode.
2. Confirm the Workbench readiness status for each pilot user.
3. Use only named pilot users.
4. Avoid inactive or unclear-role users.
5. Use fresh browser/incognito for role switching.
6. Use Complete Secure Logout between user switches.
7. Record any unexpected routing, visibility, or logout behavior.
8. Return to Auth0 mode after testing.
9. Confirm Auth0 admin login works after rollback.

## 7. Batch Readiness Design

Batch readiness means determining which existing HealthyMe users are safe candidates for controlled Supabase login access later. It does not mean automatic migration.

A user is batch-ready only when all of the following are true:

| Requirement | Rule |
| --- | --- |
| Existing HealthyMe profile | User exists in `hm_users` |
| Active status | User is active |
| Role | Role is clear and expected |
| Email | Email matches the intended login identity |
| Supabase user | Supabase Auth user exists or is planned through an approved provisioning step |
| Workbench readiness | Readiness passes without triggering email actions |
| Data visibility | Member/admin data visibility is expected |
| Rollback safety | Auth0 fallback remains available |

Users must not be considered batch-ready when:

- They are inactive.
- Their role is unclear.
- Their email identity is mismatched.
- They exist only in Supabase Auth without an approved HealthyMe mapping.
- Their data visibility is uncertain.
- Their login path requires manual workaround.

## 8. Complete Secure Logout Requirement

Before wider rollout, Complete Secure Logout must provide visible feedback.

Expected future behavior:

| Scenario | Required response |
| --- | --- |
| Logout succeeds | Show clear success confirmation and tell the operator to open a fresh login session |
| Logout cannot be confirmed | Show clear warning and tell the operator to close the browser/incognito session before switching users |
| Session switch attempted without logout | Prevent or warn clearly if a prior role/session is still active |

This is a required condition before larger pilot waves. It is not required to start this documentation-only 5G step.

## 9. Rollback Model

Rollback must remain simple:

1. Return `AUTH_MODE` to `auth0`.
2. Save configuration.
3. Restart or rerun the app if required.
4. Open a fresh browser/incognito session.
5. Confirm Supabase pilot path is not active.
6. Confirm Auth0 admin login works.
7. Record rollback result.

Rollback must not require SQL, schema changes, Auth0 removal, Flutter change, or user deletion.

## 10. No-Go Conditions

Stop pilot expansion if any of these occur:

- Auth0 baseline fails.
- Rollback to Auth0 fails.
- Member reaches an admin experience.
- Admin routes incorrectly as member.
- Member sees another member's data.
- Workbench readiness is unclear.
- Complete Secure Logout cannot be confirmed.
- A Supabase Auth-only user bypasses HealthyMe authorization.
- Any fix requires emergency SQL or runtime change during pilot testing.

## 11. Next-Step Decision Gate

The next Auth-XPLAT step may start only after:

- This 5G design is reviewed and accepted.
- 5F-A Conditional Go is recorded.
- Complete Secure Logout visibility is converted into a required implementation item before wider rollout.
- NSP second-instance carryover is tracked separately and not mixed with Auth-XPLAT scope.
- Vineet explicitly approves the next step.

Possible next step:

```text
AUTH-XPLAT-5H — Secure Logout Visibility Implementation & Pilot Hardening
```

5H should be a small runtime hardening sprint. It should not remove Auth0 or expand the rollout by itself.

## 12. 5G Final Guardrail Statement

AUTH-XPLAT-5G is design-only. It prepares the operating model and readiness gates. It does not change production authentication behavior.
