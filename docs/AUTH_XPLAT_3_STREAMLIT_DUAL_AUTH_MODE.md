# AUTH-XPLAT-3 — Streamlit Dual-Auth Mode Foundation

Status: Stage 3 code scaffold
Scope: Streamlit auth-mode foundation
Date: 2026-06-25

## 1. Purpose

This stage introduces a controlled Streamlit authentication mode switch without removing Auth0.

The goal is to prepare a safe Supabase Auth pilot path while keeping current production behavior unchanged by default.

## 2. Auth mode values

```text
AUTH_MODE = auth0 | dual | supabase
```

Default:

```text
auth0
```

Mode behavior:

```text
auth0     Current Streamlit Auth0/OIDC behavior only.
dual      Auth0 remains available and Supabase Auth pilot login is also shown.
supabase  Supabase Auth login only. Use only after pilot approval.
```

## 3. Files introduced

```text
components/auth_mode.py
components/supabase_auth_session.py
```

## 4. Files updated

```text
app.py
pages/01_Login.py
components/auth_session.py
```

## 5. Safety rules

This stage must not:

- remove Auth0
- remove Auth0 secrets
- change Supabase schema
- run SQL migration
- change Flutter code
- change member data persistence
- change LAF/NSP workflow state
- alter reports/admin evaluation
- expose service-role key to the client

## 6. Expected default behavior

If `AUTH_MODE` is not configured, the app must behave as it did before:

```text
Continue with Auth0
```

No Supabase login form should appear in default mode.

## 7. Supabase pilot behavior

When `AUTH_MODE = dual`, the login page should show:

```text
Continue with Auth0
Pilot only: Supabase Auth login
```

Supabase login should:

1. authenticate against Supabase Auth;
2. resolve the email against existing active `hm_users` authorization;
3. route admin users to Admin Dashboard;
4. route member users to Member Home;
5. block authenticated-but-unauthorized emails.

## 8. Manual UAT after merge

### Default mode smoke test

Do not add `AUTH_MODE` yet.

Expected:

- Login page still shows Auth0 login.
- Existing Auth0 admin login works.
- Existing member login works if currently supported by Auth0/OIDC.
- Logout works.
- No Supabase login form appears.

### Dual mode pilot test

Only after default smoke passes, add this Streamlit secret:

```text
AUTH_MODE = "dual"
```

Expected:

- Auth0 button remains visible.
- Supabase Auth pilot form appears.
- Supabase admin pilot user can login and reach Admin Dashboard.
- Supabase member pilot user can login and reach Member Home.
- Unauthorized Supabase Auth email is blocked.
- Logout clears the app session.

## 9. Rollback

Fast rollback:

```text
Set AUTH_MODE = "auth0" or remove AUTH_MODE from Streamlit secrets.
```

Code rollback anchor:

```text
backup/pre-auth-xplat-current-streamlit-20260625-clean
```

## 10. Next stage

```text
AUTH-XPLAT-4 — Pilot Supabase Auth UAT and Mapping Execution
```

AUTH-XPLAT-4 should only start after this PR is merged and default Auth0 smoke passes.
