# AUTH-XPLAT-5J - Pilot Batch Execution Log and Controlled Expansion Evidence

## 1. Title

AUTH-XPLAT-5J - Pilot Batch Execution Log and Controlled Expansion Evidence

## 2. Purpose

This document captures pilot execution evidence for approved Supabase Auth pilot candidates. It is intended to support controlled validation after AUTH-XPLAT-5I established the candidate registry and expansion gate.

This document is documentation-only. It does not execute migration, provision users, send emails, change authentication behavior, change secrets, or alter runtime code.

## 3. Current Approved Baseline

The current approved baseline is:

- AUTH-XPLAT-5H passed UAT.
- AUTH-XPLAT-5I has been merged.
- Auth0 remains the default production authentication path and fallback.
- Default `AUTH_MODE` remains `auth0`.
- `AUTH_MODE=dual` is allowed only during controlled pilot windows.
- No public signup is approved.
- No bulk migration or mass migration is approved.

## 4. Pilot Execution Rules

- Test one candidate at a time.
- Use `AUTH_MODE=dual` only during a planned pilot window.
- Use Complete Secure Logout before switching users.
- Prefer a fresh or incognito browser for admin/member switch testing.
- Return to `AUTH_MODE=auth0` after the pilot window unless explicitly approved.
- Do not continue pilot execution if any rollback criterion appears.
- Do not record passwords, tokens, recovery links, invite links, service-role keys, or other secrets.
- Do not test unapproved users.
- Do not enable public signup.
- Do not execute SQL, provisioning, or batch migration during this evidence sprint.

## 5. Pilot Execution Log Table

The rows below are placeholders only. Do not include real personal user data in this repository document.

| Test ID | Candidate ID | Role tested: Admin / Member | Batch | Test date | Tester | AUTH_MODE used | Supabase login success: Yes/No | Correct landing page: Yes/No | Correct role access: Yes/No | Wrong role/page observed: Yes/No | Secure Logout visible feedback: Yes/No | Complete Secure Logout used: Yes/No | No cross-role carryover: Yes/No | Auth0 rollback checked: Yes/No/Not required | Result: Pass / Conditional Pass / Fail | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TEST-001 | CAND-001 | Admin | Batch 1 | YYYY-MM-DD | Tester name | dual | Yes | Yes | Yes | No | Yes | Yes | Yes | Yes | Pass | Placeholder row only. Replace in private execution log, not with real data here. |
| TEST-002 | CAND-002 | Member | Batch 1 | YYYY-MM-DD | Tester name | dual | Yes | Yes | Yes | No | Yes | Yes | Yes | Yes | Pass | Placeholder row only. Replace in private execution log, not with real data here. |
| TEST-003 | CAND-003 | Member | Hold | YYYY-MM-DD | Tester name | dual | No | No | No | Yes | No | No | No | Not required | Fail | Placeholder row only for rollback-example capture. |

## 6. Evidence Checklist Per Candidate

For each approved candidate, capture evidence for the following items:

- Candidate exists in `hm_users`.
- Candidate active status confirmed.
- Role in `hm_users` verified.
- Supabase Auth user exists.
- Workbench readiness passed.
- Login succeeds.
- Correct page opens.
- Role boundary behaves correctly.
- Secure Logout has visible feedback.
- Complete Secure Logout works before account switch.
- No admin/member carryover occurs.
- Auth0 fallback works where applicable.

Evidence must be captured in the approved private pilot execution log. Do not store secrets, passwords, recovery links, invite links, one-time codes, access tokens, refresh tokens, service-role keys, or personal data in this repository document.

## 7. Result Classification

### GO

All pilot users pass, and there is no authentication, data visibility, security, logout, role-boundary, or rollback issue.

### CONDITIONAL GO

Only minor UX or documentation issues are found, and there is no authentication risk, no data visibility issue, no unauthorized access, no role-boundary issue, and no rollback failure.

### NO-GO

Any wrong role, wrong page, unauthorized access, cross-role carryover, logout failure, Auth0 fallback failure, data visibility issue, or secret exposure is observed.

A NO-GO result stops expansion until a separate approved corrective sprint is completed and reviewed.

## 8. Rollback Trigger Table

| Trigger | Required action | Owner | Evidence to capture |
| --- | --- | --- | --- |
| Supabase login opens wrong role/page | Stop pilot testing, return to `AUTH_MODE=auth0`, capture route and role details | Pilot operator / Victor | Screenshot or notes showing expected vs actual role/page |
| Member sees admin page | Stop pilot testing immediately, return to `AUTH_MODE=auth0`, escalate for review | Pilot operator / Victor | Page name, candidate role, timestamp, access path |
| Admin/member carryover occurs | Use Complete Secure Logout, retest only if approved, otherwise return to `AUTH_MODE=auth0` | Pilot operator | Before/after identity state and observed carryover behavior |
| Secure Logout feedback missing | Stop account-switch testing, record missing feedback, require fix before expansion | Pilot operator / Cody | Screenshot or notes showing missing success/warning feedback |
| Complete Secure Logout fails | Close browser/incognito window, return to `AUTH_MODE=auth0`, require fix before expansion | Pilot operator / Cody | Error text, browser state, steps to reproduce |
| Auth0 fallback fails | Stop Supabase pilot, return to default Auth0 path, escalate | Pilot operator / Victor | Auth0 login/logout result and error details |
| Wrong member data visible | Stop pilot immediately, return to `AUTH_MODE=auth0`, escalate as data visibility risk | Pilot operator / Victor | Candidate ID, expected data boundary, observed mismatch |
| Unauthorized user gets app access | Stop pilot immediately, return to `AUTH_MODE=auth0`, escalate as security risk | Pilot operator / Victor | User state, login path, observed access |
| Secret/token/invite link exposed | Stop pilot immediately, rotate/revoke if required, escalate security review | Vineet / Victor | What was exposed, where, timestamp, corrective action |

## 9. Expansion Decision Section

Use this section after Batch 1 evidence is complete.

- Batch 1 result: GO / CONDITIONAL GO / NO-GO
- Expansion decision: GO / CONDITIONAL GO / NO-GO
- Approved next batch size: TBD
- Approval owner: Vineet / Victor
- Date approved: YYYY-MM-DD
- Notes: TBD

Expansion must not proceed unless the result classification and evidence satisfy the AUTH-XPLAT-5I expansion gate.

## 10. Explicit Non-Scope

This sprint does not include:

- Migration execution.
- Provisioning changes.
- SQL changes.
- Supabase schema changes.
- Supabase RLS, function, trigger, or policy changes.
- Auth0 removal.
- Auth0 settings changes.
- Default `AUTH_MODE` changes.
- Streamlit runtime code changes.
- Secret changes.
- Invite, recovery, or email actions.
- Flutter changes.
- LAF changes.
- NSP changes.
- Report changes.
- Recommendation changes.
- Admin workflow changes.
- Public signup enablement.
- Batch migration execution.

## 11. Next Step After 5J

If pilot evidence passes, the next sprint can be:

AUTH-XPLAT-5K - Controlled Pilot Batch 1 Execution Review and Expansion Decision

AUTH-XPLAT-5K should review captured Batch 1 evidence, classify the result as GO / CONDITIONAL GO / NO-GO, and decide whether any controlled expansion is approved.