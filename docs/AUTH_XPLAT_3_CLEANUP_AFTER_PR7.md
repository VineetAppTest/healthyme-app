# AUTH-XPLAT-3 — Clean Stage 3 Recovery After PR #7

Status: corrective Stage 3 cleanup
Scope: Streamlit auth-mode scaffold cleanup
Date: 2026-06-25

## 1. Why this corrective PR exists

PR #7 was merged before the newer Stage 3 foundation PR was merged. This corrective PR is based on the current `main` after PR #7 and cleans the Stage 3 implementation without removing Auth0.

## 2. What this cleanup keeps

- Auth0 remains the default login path.
- `AUTH_MODE` remains optional.
- If `AUTH_MODE` is not set, behavior must remain Auth0-only.
- No Supabase schema change is made.
- No SQL migration is executed.
- No Flutter code is touched.
- No LAF/NSP/workflow/report behavior is changed.

## 3. What this cleanup improves

- Root routing can now restore a Supabase pilot session when `AUTH_MODE` allows it.
- Supabase pilot session state is tracked consistently.
- Supabase pilot logout clears only the app session and does not force the Auth0/OIDC logout path.
- Login page copy clearly marks Supabase as pilot-only in dual mode.
- Supabase login remains hidden unless `AUTH_MODE` is `dual` or `supabase`.

## 4. Expected default behavior

With no `AUTH_MODE` secret configured:

```text
Login page shows Auth0 only.
Supabase login form does not appear.
Existing Auth0 login continues to work.
Existing logout continues to work.
```

## 5. Dual mode pilot behavior

Only after default smoke passes, set:

```text
AUTH_MODE = "dual"
```

Expected:

```text
Auth0 login remains visible.
Supabase Auth pilot login appears.
Authorized Supabase admin routes to Admin Dashboard.
Authorized Supabase member routes to Member Home.
Unauthorized Supabase Auth email is blocked.
```

## 6. Rollback

Fast rollback:

```text
Remove AUTH_MODE or set AUTH_MODE = "auth0".
```

Code rollback anchor:

```text
backup/pre-auth-xplat-current-streamlit-20260625-clean
```

## 7. Next stage

After this cleanup PR is merged and default Auth0 smoke passes:

```text
AUTH-XPLAT-4 — Pilot Supabase Auth UAT Readiness
```
