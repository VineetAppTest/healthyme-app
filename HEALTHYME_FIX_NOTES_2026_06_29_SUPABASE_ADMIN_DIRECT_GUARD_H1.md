# HealthyMe Streamlit Admin - Sprint 3A/3B H1 Direct Admin Guard Hotfix

## Issue
Smoke test failed for: Supabase member pilot login should not allow direct admin page access.

## Fix
- Strengthened central admin/member route guard.
- Supabase pilot sessions are now role-refreshed from `hm_users` before admin/member page access.
- Supabase login clears stale Auth0/admin role state before applying the new Supabase identity.
- Provisioning Workbench and Pilot Readiness pages now use the same central `require_admin()` guard as other admin pages.

## Expected result
- Auth0 admin login continues to access admin pages.
- Supabase admin/super_admin login can access admin pages.
- Supabase member login direct admin page access shows `Admin access required`.

## SQL
No new SQL required beyond Sprint 3A/3B role model SQL.
