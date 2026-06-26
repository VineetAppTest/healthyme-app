# AUTH-XPLAT-5A Dual Mode Session Priority

## Purpose

AUTH-XPLAT-5A clarifies and fixes session restore priority during controlled Supabase Auth pilot testing.

In `AUTH_MODE = "dual"`, HealthyMe can have an active Auth0/OIDC browser identity and a Supabase pilot session in Streamlit state. During pilot testing, the Supabase pilot session must win when it exists so a Supabase member test is not routed back to an existing Auth0 admin session.

## What Changed

- Root routing in `app.py` now restores a Supabase pilot session first when Supabase Auth is enabled.
- The login page in `pages/01_Login.py` uses the same order.
- If no Supabase pilot session exists, Auth0/OIDC restore still runs normally.
- Dual-mode logout copy now warns that an Auth0 browser identity may remain active and that `Complete secure logout` should be used before switching from Auth0 admin testing to Supabase member testing.

## Restore Order

When Supabase Auth is enabled by `AUTH_MODE = "dual"` or `AUTH_MODE = "supabase"`:

1. Try to restore the Supabase pilot session.
2. If no Supabase pilot session is restored, try Auth0/OIDC restore.
3. Route by the restored HealthyMe role.
4. If nothing restores, show the Login page.

When `AUTH_MODE` is unset or `AUTH_MODE = "auth0"`, Supabase Auth is not enabled and the existing Auth0/OIDC restore behavior remains the default path.

## What This Stage Does Not Do

- Does not change default `AUTH_MODE`.
- Does not enable Supabase login by default.
- Does not change Streamlit secrets.
- Does not change Auth0 settings.
- Does not execute SQL.
- Does not change Supabase schema.
- Does not create or update users.
- Does not touch Flutter.
- Does not change LAF, NSP, workflow, reports, or admin evaluation behavior.
- Does not touch deployment files or GitHub Actions.

## Pilot Test Steps

In `AUTH_MODE = "dual"`:

1. Sign in as an Auth0 admin and confirm admin routing still works.
2. Use logout.
3. If switching to Supabase member testing, click `Complete secure logout` so the Auth0 browser identity is cleared.
4. Sign in as Supabase admin and confirm admin routing works.
5. Sign out.
6. Sign in as Supabase member and confirm member routing works.
7. Confirm the Supabase member is not routed back to the prior Auth0 admin when the Supabase session is active.
8. Confirm unauthorized Supabase users remain blocked.
9. Confirm logout still works.

## Rollback

Fast rollback:

```text
Remove AUTH_MODE or set AUTH_MODE = "auth0"
```

Code rollback branch:

```text
backup/pre-auth-xplat-current-streamlit-20260625-clean
```

## Risks / Open Questions

- Auth0 browser identity can still exist outside Streamlit session state until the Auth0/OIDC logout flow is completed.
- Supabase pilot session priority only applies when Supabase Auth is enabled by `AUTH_MODE`.
- Deployed Streamlit testing is required to confirm direct browser behavior across Auth0 and Supabase pilot sessions.
