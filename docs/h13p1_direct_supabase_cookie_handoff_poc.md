# H13P1 — Direct Supabase top-level cookie handoff PoC

## Objective
Resolve Streamlit refresh logout without relying on Streamlit native OIDC identity restoration.

## Security boundary
- Supabase access and refresh tokens remain only in the restricted server-side durable-session table.
- The browser receives only `hm_supabase_sid_v2`, a random opaque marker.
- No password, access token, refresh token, email address or user ID is placed in the URL, localStorage, UI or logs.
- The browser marker uses `Path=/`, `SameSite=Strict`, `Secure` on HTTPS and a bounded `Max-Age`.

## Why this differs from H13D/H13E
The previous handoff wrote the marker through an iframe-based third-party Streamlit component. H13P1 uses Streamlit 1.59 `st.html(..., unsafe_allow_javascript=True)`, which executes trusted JavaScript in the top-level app DOM rather than an iframe.

## Flow
1. The user signs in directly with Supabase email and password.
2. HealthyMe creates the durable server-side session and random opaque marker.
3. The Session Handoff page writes the marker as a first-party cookie.
4. The browser opens a fresh root session.
5. `st.context.cookies` supplies the marker to the server.
6. HealthyMe restores the Supabase tokens and Admin or Member role before opening the protected page.
7. Logout revokes the durable session, signs out from Supabase and expires the opaque browser cookie through the same top-level mechanism.

## Temporary deployment
- Repository: `VineetAppTest/healthyme-app`
- Branch: `h13p1-supabase-cookie-handoff-poc`
- Main file: `app.py`
- Python: `3.11`
- Secrets: use `.streamlit/secrets.h13p1.example.toml`

## Acceptance gates
1. Admin login opens Admin Dashboard.
2. Admin refresh passes 5/5.
3. Logout works with one click.
4. Login refresh remains logged out 3/3.
5. Member login opens Member Home.
6. Member refresh passes 5/5.
7. Admin → logout → Member → logout → Admin passes.
8. Root and direct protected URLs restore the correct role.
9. Diagnostics show the opaque cookie and HealthyMe role without exposing values.
10. Production H13R1 remains untouched until a separate cutover is approved.
