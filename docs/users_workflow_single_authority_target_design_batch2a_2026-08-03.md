# Users and Workflow single-authority target design — Batch 2A

Date: 2026-08-03  
Issue: #346  
Follows: merged PR #366, `Trace Users and Workflow authorities before cutover`

## Decision

**Design only — no implementation.**

This document defines the accepted target architecture for Users and Workflow. It does not change application code, authentication, database schema, RLS, RPC grants, sessions, Flutter behaviour, local fallback or production data.

The target end state is:

- `hm_users` is the sole live User authority.
- `hm_workflow` is the sole live Workflow authority.
- shared-state `users` and `workflow` may exist temporarily only as a non-authoritative compatibility projection and later as frozen rollback evidence;
- Session migration remains a separate batch.

No runtime, SQL, RLS, RPC, authentication or Flutter change is included in Batch 2A.

## Evidence used

This target is based on:

- the complete runtime classification merged in PR #366;
- live production schema, constraints, indexes, grants, RLS policies and function definitions;
- live parity of 15 dedicated and 15 shared-state Users with zero key-field mismatches;
- live parity of 15 dedicated and 15 shared-state Workflow rows with zero key-field mismatches;
- the separate Flutter member repository at revision `a2de87cb37bea2dfecacbbb04cf03069f505077a`;
- current Streamlit storage, role resolution, User Manager, Demo Mode and durable-session code.

No member identity, password material, assessment response or clinical content is recorded here.

## Current production facts that shape the design

### Users and Workflow are consistent but not single-authority

Streamlit currently writes the shared JSON document first and only then synchronises `hm_users` and `hm_workflow`. A dedicated-table synchronisation failure does not roll back the accepted shared-state save.

Streamlit reads the shared JSON document and then overlays dedicated Users and Workflow. If that overlay fails, shared JSON can silently become the read source.

A Supabase failure can write the complete state, including Users and Workflow, to `data/db.json`.

### Flutter already depends on the dedicated tables

`VineetAppTest/healthyme-flutter-member/lib/repositories/member_repository.dart` directly reads `hm_users` and `hm_workflow`.

The live Flutter LAF contract also:

- reads Workflow from `hm_workflow` but falls back to shared-state Workflow when a dedicated row is absent;
- updates shared-state Workflow during LAF saves;
- updates `hm_workflow` when LAF is marked complete.

The live NSP Workflow RPC writes `hm_workflow` directly.

### Access and permission cleanup cannot be bundled blindly

The live tables have RLS enabled, but `anon`, `authenticated` and `service_role` currently hold broad table-level privileges. RLS limits effective row access, but the target should move to explicit least-privilege grants after compatibility testing.

Current `hm_users` indexing includes several overlapping lower-email indexes. Index cleanup is desirable but must be separated from the first authority cutover.

### Mandatory security blocker

The live function `hm_flutter_upsert_nsp_workflow(text, boolean, boolean, boolean)` is:

- `SECURITY DEFINER`;
- executable by `anon` and `authenticated`;
- parameterised by an arbitrary member ID;
- not self-resolving through the authenticated identity in its current definition.

The live function `hm_flutter_current_member_id()` is also directly executable by `anon`.

**First implementation gate: Flutter Workflow RPC permission hardening.** No broader authority cutover may begin until anonymous execution is removed and every member mutation resolves and verifies the current authenticated member inside the database function.

## Target architecture

```text
Supabase Auth identity
        |
        v
Canonical identity resolution
        |
        +--> hm_users ----------------------+
        |                                    |
        |                                    +--> User event history
        |
        +--> hm_workflow -------------------+
                                             |
                                             +--> Workflow event history

Streamlit server-side writers --> explicit service-role contracts
Flutter member writers --------> authenticated self-scoped RPCs
All live readers --------------> canonical tables/contracts only

Temporary observation projector
        |
        +--> healthyme_app_state.data.users       [non-authoritative]
        +--> healthyme_app_state.data.workflow    [non-authoritative]
```

## Authority matrix

| Business purpose | Target authority | Allowed live readers | Allowed live writers | Explicitly non-authoritative |
|---|---|---|---|---|
| User identity and application role | `hm_users` | Streamlit server, Flutter authenticated self-read, approved Admin services | server-side Admin/provisioning contracts only | shared `users`, local JSON, session snapshots |
| Member assessment Workflow | `hm_workflow` | Streamlit, Flutter authenticated self-read, approved reports | authenticated self-scoped member RPCs and server-side Admin Workflow contracts | shared `workflow`, local JSON, UI-derived status |
| Streamlit browser sessions | `hm_streamlit_auth_sessions` during later Session batch | Streamlit auth layer only | durable session adapter only | `auth_sessions`, `login_sessions` after separate migration |
| Historical cutover evidence | immutable export or frozen shared projection | restricted Admin/audit tooling | none after freeze | never a runtime fallback |

## User target contract

### Canonical record

`hm_users` remains the stable application User record. The existing text `id` is preserved because it is referenced by profiles, assessments, packages, recommendations, schedules, journals and Flutter contracts.

Required live fields remain:

- `id`;
- `name`;
- normalized `email`;
- `role`;
- `is_active`;
- `auth_provider`;
- `auth_user_id` where linked;
- timestamps.

### Identity rules

1. User IDs never change during cutover.
2. Email is stored lower-case and compared case-insensitively.
3. One active Supabase Auth identity maps to at most one HealthyMe User.
4. Role values remain `admin` and `member` unless a separately approved role-model migration is created.
5. Inactive Users remain readable for history by authorised server-side services but cannot authenticate into active member/admin routes.
6. Flutter self-read remains compatible with the current selected fields.

### User write contracts

Streamlit and provisioning code must stop mutating `db["users"]` directly. The target server-side contracts are explicit operations such as:

- create User and initial Workflow together for a new member;
- update name/email mapping;
- link or relink `auth_user_id` under controlled rules;
- activate/deactivate User;
- change application role;
- record provisioning outcome.

Each material write must:

1. verify the acting Admin or approved system actor;
2. execute transactionally in the database;
3. capture before/after event evidence;
4. return the canonical row;
5. receive a fresh read-after-write verification in the caller;
6. never write an alternate authority when the canonical operation fails.

## Workflow target contract

### Canonical record

`hm_workflow` remains one row per HealthyMe User ID.

The existing persisted fields remain the source facts:

- `laf_completed`;
- `nsp1_completed`;
- `nsp2_completed`;
- `submitted_for_review`;
- `admin_completed`;
- `final_report_ready`.

`workflow_status` must be derived by one database-owned contract with the current precedence:

1. `finalized`;
2. `admin_completed`;
3. `submitted`;
4. `in_progress`;
5. `not_started`.

Python, Flutter and SQL callers must not independently invent or persist a conflicting status.

### Member write boundary

Authenticated members may update only their own member-progress fields through self-scoped RPCs. The database must resolve the member from `auth.uid()` with controlled email fallback only while unmigrated Auth links remain.

Member writes must never accept an unchecked arbitrary member ID. Members cannot set:

- `admin_completed`;
- `final_report_ready`;
- another member's Workflow;
- another member's User fields.

### Admin write boundary

Admin assessment/finalisation operations use server-side contracts. They may update Admin-owned Workflow fields and any required related assessment records in one controlled transaction.

Reports and routing read Workflow only through the canonical contract. They do not derive authority from shared JSON.

## Event and audit contract

A later foundation migration should add append-only material-change evidence for Users and Workflow. One shared event table may be used if it has an explicit entity type and stable contract.

Minimum event fields:

- event ID;
- entity type: `user` or `workflow`;
- entity ID;
- event type;
- before snapshot;
- after snapshot;
- actor ID;
- actor source: Admin, member RPC, provisioning service or controlled migration;
- correlation/idempotency key where applicable;
- event timestamp.

Reads of current state do not create events. Material lifecycle changes do.

## Read architecture

### Streamlit

Introduce a dedicated identity/Workflow repository rather than treating the full application-state document as the authority.

During transition, `load_db()` may continue returning an in-memory compatibility shape for old pages, but its `users` and `workflow` values must come from canonical reads. If canonical reads fail, identity- or Workflow-dependent operations fail closed.

No identity or Workflow read may fall back to:

- shared-state `users` or `workflow`;
- `data/db.json`;
- `data/db_sample.json`;
- a stale browser/session User snapshot for authorisation.

A session snapshot may support display continuity only after current role and active state are revalidated against `hm_users`.

### Flutter

Preserve direct self-read of `hm_users` and `hm_workflow` or replace it only with an equivalent authenticated contract after parity testing.

Remove the shared-state Workflow fallback from `hm_flutter_get_laf()` only after every production member has a canonical Workflow row and the member read contract is verified.

## Write architecture and fail-closed behaviour

No identity or Workflow write may fall back to shared JSON or `data/db.json`.

Canonical write failure means the business operation fails visibly. The application may retry safely with an idempotency key, but it cannot report success after writing a different store.

General non-identity domains may retain their existing storage behaviour until their own issue #346 batch. This design changes only the future contract for Users and Workflow.

## Temporary compatibility projection

Compatibility projection is non-authoritative and temporary.

During a controlled observation window, one projector may refresh shared-state `users` and `workflow` from committed canonical rows so an emergency rollback to the preceding release still has current compatibility data.

Projection rules:

1. canonical write commits first;
2. projection runs after the canonical transaction;
3. projection never becomes the accepted source of truth;
4. projection failure is logged and blocks progression to mirror retirement, but does not rewrite canonical data;
5. no application business function writes the shared arrays directly;
6. projection output is compared with canonical rows during observation;
7. after accepted observation, projection is disabled and the last copies are frozen as rollback evidence.

The existing shared Users and Workflow collections remain untouched in this design PR.

## Rollback model

### Before compatibility projection retirement

Rollback may restore the preceding application release while the projector keeps shared arrays current. Canonical tables remain preserved.

### After compatibility projection retirement

Rollback must not reactivate shared JSON or local files as authority. A rollback release must continue reading canonical Users and Workflow. Recovery uses canonical database snapshots and event history.

## Password retirement

Legacy `password_hash` and `must_reset_password` fields are not removed in the authority cutover.

Accepted sequence:

1. prove native Supabase identity is the only active production login path;
2. stop creating or changing local password hashes;
3. remove local password authentication calls from production routes;
4. make legacy password fields nullable or move them to restricted historical evidence through a separate migration;
5. scrub password material only after rollback and legal/retention requirements are accepted.

Password retirement is not bundled with the first User write cutover.

## Default-Admin recovery

Runtime `ensure_default_admin()` creation is not part of the target architecture.

The future break-glass process is explicit and audited:

1. provision or identify a Supabase Auth User;
2. create/link one active `hm_users` Admin record through a controlled runbook or Admin recovery RPC;
3. verify role resolution;
4. record the recovery actor and reason.

The application must not silently create `admin@healthyme.local` or a known local password when canonical identity is unavailable.

## Demo Mode

Demo Mode must not directly append to shared Users or Workflow after cutover.

The safe target is either:

- environment-gated canonical demo provisioning with explicit demo identity and cleanup rules; or
- disabling demo User creation in production while retaining non-identity demo data utilities.

A decision on Demo Mode is required before User write cutover.

## Session migration scopes

Session migration remains a separate batch.

This design does not change:

- `hm_streamlit_auth_sessions`;
- shared `auth_sessions`;
- shared `login_sessions`;
- browser marker handling;
- access/refresh token rotation;
- Streamlit native routing.

Users/Workflow cutover may revalidate a session's role against `hm_users`, but it must not reinterpret or delete session records.

## Target security model

### Tables

Later implementation should converge toward:

- `anon`: no table access to `hm_users` or `hm_workflow`;
- `authenticated`: self-scoped SELECT required by Flutter; no direct broad DML after RPC migration;
- `service_role`: server-side DML only;
- RLS policies aligned to `auth_user_id`, with temporary email fallback only for unmigrated links;
- explicit `USING` and `WITH CHECK` on any retained UPDATE policy.

### Functions

Every exposed privileged function must:

- revoke default/public execution;
- grant only the roles that need it;
- use a fixed `search_path`;
- verify `auth.uid()` for member operations;
- resolve the member internally;
- reject arbitrary cross-member IDs;
- preserve Admin-only fields;
- return enough data for read-after-write verification.

Permission hardening is implemented and tested before broader cutover.

### Indexes and constraints

A later schema-hardening PR should:

- verify and enforce case-insensitive email uniqueness;
- remove redundant lower-email indexes only after plan review;
- add an allowed-value constraint for `workflow_status`;
- retain unique `auth_user_id` mapping;
- preserve the `hm_workflow.user_id` foreign key.

Index cleanup is not bundled with the first permission fix.

## Writer migration map

| Current writer or consumer | Target treatment |
|---|---|
| `components/storage_backend.py` | stop authoritative User/Workflow JSON writes; fail closed for canonical identity/Workflow reads |
| `components/normalized_store.py` | evolve into canonical repository or be replaced by one; remove full-document sync semantics |
| `components/db.py` | compatibility APIs delegate to explicit canonical contracts; direct User/Workflow mutation retired |
| `components/admin_role_model.py` | remove legacy local User fallback; canonical role revalidation required |
| `components/assessment_instances.py` | Workflow changes delegated to canonical Workflow service |
| `pages/17_Admin_User_Manager.py` | canonical create/list User contracts; no `load_db()["users"]` authority |
| `pages/29_Admin_Demo_Mode.py` | environment-gated canonical demo path or production disablement |
| Supabase provisioning modules | transactional Auth-link/User updates plus audit evidence |
| Flutter `MemberRepository` | preserve canonical direct reads |
| Flutter LAF RPCs | canonical Workflow read, no shared Workflow fallback after coverage gate |
| Flutter NSP Workflow RPC | authenticate, self-resolve, revoke anon execution, canonical write only |
| reports, scheduling, email and recommendation readers | canonical compatibility repository during transition, then direct contracts |

## Controlled implementation sequence

### Gate 1 — Flutter Workflow RPC permission hardening

- revoke anonymous execution from member identity and Workflow mutation functions;
- make NSP Workflow mutation self-resolve the authenticated member;
- reject arbitrary member IDs;
- preserve authenticated Flutter behaviour;
- run security advisors and Flutter smoke checks.

No authority cutover proceeds until this gate passes.

### Gate 2 — Canonical contract foundation

- define one Workflow status derivation function;
- add event/audit structure;
- add transactional server-side User and Admin Workflow contracts;
- add idempotency and read-after-write responses;
- prepare least-privilege grants without changing active readers prematurely.

### Gate 3 — User write cutover

- migrate Admin User Manager and provisioning writers;
- redesign default-Admin recovery;
- decide Demo Mode handling;
- retain temporary compatibility projection;
- verify User parity after each controlled operation.

### Gate 4 — Workflow write cutover

- migrate Streamlit assessment and finalisation writers;
- migrate Flutter LAF/NSP Workflow writers;
- centralise Workflow status derivation;
- retain temporary compatibility projection;
- verify Workflow parity and history.

### Gate 5 — Canonical read cutover

- remove shared/local identity fallback;
- move reports, scheduling, recommendation, email and Admin lists to canonical reads;
- remove shared Workflow fallback from mobile RPCs;
- preserve session role revalidation.

### Gate 6 — Observation

- signed-in Admin and member route smoke;
- Flutter member login, LAF, NSP and dashboard smoke;
- canonical/shared projection parity monitoring;
- no local identity/Workflow writes;
- audit/event completeness;
- rollback rehearsal.

### Gate 7 — Projection retirement

- stop compatibility projection;
- freeze shared arrays as evidence;
- prevent new direct shared-array writers through permanent tests;
- retain canonical snapshots and event history.

### Gate 8 — Password and legacy recovery cleanup

- retire local password logic;
- remove runtime default-Admin creation;
- handle legacy password fields through a separately approved migration.

### Later batch — Sessions

Define one session identity, expiry, revocation, device and retention contract. Do not combine this with Users/Workflow cutover.

## Deployment acceptance gates

Before any production authority cutover:

1. production Users and Workflow parity remains exact;
2. every active User has an expected canonical Workflow row where required;
3. Flutter authenticated reads pass;
4. Flutter Workflow mutation functions are not executable by `anon`;
5. member RPCs cannot mutate another member's Workflow;
6. Admin User and Workflow writes are transactional and read-after-write verified;
7. no identity/Workflow write can report local-fallback success;
8. native Streamlit login, refresh, logout and role routing pass;
9. retained compatibility projection is monitored and reversible;
10. no historical assessment, report, recommendation, package or schedule reference is lost.

## Batch 2A boundary

This PR approves a design and implementation order only.

It does not:

- alter production data;
- apply SQL;
- change RLS or grants;
- modify RPCs;
- change Streamlit or Flutter runtime;
- remove passwords;
- remove default-Admin code;
- modify sessions;
- freeze or delete shared arrays.
