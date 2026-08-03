# Identity fallback closure — Gate 7

Date: 2026-08-03  
Issue: #346  
Follows: merged PR #373, `Add identity observation window and smoke-evidence gate`

## Decision

Gate 7 closes the remaining database and RPC fallback paths identified by Gate 6 and completes the accepted database observation window.

It does **not** retire the shared Users or Workflow projection. Projection retirement still requires genuine signed-in Streamlit and Flutter device evidence and a separate explicitly approved PR.

## Clubbed actions

The following related actions are delivered together:

1. link the sole active member still using controlled Auth email fallback;
2. commit the canonical User and shared rollback projection atomically;
3. make Flutter member resolution `auth_user_id`-only;
4. remove shared Workflow fallback from Flutter LAF and NSP reads;
5. preserve LAF and NSP response payloads in shared application state;
6. consolidate direct member reads to Auth-ID-based RLS;
7. retire obsolete direct authenticated Workflow writes;
8. remove anonymous identity-table privileges;
9. expose a permanent fallback-closure status contract;
10. retain healthy post-closure and window-completion observations;
11. add Admin visibility, evidence, tests and CI.

## Production migration

Applied to Supabase project `arptwzvlugxrqtvbrmtl`:

- `identity_blocker_closure_gate7`

Repository migration:

- `supabase/migrations/20260803183000_identity_blocker_closure_gate7.sql`

## Auth linkage

Production contained exactly one active member without `auth_user_id`.

The candidate had:

- exactly one case-insensitive Auth email match;
- no competing HealthyMe member match;
- no conflicting existing `auth_user_id` linkage.

The migration does not hardcode an Auth UUID or silently guess a member. It proceeds only when the conditions above are uniquely true.

The existing `hm_admin_commit_identity_and_state(...)` contract performs the update so that:

- canonical `hm_users` and the shared User rollback projection change atomically;
- `auth_provider` becomes `supabase`;
- `auth_user_id` and `auth_migrated_at` are retained;
- one canonical User event is recorded;
- the child and parent idempotency requests are recorded;
- no projection repair event is required.

After migration:

- active members: `7`;
- active members with `auth_user_id`: `7`;
- active members using email fallback: `0`;
- active members missing canonical Workflow: `0`.

## Flutter member resolution

`hm_flutter_current_member_id()` now resolves an active member only through:

- `auth.uid()`;
- `hm_users.auth_user_id`;
- active member role/status checks.

It no longer reads JWT email and no longer accepts a User row with missing `auth_user_id`.

The function signature is unchanged and remains callable only by `authenticated` and `service_role`, not `anon` or `PUBLIC`.

## LAF and NSP Workflow authority

`hm_flutter_get_laf()` and `hm_flutter_get_nsp()` now require a canonical `hm_workflow` row.

Removed:

- LAF fallback to `healthyme_app_state.data.workflow`;
- NSP fallback to `healthyme_app_state.data.workflow`.

Preserved:

- LAF response payloads from `healthyme_app_state.data.laf_responses`;
- NSP response payloads from `healthyme_app_state.data.nsp1_responses` and `nsp2_responses`;
- existing Flutter RPC names;
- existing Flutter repository method names;
- existing JSON payload keys;
- lifecycle and navigation flags derived from canonical Workflow.

If canonical Workflow is missing, the read now fails visibly instead of returning a shared fallback.

## RLS and direct-write hardening

Three overlapping email-based `hm_users` read policies were replaced with one authenticated Auth-ID policy.

Three overlapping `hm_workflow` read policies were replaced with one authenticated Auth-ID policy.

The obsolete direct authenticated Workflow insert and update policies were removed. Current Flutter source contains no direct `hm_workflow` write; LAF and NSP changes use self-scoped RPCs.

Privileges after Gate 7:

- `anon`: no table privileges on `hm_users` or `hm_workflow`;
- `authenticated`: `SELECT` only on `hm_users` and `hm_workflow`;
- authenticated direct Workflow insert/update: blocked;
- service role: unchanged for server-side canonical contracts.

The new RLS predicates use `(select auth.uid())`, avoiding repeated per-row JWT-function evaluation.

## Closure status contract

`hm_identity_fallback_closure_status()` is:

- read-only;
- `STABLE`;
- `SECURITY DEFINER` with an empty fixed `search_path`;
- executable only by `service_role`.

It reports:

- active members missing Auth linkage;
- active members missing canonical Workflow;
- whether `hm_flutter_current_member_id()` still uses email fallback;
- Flutter functions still using shared Workflow fallback;
- email-based identity policies;
- direct Workflow write policies;
- anonymous identity-table privileges;
- authenticated non-SELECT identity-table privileges;
- exact blockers and overall closure state.

Production result:

- closure: `true`;
- blockers: `[]`;
- email fallback policies: `[]`;
- direct Workflow write policies: `[]`;
- anonymous identity privileges: `0`;
- authenticated non-SELECT identity privileges: `0`.

## Verification

A complete rolled-back probe validated the exact migration before production application:

- exact unique Auth linkage through the Gate 4 transaction;
- canonical and shared projection parity;
- Auth-ID member resolution;
- direct authenticated User and Workflow self-read;
- LAF canonical Workflow plus shared response payload;
- NSP canonical Workflow plus shared response payloads;
- no direct authenticated Workflow insert/update privilege;
- closure status `true`;
- no persisted dry-run data, event or observation.

Post-migration production verification confirmed:

- canonical Users: `15`;
- shared Users: `15`;
- canonical Workflow: `15`;
- shared Workflow: `15`;
- projection healthy: `true`;
- User mismatches: `0`;
- Workflow mismatches: `0`;
- Gate 7 User events: `1`;
- Gate 7 domain-write request rows: `2`;
- Gate 7 post-closure observations: `1`;
- Gate 7 window-completion observations: `1`;
- projection repairs in the observation window: `0`.

Machine-readable evidence:

- `docs/evidence/identity_gate7_fallback_closure_evidence_2026-08-03.json`

## Completed observation window

The threshold was not reduced or bypassed.

A window-completion observation was recorded only after real elapsed time exceeded 60 minutes.

Final production result:

- observations: `5`;
- healthy observations: `5`;
- repairs: `0`;
- first observation: `2026-08-03T11:32:02.340453Z`;
- latest observation: `2026-08-03T12:35:13.516001Z`;
- retained observation span: approximately `63.19` minutes;
- required span: `60` minutes;
- database observation ready: `true`;
- automated retirement preconditions ready: `true`;
- automated blockers: `[]`.

Automated readiness remains evidence only. It does not substitute for signed-in browser and device validation.

## Signed-in smoke boundary

Still pending and not represented by static or SQL verification:

- Streamlit Admin login, refresh, protected route and logout;
- Streamlit Member login, refresh, protected route and logout;
- Flutter authenticated login, dashboard, LAF, NSP and Submit for Review on an actual build/device.

## Safety boundary

Gate 7 does not:

- retire, freeze or delete the shared Users/Workflow projection;
- remove LAF or NSP response payloads from shared state;
- change Flutter source code;
- change Flutter public method names or RPC payload keys;
- change assessment, report, recommendation, package, schedule or email business logic;
- change Streamlit login, logout, refresh, routing or Session storage;
- retire password hashes;
- redesign default-Admin recovery;
- approve projection retirement.

## Next controlled gate

After merge:

1. capture signed-in Streamlit Admin route/refresh/logout evidence;
2. capture signed-in Streamlit Member route/refresh/logout evidence;
3. capture Flutter device login/dashboard/LAF/NSP/submit-review evidence;
4. prepare a separate projection-retirement decision PR only when every manual acceptance item passes.

Sessions, password retirement and default-Admin redesign remain separate batches.
