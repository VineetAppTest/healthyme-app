# Identity manual smoke and retirement-decision evidence — Gate 8

Date: 2026-08-03  
Issue: #346  
Follows: merged PR #374, `Close identity fallback paths before projection retirement`

## Decision

Gate 8 creates the controlled evidence layer required before any Users/Workflow projection-retirement decision.

It does **not** retire, freeze, delete or stop updating the shared Users/Workflow projection. It does not approve projection retirement. A positive Gate 8 result means only that a separate retirement-decision PR may be considered.

## Clubbed actions

The following related actions are delivered together:

1. create a private manual smoke evidence store;
2. define three mandatory signed-in smoke bundles;
3. require step-level checklists for every bundle;
4. bind evidence to an exact revision and deployment/build reference;
5. distinguish production, staging and test evidence;
6. reject a passing record when any mandatory step is false or missing;
7. make request replay idempotent and reject request-ID reuse with different evidence;
8. require evidence writes to use the validated RPC rather than direct table inserts;
9. expire old evidence after a controlled age window;
10. aggregate automated, fallback-closure, manual-smoke and rollback evidence;
11. expose the decision gate and evidence form in Admin Database Status;
12. document rollback triggers and pre-retirement requirements;
13. add production verification, tests and CI guards.

## Production migrations

Applied to Supabase project `arptwzvlugxrqtvbrmtl`:

- `identity_manual_smoke_gate8`;
- `identity_manual_smoke_gate8_harden_service_role_grants`;
- `identity_manual_smoke_gate8_contract_only_writes`.

Repository migrations:

- `supabase/migrations/20260803184500_identity_manual_smoke_gate8.sql`;
- `supabase/migrations/20260803185000_identity_manual_smoke_gate8_harden_service_role_grants.sql`;
- `supabase/migrations/20260803185500_identity_manual_smoke_gate8_contract_only_writes.sql`.

## Manual smoke bundles

### Streamlit Admin

Mandatory checks:

- login succeeds;
- login persists after refresh;
- an Admin-protected route opens with the correct role;
- logout completes.

### Streamlit Member

Mandatory checks:

- login succeeds;
- login persists after refresh;
- a Member-protected route opens with the correct role;
- logout completes.

### Flutter Member

Mandatory checks:

- authenticated login succeeds;
- dashboard loads the correct member;
- LAF opens and reads expected saved data;
- NSP opens and reads expected saved data;
- Submit for Review completes successfully.

A `pass` record is rejected unless every mandatory checklist value for the selected bundle is explicitly `true`.

## Evidence provenance

Every evidence record requires:

- evidence bundle;
- pass/fail result;
- tested repository revision;
- build or deployment reference;
- environment;
- mandatory checklist;
- test timestamp;
- Admin actor context when available.

Optional fields:

- notes;
- secure evidence reference such as an issue comment, approved video location or test run ID.

Credentials, access tokens and other secrets must never be stored in notes or evidence references.

## Evidence store and permissions

`hm_identity_manual_smoke_evidence`:

- has RLS enabled;
- has no public policies;
- is not accessible by `PUBLIC`, `anon` or `authenticated`;
- is directly readable by `service_role` for diagnostics;
- does not allow direct `service_role` inserts;
- accepts writes only through `hm_admin_record_identity_smoke_evidence(...)`;
- stores the original request payload for idempotency comparison;
- retains historical pass and fail records;
- uses the latest record for each bundle when calculating readiness.

`hm_admin_record_identity_smoke_evidence(...)`:

- is `SECURITY DEFINER` with an empty fixed `search_path`;
- is executable only by `service_role`;
- validates the bundle-specific checklist;
- requires revision and build references;
- rejects a false or missing mandatory step on a passing record;
- returns an idempotent replay only for an identical request payload.

## Retirement-decision readiness

`hm_identity_projection_retirement_readiness(...)` aggregates:

1. Gate 6 automated observation-window readiness;
2. Gate 7 fallback closure;
3. the latest Streamlit Admin smoke bundle;
4. the latest Streamlit Member smoke bundle;
5. the latest Flutter Member smoke bundle;
6. retained and aligned shared Users/Workflow rollback projection.

Default evidence age limit:

- `72 hours`.

A bundle is not ready when its latest evidence is:

- missing;
- not from production;
- stale;
- failed.

The function returns:

- `ready_for_retirement_decision`;
- `projection_retirement_approved` — always `false` in Gate 8;
- latest evidence by bundle;
- exact blockers;
- rollback requirements.

No function in Gate 8 deletes or mutates the shared projection.

## Production baseline after migration

Automated evidence:

- automated database readiness: `true`;
- fallback closure readiness: `true`;
- rollback projection readiness: `true`;
- canonical/shared Users: `15 / 15`;
- canonical/shared Workflow: `15 / 15`;
- projection mismatches: `0`;
- observation span: approximately `63.19 minutes`;
- healthy observations: `5`;
- repairs: `0`.

Manual evidence:

- Streamlit Admin: missing;
- Streamlit Member: missing;
- Flutter Member: missing;
- passing bundles: `0 / 3`;
- persisted evidence rows: `0`.

Current blockers:

- `streamlit_admin_smoke_missing`;
- `streamlit_member_smoke_missing`;
- `flutter_member_smoke_missing`.

Current decision:

- ready for retirement decision: `false`;
- projection retirement approved: `false`.

## Rolled-back verification

A sequential transaction inserted temporary passing records for all three bundles and verified:

- each record was accepted;
- duplicate identical request replay was idempotent;
- all three bundles were recognized as recent production passes;
- `ready_for_retirement_decision` became `true`;
- `projection_retirement_approved` remained `false`;
- the rollback projection remained healthy;
- no automated blocker remained.

The transaction was rolled back. No temporary smoke evidence persisted.

A separate rolled-back contract-only probe set the caller role to `service_role` and verified:

- direct table `SELECT`: allowed;
- direct table `INSERT`: denied;
- the validated smoke evidence RPC: allowed and functional.

A first single-statement probe correctly demonstrated PostgreSQL statement-snapshot behavior: function-side inserts are not visible to other reads in the same SQL statement. The accepted verification therefore uses sequential statements within one transaction. This is a test-method detail, not a runtime defect.

## Admin Database Status

The page now displays:

- automated readiness;
- latest manual evidence by bundle;
- rollback-projection readiness;
- exact blockers;
- rollback requirements;
- a controlled manual evidence form.

The form requires an explicit confirmation that the selected checks were genuinely completed using the referenced build and environment.

The page contains no projection-retirement action.

## Rollback boundary

Before any future projection-retirement PR:

1. download and retain the complete current database backup;
2. record the deployed HealthyMe commit;
3. record the Flutter commit and APK/build reference;
4. keep the shared Users/Workflow projection unchanged until the retirement PR is merged and post-deployment checks pass;
5. treat any login, refresh, role-route, LAF, NSP or Submit-for-Review regression as an immediate rollback trigger.

## Safety boundary

Gate 8 does not:

- fabricate or seed manual smoke evidence;
- accept static tests or SQL probes as signed-in UI/device smoke;
- retire, freeze or delete shared Users/Workflow;
- alter User or Workflow business records;
- change Streamlit login, logout, refresh, routing or Session storage;
- change Flutter source, method names or payloads;
- remove LAF/NSP response payloads from shared state;
- change assessment, report, recommendation, package, schedule or email business logic;
- retire password hashes;
- redesign default-Admin recovery;
- approve or execute projection retirement.

## Next controlled gate

After PR merge:

1. deploy the Gate 8 Admin evidence form;
2. perform and record the real Streamlit Admin production smoke;
3. perform and record the real Streamlit Member production smoke;
4. perform and record the real Flutter build/device smoke;
5. recheck that all evidence is recent and tied to exact builds;
6. prepare a separate projection-retirement decision PR only when Gate 8 is fully ready.

Sessions, password retirement and default-Admin redesign remain separate batches.
