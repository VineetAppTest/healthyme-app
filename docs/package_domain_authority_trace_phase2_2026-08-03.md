# Package domain authority trace — Phase 2

Date: 2026-08-03  
Issue: #346  
Preceded by: merged PR #362 and completed Content Repository issue #347

## Decision

The dedicated Supabase Package structures are the accepted runtime authority:

- `hm_packages` — Package catalogue masters;
- `hm_member_package_subscriptions` — immutable member commercial snapshots and lifecycle state;
- `hm_package_usage_events` — allowance and consumption events;
- `hm_package_payments` — payment/refund ledger;
- `hm_package_subscription_events` — subscription lifecycle history.

The `healthyme_app_state_v1.data.packages` and `healthyme_app_state_v1.data.member_packages` collections are compatibility mirrors only. They are not the accepted write authority, but they are still rewritten after successful canonical Admin Package operations by `_sync_legacy_package_state()`.

This phase changes no runtime, table, RPC, data or UI behaviour. It freezes the current reader/writer map before any compatibility mirror is retired.

## Production baseline

Read-only verification on 2026-08-03 returned:

| Structure | Dedicated rows | App-state mirror rows | Missing identities | Key-field mismatches |
|---|---:|---:|---:|---:|
| Package catalogue | 3 | 3 | 0 | 0 |
| Member subscriptions | 3 | 3 | 0 | 0 |

Event baseline:

- Package usage events: 2
- Package payments: 0
- Package subscription lifecycle events: 0

The zero-mismatch result means the current mirror can be retired through a controlled code change without a data reconciliation migration, provided the reader trace and deployment smoke gate remain clean.

## Canonical write map

### Package catalogue create and update

1. `pages/41_Admin_Packages.py`
2. `components/package_hardening_ui.py`
3. `components.package_hardening.save_package()`
4. service-role RPC `hm_admin_save_package(...)`
5. canonical write to `hm_packages`
6. fresh RPC result returned to Streamlit
7. `_sync_legacy_package_state()` rewrites both Package mirrors inside `healthyme_app_state`

Package Library edits apply only to future subscriptions. Existing member subscriptions retain their saved package name, session allowance, price, currency and inclusions snapshot.

### Assign, replace or renew a member subscription

1. `components/package_hardening_ui.py`
2. `assign_or_replace_member_package()`
3. service-role RPC `hm_admin_assign_member_package(...)`
4. canonical subscription and event logic
5. `_sync_legacy_package_state()` refreshes both mirrors
6. member message/notification/email state is appended through the existing shared-state communication contract

### Subscription adjustment and lifecycle update

- `adjust_subscription_sessions()` calls `hm_admin_adjust_package_sessions(...)` and then refreshes the mirrors.
- `update_subscription()` calls `hm_admin_update_package_subscription(...)`, refreshes the mirrors and queues the relevant member communication.
- Payment, refund, pause, resume, extension, cancellation and completion fields remain canonical in the dedicated subscription/payment/event structures.

## Canonical read map

### Admin Packages

`pages/41_Admin_Packages.py` renders `components/package_hardening_ui.py`.

The page reads:

- `hm_packages` through `list_packages()`;
- `hm_member_package_subscriptions` through `list_member_subscriptions()`;
- metrics through `hm_package_subscription_metrics(...)`;
- lifecycle events through `hm_package_subscription_events`;
- payments through `hm_package_payments`;
- usage through `hm_package_usage_events`.

`components/admin_performance_optimization.py` replaces the subscription list only with a request-local lazy-metrics reader. It still queries the canonical subscription table and canonical metrics RPC.

### Admin Scheduling

`pages/32_Admin_Scheduling.py` renders `components/admin_scheduling_consolidated.py`.

Package reads are canonical:

- `schedule_capacity()` reads `hm_package_member_summary(...)`;
- `member_session_ledger()` reads canonical package metrics and historical subscription identity/cost;
- schedule rows themselves remain inside `healthyme_app_state.data.schedules` and are outside this Package mirror retirement step.

Schedule creation and status changes are wrapped by `components/package_hardening_bootstrap.py` so package capacity is checked before creation and a canonical usage event is recorded when a session becomes consumed.

### Member My Schedule — Streamlit

`pages/33_My_Schedule.py` installs `components/package_hardening_schedule_ui.py`.

The visible Package Subscribed and Session Usage sections therefore read:

- current subscription and metrics from the canonical Package contract;
- historical subscription identity and price from the canonical helpers;
- schedule rows from the existing shared schedule collection.

The older renderers inside `components/schedule_timezone_ui.py` call the legacy-named `components.db` Package APIs, but the normal HealthyMe bootstrap replaces those APIs with canonical functions before page rendering.

### Legacy-named `components.db` API

`components/package_hardening_bootstrap.py` installs canonical implementations for:

- `list_packages_v1024b14`;
- `create_package_v1024b14`;
- `update_package_v1024b14`;
- `get_member_active_package_v1024b14`;
- `list_member_packages_v1024b14`;
- `get_member_session_ledger_v1024b13`.

The original app-state implementations remain in `components/db.py` as compatibility code, but they are replaced during the standard `components` package bootstrap used by the Streamlit application.

## Flutter boundary

The repository-owned Flutter Package boundary is the authenticated member-scoped RPC:

`hm_member_schedule_contract()`

It returns:

- current subscription snapshot;
- package metrics;
- upcoming sessions;
- session ledger;
- package history;
- informational inclusions;
- resolved member identity.

The function reads `hm_member_package_subscriptions` and Package metric helpers directly. It still reads schedule rows from `healthyme_app_state.data.schedules` because scheduling has not yet been normalised.

No Dart Package client implementation was identified in this repository during this trace. Therefore the controlled source-of-truth boundary available here is the SQL RPC contract, not a Flutter UI/client implementation. When Flutter source is added or linked, its RPC invocation and payload mapping must be added to this authority map before any Package contract change.

## Permissions boundary

Production verification confirms:

- Admin Package write and helper RPCs are executable by `service_role` only.
- `anon` and `authenticated` cannot execute Admin Package RPCs.
- `hm_member_schedule_contract()` is executable by `authenticated` and `service_role`, but not by `anon`.
- Package tables retain RLS and are not exposed directly to member clients.

## Remaining dual-write and risk points

### 1. Compatibility mirror rewrite

`_sync_legacy_package_state()` rewrites all Package masters and subscriptions into the shared JSON state after every successful canonical Admin write.

The mirror function catches every exception. A canonical write can therefore succeed while the mirror silently becomes stale. The current production parity is clean, but the mirror is not an independently verified authority.

### 2. Silent usage-event failure

`record_schedule_consumption_event()` catches write exceptions. Schedule status can therefore change even when the immutable usage event was not recorded. This is a separate reliability hardening item and should not be bundled into mirror retirement.

### 3. Schedule authority remains shared JSON

Package metrics and historical cost helpers still derive consumed and reserved sessions from schedules stored in `healthyme_app_state`. Removing Package mirrors does not remove or migrate schedules.

### 4. Local fallback

The shared storage backend can fall back to local JSON when Supabase is unavailable. Canonical Package operations require the service-role Supabase client and do not have a valid local write authority. Package pages must continue to fail visibly rather than silently treating local mirrors as successful canonical writes.

## Controlled next migration candidate

After this trace is merged, the next Package-domain change should be a narrowly scoped mirror-retirement PR:

1. remove `_sync_legacy_package_state()` calls from successful canonical Package writes;
2. keep the existing app-state arrays untouched as rollback evidence during observation;
3. keep the legacy-named `components.db` APIs mapped to canonical readers through the bootstrap;
4. add permanent guards against new direct runtime reads of `data.packages` or `data.member_packages`;
5. verify Admin Package create/edit and subscription lifecycle actions through fresh canonical reads;
6. smoke Admin Scheduling and Member My Schedule;
7. verify `hm_member_schedule_contract()` output for an authenticated member;
8. retire the stored app-state arrays only in a later, explicitly approved data migration.

No mirror retirement or data deletion is included in this Phase 2 trace.
