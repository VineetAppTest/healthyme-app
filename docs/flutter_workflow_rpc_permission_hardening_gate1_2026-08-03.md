# Flutter Workflow RPC permission hardening — Gate 1

Date: 2026-08-03  
Issue: #346  
Follows: merged PR #367, `Define Users and Workflow single-authority target design`

## Decision

Gate 1 is implemented before any broader User or Workflow authority cutover.

The public Flutter RPC signatures remain unchanged. This gate changes only function identity resolution and execution privileges. It does not retire shared Workflow projection, migrate User or Workflow rows, change Streamlit authentication, alter sessions, or modify Flutter source code.

## Production migrations

Applied to Supabase project `arptwzvlugxrqtvbrmtl`:

1. `20260803092801_harden_flutter_workflow_rpc_permissions`
2. `20260803093059_restrict_flutter_member_rpc_execution`

Repository migration files:

- `supabase/migrations/20260803144800_harden_flutter_workflow_rpc_permissions.sql`
- `supabase/migrations/20260803145200_restrict_flutter_member_rpc_execution.sql`

## Identity resolution hardening

`hm_flutter_current_member_id()` now:

- requires a Supabase Auth identity;
- prefers exact `hm_users.auth_user_id = auth.uid()` linkage;
- permits email fallback only when `hm_users.auth_user_id` is still null;
- rejects no-match and duplicate-match conditions;
- uses `SECURITY DEFINER` with an empty fixed `search_path` and fully qualified objects;
- cannot be executed by `anon`;
- remains executable by `authenticated` for current-member self-resolution.

The earlier unconditional email alternative for an already-linked row is removed. A row linked to a different Auth identity can no longer be selected merely because its email matches the JWT email.

## Workflow helper hardening

`hm_flutter_upsert_nsp_workflow(text, boolean, boolean, boolean)` keeps its existing signature for the outer Flutter RPCs but now:

1. resolves the current authenticated member inside the function;
2. compares that identity with the supplied member ID;
3. raises SQLSTATE `42501` before any read or write when the IDs differ;
4. writes only the resolved current member's canonical `hm_workflow` row;
5. preserves the existing Workflow status calculation and Admin-owned fields;
6. uses an empty fixed `search_path` and fully qualified objects.

Direct execution is removed from `PUBLIC`, `anon` and `authenticated`. The authenticated outer Flutter RPCs continue to call this internal helper as their function owner.

## Flutter RPC execution boundary

Anonymous/default execution is removed from:

- `hm_flutter_link_current_member_auth_user()`;
- `hm_flutter_get_nsp()`;
- `hm_flutter_save_nsp1_draft(jsonb)`;
- `hm_flutter_submit_nsp1(jsonb)`;
- `hm_flutter_save_nsp2_draft(jsonb)`;
- `hm_flutter_submit_nsp2(jsonb)`;
- `hm_flutter_submit_assessment_review()`.

Each remains executable by `authenticated`, preserving the current Flutter member API.

## Production verification

Read-only and transaction-rolled-back verification confirmed:

- `anon` execute: false for all nine Gate 1 functions;
- `authenticated` execute: true for the identity helper and seven public member RPCs;
- `authenticated` execute: false for the internal Workflow helper;
- authenticated current-member resolution returns the expected HealthyMe member;
- authenticated `hm_flutter_get_nsp()` returns the current member, Workflow object, NSP Page 1 object and NSP Page 2 object;
- the internal helper succeeds for the resolved current member inside a rolled-back transaction;
- a different member ID is rejected before mutation;
- all six existing public NSP RPCs retain authenticated access;
- production row counts remain 15 Users and 15 Workflow rows;
- no User, Workflow, assessment, shared-state or session row was migrated or deleted.

## Advisor review

Supabase security and performance advisors were run after the DDL changes.

Gate 1 removes the identified anonymous execution exposure from its Flutter identity and NSP scope. Remaining notices relate to pre-existing items outside this gate, including other member RPC grants, duplicated or non-optimised RLS policies, mutable search paths on older helper functions, and duplicate/unused indexes. Those items must be handled through separate controlled batches rather than bundled into this permission change.

Reference guidance:

- https://supabase.com/docs/guides/database/functions
- https://supabase.com/docs/guides/api/securing-your-api

## Safety boundary

This gate does not:

- change Flutter method names or payloads;
- remove shared Workflow fallback or projection;
- change LAF/NSP response persistence;
- change Streamlit login, refresh, logout or routing;
- change RLS policies or table grants;
- add or remove User, Workflow, assessment or session rows;
- start the User or Workflow authority cutover.

## Next controlled gate

After this PR is merged, Gate 2 may create the canonical contract foundation:

1. one database-owned Workflow status derivation contract;
2. append-only User and Workflow material-change events;
3. transactional server-side User and Admin Workflow operations;
4. idempotency and fresh read-after-write responses;
5. no Streamlit writer cutover until those foundations are separately validated.
