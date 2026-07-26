# H13R2 — HealthyMe production cutover (Step 5)

## Objective
Move the fully accepted H13R1 Member and Admin native Supabase OIDC runtime from the temporary role-bridge app to the existing HealthyMe production Streamlit application.

## Production deployment
- Production app: `https://healthymeappbyankita.streamlit.app`
- Existing Streamlit entry: `app.py`
- Cutover build: `H13R2-production-cutover-v1`
- Accepted native fallback: PR #193 / `H13R1-production-native-full-app-v1`
- Immediate production rollback: revert the Step 5 merge commit on `main`

## Code boundary
Step 5 changes the production entry only:

`app.py` → `production_cutover/production_live_cutover_app.py` → accepted H13R1 full native application

The old password-session, Auth0 and legacy page files remain physically available in Git history and are not deleted in Step 5.

## Pre-cutover checklist
Do not merge the Step 5 PR until all items are complete.

1. Keep `healthyme-native-role-bridge` deployed on PR #193 until Step 6 closes the migration.
2. In Supabase OAuth Server, create a new confidential OAuth client for production.
   - Suggested name: `HealthyMe Production Native Identity`
   - Callback URL: `https://healthymeappbyankita.streamlit.app/oauth2callback`
   - Store the generated client ID and client secret securely.
   - Do not overwrite or delete the temporary role-bridge OAuth client.
3. Merge the native auth keys from `production_cutover/secrets.example.toml` into the existing production Streamlit Secrets.
   - Preserve all existing application, Supabase, Resend, Sentry and other secrets.
   - Use a new production-specific `auth.cookie_secret`.
4. Set the Supabase OAuth authorization-page URL to the production app root:
   - `https://healthymeappbyankita.streamlit.app`
   - The root receives `?authorization_id=...` and renders the one-time Supabase authorization screen.
5. Confirm the production Streamlit app is still configured as:
   - repository: `VineetAppTest/healthyme-app`
   - branch: `main`
   - main file: `app.py`
   - Python: `3.11`

## Cutover sequence
1. Merge the Step 5 PR into `main`.
2. Wait for the production Streamlit app to reboot.
3. Open `https://healthymeappbyankita.streamlit.app/Login` in a normal browser window.
4. Confirm build `H13R2-production-cutover-v1` before logging in.
5. Run the production smoke test in the exact order supplied in the PR conversation.
6. Do not delete the temporary role-bridge app or its OAuth client during Step 5.

## Stop rule
Stop testing and roll back immediately for any of these:
- production `/Login` does not show H13R2 after the Streamlit reboot;
- callback failure repeats twice from a fresh `/Login`;
- Member and Admin roles cross routes;
- logout fails to clear native identity;
- refresh or tab reopen loses identity for either role;
- two unrelated real application pages fail before their page logic executes;
- a production database write is corrupted or duplicated unexpectedly.

A single isolated page defect that leaves identity and routing intact may be investigated without rollback, but no broad patch should be attempted during the live cutover window.

## Immediate production rollback
Perform both configuration and code rollback in this order:

1. In Supabase OAuth Server, restore the shared Site URL to:
   - `https://healthyme-native-role-bridge.streamlit.app`
   - Keep Authorization Path as `/`.
2. Revert the Step 5 merge commit on `main`.
3. Wait for Streamlit to redeploy `app.py` from the pre-cutover production state.
4. Confirm the prior production Login flow is restored.
5. Confirm a fresh login still works on the temporary role-bridge fallback app.
6. Leave the production OAuth client and added Secrets in place; the legacy production entry ignores the native `[auth]` configuration.

## Accepted native fallback
PR #193 remains the accepted native full-application runtime. To use the temporary app as the fallback after a production rollback:

- branch: `h13r1-native-full-admin-step4`
- main file: `production_cutover/production_native_full_app.py`
- app: `healthyme-native-role-bridge`

The shared Supabase OAuth Server Site URL must point to:

`https://healthyme-native-role-bridge.streamlit.app`

before starting a fresh login on the temporary fallback app.

## Step 5 acceptance
Step 5 is accepted only after production passes:
- logged-out H13R2 diagnostics;
- fresh Member login, five refreshes, tab reopen, representative read/write and logout;
- fresh Admin login, five refreshes, tab reopen, representative read/write and logout;
- Member/Admin role-crossover blocking;
- logged-out direct-route blocking;
- production root and clean route behavior.

Legacy code deletion is not part of Step 5. It belongs to Step 6 after the production observation window.
