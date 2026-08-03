# Workflow canonical write cutover — Gate 4

Date: 2026-08-03  
Issue: #346  
Follows: merged PR #370, `Cut User writes over to canonical transactional authority`

## Decision

Gate 4 cuts over the **Streamlit/shared-state Workflow write authority**.

Whenever a save changes either the shared User projection or the shared Workflow projection, HealthyMe now commits:

1. changed canonical Users;
2. changed canonical Workflow rows; and
3. the complete `healthyme_app_state_v1` compatibility state

through one database transaction.

This combined contract is required for operations such as member creation, where a new `hm_users` row and its new `hm_workflow` row must either both succeed or both fail.

## Clubbed actions

The following safe actions are delivered together:

1. combined User + Workflow + state transactional contract;
2. canonical Workflow diff adapter;
3. fail-closed Workflow save selection;
4. removal of direct bulk Workflow upsert from runtime compatibility helpers;
5. residual direct service-role Workflow audit trigger;
6. canonical Workflow protection for local-to-Supabase pushes;
7. preservation of complete shared-state side effects;
8. production verification, documentation, tests and CI guards.

## Production migration

Applied to Supabase project `arptwzvlugxrqtvbrmtl`:

- `workflow_gate4_identity_state_commit`

Repository migration:

- `supabase/migrations/20260803165000_workflow_gate4_identity_state_commit.sql`

## Combined identity-and-state contract

`hm_admin_commit_identity_and_state(...)`:

- accepts one idempotent parent request ID;
- accepts the complete compatibility state;
- accepts only changed/new canonical User patches;
- accepts only changed/new canonical Workflow patches;
- commits Users before Workflow so new-member foreign-key dependencies remain valid;
- calls the Gate 2 audited User and Workflow contracts;
- commits all child events, request-ledger rows and the app-state projection in one transaction;
- replays an accepted parent request without repeating child mutations;
- uses `SECURITY DEFINER`, an empty fixed `search_path` and fully qualified objects;
- is executable only by `service_role`;
- is not executable by `PUBLIC`, `anon` or `authenticated`.

The request-ledger operation vocabulary now includes `identity_state_commit`.

## Workflow projection contract

The canonical Workflow fields remain:

- `laf_completed`;
- `nsp1_completed`;
- `nsp2_completed`;
- `submitted_for_review`;
- `admin_completed`;
- `final_report_ready`.

`workflow_status` remains database-owned and is derived by the existing canonical status trigger.

Shared-only fields remain in the compatibility projection, including Body-Mind flags and any other temporary UI state. They are not sent as canonical Workflow patch fields.

The outgoing compatibility state keeps one normalized Workflow projection for every known User. This preserves the existing one-User/one-Workflow baseline, including default rows created alongside new accounts.

## Save selection

`components/storage_backend.py` now compares both outgoing identity projections with the previously loaded session projection.

When Users or Workflow changed:

1. call `commit_identity_and_state(...)`;
2. reject the complete save if the canonical contract fails;
3. do not report success through `data/db.json`;
4. cache only the accepted complete state.

When neither projection changed, ordinary journal, message, schedule and other state saves continue through the lightweight app-state path.

Local fallback remains available only for saves that do not change Users or Workflow.

## Preserved application side effects

The combined contract writes the complete compatibility state, not only the Workflow object. Existing business functions therefore keep their current side effects in the same accepted state payload, including:

- first-submission `admin_review_required` notifications;
- reassessment instance submission and status updates;
- admin assessment and final-report records;
- assessment-instance finalization fields;
- Body-Mind request and unlock flags;
- explicit Body-Mind access markers;
- audit and message collections.

Gate 4 does not move these collections into new tables and does not reinterpret their business rules.

## Compatibility helpers

`sync_workflow_to_normalized(...)` and `sync_users_workflow_to_normalized(...)` remain as compatibility names, but both now route through the combined transactional contract.

No runtime Python path performs a direct bulk `.table("hm_workflow").upsert(...)` after Gate 4.

## Direct service-role audit

`hm_workflow_capture_direct_event` records any remaining direct `service_role` insert or update against `hm_workflow` with:

- source `service_role_direct`;
- canonical before/after snapshots;
- exact changed fields;
- Gate 4 metadata.

Writes through the security-definer Workflow contract already create their own event and do not produce a duplicate direct-write event.

Existing Flutter Workflow functions are unchanged by this gate.

## Local push protection

`push_local_data_to_supabase()` now loads and preserves both canonical Users and canonical Workflow before pushing non-identity local state.

A local file cannot replace either canonical identity projection.

## Production verification

After migration and rolled-back functional probes:

- canonical Users: `15`;
- canonical Workflow rows: `15`;
- shared Workflow rows: `15`;
- missing shared Workflow identities: `0`;
- missing canonical Workflow identities: `0`;
- Workflow field mismatches: `0`;
- Workflow status mismatches: `0`;
- persisted User events: `0`;
- persisted Workflow events: `0`;
- persisted request-ledger rows: `0`;
- combined contract: service-role executable only;
- direct Workflow audit trigger: present.

A rolled-back combined creation probe verified:

- one new User row;
- one new Workflow row;
- both shared-state projections;
- one User event;
- one Workflow event;
- three request-ledger rows: User child, Workflow child and parent;
- idempotent parent replay.

A separate rolled-back direct service-role Workflow update produced exactly one `service_role_direct` Workflow event with changed fields.

No probe row, state change, event or request row persisted.

## Safety boundary

Gate 4 does not:

- retire the shared User or Workflow projections;
- change Workflow reads or remove Flutter shared-state fallback reads;
- change existing Flutter Workflow functions, public method names or payloads;
- change login, logout, refresh, routing or durable sessions;
- retire password hashes;
- remove or redesign default-Admin recovery;
- change Demo Mode behavior;
- delete or rewrite existing User or Workflow rows;
- backfill synthetic Workflow events;
- move notifications, assessment instances, reports or Body-Mind state into new tables.

## Next controlled gate

After merge and deployment observation, the next safe combined batch is **read-authority hardening and compatibility projection observation**:

1. prove all Streamlit User and Workflow readers are canonical-overlay consumers;
2. measure whether any runtime depends on stale shared projections;
3. add projection drift telemetry and repair tooling;
4. keep Session migration, password retirement and default-Admin redesign separate.

Shared projection retirement remains later and requires its own observation gate.
