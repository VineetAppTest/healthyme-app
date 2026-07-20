# H13A — Streamlit Supabase Auth Stability Correction

## Objective

Correct the failed H13 smoke-test items before starting Flutter Admin Lite:

- normal browser refresh must retain an active Supabase Admin or Member login;
- a stale Member recovery hint must not block a later explicit Admin login;
- logout and login-page layout must remain stable.

Streamlit remains on `AUTH_MODE=supabase`; this build does not add another production authentication route.

## Changes

- A successful Supabase login creates a random opaque browser-session marker.
- The browser receives only that marker in a Secure, SameSite cookie. Supabase access and refresh tokens remain in the Streamlit server process.
- Normal browser refresh restores the matching server-side session and re-applies the authorized HealthyMe role.
- Expiring Supabase access tokens are refreshed through the server-held refresh token.
- Active user-role data is cached briefly for refresh speed and periodically revalidated.
- Logout attempts Supabase remote sign-out, removes the server record, expires both the current v2 marker and retired v1 marker, and clears HealthyMe state.
- The authenticated HealthyMe role is authoritative after login. A stale `_hm_expected_login_role=member` recovery hint no longer rejects a valid Admin login.
- The H13 reserved login/error/logout status areas and single-step logout flow are retained.

## Security boundaries

- No password, access token, or refresh token is written to query parameters.
- No authentication token is written to browser local storage.
- No password, access token, or refresh token is written to the browser cookie.
- The opaque marker cannot authenticate without its matching process-local server record.
- A Render process restart clears that server record. The stale marker is then expired and the user receives one clean request to sign in again.

## Expected login timing

The first Admin or Member login still performs Supabase authentication and HealthyMe role resolution over the network. A few seconds can therefore occur on the initial login. Normal protected-page navigation and browser refresh should not repeat the complete login sequence.

## Deployment smoke test

### Admin refresh

1. Confirm `AUTH_MODE=supabase` in the deployed Streamlit environment.
2. Sign in using an authorized Supabase Admin account.
3. Refresh Admin Dashboard.
4. Open another protected Admin page and refresh it.
5. Confirm the same Admin remains signed in and no Member recovery message appears.

### Member refresh

1. Sign in using an authorized Supabase Member account.
2. Refresh Member Home.
3. Open Daily Log and refresh.
4. Open My Schedule and refresh.
5. Confirm the same Member remains signed in on all four pages.

### Role switching

1. Admin login → logout.
2. Member login → logout.
3. Attempt Admin login again.
4. Confirm Admin Dashboard opens and no “member account was being recovered” error appears.

### Logout protection

1. Log out from Admin and Member separately.
2. Use browser Back.
3. Open a protected-page direct URL.
4. Confirm the prior session is not restored and a fresh login is required.

### Login layout

1. Submit invalid credentials.
2. Confirm the login form and wellness-journey panel remain top-aligned.
3. Confirm the error and signed-out messages use the reserved status area.

## Exclusions

- No Flutter or Admin Lite change.
- No SQL or Supabase schema change.
- No assessment, report, recommendation, or member-data logic change.
