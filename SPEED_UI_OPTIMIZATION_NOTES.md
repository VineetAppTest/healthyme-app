# HealthyMe Speed / UI Optimization Notes

Implemented in this build:

## 1. Sidebar flash reduction
- Default Streamlit sidebar/nav is hidden with global CSS.
- All pages use `initial_sidebar_state="collapsed"`.

Reason:
- HealthyMe uses its own role-based navigation.
- Streamlit's default multipage sidebar can briefly appear during page load.
- Hiding it improves perceived polish.

## 2. Auth0 Management API only on button clicks
- The app does not call Auth0 Management API on every page load.
- User Access Manager calls Auth0 only when admin clicks:
  - Check Auth0 Status
  - Resend Password Setup Email
  - Save Changes

Reason:
- Avoid unnecessary network delay.

## 3. Dashboard optimization retained
- Dashboard uses consolidated snapshot logic from previous stability build.
- Database Status active health check remains separate.

## 4. Recommended future speed upgrade
If app still feels slow with more users:
- Normalize Supabase storage into separate tables:
  - users
  - workflow
  - laf_responses
  - nsp_responses
  - admin_assessments
  - reports
  - audit_logs
- Current JSONB app-state approach is safe for MVP but can get heavier as data grows.