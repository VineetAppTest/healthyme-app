# HealthyMe Streamlit Admin — Sprint 3A/3B H3

## Scope
Supabase admin direct-page no-logout guard hotfix.

## Fix
- Protected admin/member pages no longer switch immediately to Login when a direct URL is opened without a valid in-app role session.
- Direct admin URLs now show an access-required card instead of behaving like a logout.
- Already-resolved Supabase admin sessions are retained if a transient role refresh fails during a protected-page guard check.
- Stale `signed_out` / `logout_requested` flags are cleared when a resolved Supabase session is already present.

## SQL
No new SQL required. Keep `RUN_ONCE_SUPABASE_ADMIN_ROLE_MODEL_SPRINT3A_3B.sql` already run.

## UAT
1. Supabase admin login -> Admin Dashboard opens.
2. From in-app navigation, open Supabase Auth Provisioning Workbench -> page opens.
3. If opening a hard-refreshed/pasted direct URL starts a fresh Streamlit session, the page shows Admin access required instead of forcing logout.
4. Supabase member login -> direct admin page shows Admin access required.
5. Auth0 admin login -> admin pages still open.
