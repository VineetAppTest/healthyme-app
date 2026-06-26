# AUTH-XPLAT-5F-A Limited Pilot Execution Log & Operator Checklist

## 1. Purpose

AUTH-XPLAT-5F-A captures actual execution evidence for the AUTH-XPLAT-5F limited Supabase Auth pilot.

This document is an operator checklist and evidence log. It does not change application behavior, provision users, send emails, alter authentication settings, or permanently switch production to Supabase Auth. It is required before AUTH-XPLAT-5G can start.

## 2. Current Baseline

| Item | Status |
| --- | --- |
| AUTH-XPLAT-5E | Passed |
| AUTH-XPLAT-5F | Merged |
| AUTH-XPLAT-5F-A | Execution evidence sprint |
| Default mode | AUTH_MODE = "auth0" |
| Controlled pilot mode | AUTH_MODE = "dual" |

## 3. Pilot Execution Rule

- Run the pilot only inside a planned testing window.
- Return AUTH_MODE to "auth0" after testing unless Vineet explicitly approves keeping dual mode active.
- Use Complete secure logout between role and session switches.
- Stop testing immediately if any No-Go issue appears.
- Do not treat this pilot as AUTH-XPLAT-5G.

## 4. Pilot User Selection Table

| Pilot user number | Name | Email | Role | Existing hm_users record confirmed? | Active user? | Supabase Auth user exists? | Workbench readiness passed? | Included in pilot? | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Admin 1 |  |  | admin |  |  |  |  |  |  |
| Admin 2 optional |  |  | admin |  |  |  |  |  |  |
| Member 1 |  |  | member |  |  |  |  |  |  |
| Member 2 |  |  | member |  |  |  |  |  |  |
| Member 3 |  |  | member |  |  |  |  |  |  |
| Member 4 optional |  |  | member |  |  |  |  |  |  |
| Member 5 optional |  |  | member |  |  |  |  |  |  |

## 5. Pre-Window Checklist

- [ ] 5F plan reviewed.
- [ ] Pilot users selected.
- [ ] Auth0 admin login tested.
- [ ] Workbench page accessible.
- [ ] Rollback owner confirmed.
- [ ] Evidence capture ready.
- [ ] No production-critical user selected without approval.
- [ ] No inactive user selected.
- [ ] No unclear role mapping.
- [ ] Current AUTH_MODE confirmed as auth0 before testing.

## 6. Workbench Readiness Log

Readiness checks must not send email. Do not trigger invite, recovery, password reset, or provisioning actions from this log.

| User email | Role | hm_users record exists | hm_users active | Role correct | Supabase Auth user exists | Readiness result | Email action triggered? | Evidence note | Pass/Fail |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  | admin |  |  |  |  |  | No |  |  |
|  | admin |  |  |  |  |  | No |  |  |
|  | member |  |  |  |  |  | No |  |  |
|  | member |  |  |  |  |  | No |  |  |
|  | member |  |  |  |  |  | No |  |  |
|  | member |  |  |  |  |  | No |  |  |
|  | member |  |  |  |  |  | No |  |  |

## 7. Controlled Pilot Window Steps

### Before Testing

1. Confirm current mode is auth0.
2. Login with Auth0 admin.
3. Confirm admin dashboard opens.
4. Complete logout.

### During Testing

1. Change AUTH_MODE to dual.
2. Open fresh browser/incognito.
3. Test selected admin users.
4. Complete logout.
5. Test selected member users.
6. Complete logout between each user.
7. Test role/session isolation.
8. Confirm data visibility.
9. Record evidence.

### After Testing

1. Change AUTH_MODE back to auth0.
2. Save/reboot/rerun app if required.
3. Open fresh browser/incognito.
4. Confirm Supabase path is not active.
5. Login through Auth0 admin.
6. Record rollback result.

## 8. UAT Execution Table

| Test ID | Test name | User email | Expected result | Actual result | Pass/Fail | Evidence note | Issue ID | Retest result |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 5F-A-T1 | Auth0 baseline before pilot |  | Auth0 admin login works and dashboard opens before dual mode. |  |  |  |  |  |
| 5F-A-T2 | Switch to dual mode during planned pilot window |  | AUTH_MODE is set to dual only for the planned pilot window. |  |  |  |  |  |
| 5F-A-T3 | Admin 1 Supabase login |  | Selected Admin 1 can log in through Supabase pilot path and route correctly. |  |  |  |  |  |
| 5F-A-T4 | Admin 2 Supabase login, if selected |  | Selected Admin 2 can log in through Supabase pilot path and route correctly. |  |  |  |  |  |
| 5F-A-T5 | Member 1 Supabase login |  | Selected Member 1 can log in through Supabase pilot path and route correctly. |  |  |  |  |  |
| 5F-A-T6 | Member 2 Supabase login |  | Selected Member 2 can log in through Supabase pilot path and route correctly. |  |  |  |  |  |
| 5F-A-T7 | Member 3 Supabase login |  | Selected Member 3 can log in through Supabase pilot path and route correctly. |  |  |  |  |  |
| 5F-A-T8 | Member 4/5 Supabase login, if selected |  | Optional selected Member 4/5 can log in through Supabase pilot path and route correctly. |  |  |  |  |  |
| 5F-A-T9 | Admin/member role isolation |  | Admin and member users route to the correct role experience without cross-session leakage. |  |  |  |  |  |
| 5F-A-T10 | Member sees only own data |  | Member access is limited to that member's expected data. |  |  |  |  |  |
| 5F-A-T11 | Admin sees expected admin data |  | Admin access shows expected admin data and controls. |  |  |  |  |  |
| 5F-A-T12 | Complete secure logout confirmed |  | Complete secure logout clears the active testing session before switching users. |  |  |  |  |  |
| 5F-A-T13 | Unauthorized Auth-only user remains blocked |  | User with Auth-only access but no approved hm_users mapping remains blocked. |  |  |  |  |  |
| 5F-A-T14 | Rollback to Auth0 |  | AUTH_MODE is returned to auth0 and Supabase pilot path is not active. |  |  |  |  |  |
| 5F-A-T15 | Auth0 login works after rollback |  | Auth0 admin login works after rollback. |  |  |  |  |  |

## 9. Rollback Execution Checklist

- [ ] Set AUTH_MODE back to auth0.
- [ ] Save secrets/config.
- [ ] Reboot/rerun Streamlit app if needed.
- [ ] Open fresh browser/incognito.
- [ ] Confirm Supabase path not active.
- [ ] Login with Auth0 admin.
- [ ] Confirm admin dashboard opens.
- [ ] Record rollback result.

Rollback must not require SQL, schema change, Auth0 change, Flutter change, user deletion, or code deployment.

## 10. Issue Log

Allowed issue types: login, role routing, data visibility, logout/session, workbench readiness, rollback, UX minor, other.

| Issue ID | Test ID | User email | Issue type | Severity | Description | No-Go risk? | Action taken | Retest result | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |  |  |  |  |

## 11. Final Pilot Result

| Field | Result |
| --- | --- |
| Pilot window date/time |  |
| Number of admins tested |  |
| Number of members tested |  |
| Auth0 baseline passed? |  |
| Supabase pilot login passed? |  |
| Data visibility passed? |  |
| Role isolation passed? |  |
| Rollback passed? |  |
| Open No-Go issues? |  |
| Final result: Go / Conditional Go / No-Go |  |
| Approved by |  |
| Approval date |  |

## 12. Decision Gate Before AUTH-XPLAT-5G

AUTH-XPLAT-5G may start only after:

- 5F-A execution log is completed.
- All selected pilot users are tested.
- Rollback is tested.
- No No-Go issue remains open.
- Evidence table is complete.
- Vineet explicitly approves moving to 5G.

Possible 5G direction: Controlled Supabase Auth operating model and batch-readiness design.

Do not implement 5G in this PR.

## 13. Strict Guardrails

- Auth0 remains fallback.
- Do not remove Auth0.
- Do not enable public signup.
- Do not batch migrate users.
- Do not migrate inactive users.
- Do not change database schema.
- Do not change RLS policies.
- Do not change Streamlit runtime code.
- Do not change Flutter code.
- Do not touch LAF/NSP/workflow/reports/recommendations.
- Do not expose service-role key.
- Do not record passwords.
- Do not trigger email actions from readiness checks.
- Do not leave AUTH_MODE as dual after testing unless explicitly approved.
