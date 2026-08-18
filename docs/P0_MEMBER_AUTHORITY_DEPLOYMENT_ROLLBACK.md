# P0 Member Authority Contract v2 — Controlled Deployment & Rollback

Date: 2026-08-18

## Rollback anchor

Pre-#425 web application anchor after approved privacy PR #426:

- `healthyme-app/main`: `6c3723afcbeb9fbd67270186271a8e369105d357`

This is the preferred emergency web rollback target if #425 causes a runtime issue.

## Deployment order

1. Confirm HealthyMe Supabase project identity by verifying `public.hm_member_exercise_logs`, `public.hm_users` and `public.healthyme_app_state` exist.
2. Capture pre-migration schema/constraint/index snapshot for `public.hm_member_exercise_logs`.
3. Apply `sql/p0_member_exercise_log_allocation_identity_v2.sql` as one Supabase migration.
4. Verify the three added columns, three constraints and allocation index exist; confirm legacy row count is unchanged.
5. Smoke the existing web app before #425 merge. Because the migration is additive, the pre-#425 web code must continue working.
6. Refresh #425 against latest `main` and rerun its CI.
7. Merge #425 only after steps 1–6 pass.
8. Verify deployment and smoke Member Home, Current Member Plan, Daily Log → Exercise Journal, saved days/history, and one existing legacy Exercise Journal day.
9. Only then proceed to native v2 RPC deployment/UAT.

## Preferred emergency rollback

If the web app regresses after #425:

1. Revert/deploy the web application to `6c3723afcbeb9fbd67270186271a8e369105d357` (or the generated revert of #425 if later main changes must be preserved).
2. **Leave the additive database migration in place.** The pre-#425 code does not depend on the added columns and this avoids deleting any v2 journal history.
3. Re-smoke Member Home, Current Member Plan and Exercise Journal.

This is the default rollback because it restores the known web behaviour without destructive data operations.

## Database rollback — last resort only

`sql/p0_member_exercise_log_allocation_identity_v2_rollback.sql` is intentionally guarded. It aborts if any v2 allocation-linked/manual rows or nullable legacy identity rows exist.

Run it only when:

- application code has already been rolled back;
- no v2 Exercise Journal rows were written; and
- the additive schema itself is demonstrated to be the cause of the incident.

Never delete or rewrite historical journal rows to make the rollback pass.

## Stop conditions

Stop deployment and keep/revert to the known functional web version if any of the following occurs:

- HealthyMe Supabase project identity cannot be confirmed;
- migration changes legacy row count;
- existing web app fails after schema migration but before #425 merge;
- #425 CI is not fully green after refresh against latest main;
- Member Home, Current Member Plan or Exercise Journal cannot load after deployment;
- saved legacy Exercise Journal history is missing or changed.
