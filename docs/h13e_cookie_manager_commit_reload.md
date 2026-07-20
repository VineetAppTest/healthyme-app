# H13E — CookieManager Commit Reload

## Deployed finding

After H13D deployment, valid Admin and Member credentials completed the Supabase
password check, but the browser displayed the secure-session retry message and
returned to Login.

H13D is therefore not accepted.

## Root cause

The H13D script was rendered inside a Streamlit component iframe. The iframe could
reload the parent page, but its plain JavaScript cookie write did not reliably create
the marker on the HealthyMe application domain. The reload therefore started with
no durable-session marker and correctly returned to Login.

## Correction

H13E separates the two responsibilities:

1. `extra-streamlit-components` CookieManager writes the opaque marker using its
   application-domain cookie component.
2. A separate zero-height browser component reloads the top-level page.
3. The initial request after reload provides the marker through
   `st.context.cookies`.
4. H13C restores the matching durable Supabase session and HealthyMe role.

The CookieManager is not used to read or confirm the cookie. That avoids the H13B
and H13C asynchronous read-back loop.

The phase changes from `commit` to `reload` before `CookieManager.set` is called.
Therefore, when CookieManager triggers a Streamlit rerun, the next run does not
repeat authentication or the cookie write; it proceeds directly to the browser
reload.

## Database and configuration

No additional SQL migration is required. Continue using:

- `sql/h13c_streamlit_durable_auth_sessions.sql`
- `AUTH_MODE=supabase`
- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- server-only `SUPABASE_SERVICE_ROLE_KEY`

## Mandatory deployed smoke test

1. Sign in as Admin.
2. Confirm the securing message appears briefly and Admin Dashboard opens without
   pressing Retry.
3. Refresh Admin Dashboard and confirm the same Admin remains signed in.
4. Sign out.
5. Sign in as Member.
6. Confirm Member Home opens without pressing Retry.
7. Refresh Member Home, Daily Log and My Schedule.
8. Confirm logout, browser Back and protected direct URLs require a fresh login.

## Acceptance rule

H13E is accepted only after both Admin and Member login complete automatically and
all four protected-page refresh checks pass on the deployed Render service.
