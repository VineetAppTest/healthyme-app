# AUTH-XPLAT-3 — Streamlit Dual-Auth Mode Scaffold

Status: Stage 3 code scaffold
Date: 2026-06-25

## 1. Purpose

Introduce a safe Streamlit authentication mode switch so HealthyMe can test Supabase Auth without removing the existing Auth0/OIDC login.

This stage is intentionally conservative.

## 2. What this stage adds

A new authentication mode helper:

```text
AUTH_MODE = auth0 | dual | supabase
```

Default behavior:

```text
AUTH_MODE defaults to auth0
```

That means the live app should continue using the current Auth0/OIDC login unless AUTH_MODE is explicitly changed in Streamlit secrets or environment.

## 3. Mode behavior

### auth0

Current production-safe behavior.

- Shows Auth0 login only.
- Uses `st.login("auth0")`.
- Existing Streamlit OIDC restore remains active.

### dual

Pilot mode.

- Shows Auth0 login.
- Shows Supabase pilot login.
- HealthyMe still checks whether the authenticated email exists in `hm_users` and is active.
- No public signup is added.
- No user creation is added.

### supabase

Future testing mode.

- Shows Supabase login only.
- Still resolves HealthyMe role/access through `hm_users`.
- Intended only after pilot readiness is confirmed.

## 4. Guardrails

This stage does not:

- remove Auth0
- change Supabase database schema
- execute SQL
- create users
- add public signup
- change admin/member business logic
- change workflow status
- change reports
- touch secrets files
- touch deployment files

## 5. Required secrets for Supabase pilot path

The Supabase pilot login path requires existing Streamlit secrets/environment values:

```text
SUPABASE_URL
SUPABASE_ANON_KEY
```

The Supabase pilot login path must not use the service-role key.

## 6. Pilot test sequence

Do not change AUTH_MODE directly in production until ready.

Recommended controlled test:

1. Confirm Auth0 mode still works with no AUTH_MODE setting.
2. Set `AUTH_MODE = "dual"` only during a controlled test window.
3. Test Auth0 admin login still works.
4. Test one Supabase Auth member login.
5. Test one Supabase Auth admin login.
6. Confirm unauthorized Supabase Auth email is blocked.
7. Confirm logout works for both login paths.
8. Return AUTH_MODE to `auth0` if anything is wrong.

## 7. Rollback

Immediate rollback:

```text
Set AUTH_MODE = "auth0"
```

Code rollback:

```text
Use branch backup/pre-auth-xplat-current-streamlit-20260625-clean
```

## 8. Next stage

AUTH-XPLAT-4 should be the controlled pilot:

- one admin
- one member
- no broad migration
- no Auth0 removal
