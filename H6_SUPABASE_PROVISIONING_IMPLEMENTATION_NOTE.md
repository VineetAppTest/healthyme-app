# H6 Supabase Auth Provisioning Hardening

This note documents the H6 implementation branch because Cody is unavailable.

## Branch

`hm-h6-provisioning`

## Scope

- Hardened Supabase Auth Readiness page.
- Hardened Supabase Auth Provisioning Workbench.
- Added server-side helper for readiness counts, member review, duplicate prevention, inactive/missing/invalid email handling, one-member provisioning, batch provisioning, and audit loading.
- Added optional RLS readiness SQL review file.
- Updated build version and manifest to H6.

## Guardrails

- Auth0 is not retired.
- Flutter UX is not changed.
- LAF/NSP/member flow logic is not changed.
- Service-role key remains server-side only.
- RLS SQL is review-first and commented by default.

## Manual smoke test

1. Deploy branch build.
2. Login as admin using existing Auth0.
3. Open Admin Dashboard.
4. Open Supabase Auth Readiness.
5. Confirm readiness checks render.
6. Open Supabase Provisioning.
7. Confirm summary and member review table render.
8. Run one single-member dry run.
9. Execute one test member only after dry run looks correct.
10. Re-run same member and confirm already-provisioned/link behavior.
11. Run batch dry run only.
12. Confirm Auth0 admin login still works.
