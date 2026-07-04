# H11 Supabase Auth Cutover Readiness Acceptance

## Purpose

H11 is an admin-only governance/readiness layer for Supabase member-auth cutover. It does not introduce a new login flow and does not replace Auth0 for Streamlit admin.

## Scope

- Adds a Supabase Auth Cutover Readiness page.
- Adds PASS / WARN / BLOCKED / INFO readiness summary.
- Adds readiness CSV download.
- Adds Flutter APK session guardrail matrix.
- Adds rollback playbook for pausing member-auth rollout.
- Uses H6 provisioning and H10 lifecycle audit helpers already present in main.

## Non-scope

- No Flutter code change.
- No Food Journal / Daily Log change.
- No LAF / NSP logic change.
- No report logic change.
- No Auth0 retirement.
- No SQL migration.
- No service-role key exposure to client or member side.

## Acceptance checks

1. Login as admin.
2. Open `pages/35_Admin_Supabase_Auth_Cutover_Readiness.py`.
3. Confirm page renders without crash.
4. Confirm Cutover decision cards render for PASS / WARN / BLOCKED / INFO.
5. Confirm H11 readiness checklist renders.
6. Download H11 readiness CSV.
7. Confirm Session guardrail test matrix renders.
8. Confirm Rollback playbook renders.
9. Confirm bottom navigation returns to Supabase Provisioning Workbench and Admin Dashboard.
10. Confirm existing Supabase Provisioning Workbench still opens.
11. Confirm Auth0 admin login remains unaffected.

## Cutover rule

Do not declare Supabase member-auth cutover ready while any BLOCKED rows remain. WARN rows require explicit admin review before broad rollout.
