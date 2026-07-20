# H13G1 — Direct Supabase Session Gateway PoC

## Decision

Keep Supabase Auth and the existing email/password experience. Do not start OIDC.
Move only browser-session ownership out of Streamlit and into a small HTTP service.

## Production safety

H13R1 remains the production login path. H13G1 is isolated and must not replace the
working login until the deployed proof of concept passes.

## Target pattern

`Gateway login form`
→ `Supabase password authentication`
→ `durable session row`
→ `Secure/HttpOnly parent-domain cookie`
→ `Streamlit initial request`
→ `HealthyMe role restoration`

## Scope

- FastAPI gateway under `auth_gateway/`.
- Reuse `public.hm_streamlit_auth_sessions`.
- Store only the SHA-256 hash of the browser marker in Supabase.
- Keep Supabase access and refresh tokens server-side.
- Issue and delete the browser cookie through real HTTP responses.
- Redirect back only to the configured Streamlit origin.
- Include signed, short-lived form tokens.
- Include `/healthz`, `/login` and `/logout`.

## Deployment sequence

1. Keep PR #167 deployed and validate basic Admin/Member login.
2. Create a separate Render web service from `auth_gateway/Dockerfile`.
3. Configure `auth.healthyme.in`.
4. Add all required server-side environment variables.
5. Set the exact deployed Streamlit login URL in `STREAMLIT_RETURN_URL`.
6. Confirm both services are under the controlled `healthyme.in` parent domain.
7. Open the gateway `/login` directly for the PoC.
8. Do not expose the gateway option on the main login page until testing passes.

## Acceptance

- Admin login completes.
- Member login completes.
- Admin Dashboard refresh retains Admin.
- Member Home, Daily Log and My Schedule refresh retain Member.
- Gateway logout revokes the durable row and expires the cookie.
- Browser Back and protected direct URLs require login after logout.
- No credential or Supabase token appears in browser cookies, URLs or local storage.
- Login and refresh timings are recorded.
- Render restart does not destroy an active session.

## Non-goals

- OIDC.
- Auth0.
- Flutter Admin Lite.
- Visual redesign.
- Assessment, reports, schedule or recommendation changes.
- Immediate production cutover.
