# H10 Supabase Auth Lifecycle Audit Workbench

This file documents the H10 admin-only hardening sprint.

## Scope

- Admin lifecycle audit
- Orphan/unlinked Supabase Auth review
- Controlled password reset dry-run/execution
- Existing H6 provisioning workbench retained

## Non-scope

- No Flutter UX change
- No H9A Recent Saved Days UI change
- No Auth0 retirement
- No LAF/NSP/report change
- No service-role key exposure to member-side code

## Smoke test

1. Login as admin.
2. Open Supabase Auth Provisioning Workbench.
3. Confirm Lifecycle Audit tab renders.
4. Confirm Orphan / Unlinked Auth review renders.
5. Run password reset dry run.
6. Confirm execution requires exact RESET PASSWORD confirmation.
