# H13 — Streamlit Supabase Auth Stability

## Objective

Stabilize the existing Streamlit application before starting Flutter Admin Lite. Streamlit remains on `AUTH_MODE=supabase`; this build does not add a second authentication path.

## Changes

- Root routing restores Auth0/OIDC only when Auth0 is explicitly enabled. In Supabase-only mode, a stale Auth0 browser identity cannot take over routing.
- Supabase access, refresh, and expiry values are retained only in the active Streamlit server session.
- Expiring Supabase access tokens are refreshed through the stored refresh token.
- Logout first attempts Supabase sign-out and then clears all HealthyMe identity, role, and token state regardless of the remote result.
- Login, recovery, error, and logout messages render in reserved-height slots to prevent the login form and adjacent wellness-journey panel from shifting.
- The redundant second “clear session” action is removed for Supabase-only logout.

## Security boundaries

- No password, access token, or refresh token is written to query parameters.
- No authentication token is written to browser local storage.
- Legacy PR #128 cookie markers are not trusted for authentication.
- A Render process restart still requires a fresh sign-in because this build does not introduce a durable browser-session registry or SQL migration.

## Deployment smoke test

### Admin

1. Confirm `AUTH_MODE=supabase` in the deployed Streamlit environment.
2. Open the app in a fresh browser or incognito window.
3. Sign in using an authorized Supabase Admin account.
4. Confirm Admin Dashboard opens directly without an Auth0 screen or admin-login flicker.
5. Refresh Admin Dashboard and one protected admin page.
6. Click Logout and confirm a single clean return to Login with a signed-out message.
7. Use browser Back and a protected-page direct URL; confirm the page does not reopen without a new sign-in.

### Member

1. Sign in using an authorized Supabase Member account.
2. Confirm Member Home opens and the member identity is correct.
3. Open Daily Log and My Schedule, then refresh each page.
4. Click Logout and confirm a single clean return to Login.
5. Use browser Back and a protected-page direct URL; confirm a fresh login is required.

### Login layout

1. Note the top position of the wellness-journey panel before entering credentials.
2. Submit invalid credentials and confirm the panel and login form remain top-aligned.
3. Complete a valid login, log out, and confirm the signed-out message uses the same reserved area without pushing the page down.

## Exclusions

- No Flutter or Admin Lite change.
- No SQL or Supabase schema change.
- No general repository cleanup.
- No assessment, report, recommendation, or member-data logic change.
