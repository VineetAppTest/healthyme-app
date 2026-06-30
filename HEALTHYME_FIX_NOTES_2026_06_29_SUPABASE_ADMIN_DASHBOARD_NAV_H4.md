# HealthyMe Streamlit Admin — Sprint 3A + 3B H4

## Build label

v102.4B15S3H4 · Supabase Admin Dashboard Navigation

## Why this hotfix exists

The Streamlit sidebar/page menu is intentionally hidden for the product UX. The previous smoke-test step said to open the Supabase Auth Provisioning Workbench from the sidebar, which is not available in this app configuration.

## Change made

Added explicit Admin Dashboard navigation buttons under System Tools:

- Supabase Auth Readiness
- Supabase Provisioning

These buttons use `st.switch_page(...)`, so they preserve the current Streamlit session better than opening a protected admin page as a fresh/direct URL.

## SQL

No new SQL required.

Keep the Sprint 3A + 3B SQL already run:

`RUN_ONCE_SUPABASE_ADMIN_ROLE_MODEL_SPRINT3A_3B.sql`

## Smoke test

1. Login through Supabase Pilot using an admin/super_admin email.
2. Confirm Admin Dashboard opens.
3. In Admin Dashboard, open System Tools.
4. Click Supabase Provisioning.
5. Expected: Admin Supabase Auth Provisioning Workbench opens.
6. Logout.
7. Login through Supabase Pilot using a member email.
8. Direct admin URL should show Admin access required.
9. Auth0 admin login should still open Admin Dashboard and Supabase Provisioning.
