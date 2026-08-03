# Users and Workflow canonical contract foundation — Gate 2

Date: 2026-08-03  
Issue: #346  
Follows: merged PR #368, `Harden Flutter Workflow RPC permissions`

## Decision

The safe Gate 2 foundation actions are combined in one change set:

1. one database-owned Workflow status derivation contract;
2. table triggers that prevent stored Workflow status drift;
3. append-only User and Workflow material-change events;
4. an append-only idempotency response ledger;
5. transactional service-role-only User and Workflow write contracts;
6. fresh canonical records returned from each accepted write;
7. permanent repository and CI guards.

This gate establishes contracts only. Streamlit writers are not cut over, the shared `users` and `workflow` projections are not retired, and Session migration remains separate.

## Production migrations

Applied to Supabase project `arptwzvlugxrqtvbrmtl`:

1. `20260803095743_users_workflow_gate2_status_contract`
2. `20260803095808_users_workflow_gate2_audit_tables`
3. `20260803100039_users_workflow_gate2_user_contract`
4. `20260803100249_users_workflow_gate2_workflow_contract`

Repository migration files:

- `supabase/migrations/20260803152500_users_workflow_gate2_status_contract.sql`
- `supabase/migrations/20260803152600_users_workflow_gate2_audit_tables.sql`
- `supabase/migrations/20260803152700_users_workflow_gate2_user_contract.sql`
- `supabase/migrations/20260803152800_users_workflow_gate2_workflow_contract.sql`

## Canonical Workflow status

`hm_derive_workflow_status(...)` is now the database-owned derivation:

1. `finalized` when `final_report_ready` is true;
2. `admin_completed` when `admin_completed` is true;
3. `submitted` when `submitted_for_review` is true;
4. `in_progress` when LAF, NSP Page 1 or NSP Page 2 is complete;
5. `not_started` otherwise.

Two `hm_workflow` triggers apply this function before insert and before any relevant update, including attempts to write `workflow_status` directly. A caller can no longer persist a status that contradicts the six lifecycle booleans.

The existing internal Flutter status helpers now delegate to the same function. Their direct execution is removed from `PUBLIC`, `anon` and `authenticated`, while the established authenticated outer Flutter RPCs continue to work through their security-definer owner context.

## Append-only foundation

### `hm_domain_write_requests`

Stores the accepted response for each request ID. This provides deterministic replay without repeating the mutation. A request ID cannot be reused for another operation or entity.

### `hm_user_events`

Stores User `created` and `updated` material-change events with actor, source, changed fields, before/after snapshots, metadata and timestamp.

Password hashes are deliberately excluded from event snapshots and returned User records. `password_hash` may still appear in `changed_fields` so the audit records that sensitive material changed without storing the value.

### `hm_workflow_events`

Stores Workflow `created` and `updated` material-change events. The derived `workflow_status` is included whenever it changes.

All three tables:

- have RLS enabled and forced;
- have no `anon` or `authenticated` table privileges;
- expose read access only to `service_role`;
- reject UPDATE and DELETE through append-only triggers;
- contain no backfilled history.

## Transactional contracts

### `hm_admin_upsert_user(...)`

- validates request, entity, patch and metadata;
- rejects unsupported fields;
- serialises duplicate request IDs with a transaction advisory lock;
- creates or updates one canonical `hm_users` row;
- skips no-op writes and preserves `updated_at`;
- appends one event only for a material change;
- stores the response for idempotent replay;
- returns the fresh canonical User without `password_hash`;
- is executable only by `service_role`.

### `hm_admin_upsert_workflow(...)`

- accepts only the six Workflow lifecycle booleans;
- never accepts caller-supplied `workflow_status`;
- rejects a missing User;
- serialises duplicate request IDs;
- creates or updates one canonical `hm_workflow` row;
- skips no-op writes and preserves `updated_at`;
- derives status through the canonical trigger;
- appends one event only for a material change;
- stores the response for idempotent replay;
- returns the fresh canonical Workflow row;
- is executable only by `service_role`.

Both contracts use `SECURITY DEFINER`, a fixed empty `search_path`, fully qualified database objects and explicit function grants.

## Production verification

Schema and permission verification confirmed:

- Users: `15`;
- Workflow rows: `15`;
- Workflow status mismatches: `0`;
- persisted write requests after tests: `0`;
- persisted User events after tests: `0`;
- persisted Workflow events after tests: `0`;
- `anon` and `authenticated` cannot execute either Admin contract;
- `service_role` can execute both Admin contracts;
- audit tables are forced-RLS and service-role-read-only.

A transaction-rolled-back functional exercise confirmed:

- real User change: one event;
- User replay: no second mutation;
- User no-op: no event and unchanged `updated_at`;
- User snapshots: no password hash;
- real Workflow change: one event;
- Workflow replay: no second mutation;
- Workflow no-op: no event and unchanged `updated_at`;
- stored Workflow status matches the canonical function;
- append-only UPDATE is rejected;
- cross-operation request-ID reuse is rejected.

The authenticated `hm_flutter_get_nsp()` contract was retested after the internal-helper changes and still returned a resolved member plus Workflow, NSP Page 1 and NSP Page 2 objects.

## Advisor review

Supabase security and performance advisors were run after all four DDL migrations.

The new Admin contracts have fixed search paths and no public/client execution. The three new service-only tables are intentionally forced-RLS with no client policies, so the advisor reports informational `RLS enabled, no policy` notices. Their explicit grants confirm `anon` and `authenticated` have no table access.

Remaining security and performance notices concern older functions, existing RLS policy duplication/init-plan optimisation, existing duplicate indexes and unrelated member RPC grants. They are outside this focused foundation and must be handled in separate controlled batches.

## Safety boundary

Gate 2 does not:

- change Streamlit User or Workflow writers;
- make the new Admin contracts an active application path;
- retire or freeze shared-state Users or Workflow;
- change login, refresh, logout, routing or durable sessions;
- remove legacy password fields or default-Admin recovery;
- change Flutter method names, payloads or authenticated outer RPC grants;
- delete or rewrite existing User or Workflow rows;
- backfill synthetic audit history.

## Next controlled gate

Gate 3 can cut over **User writes only** after tracing each `components/db.py` User operation into the new User contract. Workflow writer cutover remains a later independent gate so authentication and assessment progression are not changed together.
