# Identity observation window and smoke evidence — Gate 6

Date: 2026-08-03  
Issue: #346  
Follows: merged PR #372, `Harden canonical identity reads and add projection observation`

## Decision

Gate 6 does **not** retire the shared Users or Workflow projection.

It combines the evidence work that can safely be performed before retirement:

1. repeated production projection observations;
2. observation-window readiness calculation;
3. canonical Streamlit route-authority contract verification;
4. current Flutter repository contract verification;
5. live Flutter RPC permission and fallback inspection;
6. explicit blockers and rollback-readiness criteria;
7. permanent tests and CI evidence.

A static repository check is not represented as a signed-in browser or Android-device smoke.

## Merge baseline

PR #372 was merged with commit:

- `bf54ed509b61a3fe6526afdab705fd1365da190d`

The Flutter member repository remains at:

- repository: `VineetAppTest/healthyme-flutter-member`;
- revision: `a2de87cb37bea2dfecacbbb04cf03069f505077a`.

## Production migration

Applied to Supabase project `arptwzvlugxrqtvbrmtl`:

- `identity_observation_window_gate6`

Repository migration:

- `supabase/migrations/20260803175000_identity_observation_window_gate6.sql`

## Observation-window contract

`hm_identity_observation_window_status(...)` is a read-only, service-role-only function with a fixed empty `search_path`.

Its default evidence threshold is:

- at least `3` retained observations;
- all observations healthy;
- no repair inside the evaluated window;
- at least `60` minutes between the first and latest observation;
- current projection healthy.

It also reports:

- active-member Auth-link coverage;
- active members missing canonical Workflow;
- anonymous and authenticated execution coverage for the ten Flutter identity/LAF/NSP RPCs;
- Flutter functions that still fall back to shared Workflow;
- exact blockers;
- database-observation readiness;
- automated retirement-precondition readiness.

Automated readiness never substitutes for signed-in route and device evidence.

## Production projection evidence

At the Gate 6 pre-PR checkpoint:

- canonical Users: `15`;
- shared Users: `15`;
- canonical Workflow rows: `15`;
- shared Workflow rows: `15`;
- projection health: `true`;
- User mismatches: `0`;
- Workflow mismatches: `0`;
- missing, orphaned or duplicate shared identities: `0`;
- persisted repair observations: `0`.

Three genuine healthy production observations are retained:

1. Gate 5A/6A production baseline at `2026-08-03T11:32:02.340453Z`;
2. post-PR-#372 merge checkpoint at `2026-08-03T11:48:58.640454Z`;
3. Gate 6 pre-PR checkpoint at `2026-08-03T12:00:17.454812Z`.

Observed span:

- approximately `28.25` minutes.

The observation-count threshold is satisfied. The observation window remains below the default `60`-minute duration threshold.

## Active-member coverage

Production coverage:

- active members: `7`;
- active members linked by `auth_user_id`: `6`;
- active members still using controlled email fallback: `1`;
- active members missing canonical Workflow: `0`.

The remaining email-fallback member blocks automated projection-retirement readiness. This gate does not guess the identity or mutate the Auth link.

## Streamlit route-authority evidence

Machine-readable evidence:

- `docs/evidence/identity_gate6_static_evidence_2026-08-03.json`

Verified against HealthyMe revision `bf54ed509b61a3fe6526afdab705fd1365da190d`:

- `components/storage_backend.py` fails closed for Users and Workflow when canonical reads fail;
- `components/admin_role_model.py` resolves roles from canonical `hm_users` only;
- `components/guards.py` restores authentication and then checks `current_user_is_admin()` or `current_user_is_member()`;
- `app.py` retains the accepted native authorization bridge.

This is a repository contract check. It does not claim an authenticated Streamlit UI session was exercised.

## Flutter repository evidence

Verified against Flutter revision `a2de87cb37bea2dfecacbbb04cf03069f505077a`:

- `lib/repositories/member_repository.dart` reads `hm_users` and `hm_workflow` directly;
- `lib/repositories/laf_repository.dart` calls authenticated self-scoped LAF RPCs;
- `lib/repositories/nsp_repository.dart` calls authenticated self-scoped NSP and submit-review RPCs;
- none of those LAF/NSP calls accepts a caller-supplied member ID.

Live Supabase inspection covered ten Flutter functions:

- anonymous-executable functions: `0`;
- functions missing authenticated execution: `0`;
- active members missing Workflow: `0`.

## Remaining Flutter shared Workflow fallback

Live function definitions still contain shared Workflow fallback in:

- `hm_flutter_get_laf()`;
- `hm_flutter_get_nsp()`.

Both functions prefer canonical `hm_workflow`, but can fall back to `healthyme_app_state.data.workflow`.

Assessment response payloads continue to live in the shared application-state document and are outside the Users/Workflow projection-retirement decision. A future Flutter fallback-removal PR must remove only the Workflow fallback while preserving LAF/NSP response payload access.

## Current automated blockers

The Gate 6 status now reports:

1. `insufficient_observation_span`;
2. `active_member_auth_email_fallback_remains`;
3. `flutter_shared_workflow_fallback_remains`.

The observation-count blocker has cleared. Projection retirement is still not approved.

## Signed-in smoke evidence

The following remain explicitly pending:

- Streamlit Admin login, refresh, logout and protected Admin route;
- Streamlit Member login, refresh, logout and protected Member route;
- Flutter authenticated login, dashboard, LAF, NSP and Submit for Review on a device/build.

No automated or static result is labelled as those smokes.

## Admin visibility

`pages/28_Admin_Database_Status.py` now displays:

- observation count and threshold;
- first/latest observation span;
- Auth-link coverage;
- missing Workflow coverage;
- Flutter RPC permission counts;
- Flutter shared Workflow fallback functions;
- exact blockers;
- automated readiness state.

It also states that manual route/device evidence and a separate retirement PR remain mandatory.

## Rollback boundary

The shared Users and Workflow projection remains current rollback evidence.

Gate 6 does not:

- freeze or delete the projection;
- change its write/repair contract;
- remove assessment response payloads;
- alter login, logout, refresh, routing or sessions;
- change Flutter source or RPC signatures;
- change User or Workflow business data;
- retire password hashes;
- redesign default-Admin recovery.

## Acceptance before projection retirement

A later retirement PR requires all of the following:

1. default database observation threshold passes;
2. current projection remains healthy;
3. no repair occurs in the accepted window;
4. all active members have canonical Workflow;
5. accepted Auth linkage decision for the remaining email-fallback member;
6. Flutter LAF/NSP shared Workflow fallback removed and regression tested;
7. signed-in Admin route/refresh/logout evidence;
8. signed-in Member route/refresh/logout evidence;
9. Flutter device login/dashboard/LAF/NSP/submit-review evidence;
10. rollback evidence and permanent no-new-writer guards.

Sessions, password retirement and default-Admin redesign remain separate batches.
