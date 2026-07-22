# H13Q1 native OIDC provider parity test

## Objective

Determine whether the previously successful Auth0 refresh behavior came from Streamlit native OIDC itself, and whether Supabase OIDC can reproduce the same behavior without HealthyMe application logic.

## Isolation rules

The test shell intentionally excludes:

- HealthyMe Admin/Member role lookup
- legacy HealthyMe pages and guards
- Supabase durable-session tables
- custom browser session markers
- JavaScript cookie writing
- localStorage
- application Session State as an authentication source

The main page uses only `st.login()`, `st.user` and `st.logout()`.

## Deployment A — Auth0 baseline

- Repository: `VineetAppTest/healthyme-app`
- Branch: `h13q1-native-oidc-provider-parity`
- Main file: `auth_parity/auth_parity_app.py`
- Python: 3.11
- Provider secret: `AUTH_TEST_PROVIDER = "auth0"`

Acceptance:

1. Fresh Auth0 login succeeds.
2. Native identity remains present across 10 consecutive refreshes.
3. Closing and reopening the tab restores identity.
4. Logout returns to logged-out state.
5. Three Login-page refreshes remain logged out.

## Deployment B — Supabase comparison

Use the same repository, branch, main file and Python version, but set `AUTH_TEST_PROVIDER = "supabaseoidc"` and configure the Supabase OIDC provider.

Supabase OAuth Server must use this app's `/OAuth_Consent` path and exact `/oauth2callback` redirect URI.

Run the same refresh and logout checks.

## Decision rules

- Auth0 passes, Supabase fails: isolate Supabase OAuth/custom authorization lifecycle.
- Both pass: HealthyMe application role/router restoration is the defect.
- Both fail: investigate Streamlit deployment/version/cookie lifecycle.

## Safety

Production `main`, production secrets, production H13R1 and Flutter remain unchanged. The implementation PR must remain Draft and unmerged until the parity result is recorded.
