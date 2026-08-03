# Package post-deployment observation — Phase 4

Date: 2026-08-03  
Issue: #346  
Preceded by: merged PR #364 (`d5cd2fd4a324665e9e294e15300ecd75e3bf7408`)

## Purpose

Record the first production observation after Package compatibility mirror writes were retired.

This phase performs read-only verification and adds permanent contract coverage. It does not create, edit, assign, replace, pause, resume, cancel, complete, refund or delete a Package or subscription.

## Merged runtime boundary

PR #364 removed `_sync_legacy_package_state()` and the four post-write mirror refresh calls from `components/package_hardening.py`.

The live authorities are:

- `hm_packages` for Package catalogue masters;
- `hm_member_package_subscriptions` for member commercial and lifecycle snapshots;
- `hm_package_usage_events` for allowance and consumption history;
- `hm_package_payments` for payment/refund history;
- `hm_package_subscription_events` for lifecycle history;
- `hm_member_schedule_contract()` for the authenticated member Package/Schedule payload.

The retained arrays below remain rollback evidence only:

- `healthyme_app_state_v1.data.packages`;
- `healthyme_app_state_v1.data.member_packages`.

They are not refreshed by canonical Package writes and must not be used as current Package data.

## Automated production observation

Read-only verification after merge returned:

| Check | Result |
|---|---:|
| Canonical Package masters | 3 |
| Retained Package rows | 3 |
| Package identities match | Yes |
| Canonical subscriptions | 3 |
| Retained subscription rows | 3 |
| Subscription identities match | Yes |
| Active or paused subscriptions | 2 |
| Usage events | 2 |
| Payment events | 0 |
| Lifecycle events | 0 |

No production row was inserted, updated or deleted during this observation.

## Authenticated member RPC observation

A read-only authenticated-context call to `hm_member_schedule_contract()` for an active member returned:

- no error;
- a resolved member identity;
- a matched current Package;
- a non-empty Package object;
- Package metrics;
- upcoming sessions as an array;
- session ledger as an array;
- Package history as an array;
- contract version `package-hardening-123-v1`.

No member email, name, assessment answer or clinical content is recorded in this document.

## Streamlit contract observation

Repository contracts confirm:

### Admin Packages

- `pages/41_Admin_Packages.py` renders `components/package_hardening_ui.py`;
- catalogue and subscription reads use the canonical Package adapter;
- create/update/assignment/lifecycle operations call canonical service-role RPCs;
- no current runtime read or write uses the retained Package arrays.

### Admin Scheduling

- `components/admin_scheduling_consolidated.py` uses `schedule_capacity()` and `member_session_ledger()`;
- Package capacity, historical subscription identity and historical cost remain canonical;
- schedule rows remain in the shared schedule collection and are outside Package mirror retirement.

### Member My Schedule

- `pages/33_My_Schedule.py` installs the hardened Package Schedule UI;
- Package Subscribed and Session Usage read the canonical Package contract;
- the authenticated Flutter/member boundary remains `hm_member_schedule_contract()`.

## Manual authenticated visual smoke

The following visual checks require a signed-in browser session and are not claimed as executed by this automated observation:

1. Admin Packages loads Package Library, Current Subscriptions and History & Audit.
2. Admin Scheduling shows current Package capacity and Session Ledger.
3. Member My Schedule shows Package Subscribed and Session Usage.
4. A future explicitly approved normal Package operation is followed by a fresh canonical read.

The automated evidence is sufficient to confirm the authority cutover and retained-array preservation. It does not replace visual acceptance of page layout, widget behaviour or signed-in routing.

## Rollback and cleanup boundary

Physical deletion of the retained arrays is not included.

Deletion must remain a separate, explicitly approved migration after:

- authenticated visual smoke passes;
- at least one approved canonical Package operation is observed through a fresh canonical read;
- no legacy reader is found during the observation window;
- a final pre-delete export/checksum is recorded.

## Issue #346 next batch

After this observation PR is merged, Batch 1 is considered code-complete but remains in observation until the manual signed-in checks are recorded.

The next architecture work may begin as a read-only trace for Batch 2 — Users and Workflow. It must not change authentication, role resolution, login persistence, local fallback or member workflow writes until every reader/writer and rollback dependency is mapped.
