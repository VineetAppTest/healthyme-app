# Users and Workflow authority trace — Batch 2

Date: 2026-08-03  
Issue: #346  
Follows: merged PR #365 and completed Package single-authority observation

## Decision

This batch is a read-only authority trace. It does not change authentication, user creation, role resolution, workflow progression, Supabase schema, RLS, RPC grants, local fallback or Flutter behaviour.

`hm_users` and `hm_workflow` are currently preferred read structures, but they are not yet the only write authority. The shared `healthyme_app_state_v1.data.users` and `healthyme_app_state_v1.data.workflow` collections are still written first by the general application-state contract and then synchronised into the dedicated tables.

No authority cutover is approved by this trace.

## Production baseline

Read-only verification returned:

| Domain | Dedicated rows | Shared-state rows | Missing identities | Key-field mismatches |
|---|---:|---:|---:|---:|
| Users | 15 | 15 | 0 | 0 |
| Workflow | 15 | 15 | 0 | 0 |

The User comparison covers `id`, `name`, `email`, `password_hash`, `role`, `must_reset_password`, `is_active` and `auth_provider`.

The Workflow comparison covers `user_id`, `laf_completed`, `nsp1_completed`, `nsp2_completed`, `submitted_for_review`, `admin_completed`, `final_report_ready` and `workflow_status`.

No production row was inserted, updated or deleted during this trace.

## Exact dedicated schemas

### `hm_users`

- stable text `id`;
- `name` and `email`;
- duplicated legacy `password_hash`;
- `role`;
- `must_reset_password`;
- `is_active`;
- `auth_provider`;
- `created_at` and `updated_at`;
- optional Supabase Auth linkage through `auth_user_id` and `auth_migrated_at`.

### `hm_workflow`

- stable text `user_id`;
- six workflow booleans;
- derived `workflow_status`;
- `created_at` and `updated_at`.

### `hm_streamlit_auth_sessions`

- UUID identity and hashed browser marker;
- email, Supabase Auth identity and application role;
- user snapshot;
- access and refresh tokens;
- token expiry, session expiry, revocation and last-seen timestamps;
- metadata.

The table currently has 4 rows: 1 active, 3 expired and 0 revoked.

## Shared-state identity and workflow structures

`healthyme_app_state_v1.data.users` is an array containing the same eight legacy business fields currently compared with `hm_users`.

`healthyme_app_state_v1.data.workflow` is a member-ID-keyed object containing the same seven workflow fields currently compared with `hm_workflow`.

The shared state also contains two other session maps:

- `auth_sessions` — 2 entries with `user_id`, `token_hash`, `created_at`, `last_seen_at` and `expires_at`;
- `login_sessions` — 4 entries with `user_id`, `created_at` and `active`.

These three session structures do not share one identity, expiry, revocation, token or retention contract.

## Streamlit load authority

`components/storage_backend.py` owns the general state load.

1. Load `healthyme_app_state_v1` from Supabase.
2. Normalise the full shared JSON document.
3. Call `_overlay_normalized_users_workflow()`.
4. `components/normalized_store.py` reads every row from `hm_users` and `hm_workflow`.
5. When both dedicated tables are available, replace `db["users"]` and `db["workflow"]` in memory.
6. Cache that overlaid state for the current Streamlit session.

Therefore dedicated tables are preferred reads only while their client, permissions and queries succeed. If the overlay fails, the shared JSON copy remains the runtime read source without a hard failure.

## Streamlit write authority

`components/storage_backend.py` owns the general state save.

1. Write the entire shared JSON document to `healthyme_app_state`.
2. Only after that succeeds, call `sync_users_workflow_to_normalized()`.
3. Upsert all Users and Workflow rows into the dedicated tables.
4. A dedicated-table sync failure does not roll back the accepted shared-state save.

This is app-state-first dual-write, not dedicated-table single authority.

## User and Workflow business writers

`components/db.py` remains the main compatibility API.

User-changing paths include:

- `ensure_default_admin()`;
- `ensure_oidc_user_record()`;
- `create_user()`;
- `change_password()`;
- legacy Auth0 linkage helpers;
- active/inactive and role-management paths elsewhere in the module.

Workflow-changing paths include:

- `update_workflow()`;
- `submit_member_for_review_once()`;
- assessment completion and finalisation helpers;
- other business functions that load the shared document, update member workflow and call `save_db()`.

All these operations currently mutate the shared object and depend on `save_state()` to synchronise the dedicated tables afterward.

`components/normalized_store.py` also exposes `upsert_user_to_normalized()`, but it is a direct dedicated-table helper and does not update the shared state. It cannot be treated as a safe replacement for the existing full business write contract until every caller and dependent profile/workflow side effect is mapped.

## Login-time and identity reads

`components/normalized_store.py` provides `find_user_by_email_fast()` for a direct `hm_users` login-time lookup. Its contract explicitly allows the caller to fall back when the normalized lookup fails.

`app.py` uses Streamlit native identity through `st.user` and routes through the native authorization bridge. The accepted Streamlit route behaviour must remain unchanged during this audit.

`native_bridge/root_authorization_ui.py` and `native_bridge/root_authorization_ui_h13r7e.py` provide the accepted Supabase-backed authorization UI and native identity handoff. They must not be altered by a Users/Workflow storage cutover.

## Flutter member boundary

Flutter source is maintained in the separate connected repository:

- repository: `VineetAppTest/healthyme-flutter-member`;
- traced source revision: `a2de87cb37bea2dfecacbbb04cf03069f505077a`;
- direct reader: `lib/repositories/member_repository.dart`.

`MemberRepository.fetchCurrentMemberByEmail()` directly reads:

1. `hm_users` by normalized authenticated email, role `member` and active state;
2. `hm_workflow` by the resolved HealthyMe member ID.

The Flutter member application therefore already treats the dedicated tables as its direct read authority. Any Streamlit cutover must preserve the Flutter field selection, RLS policies, identity mapping and error behaviour.

## RLS and permissions boundary

All three dedicated tables have RLS enabled.

- `hm_users` has member self-read policies based on Auth identity or email.
- `hm_workflow` has member self-read plus member-owned insert/update policies used by Flutter assessment progression.
- `hm_streamlit_auth_sessions` has forced RLS and no ordinary table policy; service-side session handling is expected.

Multiple legacy/member RPCs reference `hm_users` or `hm_workflow`. Some older functions still have broader `anon` execution grants. This trace records the condition but does not change grants because permission hardening must be separated from authority migration and tested against the live Flutter build.

## Critical divergence risks

### 1. Shared-state save can succeed while normalized sync fails

The application can report a successful Supabase state save while `hm_users` or `hm_workflow` remains stale.

### 2. Dedicated read overlay can hide shared-state changes

A later load replaces shared Users and Workflow with dedicated rows. A change written only to shared state can therefore appear to disappear.

### 3. Local fallback creates a third write authority

When Supabase save fails, `components/storage_backend.py` writes the complete document to `data/db.json`. Dedicated Users and Workflow are not updated. This is especially unsafe for roles, active status, passwords and workflow progression.

### 4. Local push does not synchronise dedicated tables

`push_local_data_to_supabase()` writes the shared JSON document but does not call `sync_users_workflow_to_normalized()`. A later normalized overlay can immediately replace locally pushed Users and Workflow with older dedicated values.

### 5. Default-admin recovery mutates identity state

`components/db.py` can create a fallback Admin when no expected Admin is present. That recovery path must be redesigned or explicitly retained before shared Users are retired.

### 6. Password material is duplicated

Legacy password hashes are present in both the shared Users array and `hm_users`, even though native Supabase identity is the target authentication mechanism. Password retirement cannot be bundled with the authority cutover.

### 7. Workflow derivation is duplicated

Both `components/db.py` and `components/normalized_store.py` derive `workflow_status`. Their field sets and future lifecycle extensions can diverge unless one contract owns derivation.

### 8. Session persistence is fragmented

`hm_streamlit_auth_sessions`, shared `auth_sessions` and shared `login_sessions` have different token, expiry and revocation semantics. Users/Workflow cutover must not silently retire or reinterpret any session store.

## Classified HealthyMe runtime sources

The repository-wide contract test requires every runtime Python source that directly mentions the dedicated identity/workflow tables or shared Users/Workflow/session collections to be classified in this document.

Initial classified sources:

- `components/storage_backend.py` — shared-state load/save, normalized overlay, normalized sync and local fallback;
- `components/normalized_store.py` — dedicated User/Workflow reads, full sync and fast email lookup;
- `components/db.py` — compatibility User, Workflow and `login_sessions` business API;
- `app.py` — accepted native Streamlit identity and role routing;
- `native_bridge/root_authorization_ui.py` — accepted authorization UI bridge;
- `native_bridge/root_authorization_ui_h13r7e.py` — accepted production authorization UI bridge.

Any additional source discovered by CI must be added here with its purpose before this trace is accepted.

## Controlled next decision after this trace

Do not remove either shared collection immediately.

The next design PR should define, without implementing, a fail-closed dedicated authority for Users and Workflow:

1. separate User, Workflow and Session migration scopes;
2. preserve Flutter direct reads and member-owned Workflow writes;
3. make Admin User and Workflow writes transactional or explicitly verified;
4. eliminate silent local authority switching for identity and workflow changes;
5. decide the future of legacy password fields and default-admin recovery;
6. define one workflow-status derivation contract;
7. define how retained shared copies will be frozen as rollback evidence;
8. add deployment and signed-in regression gates before any runtime cutover.

No authentication, workflow, session or data migration is included in this Batch 2 trace.
