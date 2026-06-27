# AUTH-XPLAT-5I Controlled Pilot Batch Candidate Registry and Expansion Gate

## 1. Title

AUTH-XPLAT-5I - Controlled Pilot Batch Candidate Registry and Expansion Gate

## 2. Purpose

This document defines the controlled pilot batch candidate registry and expansion gate for the HealthyMe Supabase Auth pilot after AUTH-XPLAT-5H passed UAT. It is a documentation-only operating control for deciding which pilot users may be included in small dual-mode validation waves.

This document does not provision users, send emails, change authentication behavior, execute SQL, or alter any runtime code.

## 3. Current Approved Baseline

The current approved baseline is:

- AUTH-XPLAT-5H UAT passed.
- Auth0 remains the default production authentication path.
- `AUTH_MODE` unset or `AUTH_MODE=auth0` continues to show Auth0 only.
- Dual mode is used only for controlled Supabase Auth pilot validation.
- Complete Secure Logout guidance is available for switching between pilot identities.
- Supabase Auth pilot checks remain manual and controlled.
- No batch migration has been approved.
- No public signup has been approved.

## 4. Non-Negotiable Guardrails

- Do not remove Auth0.
- Do not change default `AUTH_MODE`.
- Do not change Auth0 settings.
- Do not change Streamlit runtime code from this documentation sprint.
- Do not change Supabase schema, SQL, RLS, functions, triggers, or policies.
- Do not change secrets or Streamlit secrets.
- Do not change provisioning logic.
- Do not trigger invite, recovery, or notification emails.
- Do not enable public signup.
- Do not execute batch migration.
- Do not touch Flutter.
- Do not touch LAF, NSP, reports, recommendations, or admin workflows.
- Do not include real personal user data in this registry document.

## 5. Candidate Registry Table

The rows below are placeholders only. Replace them during the operating review with approved pilot candidates in the private operational tracking location, not in this repository document if personal data would be exposed.

| Candidate ID | Name | Email | Role: Admin / Member | Active in hm_users: Yes/No | Supabase Auth user exists: Yes/No | Workbench readiness passed: Yes/No | Invite/recovery path confirmed: Yes/No/Not required | Pilot batch: Batch 1 / Batch 2 / Hold | Approved for dual-mode pilot: Yes/No | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CAND-001 | Sample Admin Candidate | pilot.admin@example.invalid | Admin | Yes | Yes | Yes | Not required | Batch 1 | Yes | Placeholder row only; do not use real data here. |
| CAND-002 | Sample Member Candidate | pilot.member@example.invalid | Member | Yes | Yes | Yes | Not required | Batch 1 | Yes | Placeholder row only; do not use real data here. |
| CAND-003 | Sample Hold Candidate | pilot.hold@example.invalid | Member | No | No | No | No | Hold | No | Placeholder row only; hold until eligibility is confirmed. |

## 6. Eligibility Rules

A candidate is eligible for a controlled dual-mode pilot batch only when all of the following are true:

- Candidate has an approved pilot role: Admin or Member.
- Candidate exists in `hm_users`.
- Candidate is active in `hm_users`.
- Candidate role in `hm_users` matches the intended pilot role.
- Supabase Auth user existence is confirmed or explicitly accepted as a manual prerequisite before testing.
- Workbench readiness has passed.
- Invite or recovery path is confirmed when required.
- Candidate has explicit approval for dual-mode pilot testing.
- Candidate understands that Auth0 remains available and default behavior is not changing.

Candidates must remain on Hold when identity, role, active status, Supabase Auth user status, or pilot approval is unclear.

## 7. Batch Size Limit

Batch 1 must stay small and controlled:

- Maximum Batch 1 size: 1 pilot admin and 1 pilot member.
- Batch 2 may be considered only after Batch 1 completes without rollback criteria being triggered.
- Any increase beyond Batch 2 requires Vineet approval and Victor review.
- No broad rollout is approved by this document.

## 8. Pilot Execution Window Rules

- Run pilot validation in a defined time window agreed by Vineet and Victor.
- Do not begin pilot validation during active production support incidents.
- Confirm Auth0 default smoke test before enabling dual-mode pilot testing.
- Use Complete Secure Logout before switching between admin and member accounts.
- Test one candidate identity at a time.
- Record evidence immediately after each login/logout test.
- Stop the pilot window if any rollback criterion is met.

## 9. Evidence Required Per Pilot User

For each pilot user, capture the following evidence before considering the user passed:

- Candidate ID.
- Pilot batch.
- Role tested: Admin or Member.
- `hm_users` active status confirmed.
- Supabase Auth user existence confirmed or marked unknown with manual follow-up.
- Login path tested.
- Expected landing page or access boundary confirmed.
- Unauthorized access blocked where applicable.
- Logout tested.
- Complete Secure Logout tested when switching identities.
- Any error message or unexpected route captured.
- Tester name and test timestamp recorded in the private pilot execution log.

Do not store passwords, one-time codes, recovery links, tokens, service-role keys, or other secrets in the evidence log.

## 10. Expansion Gate

Expansion from Batch 1 to Batch 2 is allowed only when all of the following are true:

- Batch 1 admin login passes.
- Batch 1 member login passes.
- Auth0 admin login still passes after dual-mode testing.
- Logout and Complete Secure Logout behavior is understandable and reliable.
- No role confusion is observed.
- No unauthorized access is observed.
- No default `AUTH_MODE` change is required.
- No Supabase schema, RLS, policy, trigger, function, or provisioning change is required to continue.
- No secret exposure risk is identified.
- Vineet approves expansion.
- Victor confirms the evidence meets the MCD/auth migration acceptance criteria.

If any condition is not met, keep additional candidates on Hold.

## 11. Rollback Criteria

Rollback to Auth0-only default posture must be used or maintained if any of the following occur:

- Supabase pilot login routes a user to the wrong role experience.
- A member can access admin-only pages.
- An admin or member cannot reliably log out.
- Complete Secure Logout does not allow safe account switching during pilot testing.
- Auth0 admin login is disrupted.
- Default Auth0 behavior changes unintentionally.
- Any secret, token, invite link, or credential is exposed.
- Supabase Auth user readiness cannot be confirmed safely.
- Pilot evidence is incomplete or conflicting.
- Any production risk is identified by Vineet or Victor.

Rollback posture:

- Remove `AUTH_MODE` or set `AUTH_MODE=auth0`.
- Keep Auth0 as the active production path.
- Do not continue pilot expansion until the issue is reviewed and corrected in a separate approved sprint.

## 12. Explicit Non-Scope

This AUTH-XPLAT-5I sprint does not include:

- Streamlit runtime code changes.
- Auth0 setting changes.
- Auth0 removal.
- Default `AUTH_MODE` changes.
- Supabase schema, SQL, RLS, functions, triggers, or policy changes.
- Secret changes.
- Provisioning logic changes.
- Invite or recovery email actions.
- Flutter changes.
- LAF changes.
- NSP changes.
- Report changes.
- Recommendation changes.
- Admin workflow changes.
- Public signup enablement.
- Batch migration execution.

## 13. Next Step After 5I

After this registry and expansion gate are approved, the next safe step is a controlled Batch 1 pilot execution using the approved candidate list and evidence checklist. The pilot should remain dual-mode only, with Auth0 default preserved, and should not expand until the Batch 1 evidence passes the expansion gate.