# H13B — Streamlit Supabase Cookie Confirmation Handoff

## Objective

Correct the deployed H13A browser-refresh failure before starting Flutter Admin Lite.

The deployed smoke test showed that Admin Dashboard, Member Home, Daily Log and My Schedule all returned to Login after a full browser refresh. The screenshot message was: “Your member session is no longer active. Please sign in again with the member account.”

Streamlit remains on `AUTH_MODE=supabase`; this build does not add another production authentication route.

## Root cause

H13A created the server-side Supabase session record and invoked the browser-cookie component, but immediately routed away from Login. The cookie component is asynchronous and may trigger its own Streamlit rerun. Therefore the page change could occur before the browser had actually committed the opaque session marker.

Pattern observed:

`Supabase login succeeds → server record exists → page switches before cookie confirmation → full refresh starts a new Streamlit session without the marker → protected-page guard returns to Login`

## H13B correction

- A successful Supabase password login no longer routes immediately.
- Login begins a two-phase browser handoff:
  1. write the opaque `hm_supabase_sid_v2` marker;
  2. read all browser cookies back through the component and confirm the exact marker.
- The handoff phase is saved before each component invocation so component-triggered reruns continue safely.
- The cookie manager is initialized once per Streamlit session rather than recreated repeatedly.
- Admin Dashboard or Member Home opens only after browser confirmation succeeds.
- A confirmation timeout fails closed, clears the authenticated session and asks the user to sign in again.
- Supabase access and refresh tokens remain in the process-local server registry; only a random opaque marker is stored in the browser.
- H13A role-switch cleanup, token refresh, logout protection and login-page layout stability are retained.

## Security boundaries

- No password, access token or refresh token is written to query parameters.
- No authentication token is written to browser local storage.
- No password, access token or refresh token is written to the browser cookie.
- The opaque marker cannot authenticate without its matching process-local server record.
- A Render process restart still requires a fresh sign-in because the registry is process-local.

## Deployment smoke test — mandatory before acceptance

### Cookie handoff

1. Sign in as Admin.
2. Confirm a brief “Securing your HealthyMe session…” handoff appears before Admin Dashboard.
3. Repeat with a Member account and confirm Member Home opens only after the handoff.
4. The handoff must complete automatically; the retry button is only a fallback.

### Admin refresh

1. Refresh Admin Dashboard.
2. Open another protected Admin page and refresh it.
3. Confirm the same Admin remains signed in.

### Member refresh

1. Refresh Member Home.
2. Refresh Daily Log.
3. Refresh My Schedule.
4. Confirm the same Member remains signed in on every page.

### Role switching

1. Admin login → logout.
2. Member login → logout.
3. Admin login again.
4. Confirm Admin Dashboard opens without a stale Member recovery error.

### Logout protection

1. Log out from Admin and Member separately.
2. Use browser Back and a protected-page direct URL.
3. Confirm a fresh login is required.

## Acceptance rule

H13B is accepted only after the deployed Render build passes refresh on Admin Dashboard, Member Home, Daily Log and My Schedule. Local or mocked lifecycle tests are not sufficient for this issue.

## Exclusions

- No Flutter or Admin Lite change.
- No SQL or Supabase schema change.
- No assessment, report, recommendation or member-data logic change.
