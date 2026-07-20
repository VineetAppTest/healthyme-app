# H13R1 — Restore Working Supabase Login

## Deployed finding

H13E did not change the deployed result. Valid Supabase credentials reached the
secure-session step, but the browser returned to Login. Admin and Member could not
reliably enter the application.

H13E is therefore not accepted.

## Immediate recovery

H13R1 removes the browser-cookie handoff from the active Login page and returns to
the last flow that allowed both account types to enter the application:

`Supabase password check → HealthyMe role validation → Admin Dashboard or Member Home`

This is an operational recovery build. It prioritizes restoring access over claiming
that browser refresh persistence has been solved.

## Expected behaviour

- Admin login works.
- Member login works.
- Admin and Member logout remain available.
- Stale Member recovery state must not block a later Admin login.
- A full browser refresh may still require a fresh login.
- The securing/retry loop is removed from the active Login page.

## Why cookie patches stop here

The H13B–H13E attempts relied on custom Streamlit components or iframe JavaScript to
commit and recover an application-domain marker. The deployed browser repeatedly
showed that this mechanism is not dependable enough for production authentication.
Further timing changes would repeat the same architectural weakness.

## Standards-based replacement direction

The next persistence build must use native OpenID Connect rather than a custom
browser marker.

Supabase Auth can operate as an OAuth 2.1/OpenID Connect identity provider. Streamlit
has native OIDC support through `st.login()`, `st.user` and `st.logout()` and manages
its own identity cookie across new sessions. The proposed flow is:

`Streamlit st.login → Supabase OIDC → Streamlit identity cookie → HealthyMe role check`

This requires Supabase OAuth Server enablement, an OAuth client, an authorization UI,
asymmetric JWT signing keys, exact callback configuration and new Render secrets.
It must be prepared as a separate migration sprint rather than another patch to the
password form.

## Smoke test for H13R1

1. Admin login opens Admin Dashboard.
2. Admin logout returns to Login.
3. Member login opens Member Home.
4. Member logout returns to Login.
5. Admin login after the Member cycle opens Admin Dashboard without a Member recovery error.
6. Confirm the securing/retry screen no longer appears.

## Acceptance boundary

H13R1 is accepted as a login-recovery build only. Browser refresh persistence remains
open and moves to the Supabase OIDC sprint.
