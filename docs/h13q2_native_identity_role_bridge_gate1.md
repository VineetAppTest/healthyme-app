# H13Q2 — Native Identity to HealthyMe Role Bridge: Gate 1

## Decision

Bridge the proven H13Q1 native Streamlit OIDC flow into HealthyMe one layer at a time.

Gate 1 adds only the existing HealthyMe role lookup after Streamlit has restored
`st.user`. It deliberately does not add protected-page routing or any legacy page.

## Flow

`st.login("supabaseoidc")`
→ Supabase OAuth authorization
→ Streamlit `/oauth2callback`
→ `st.user`
→ `resolve_app_user(email, sub)`
→ lightweight Admin or Member test screen

## Included

- Isolated app at `native_bridge/native_bridge_app.py`.
- Isolated Supabase authorization route at
  `native_bridge/pages/01_OAuth_Consent.py`.
- Native Streamlit identity lifecycle: `st.login`, `st.user`, `st.logout`.
- Existing HealthyMe role lookup through `components.admin_role_model.resolve_app_user`.
- Safe diagnostics showing only presence/status values.
- Streamlit 1.59 auth dependency.
- Placeholder-only secrets template.

## Explicitly excluded

- Production `app.py`.
- Production Login page.
- Real Admin Dashboard or Member Home.
- `st.switch_page` and protected-page routing.
- Legacy page guards.
- `st.session_state` as an authentication source.
- `hm_supabase_sid_v2`.
- Durable authentication-session table.
- `extra-streamlit-components`.
- CookieManager, custom JavaScript cookie writes, localStorage.
- Retry loops, sleeps, browser bootstrap parameters or reload handoffs.
- Flutter and Admin Lite.

## Deployment

Create a new temporary Streamlit Community Cloud app:

- Repository: `VineetAppTest/healthyme-app`
- Branch: `h13q2-native-identity-role-bridge-gate1`
- Main file: `native_bridge/native_bridge_app.py`
- Python: 3.11
- Authorization path configured in Supabase:
  `https://<assigned-app>.streamlit.app/OAuth_Consent`
- OIDC callback:
  `https://<assigned-app>.streamlit.app/oauth2callback`

Use a new Streamlit `cookie_secret`. Do not reuse the production or H13Q1 secret.

## Acceptance sequence

Run Admin and Member independently.

1. Fresh login.
2. Confirm native identity Present.
3. Confirm email and subject claims Present.
4. Confirm HealthyMe role lookup resolved the correct role.
5. Refresh the root page five consecutive times.
6. Close only the tab and reopen the root URL.
7. Confirm the role still resolves correctly.
8. Logout once.
9. Refresh the logged-out root page three times.
10. Repeat for the other role.

## Acceptance rule

Gate 1 passes only if both Admin and Member complete the full sequence without:

- displaying the login form during an authenticated refresh,
- using any custom session marker,
- losing the native identity,
- resolving the wrong role,
- or requiring a retry/reload workaround.

Do not add routing or real HealthyMe pages until Gate 1 passes for both roles.
