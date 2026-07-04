# H12 Streamlit Supabase Admin Cutover

## Purpose

H12 makes the Streamlit app ready to run in strict Supabase mode for both admin and member access.

## Main change

When `AUTH_MODE` is set to `supabase`, Streamlit login restore and protected page guards now use only the Supabase session path. The older login path remains available only when the configured mode allows it.

## Configuration modes

- `AUTH_MODE=auth0` keeps the legacy Streamlit login path.
- `AUTH_MODE=dual` allows controlled migration testing.
- `AUTH_MODE=supabase` runs the cutover mode.

## Smoke test

1. Set `AUTH_MODE=supabase` in the Streamlit environment or secrets.
2. Open Login and confirm only the Supabase login path is shown.
3. Login as a Supabase admin user.
4. Confirm Admin Dashboard opens.
5. Open Supabase Provisioning Workbench.
6. Open Supabase Auth Cutover Readiness.
7. Open a protected admin page by direct URL after login and confirm access works.
8. Logout and confirm a protected page requires login again.
9. Login as a member and confirm Member Home opens.
10. Login with a non-authorized Supabase user and confirm access is blocked.
11. Switch back to `AUTH_MODE=dual` only if rollback is needed.

## Acceptance rule

H12 is accepted when Streamlit can operate with `AUTH_MODE=supabase` for admin and member access, while fallback modes remain available by configuration.
