# Canonical identity read and projection observation — Gates 5A + 6A

Date: 2026-08-03  
Issue: #346  
Follows: merged PR #371, `Cut Workflow writes over to canonical transactional authority`

## Decision

This batch clubs the safe parts of canonical read cutover and observation:

1. fail-closed Streamlit User and Workflow reads;
2. canonical-only Admin role resolution;
3. canonical/shared projection drift telemetry;
4. explicit dry-run observation;
5. explicit service-role projection repair;
6. permanent repository guards and production evidence.

It does not retire the compatibility projection or change sessions, passwords, default-Admin recovery, Flutter public contracts or business pages outside Database Status.

## Canonical read authority

`hm_users` and `hm_workflow` remain the only accepted live identity and Workflow authority.

`components/storage_backend.py` continues loading the general application-state document for non-identity domains. It then overlays Users and Workflow from the canonical repository.

When the canonical overlay succeeds:

- canonical User and Workflow fields replace the corresponding shared fields in memory;
- shared-only compatibility metadata is preserved for canonical identities;
- orphan shared identities are not retained;
- the session cache receives only the overlaid identity projection.

When the canonical overlay fails:

- `db["users"]` becomes an empty array;
- `db["workflow"]` becomes an empty object;
- local/shared identity is not returned to callers;
- storage status records `identity_authority_available=false` and `identity_fail_closed=true`;
- non-identity state may remain available, but identity-dependent operations cannot authorize against it.

When Supabase is not configured, local Users and Workflow are removed from the returned compatibility state. Local identity fallback is not accepted.

## Role resolution

`components/admin_role_model.py` no longer imports or calls `components.db.find_user_by_email()`.

Role resolution now uses only:

1. `hm_users.auth_user_id` through the service-role client;
2. canonical `hm_users.email` through the service-role client;
3. the canonical fast `hm_users` lookup.

A canonical lookup error returns an unavailable result. It does not fall back to shared JSON, `data/db.json`, `data/db_sample.json` or a stale session User snapshot.

Existing native identity, routing, login, refresh and logout components are unchanged.

## Projection snapshot

Production migration:

- `identity_projection_observation_gate5a6a`

Repository migration:

- `supabase/migrations/20260803172500_identity_projection_observation_gate5a6a.sql`

`hm_identity_projection_snapshot()` is a read-only, service-role-only function. It reports:

- canonical and shared User counts;
- canonical and shared Workflow counts;
- canonical identities missing from the shared projection;
- orphan shared identities;
- duplicate shared User identities;
- User field mismatches;
- Workflow field mismatches;
- an overall `healthy` result.

User comparison covers the seven shared canonical fields plus the stable ID. Canonical-only Auth linkage fields are intentionally excluded from shared-projection parity.

Workflow comparison covers the six lifecycle fields plus database-derived `workflow_status`.

## Observation history

`hm_identity_projection_observations` stores append-only observation evidence:

- request ID;
- timestamp and source;
- actor context;
- dry-run or repair intent;
- healthy-before and healthy-after results;
- before and after snapshots;
- response payload and metadata.

The table has RLS enabled. `PUBLIC`, `anon` and `authenticated` have no access. The service role has the controlled observation access.

## Explicit repair

`hm_admin_observe_identity_projection(...)` is service-role only, idempotent and defaults to observation without repair.

When `p_apply_repair=false`:

- no application data is changed;
- one observation record is appended;
- drift evidence is returned.

When `p_apply_repair=true` and drift exists:

1. lock the application-state row;
2. rebuild shared Users from canonical `hm_users`;
3. rebuild shared Workflow from canonical `hm_workflow`;
4. preserve shared-only fields for identities that still exist canonically;
5. remove duplicate and orphan shared identities;
6. update only the shared projection;
7. capture the after snapshot and observation evidence.

The repair contract never changes canonical Users or Workflow.

When the projection is already healthy, explicit repair is a no-op and the observation records that no repair was required.

No automatic repair runs during application load or save.

## Admin Database Status

`pages/28_Admin_Database_Status.py` now shows:

- application-state connection;
- canonical identity authority availability;
- fail-closed status;
- projection health;
- detailed drift snapshot;
- `Record Projection Observation`;
- an explicitly confirmed `Repair Shared Projection from Canonical` action.

The former bulk `Migrate Users + Workflow to Normalized Tables` action is retired. It is no longer valid after canonical write cutover.

The local push action is relabelled as a non-identity transfer and continues preserving canonical Users and Workflow.

## Production baseline

Immediately after migration:

- canonical Users: `15`;
- shared Users: `15`;
- canonical Workflow rows: `15`;
- shared Workflow rows: `15`;
- missing shared User IDs: `0`;
- orphan shared User IDs: `0`;
- duplicate shared User IDs: `0`;
- User mismatches: `0`;
- missing shared Workflow IDs: `0`;
- orphan shared Workflow IDs: `0`;
- Workflow mismatches: `0`;
- snapshot health: `true`.

## Controlled probes

Jarvis must verify in rolled-back transactions:

1. a deliberately corrupted shared User and Workflow projection is detected;
2. dry-run observation leaves the corrupted projection unchanged;
3. explicit repair restores canonical fields;
4. shared-only fields remain present after repair;
5. duplicate and orphan shared identities are removed;
6. canonical Users and Workflow remain unchanged;
7. replaying the same request ID does not repeat the repair or observation insert.

A real healthy baseline observation may be retained as operational evidence. Synthetic drift probes must roll back completely.

## Repository guards

The focused CI gate verifies:

- local/shared identity is stripped when canonical reads fail;
- canonical overlay success remains supported;
- Admin role resolution contains no local User fallback;
- projection functions and grants are service-role only;
- repair is explicit and defaults to dry-run;
- repair preserves shared-only fields and never writes canonical tables;
- the obsolete bulk migration button is removed;
- existing Gate 3 and Gate 4 write protections remain intact;
- session, routing and Flutter boundaries remain unchanged.

## Safety boundary

This batch does not:

- stop or freeze the compatibility projection;
- remove shared User or Workflow data;
- automatically repair drift;
- remove Flutter shared Workflow fallback reads;
- change Flutter function names, parameters or payloads;
- change login, logout, refresh or routing;
- migrate or delete any session representation;
- retire local password logic or password fields;
- remove or redesign runtime default-Admin recovery;
- change assessment, report, recommendation, schedule or email business logic;
- delete canonical User or Workflow rows;
- rewrite historical User or Workflow events.

## Next controlled gate

After an accepted observation window, the next combined batch can prepare projection retirement evidence:

1. review accumulated healthy observations;
2. run Admin and Member route smoke tests;
3. run Flutter login, LAF, NSP and dashboard smoke tests;
4. prove no direct shared-array reader or writer is required;
5. freeze the last shared projection as rollback evidence;
6. disable projection refresh only in a separately approved PR.

Sessions, password retirement and default-Admin redesign remain separate workstreams.
