# HealthyMe data architecture inventory — Phase 1

Date: 2026-08-03  
Issue: #346  
Baseline: `main` after merged PR #359

## Purpose

Freeze the current HealthyMe persistence landscape before changing another business workflow. This is a read-only architecture inventory. It does not migrate, delete, rename or re-route production data.

The governing rule is: where two or more structures serve the same business purpose, they should follow one approved persistence and contract pattern unless an exception is documented.

## Evidence used

- Live Supabase `public` schema and RLS metadata.
- Exact row counts from the live project.
- Top-level keys and collection sizes in `healthyme_app_state_v1`.
- Central storage contracts in `components/storage_backend.py` and `components/normalized_store.py`.
- The canonical Content Repository baseline completed under issue #347.

No member names, emails, assessment answers or clinical content are recorded in this document.

## Current architecture layers

### 1. Dedicated Supabase tables

All currently observed public tables have RLS enabled.

#### Identity, authentication and workflow

- `hm_users` — 15 rows.
- `hm_workflow` — 15 rows.
- `hm_streamlit_auth_sessions` — 4 rows.
- `hm_supabase_auth_provisioning_audit` — 24 rows.
- `sms_users` — 1 row; separate legacy or external-purpose user structure requiring classification.

#### Canonical reusable content

- `hm_content_repository_items` — 10 rows.
- `hm_content_repository_events` — 10 rows.

#### Recommendation profile definitions

- `hm_recommendation_profiles` — 8 rows.
- `hm_recommendation_profile_items` — 19 rows.
- `hm_recommendation_profile_events` — 25 rows.
- `hm_recommendation_master_options` — 33 rows.

#### Packages, subscriptions, payments and usage

- `hm_packages` — 3 rows.
- `hm_member_package_subscriptions` — 3 rows.
- `hm_package_payments` — 0 rows.
- `hm_package_subscription_events` — 0 rows.
- `hm_package_usage_events` — 2 rows.

#### Member journal/log records

- `hm_member_exercise_logs` — 5 rows.

### 2. Shared JSON application state

`healthyme_app_state_v1` remains a broad shared JSON authority for multiple unrelated domains.

#### Identity, role and workflow

- `users` — 15 records.
- `workflow` — 15 member entries.
- `auth_sessions` — 2 entries.
- `login_sessions` — 4 entries.
- `user_timezones` — 2 entries.
- `profiles` — 15 entries.

#### Assessment and evaluation

- `laf_responses` — 7 entries.
- `nsp1_responses` — 5 entries.
- `nsp2_responses` — 5 entries.
- `nsp_scores` — 4 entries.
- `nsp_system_scores` — 4 entries.
- `nsp_system_scores_by_instance` — 4 entries.
- `assessment_instances` — 13 entries.
- `assessment_instance_responses` — 15 entries.
- `admin_assessments` — 4 entries.
- `admin_assessments_by_instance` — 2 entries.
- `body_mind_access` — 3 entries.
- `body_mind_responses` — 2 entries.

A second `healthyme_app_state` row, `flutter_laf_draft:982a04f9`, stores 105 Flutter draft responses plus draft metadata. It is a separate document-style authority inside the same table.

#### Member planning and allocations

- `member_recipe_allocations` — 1 member entry.
- `member_exercise_allocations` — 1 member entry.
- `member_supplements` — 6 rows.
- `resource_assignments` — 2 resource groups.
- `resource_feedback` — 2 resource groups.
- `resource_feedback_log` — 6 events.
- `recommendation_shares` — 1 member entry.
- `nutritionist_structured_notes` — 8 rows.

#### Scheduling, packages and usage

- `packages` — 3 rows.
- `member_packages` — 3 rows.
- `schedules` — 16 rows.
- `reschedule_requests` — 3 rows.
- `schedule_timezone_audit` — 8 events.

#### Journals and supervision

- `daily_food_journals` — 5 member/date entries.
- `daily_logs` — 5 member/date entries.
- `daily_log_supervision_notes` — 2 entries.

#### Communications

- `messages` — 51 rows, all currently `queued`.
- `notifications` — 81 rows, all currently `queued`.
- `email_delivery_logs` — 21 rows.

#### Audit collections

Audit history is fragmented across dedicated tables and JSON arrays, including:

- `audit_logs` — 11 rows.
- `response_audit_log` — 4 rows.
- `nsp_recalculation_audit` — 10 rows.
- `recommendation_contract_audit` — 6 rows.
- `recommendation_share_audit` — 3 rows.
- `supplement_audit_logs` — 9 rows.
- `exercise_repository_audit` — 2 rows.
- `supplement_repository_audit` — 5 rows.

#### Retained rollback evidence from issue #347

- `recipes` — 2 rows.
- `exercises` — 3 rows.
- `supplement_repository` — 5 rows.
- Repository migration metadata and old repository audit arrays.

These collections are no longer live repository authorities. They remain inert rollback evidence and are outside the first migration batch for issue #346.

### 3. Local fallback and archived evidence

`components/storage_backend.py` can still load `data/db.json` or `data/db_sample.json` when Supabase is unavailable. On a failed Supabase save, it writes the full shared state to local `data/db.json` and reports `LOCAL_FALLBACK`.

The Recipe and Exercise CSV sources are archived under `docs/archive/content_repository_legacy/` and are not active application authorities.

## Verified same-purpose dual structures

### Users and workflow

| Domain | Dedicated rows | App-state rows | Matching IDs | Missing identities | Key-field mismatches |
|---|---:|---:|---:|---:|---:|
| Users | 15 | 15 | 15 | 0 | 0 |
| Workflow | 15 | 15 | 15 | 0 | 0 |

Current implementation:

- `load_state()` loads the shared JSON document and overlays `users` and `workflow` from `hm_users` and `hm_workflow` when available.
- `save_state()` writes the entire JSON document first and then synchronises users/workflow into dedicated tables.
- A normalized-table sync failure does not fail the shared-state save.
- A Supabase save failure can fall back to a local file.

Conclusion: the dedicated tables are preferred reads, but the system still maintains dual copies and dual-write behaviour. This domain is consistent today but carries high authentication and divergence risk.

### Packages and subscriptions

| Domain | Dedicated rows | App-state rows | Matching IDs | Missing identities | Key-field mismatches |
|---|---:|---:|---:|---:|---:|
| Package catalogue | 3 | 3 | 3 | 0 | 0 |
| Member package subscriptions | 3 | 3 | 3 | 0 | 0 |

The dedicated package schema already includes lifecycle, payment, refund, replacement, pause/resume, actor and timestamp fields. The app-state copies currently match the dedicated identities and key fields exactly.

Conclusion: package catalogue and member subscriptions are the lowest-risk first candidate for single-authority cutover, subject to a complete reader/writer trace.

## Other same-purpose clusters requiring contract decisions

### Authentication sessions

- `hm_streamlit_auth_sessions` is a dedicated session store.
- `auth_sessions` and `login_sessions` remain in shared app-state.
- The three structures do not yet have one documented identity, revocation, expiry and retention contract.

### Recommendation profiles, allocations and current member plans

- Profile definitions use dedicated normalized tables and source snapshots.
- Member Recipe and Exercise allocations, Supplement regimens, resource assignments and recommendation shares remain in shared app-state.
- These records serve different lifecycle stages, but the boundary between reusable profile, member allocation, published snapshot and current plan must be made explicit before Member Planning restructuring.

### Scheduling and package usage

- Schedules and reschedule requests remain in app-state.
- Package usage is recorded in a dedicated append-oriented table.
- Schedule lifecycle uses `scheduled`, `acknowledged`, `rescheduled`, `completed` and `cancelled`; usage events use a separate event vocabulary and dedupe contract.

### Journals

- Exercise daily logs use `hm_member_exercise_logs`.
- Food journals, combined daily logs and supervision notes remain in shared app-state.
- The two journal families therefore differ in storage, identity, status, write verification, history and Flutter-readiness.

### Communications

- Messages, notifications and email delivery logs are separate app-state arrays.
- Messages and notifications both use `queued`, but their delivery, read, archive, retry and dedupe rules are not represented by a shared durable contract.

### Assessment and evaluation

- LAF, NSP, scoring, assessment instances, admin assessments and Body–Mind state are split across many JSON collections.
- Flutter LAF drafts use a separate row/document pattern.
- Instance identity exists for some records but not consistently across legacy member-keyed collections.

### Audit and event history

- Some domains use dedicated append-only event tables.
- Others append domain-specific arrays inside the shared JSON document.
- Actor fields, event names, before/after snapshots, retention and read access are inconsistent.

## Cross-cutting inconsistencies

### Status vocabulary

Observed storage values include:

- lower-case lifecycle values: `active`, `draft`, `replaced`, `scheduled`, `completed`, `cancelled`;
- title-case activity values: `Not Started`, `In Progress`, `Completed`;
- title-case legacy value: `Active` in `sms_users`;
- booleans such as `is_active` alongside text statuses;
- separate payment statuses such as `not_recorded`.

A single global status enum would be incorrect. Each business domain needs a documented lower-snake-case storage vocabulary, with presentation labels kept outside persistence.

### Identity patterns

Observed identities include UUIDs, full text IDs, eight-character text IDs, member-keyed JSON objects, array position history and composite repository identity. The standard must be domain-specific but stable, non-display-name-based and preserved through migration.

### Timestamps and actors

Some tables carry `created_at`, `updated_at`, `created_by` and `updated_by`; others carry only timestamps, only one actor field or app-generated timestamps inside JSON payloads.

### Audit pattern

The Content Repository has immutable before/after events. Package and recommendation-profile domains have dedicated event tables. Multiple other domains append informal JSON audit rows without one contract.

### Failure and fallback behaviour

The shared storage layer can report a successful local write after Supabase failure. That behaviour may protect short-term availability, but it can create an unreplicated authority. Every future cutover must explicitly choose fail-closed, queued retry or controlled offline operation; silent authority switching is not acceptable for administrative writes.

### Snapshot and historical-reference rules

The strongest current examples are:

- Content Repository stable source identity plus immutable downstream references.
- Recommendation profile items with `source_type`, `source_id`, `source_label` and `source_snapshot`.

Equivalent historical records should retain snapshots where later source edits must not rewrite history.

## Proposed application-wide standard

This is the starting standard for issue #346. Each migration batch must confirm or document an exception.

1. One live write authority per business purpose.
2. Dedicated Supabase tables for multi-record lifecycle domains; shared JSON only for explicitly temporary or document-style state.
3. Stable IDs that never depend on display names or array positions.
4. Lower-snake-case persisted statuses with domain-specific allowed values.
5. `created_at`, `updated_at`, `created_by` and `updated_by` where records are mutable.
6. Soft deletion or inactive/replaced states when history can reference a record.
7. Append-only events for material lifecycle changes.
8. Fresh read verification after administrative writes.
9. No silent production fallback to another write authority.
10. Immutable source snapshots for historical plans, recommendations and other referenced records.
11. RLS and least-privilege grants for every exposed table.
12. Streamlit remains the behavioural source of truth until the Flutter contract is proven equivalent.

## Controlled migration order

### Batch 1 — Package catalogue and member subscriptions

Reason: exact identity and key-field parity already exists between dedicated tables and app-state, and the dedicated schema is lifecycle-complete.

Required next work:

- trace every Streamlit and Flutter reader/writer;
- identify which path is currently authoritative for each operation;
- freeze a compatibility map;
- add read-after-write and no-fallback guards;
- cut over catalogue first, then subscriptions;
- retain app-state copies read-only for an observation window.

### Batch 2 — Users and workflow

Reason: exact parity exists, but auth, role, login and local-fallback behaviour make the blast radius higher.

### Batch 3 — Authentication session stores

Define one session identity, expiry, revocation and retention contract before retiring app-state session maps.

### Batch 4 — Scheduling and package usage

Align schedule lifecycle, reschedule history, session consumption, dedupe and current-usage projection.

### Batch 5 — Member Planning contracts

Separate reusable Meal Profile definitions, member Exercise/Supplement allocations, published recommendation snapshots and Current Member Plan projections without changing history.

### Batch 6 — Journals

Create one journal identity and persistence pattern while preserving food-specific and exercise-specific payloads.

### Batch 7 — Communications

Standardise message, notification, delivery-attempt, read/archive and dedupe contracts.

### Batch 8 — Assessment, evaluation and audit consolidation

Move only after instance identity, historical scoring and Flutter draft continuity are fully mapped.

## Phase 1 decision

Issue #346 begins with documentation and contract tests only. No production schema, application runtime, app-state data or local fallback behaviour is changed in this phase.

The next implementation PR after this inventory should be a Package domain reader/writer trace and authority-freeze document. It must not cut over writes until all live paths are accounted for.
