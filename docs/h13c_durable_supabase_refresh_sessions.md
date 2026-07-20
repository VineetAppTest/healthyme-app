# H13C — Durable Supabase-backed Streamlit refresh sessions

## Objective

Replace the H13A/H13B process-local session registry with a durable Supabase
session registry so normal browser refresh can restore the same Admin or Member
across Render processes and Streamlit WebSocket sessions.

## Required deployment order

1. Run `sql/h13c_streamlit_durable_auth_sessions.sql` in the Supabase SQL Editor.
2. In the Render Streamlit service, add the server-only secret:
   - `SUPABASE_SERVICE_ROLE_KEY`
3. Keep the existing values:
   - `AUTH_MODE=supabase`
   - `SUPABASE_URL`
   - `SUPABASE_ANON_KEY`
4. Deploy the H13C Streamlit code.
5. Sign in once again. H13A/H13B browser markers have no durable database row and
   are intentionally expired during the first H13C restore attempt.

Never place `SUPABASE_SERVICE_ROLE_KEY` in Flutter, browser JavaScript, a public
repository, a URL or a user-visible configuration file.

## Session flow

### Login

`Supabase password authentication`
→ `HealthyMe role resolution`
→ `random opaque marker generated`
→ `SHA-256 marker hash + server tokens stored in Supabase`
→ `opaque marker written to the browser cookie`
→ `Admin Dashboard or Member Home`

### Browser refresh

`new Streamlit/WebSocket session`
→ `read opaque browser marker`
→ `hash marker`
→ `load active durable session using the service-role client`
→ `refresh Supabase token when required`
→ `restore HealthyMe Admin or Member role`

### Logout

`load server tokens`
→ `revoke durable row`
→ `attempt Supabase sign-out`
→ `expire current and legacy browser markers`
→ `clear Streamlit identity state`

## Security boundaries

- The raw browser marker is never stored in Supabase.
- The database stores only its SHA-256 hash.
- The browser cookie contains no password, email, role, access token or refresh
  token.
- The session table has RLS enabled and forced.
- No anon or authenticated policy is created.
- All table privileges are revoked from `public`, `anon` and `authenticated`.
- Only the server-side `service_role` can read or change session rows.
- Unknown, expired or revoked markers fail closed.
- Logout clears token values in the revoked row.
- Streamlit continues to use the anon key for normal Supabase Auth. The
  service-role key is used only by the isolated durable session repository.

## Files

- `sql/h13c_streamlit_durable_auth_sessions.sql`
- `components/supabase_durable_session_store.py`
- `components/supabase_auth_session.py`
- `docs/h13c_durable_supabase_refresh_sessions.md`

## Mandatory deployed smoke test

### Admin

1. Sign in as an authorized Admin.
2. Confirm the secure-session handoff completes.
3. Refresh Admin Dashboard.
4. Open and refresh another protected Admin page.
5. Confirm the same Admin remains signed in.

### Member

1. Sign in as an authorized Member.
2. Refresh Member Home.
3. Refresh Daily Log.
4. Refresh My Schedule.
5. Confirm the same Member remains signed in on all three pages.

### Role switching

1. Admin login → logout.
2. Member login → logout.
3. Admin login.
4. Confirm Admin Dashboard opens without a stale Member recovery message.

### Logout protection

1. Log out.
2. Use browser Back.
3. Open a protected-page direct URL.
4. Confirm a fresh login is required.

### Render restart

1. Sign in.
2. Restart or redeploy the Render service.
3. Refresh the browser.
4. Confirm the durable Supabase row restores the same user.

## Acceptance rule

H13C is accepted only after the deployed Render build passes Admin Dashboard,
Member Home, Daily Log and My Schedule refresh. Static validation and mocked
lifecycle tests are necessary but not sufficient.
