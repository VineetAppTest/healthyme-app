# CODEX MCD v1.8 Readiness Audit

Audit date: 2026-06-24
Repository: `VineetAppTest/healthyme-app`
Branch: `codex-mcd18-readiness-audit`
FMOT reviewed against: MCD v1.8 Candidate - Supabase-Aligned Production Architecture Update

## 1. Executive Summary

The repository appears partially aligned with MCD v1.8.

Aligned areas:

- `AGENTS.md` is present and defines the Supabase-aligned target architecture.
- `.gitignore` is present and ignores environment files, Streamlit secrets, build outputs, IDE files, logs, and credential-like files.
- Supabase is already present as a persistence backend through `supabase-py` and Streamlit/env secrets.
- The app has admin/member role gates in Streamlit and normalized Supabase table support for `hm_users` and `hm_workflow`.

Not aligned or not yet verified:

- The visible authentication path is Streamlit OIDC/Auth0, not Supabase Auth.
- Supabase Auth usage was not found in the reviewed files.
- Auth0 is used in the Streamlit login flow and member access flow, not only in admin-only code.
- Flutter app files and Flutter Web files were not visible at the checked root/common paths, so Flutter member-app readiness could not be confirmed.
- Member identity maps by email to internal HealthyMe user records, not by Supabase Auth user ID.
- Practitioner role handling was not visible in the reviewed role gates or user-management UI.

Overall: the repo is useful as a Streamlit/admin production base with Supabase persistence support, but it is not yet ready for further Flutter member development under MCD v1.8 until the Supabase Auth identity model, Flutter app location/scaffold, role model, and data ownership gates are documented and approved.

## 2. Files Reviewed

Reviewed files found in the repository:

- `AGENTS.md`
- `.gitignore`
- `requirements.txt`
- `runtime.txt`
- `app.py`
- `components/auth_session.py`
- `components/auth0_management.py`
- `components/db.py`
- `components/guards.py`
- `components/normalized_store.py`
- `components/storage_backend.py`
- `components/ui_common.py`
- `pages/01_Login.py`
- `pages/02_Member_Home.py`
- `pages/10_Admin_Dashboard.py`
- `pages/17_Admin_User_Manager.py`
- `pages/28_Admin_Database_Status.py`
- `pages/30_Admin_User_Access_Manager.py`
- `data/db.json`
- `data/db_sample.json`

Important paths checked but not found at the reviewed locations:

- `README.md`
- `pubspec.yaml`
- `pubspec.lock`
- `lib/main.dart`
- `web/index.html`
- `web/manifest.json`
- `android/app/build.gradle`
- `android/app/build.gradle.kts`
- `ios/Runner/Info.plist`
- `analysis_options.yaml`
- `test/widget_test.dart`
- `supabase/config.toml`
- `supabase/migrations/README.md`
- `.env`
- `.env.example`
- `.streamlit/config.toml`
- `.streamlit/secrets.toml`
- `render.yaml`
- `Procfile`
- `SUPABASE_LAYMAN_CONNECTION_GUIDE.md`

Audit limitation:

- GitHub connector code search returned no results for repository-wide searches, likely because code search indexing was unavailable for this private repository in the connector.
- A temporary local clone was attempted for read-only inspection, but local Git authentication failed with no credentials available. The audit therefore uses direct authenticated connector reads of known and discovered paths rather than a full recursive tree scan.

## 3. Current Authentication Findings

Current visible authentication is Streamlit OIDC/Auth0 based.

Key observations:

- `app.py` routes through `restore_login_from_token()` and then sends authenticated admins to `pages/10_Admin_Dashboard.py` and other users to `pages/02_Member_Home.py`.
- `pages/01_Login.py` displays Auth0/OIDC login copy and calls `st.login("auth0")`.
- `components/auth_session.py` uses `st.user`, `st.user.is_logged_in`, OIDC email extraction, and `st.logout()`.
- After OIDC login, the app maps the authenticated email to an internal HealthyMe user by calling `find_user_by_email_fast(email)` and then `find_user_by_email(email)`.
- The app stores app-level session state values such as `logged_in`, `user_id`, `user_role`, `user_name`, and `oidc_email`.
- `components/guards.py` enforces `require_admin()` and `require_member()` through the app-level `user_role` session value.

Supabase Auth does not appear to be the current login/session source in the reviewed files. The current login source is Streamlit OIDC/Auth0, with HealthyMe authorization resolved by matching OIDC email to a HealthyMe user record.

## 4. Auth0 Findings

Auth0 is present and actively used.

Files with Auth0/OIDC usage:

- `app.py`: comments identify Auth0 redirect behavior and route after login.
- `pages/01_Login.py`: login page copy and `st.login("auth0")` flow.
- `components/auth_session.py`: Streamlit OIDC identity read, app-session restore, and `st.logout()`.
- `components/auth0_management.py`: Auth0 Management API helper functions for provisioning, lookup, blocking/unblocking, profile updates, password setup emails, and deletion helper.
- `pages/17_Admin_User_Manager.py`: creates Auth0 users before saving HealthyMe user records.
- `pages/30_Admin_User_Access_Manager.py`: checks, repairs, blocks/unblocks, and syncs Auth0 user records.
- `components/db.py`: stores `auth_provider`, `auth0_user_id`, and `auth0_email_verified` fields on users.

Assessment against MCD v1.8:

- No Auth0 dependency was found in Flutter code because no Flutter code was visible in the checked paths.
- Auth0 is not limited to admin-only behavior in the current Streamlit app. The visible Streamlit login is also member-facing because successful non-admin users are routed to `pages/02_Member_Home.py`.
- This is a gap against the MCD v1.8 target where Supabase Auth should become the target member authentication source for Flutter Android, iOS, and Web.

## 5. Supabase Findings

Supabase is present, but primarily as a storage/persistence backend rather than the visible authentication provider.

Evidence reviewed:

- `requirements.txt` includes `supabase>=2.0.0`.
- `components/storage_backend.py` creates a Supabase client with `SUPABASE_URL` and either `SUPABASE_SERVICE_ROLE_KEY` or `SUPABASE_ANON_KEY`.
- `components/storage_backend.py` reads/writes a JSON state row in `healthyme_app_state` using `APP_STATE_ID = "healthyme_app_state_v1"`.
- `components/storage_backend.py` can fall back to local JSON state if Supabase is not configured or not reachable.
- `components/normalized_store.py` supports normalized tables `hm_users` and `hm_workflow` and can sync users/workflow from the app state into those tables.
- `pages/28_Admin_Database_Status.py` exposes admin-only checks for Supabase connection status, fallback mode, normalized table status, and manual migration/backup tools.

Not found in reviewed files:

- Supabase Auth login calls.
- Supabase Auth session persistence.
- Supabase Auth user ID as the primary user identity.
- Supabase migration files or `supabase/config.toml` at the checked paths.
- RLS policy definitions in repository paths checked.

Risk note:

- Server-side Streamlit use of a service role key can be acceptable if kept only in platform secrets and never exposed to clients. However, the current helper falls back to either `SUPABASE_SERVICE_ROLE_KEY` or `SUPABASE_ANON_KEY`, so the exact production key model should be documented before Flutter development begins.

## 6. Flutter Web Readiness

Flutter Web readiness is not visible in the reviewed paths.

Checked and not found at root/common Flutter locations:

- `pubspec.yaml`
- `pubspec.lock`
- `lib/main.dart`
- `web/index.html`
- `web/manifest.json`
- `android/app/build.gradle`
- `ios/Runner/Info.plist`
- `analysis_options.yaml`
- `test/widget_test.dart`

Based on this audit, the visible repository appears to be a Streamlit application, not an inspectable Flutter member app. If a Flutter app exists in a nonstandard subdirectory, it was not discoverable through the available connector reads and should be identified explicitly before further Flutter development.

## 7. Member Identity and Role Mapping Risks

Current visible identity mapping:

- OIDC/Auth0 authenticates the browser identity and provides email through `st.user`.
- `components/auth_session.py` maps the OIDC email to a HealthyMe app user.
- `components/normalized_store.py` first attempts to find the user in `hm_users` by email.
- If normalized lookup is unavailable or empty, the app falls back to `components/db.py` and local/app-state user lists.
- Internal `user_id` becomes the main app identity used for profiles, workflow, assessments, messages, daily logs, and reports.

Risks against MCD v1.8 gates:

- Supabase Auth user ID is not visible as the primary identity key.
- Email appears to be the login-time bridge between Auth0/OIDC identity and HealthyMe records. Email-based mapping can drift if email changes in Auth0, Supabase Auth, or app records.
- Role handling in reviewed guards is `member` and `admin`. Practitioner role handling was not visible.
- `pages/30_Admin_User_Access_Manager.py` allows only `member` and `admin` in the role select box.
- Member status is represented by `is_active`; subscription/package status was not confirmed as part of the auth identity mapping in reviewed files.
- Data ownership is keyed to internal `user_id`, not visibly to Supabase `auth.uid()`.
- No RLS policy mapping was visible in repository files reviewed.

## 8. Secrets and Credential Safety Check

Checked paths not found:

- `.env`
- `.env.example`
- `.streamlit/secrets.toml`
- `.streamlit/config.toml`

Secret names referenced in code:

- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `SUPABASE_ANON_KEY`
- `AUTH0_DOMAIN`
- `AUTH0_M2M_CLIENT_ID`
- `AUTH0_M2M_CLIENT_SECRET`
- `AUTH0_CONNECTION`
- `AUTH0_APP_CLIENT_ID`
- `AUTH0_AUDIENCE`

No actual secret values were observed in the reviewed code snippets.

Safety concerns:

- `data/db.json` and `data/db_sample.json` are committed and contain demo user records with password hashes. These appear to be local/demo credentials, but the pattern should be reviewed because committed auth-like state is risky if ever replaced with real member/admin data.
- `components/storage_backend.py` references `SUPABASE_SERVICE_ROLE_KEY`. This must remain server-only and must not be copied into Flutter, browser, frontend, logs, or committed config.
- `.gitignore` now ignores `.env`, `.env.*`, Streamlit secrets files, key/certificate files, and credential-like JSON patterns.

## 9. MCD v1.8 Gap List

* Gap: Supabase Auth is not the visible authentication provider.
  Impact: Further Flutter member development could be built on the wrong auth foundation.
  Recommended action: Create an approved Supabase Auth migration design before Flutter implementation.

* Gap: Auth0/OIDC currently gates member access in Streamlit.
  Impact: Auth0 is not confined to admin-only legacy use in the visible app.
  Recommended action: Define which Streamlit member flows remain temporarily accessible and which member access moves to Flutter/Supabase Auth.

* Gap: No visible Flutter app scaffold or Flutter Web files in checked paths.
  Impact: Flutter Android/iOS/Web readiness cannot be confirmed.
  Recommended action: Identify the Flutter app location or create a documented Flutter scaffold only after the MCD v1.8 auth and data gates are approved.

* Gap: Identity mapping relies on email and internal app `user_id`, not Supabase Auth `auth.uid()`.
  Impact: Email drift or duplicate records could break member ownership and access control.
  Recommended action: Define a canonical identity map: Supabase auth user ID, member profile record, email, role, status, package/subscription status, and legacy Auth0 identifiers if needed.

* Gap: Practitioner role is not visible in reviewed role gates.
  Impact: MCD v1.8 future Practitioner Lite architecture is not yet enabled in access control.
  Recommended action: Document role enum and access model before implementing practitioner-facing functionality.

* Gap: RLS policies and Supabase migration files were not visible in checked paths.
  Impact: Data ownership and API access guarantees cannot be audited from repository state.
  Recommended action: Add reviewed migrations/RLS policy documentation or export schema policy references through an approved database governance process.

* Gap: `data/db.json` is committed with demo user records and password hashes.
  Impact: Demo data can become a privacy/security risk if real member data or credential hashes are ever committed.
  Recommended action: Confirm it is non-production demo data, consider keeping only sanitized seed/sample data, and keep real state in Supabase/platform secrets/backups.

* Gap: Supabase service role key is part of the server-side configuration path.
  Impact: Safe for server-only admin tooling if protected, unsafe for Flutter/frontend exposure.
  Recommended action: Document key usage by runtime surface and prohibit service-role access outside server/admin backends.

## 10. Recommended Next Sprint

Recommended next safe technical sprint: MCD v1.8 Auth and Identity Gate Sprint.

Scope should be documentation-first and review-first:

- Produce a Supabase Auth migration design for member identity.
- Define canonical tables/fields for member identity, role, status, and package/subscription status.
- Decide how existing Auth0/OIDC users map to Supabase Auth users.
- Decide which Streamlit flows remain Auth0/admin-only during transition.
- Define RLS ownership rules before Flutter implementation.
- Identify or create the Flutter member app scaffold only after the auth/data ownership design is approved.
- Add acceptance criteria for Android, iOS, and Flutter Web login/session persistence.

Do not begin Flutter feature development until this sprint output is reviewed by Victor and approved by Vineet.

## 11. Files Changed

* `docs/CODEX_MCD18_READINESS_AUDIT.md`

## 12. Tests/Checks Run

Checks run:

- Read `AGENTS.md` and `.gitignore` from `main`.
- Read direct repository files through the GitHub connector for authentication, storage, user management, role gates, and database status.
- Checked root/common Flutter paths including `pubspec.yaml`, `lib/main.dart`, `web/index.html`, Android, iOS, analysis, and test files.
- Checked root/common Supabase paths including `supabase/config.toml` and `supabase/migrations/README.md`.
- Checked root/common secret paths including `.env` and `.streamlit/secrets.toml`.
- Attempted GitHub connector code searches for Supabase/Auth0/login/logout/session terms; no search results were returned.
- Attempted a temporary read-only local clone for full tree inspection; clone failed because local Git credentials were unavailable.

Build/test status:

- No Flutter build, Flutter analyze, Flutter test, Streamlit runtime test, Supabase query, or database advisor check was run.
- This was an audit/report-only task and no app logic was changed.

## 13. Risks / Open Questions

Risks:

- The report is based on direct file reads and common-path probing, not a complete recursive file inventory.
- If Flutter code exists in a nonstandard folder, it was not visible through the available connector reads.
- Supabase Auth readiness cannot be confirmed from reviewed files.
- RLS readiness cannot be confirmed from reviewed repository files.
- Auth0 currently appears to be used for member-facing Streamlit access.
- Committed `data/db.json` should be reviewed to confirm it contains only sanitized demo data.

Open questions for Vineet/Victor:

- Where is the approved Flutter member app source expected to live in this repository?
- Is Streamlit member access intended to remain temporarily Auth0/OIDC during the Supabase Auth migration?
- What is the canonical Supabase identity map for `auth.users.id`, HealthyMe member profile ID, email, role, status, and package/subscription status?
- Are `hm_users` and `hm_workflow` the approved normalized tables for MCD v1.8, or temporary bridge tables?
- Where are the reviewed Supabase migrations and RLS policies maintained?
- Should committed `data/db.json` remain in the repository, or should only a sanitized sample fixture be retained?
