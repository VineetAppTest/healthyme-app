# Users canonical write cutover — Gate 3

Date: 2026-08-03  
Issue: #346  
Follows: merged PR #369, `Add Users and Workflow Gate 2 contract foundation`

## Decision

Gate 3 cuts over the **User write authority only**.

All User changes that flow through the shared Streamlit state now commit through one transactional database contract before the application accepts the save. The same transaction writes the canonical `hm_users` changes and the complete `healthyme_app_state_v1` compatibility state.

Workflow remains on its existing dedicated synchronization path. Sessions, password retirement, default-Admin redesign, Flutter source and shared User retirement remain separate gates.

## Clubbed actions

The following safe actions are delivered together:

1. transactional User-and-app-state database contract;
2. canonical User diff detection in `components/normalized_store.py`;
3. fail-closed User save selection in `components/storage_backend.py`;
4. removal of bulk User synchronization from the normal save path;
5. Workflow-only normalized synchronization retained temporarily;
6. direct service-role provisioning/linkage audit trigger;
7. canonical-User protection for manual local-to-Supabase pushes;
8. production verification, documentation, tests and CI guards.

## Production migration

Applied to Supabase project `arptwzvlugxrqtvbrmtl`:

- `users_gate3_transactional_state_commit`

Repository migration:

- `supabase/migrations/20260803161100_users_gate3_transactional_state_commit.sql`

## Transactional User-and-state contract

`hm_admin_commit_users_and_state(...)`:

- accepts one idempotent request ID;
- accepts the full compatibility state and only the changed canonical User patches;
- calls the Gate 2 `hm_admin_upsert_user(...)` contract for each changed User;
- commits all User events, request-ledger rows and the app-state projection in one transaction;
- replays an accepted request without repeating mutations;
- uses `SECURITY DEFINER`, an empty fixed `search_path` and fully qualified objects;
- is executable only by `service_role`;
- is not executable by `PUBLIC`, `anon` or `authenticated`.

The request ledger operation vocabulary now includes `user_state_commit`.

## Streamlit save selection

`components/storage_backend.py` compares the outgoing shared User projection with the previously loaded session projection.

When Users changed:

1. call `commit_users_and_state(...)`;
2. reject the save if the canonical contract fails;
3. do not report success through `data/db.json`;
4. cache the accepted complete state;
5. synchronize Workflow separately through the existing temporary path.

When Users did not change, the existing general app-state save continues. This avoids forcing every food log, schedule, message or journal save through an identity contract.

## Canonical adapter

`components/normalized_store.py` now:

- uses the service-role client for User mutations;
- compares the outgoing canonical User fields against `hm_users`;
- sends only changed/new User patches to the transactional contract;
- omits `auth_user_id` and `auth_migrated_at` unless they are explicitly present, preventing an older shared projection from clearing canonical Auth linkage;
- ignores shared-only compatibility fields such as older Auth0 metadata;
- retains `sync_workflow_to_normalized(...)` until the Workflow cutover;
- routes the old manual Users/Workflow sync action through the new User contract plus the temporary Workflow sync.

## Direct provisioning audit

Some Supabase Auth provisioning helpers already write directly to canonical `hm_users` rather than shared state.

`hm_users_capture_direct_event` records material direct `service_role` inserts or updates in `hm_user_events` with:

- source `service_role_direct`;
- password-redacted snapshots;
- exact changed fields;
- Gate 3 metadata.

Writes performed through the security-definer User contract run as the function owner and therefore do not generate a duplicate direct-write event.

## Local push protection

`push_local_data_to_supabase()` no longer allows Users from `data/db.json` to replace the canonical identity projection. It first loads canonical Users and inserts those Users into the outgoing compatibility state. Failure to load canonical Users blocks the push.

## Production verification

After migration and rolled-back functional probes:

- canonical Users: `15`;
- shared User rows: `15`;
- missing shared identities: `0`;
- Workflow rows: `15`;
- Workflow status mismatches: `0`;
- persisted User events: `0`;
- persisted Workflow events: `0`;
- persisted request-ledger rows: `0`;
- Gate 3 contract: service-role executable only;
- Gate 3 contract: fixed empty `search_path`;
- direct User audit trigger: present.

A rolled-back service-role contract probe returned `ok=true` and `changed_user_count=0` for an unchanged User.

A separate rolled-back direct service-role User update appended exactly one `service_role_direct` event. The transaction was rolled back and no User or event remained changed.

## Safety boundary

Gate 3 does not:

- cut over Workflow writers;
- retire the shared User projection;
- change login, logout, refresh, routing or durable sessions;
- retire password hashes;
- remove or redesign default-Admin recovery;
- change Admin User Manager layout or Auth0-first provisioning order;
- change Flutter source, method names or payloads;
- delete or rewrite existing User or Workflow rows;
- backfill synthetic User events.

## Next controlled gate

After merge and deployment observation, Gate 4 may cut over **Workflow writes only** through `hm_admin_upsert_workflow(...)` while preserving assessment-instance, notification and final-report side effects. User and Workflow read cutover remains later.
