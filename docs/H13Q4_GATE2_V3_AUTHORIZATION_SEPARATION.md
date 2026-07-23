# H13Q4 Gate 2 v3 — OAuth authorization separation

## Decision

Separate the Supabase OAuth authorization frontend from the Streamlit native identity and HealthyMe protected-role router.

## App A — HealthyMe native role bridge

- Existing URL: `https://healthyme-native-role-bridge.streamlit.app`
- Main file: `native_bridge/native_bridge_app.py`
- Responsibilities:
  - call `st.login("supabaseoidc")`
  - receive Streamlit `/oauth2callback`
  - restore `st.user`
  - resolve the HealthyMe Admin or Member role
  - route to `/Admin_Dashboard` or `/Member_Home`
  - call `st.logout()`
- Does not register or render `/OAuth_Consent`.

Existing Native Role Bridge OAuth client values remain unchanged:

- Redirect URI: `https://healthyme-native-role-bridge.streamlit.app/oauth2callback`
- Existing Client ID
- Existing Client Secret
- Existing Streamlit cookie secret

## App B — HealthyMe OAuth authorizer

- Suggested URL: `https://healthyme-oauth-authorizer.streamlit.app`
- Main file: `oauth_authorizer/authorization_app.py`
- Responsibilities:
  - receive `authorization_id`
  - authenticate against Supabase with email/password
  - load OAuth request details
  - approve or deny the request
  - follow the `redirect_url` returned by Supabase
- Does not use `st.login`, `st.user`, HealthyMe role lookup, protected routes or logout.

### Streamlit secrets

```toml
SUPABASE_URL = "https://YOUR_PROJECT_REF.supabase.co"
SUPABASE_ANON_KEY = "YOUR_EXISTING_ANON_OR_PUBLISHABLE_KEY"
CLIENT_LOGIN_URL = "https://healthyme-native-role-bridge.streamlit.app/Login"
```

No OAuth Client ID, OAuth Client Secret, `[auth]` section, cookie secret or service-role key belongs in the authorization-only app.

## Deployment order

1. Deploy the authorization-only app first.
2. Open its root URL without `authorization_id`.
3. Confirm build `H13Q4-supabase-oauth-authorizer-v1` and the controlled missing-request message.
4. Change Supabase OAuth Server frontend configuration:
   - Site URL: `https://healthyme-oauth-authorizer.streamlit.app`
   - Authorization Path: `/`
5. Redeploy the existing Native Role Bridge app from branch `h13q4-gate2-v3-oauth-authorizer-separation` using the unchanged main file `native_bridge/native_bridge_app.py`.
6. Confirm build `H13Q4-native-role-protected-routing-gate2-v3-separated-authorizer` on `/Login`.

## Mandatory acceptance

Run Member and Admin independently:

1. Logged-out `/Login` is stable.
2. Continue with Supabase OIDC opens the separate authorization app with `authorization_id`.
3. Authorization completes without manually refreshing the authorization app.
4. Browser finishes on the correct protected route in the Native Role Bridge app.
5. Five direct protected-route refreshes succeed with no Page-not-found modal.
6. Close/reopen direct protected URL succeeds.
7. Wrong-role URL corrects to the authorized route.
8. Root returns to the correct protected route.
9. Logout finishes on `/Login`.
10. Three logged-out `/Login` refreshes remain stable.

## Non-regression boundary

No real HealthyMe page, legacy guard, application Session State authentication, custom browser marker, durable authentication session, CookieManager, localStorage, retry, sleep or browser reload workaround is introduced.
