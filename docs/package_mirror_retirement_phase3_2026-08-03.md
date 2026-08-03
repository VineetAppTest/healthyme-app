# Package compatibility mirror retirement — Phase 3

Date: 2026-08-03  
Issue: #346  
Preceded by: merged PR #363 Package authority trace

## Decision

The dedicated Supabase Package structures remain the only runtime authority:

- `hm_packages` — Package catalogue masters;
- `hm_member_package_subscriptions` — member commercial snapshots and lifecycle state;
- `hm_package_usage_events` — allowance and consumption events;
- `hm_package_payments` — payment and refund ledger;
- `hm_package_subscription_events` — lifecycle event history.

The successful canonical write paths no longer refresh these shared-state collections:

- `healthyme_app_state_v1.data.packages`;
- `healthyme_app_state_v1.data.member_packages`.

The stored arrays are retained unchanged as rollback evidence during the observation period. They are not deleted, rewritten or treated as a fallback write authority.

## Runtime change

`components/package_hardening.py` no longer contains or calls `_sync_legacy_package_state()`.

The following operations now complete only through their existing canonical RPC and fresh canonical readers:

1. Package catalogue create or update — `hm_admin_save_package(...)`;
2. Member package assign, replace or renew — `hm_admin_assign_member_package(...)`;
3. Allowance or consumption adjustment — `hm_admin_adjust_package_sessions(...)`;
4. Subscription lifecycle, payment or refund update — `hm_admin_update_package_subscription(...)`.

Member messages, notifications and email delivery remain in their established shared-state communication contract. Removing Package mirror refreshes does not remove those communication writes.

## Read boundary retained

The normal HealthyMe bootstrap continues to redirect the legacy-named `components.db` Package APIs to canonical readers:

- `list_packages_v1024b14`;
- `create_package_v1024b14`;
- `update_package_v1024b14`;
- `get_member_active_package_v1024b14`;
- `list_member_packages_v1024b14`;
- `get_member_session_ledger_v1024b13`.

Admin Packages, Admin Scheduling and Member My Schedule therefore remain on canonical Package contracts.

The authenticated member boundary remains `hm_member_schedule_contract()` and continues to read the canonical subscription and metrics structures. Schedule rows remain in shared app-state and are outside this change.

## Production evidence retained

The pre-cutover read-only baseline was:

| Structure | Canonical rows | Retained app-state rows | Key-field mismatches |
|---|---:|---:|---:|
| Package catalogue | 3 | 3 | 0 |
| Member subscriptions | 3 | 3 | 0 |

This PR performs no production write. The two retained arrays remain at their existing values when the code is merged.

After a future canonical Package mutation, divergence from these frozen arrays is expected. The arrays must not be used for reconciliation, display, scheduling decisions or rollback without an explicit reviewed recovery procedure.

## Safety boundary

- No database migration or SQL change.
- No Package row, subscription, payment, lifecycle event or usage event mutation.
- No physical deletion of app-state arrays.
- No authentication, routing, RLS or RPC permission change.
- No scheduling authority change.
- No Package UI, label or form-flow change.
- No Flutter contract change.

## Permanent guards

Repository validation now requires:

- no `_sync_legacy_package_state` function or call;
- no Package mirror assignment in `components/package_hardening.py`;
- no new direct Package mirror reader outside the explicitly retained legacy/fallback inspection files;
- canonical Admin and member readers to remain wired through the Package contract;
- the authenticated member RPC boundary to remain present;
- any future Dart Package client to be added to the authority trace before merge.

## Post-deployment observation gate

Before any physical cleanup of `data.packages` or `data.member_packages`:

1. Open Admin Packages and confirm catalogue and subscriptions load from canonical tables.
2. Verify Package Library edit/create through an explicitly approved controlled test or normal business operation.
3. Verify assign/replace and lifecycle actions through fresh canonical reads.
4. Open Admin Scheduling and verify package capacity and historical-cost ledger.
5. Open Member My Schedule and verify Package Subscribed and Session Usage.
6. Verify `hm_member_schedule_contract()` for an authenticated member.
7. Confirm no application path reads the frozen arrays as current Package data.
8. Observe production before proposing physical array deletion.

Physical cleanup remains a later, separately approved data migration. It is not part of Phase 3.
