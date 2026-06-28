# AUTH-XPLAT-5L — Controlled Expansion Execution Pack

## Purpose

This document consolidates the remaining controlled Supabase Auth expansion documentation into one execution-ready pack. It covers candidate approval, approved execution windows, operator checklists, rollback posture, evidence capture, and post-window decisioning for controlled expansion after the Batch 1 review.

## Current Approved Baseline

- AUTH-XPLAT-5H Secure Logout Visibility passed UAT.
- AUTH-XPLAT-5I Controlled Pilot Batch Candidate Registry has been merged.
- AUTH-XPLAT-5J Pilot Batch Execution Log has been merged.
- AUTH-XPLAT-5K Batch 1 Review and Expansion Decision has been merged.
- Auth0 remains the fallback and default production authentication path.
- Default `AUTH_MODE` remains `auth0`.
- `AUTH_MODE=dual` remains allowed only during controlled pilot windows.
- No bulk migration or mass migration is approved.
- No public signup is approved.

## Dependency Gate Before Use

This execution pack can be used only if the latest approved AUTH-XPLAT-5K decision is GO or accepted CONDITIONAL GO.

If the latest AUTH-XPLAT-5K result is NO-GO, do not use this pack for expansion. Create and complete a corrective sprint first.

## Controlled Expansion Candidate Approval

| Candidate ID | Role: Admin / Member | Batch | Approved for expansion: Yes / No | Exists in hm_users: Yes / No | Active in hm_users: Yes / No | Supabase Auth user exists: Yes / No | Workbench readiness passed: Yes / No | Invite/recovery path confirmed: Yes / No / Not required | Approved by | Approval date | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| B2-ADMIN-001 | Admin | Placeholder | Placeholder | Placeholder | Placeholder | Placeholder | Placeholder | Placeholder | Placeholder | Placeholder | Placeholder only; no personal data. |
| B2-MEMBER-001 | Member | Placeholder | Placeholder | Placeholder | Placeholder | Placeholder | Placeholder | Placeholder | Placeholder | Placeholder | Placeholder only; no personal data. |
| B2-MEMBER-002 | Member | Placeholder | Placeholder | Placeholder | Placeholder | Placeholder | Placeholder | Placeholder | Placeholder | Placeholder | Placeholder only; no personal data. |

## Approved Execution Window

| Window ID | Date | Start time | End time | AUTH_MODE during window | Operator | Backup operator | Rollback owner | Approved candidates | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| WINDOW-001 | Placeholder | Placeholder | Placeholder | `dual` during approved window only | Placeholder | Placeholder | Placeholder | Placeholder | Placeholder only. |

Execution window rules:

- Use `AUTH_MODE=dual` only inside the approved window.
- Return to `AUTH_MODE=auth0` after the window unless explicitly approved otherwise.
- Test one candidate at a time.
- Use Complete Secure Logout before switching users.
- Prefer a fresh or incognito browser for role-switch tests.
- Do not test unapproved users.

## Pre-Window Checklist

- PR baseline confirmed.
- Deployment target identified.
- `AUTH_MODE` rollback path confirmed.
- Auth0 login tested before pilot.
- Supabase candidate users confirmed.
- `hm_users` role and status verified.
- Complete Secure Logout visible.
- Browser or incognito plan ready.
- Evidence capture method ready.
- No secrets, tokens, or invite links will be recorded.

## During-Window Operator Checklist

1. Confirm current `AUTH_MODE`.
2. Switch to `AUTH_MODE=dual` only for the approved pilot window.
3. Test approved admin candidate.
4. Use Complete Secure Logout.
5. Test approved member candidate.
6. Check correct landing page.
7. Check correct role access.
8. Check no wrong member data.
9. Check no admin/member carryover.
10. Check Auth0 rollback or fallback if required.
11. Capture result.
12. Return to `AUTH_MODE=auth0` after the window.

## Evidence Capture Table

| Test ID | Candidate ID | Role | Login result | Landing page result | Role access result | Logout result | Carryover result | Data visibility result | Auth0 fallback result | Final result: Pass / Conditional Pass / Fail | Evidence location | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TEST-001 | Placeholder | Admin | Placeholder | Placeholder | Placeholder | Placeholder | Placeholder | Placeholder | Placeholder | Placeholder: Pass / Conditional Pass / Fail | Placeholder | Placeholder only; no personal data. |
| TEST-002 | Placeholder | Member | Placeholder | Placeholder | Placeholder | Placeholder | Placeholder | Placeholder | Placeholder | Placeholder: Pass / Conditional Pass / Fail | Placeholder | Placeholder only; no personal data. |

## Rollback Playbook

| Trigger | Immediate action | Rollback action | Evidence to capture | Owner | Follow-up sprint required: Yes / No |
| --- | --- | --- | --- | --- | --- |
| wrong role/page | Stop testing immediately. | Return to `AUTH_MODE=auth0`. | Screenshot or redacted notes without secrets. | Placeholder | Yes |
| member sees admin page | Stop testing immediately. | Return to `AUTH_MODE=auth0`. | Redacted page evidence and user role context. | Placeholder | Yes |
| admin/member carryover | Stop role-switch testing immediately. | Complete logout, clear session context, and return to `AUTH_MODE=auth0`. | Redacted carryover description and browser/session notes. | Placeholder | Yes |
| logout feedback missing | Pause testing and confirm whether logout completed. | Return to `AUTH_MODE=auth0` if completion cannot be confirmed. | Redacted UX notes and timestamp. | Placeholder | Yes / No |
| Complete Secure Logout fails | Stop testing immediately. | Return to `AUTH_MODE=auth0`. | Redacted logout failure evidence. | Placeholder | Yes |
| Auth0 fallback fails | Stop expansion immediately. | Restore Auth0-only posture and investigate fallback. | Redacted fallback failure notes. | Placeholder | Yes |
| wrong member data visible | Stop testing immediately. | Return to `AUTH_MODE=auth0`. | Redacted data visibility notes without personal data. | Placeholder | Yes |
| unauthorized user gets access | Stop testing immediately. | Return to `AUTH_MODE=auth0`. | Redacted access evidence and route/action details. | Placeholder | Yes |
| secret/token/invite link exposure | Stop testing immediately and preserve minimal redacted evidence. | Return to `AUTH_MODE=auth0` and rotate or revoke exposed material as required. | Redacted exposure notes only; do not record the secret/token/link. | Placeholder | Yes |
| unexpected Supabase Auth error | Pause testing and classify severity. | Return to `AUTH_MODE=auth0` if the issue affects auth, role, data, logout, fallback, or security behavior. | Redacted error summary and timestamp. | Placeholder | Yes / No |

## Stop/Go Decision After Execution Window

| Window result: GO / CONDITIONAL GO / NO-GO | Expansion can continue: Yes / No | Next approved batch size | Conditions before next batch | Approval owner | Date | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| Placeholder | Placeholder | Placeholder | Placeholder | Placeholder | Placeholder | Placeholder |

## Rule For CONDITIONAL GO

CONDITIONAL GO is allowed only for minor UX or documentation issues. It is not allowed if there is any auth, role-boundary, logout, rollback, data visibility, unauthorized access, or secret exposure issue.

## Explicit NO-GO Rules

NO-GO is mandatory for any wrong role, wrong page, unauthorized access, admin/member carryover, logout failure, Auth0 fallback failure, wrong member data, data visibility issue, or secret/token exposure.

## Explicit Non-Scope

This sprint does not execute migration, provisioning, SQL changes, Auth0 removal, default `AUTH_MODE` changes, Streamlit runtime code changes, Flutter changes, LAF/NSP/report changes, public signup, email/invite actions, or actual batch execution.

This sprint also does not change Streamlit runtime code, Auth0 settings, Supabase schema, SQL, RLS, functions, triggers, policies, secrets, provisioning logic, recommendations, admin workflows, or any batch migration execution.

## Next Step After 5L

If 5L is merged and the approved decision is GO or accepted CONDITIONAL GO, the next sprint should be operational and not another documentation-only sprint:

AUTH-XPLAT-5M — Controlled Pilot Expansion Execution

If the result is NO-GO:

AUTH-XPLAT-5L-FIX — Corrective Action Before Further Supabase Auth Expansion
