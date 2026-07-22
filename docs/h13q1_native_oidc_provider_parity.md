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

Accepted result on 2026-07-22:

1. Fresh Auth0 login succeeded.
2. Native identity remained present across 10 consecutive refreshes.
3. Closing and reopening the tab restored identity.
4. Logout returned to logged-out state after the exact `/oauth2callback` URL was added to Auth0 Allowed Logout URLs.
5. Three Login-page refreshes remained logged out.

This proves Streamlit Community Cloud native OIDC identity persistence works independently of HealthyMe role, router and Session State logic.

## Deployment B — Supabase comparison

Create a second temporary Streamlit app using the same repository, branch, main file and Python version. Do not replace the accepted Auth0 deployment.

Recommended app URL: `healthyme-identity-parity-b`.

Set `AUTH_TEST_PROVIDER = "supabaseoidc"` and configure the Supabase OIDC provider.

Required Supabase configuration:

- OAuth 2.1 Server enabled.
- OAuth client type: Confidential.
- OAuth client redirect URI: exact Streamlit `/oauth2callback` URL.
- Authorization Path: `/OAuth_Consent`.
- The Supabase Site URL and Authorization Path must combine to the deployed consent page URL.
- OIDC discovery URL: `https://<project-ref>.supabase.co/auth/v1/.well-known/openid-configuration`.
- The Supabase project must use an asymmetric JWT signing key for OIDC ID tokens.

Run the same login, 10-refresh, tab-reopen and logout checks.

## Decision rules

- Auth0 passes, Supabase fails: isolate Supabase OAuth/custom authorization lifecycle.
- Both pass: HealthyMe application role/router restoration is the defect.
- Both fail: investigate Streamlit deployment/version/cookie lifecycle.

## Safety

Production `main`, production secrets, production H13R1 and Flutter remain unchanged. The implementation PR must remain Draft and unmerged until the parity result is recorded.
