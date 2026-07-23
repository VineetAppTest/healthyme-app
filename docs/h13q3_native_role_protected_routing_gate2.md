# H13Q3 — Native Identity + HealthyMe Role + Protected Routing: Gate 2

## Decision

Build directly on the accepted H13Q2 Gate 1 baseline and add exactly one new layer:
lightweight protected routing.

## Flow

`st.login("supabaseoidc")`
→ Supabase authorization
→ Streamlit `/oauth2callback`
→ native `st.user`
→ `resolve_app_user(email, sub)`
→ central `st.navigation` router
→ lightweight `/Admin_Dashboard` or `/Member_Home`

## Included

- The accepted Gate 1 native identity and HealthyMe role lookup.
- A central `st.navigation(..., position="hidden")` entrypoint.
- Lightweight protected routes:
  - `/Admin_Dashboard`
  - `/Member_Home`
- `/Login`, `/OAuth_Consent`, and `/` routing.
- Role-aware correction:
  - Admin opening Member Home is returned to Admin Dashboard.
  - Member opening Admin Dashboard is returned to Member Home.
- Direct native `st.logout()` from each protected test page.
- Safe route, identity, cookie, and role diagnostics without values.

## Explicitly excluded

- The real Admin Dashboard.
- The real Member Home.
- Any other HealthyMe page.
- Legacy `pages/` guards and page defaults.
- Existing HealthyMe login/session restoration code.
- Application Session State as the authentication source.
- `hm_supabase_sid_v2` and the durable authentication-session table.
- CookieManager, custom cookie writes, localStorage, retry loops, sleeps,
  browser reloads, bootstrap parameters, or recovery redirects.
- Flutter and Admin Lite.

## Deployment

Reuse the existing temporary Streamlit app and existing Gate 1 configuration.

- App: `healthyme-native-role-bridge.streamlit.app`
- Branch: `h13q3-native-role-protected-routing-gate2`
- Main file: `native_bridge/native_bridge_app.py`

No new Supabase OAuth client, callback URL, authorization path, cookie secret,
or Streamlit Secrets change is required because the deployed app URL is unchanged.

## Mandatory Admin acceptance

1. Logged out root routes to `/Login`.
2. Fresh Admin login routes automatically to `/Admin_Dashboard`.
3. Refresh `/Admin_Dashboard` five consecutive times.
4. Close only the tab; reopen the direct `/Admin_Dashboard` URL.
5. Open `/Member_Home` while signed in as Admin; confirm automatic return to
   `/Admin_Dashboard`.
6. Open `/`; confirm automatic return to `/Admin_Dashboard`.
7. Logout once.
8. Refresh `/Login` three consecutive times and remain logged out.

## Mandatory Member acceptance

1. Fresh Member login routes automatically to `/Member_Home`.
2. Refresh `/Member_Home` five consecutive times.
3. Close only the tab; reopen the direct `/Member_Home` URL.
4. Open `/Admin_Dashboard` while signed in as Member; confirm automatic return to
   `/Member_Home`.
5. Open `/`; confirm automatic return to `/Member_Home`.
6. Logout once.
7. Refresh `/Login` three consecutive times and remain logged out.

## Acceptance rule

Gate 2 passes only if both roles complete the full sequence without:

- displaying the Login page during an authenticated protected-route refresh,
- opening the wrong role route,
- losing the native identity,
- requiring another login,
- relying on Session State authentication, a custom marker, durable session,
  retry, sleep, or browser reload workaround.

Do not connect a real HealthyMe page until Gate 2 passes for both roles.
