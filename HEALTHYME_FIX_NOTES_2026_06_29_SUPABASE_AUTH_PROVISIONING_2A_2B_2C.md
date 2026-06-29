# HealthyMe Streamlit Admin — Supabase Auth Provisioning Sprint 2A + 2B + 2C

## Scope

This build adds the admin/server-side provisioning bridge required before wider Supabase Auth rollout.

- Sprint 2A: single member Supabase Auth provisioning
- Sprint 2B: batch existing member provisioning
- Sprint 2C: provisioning audit log

## Key files

- `pages/34_Admin_Supabase_Auth_Provisioning_Workbench.py`
- `components/supabase_provisioning.py`
- `RUN_ONCE_SUPABASE_AUTH_PROVISIONING_SPRINT2A_2B_2C.sql`

## What changed

- Replaced the earlier readiness-only workbench with an execution-capable admin provisioning page.
- Added single-member dry run and execution flow.
- Added batch dry run and execution flow.
- Added audit log read/write helper.
- Added safeguards for inactive members, duplicate emails and non-member roles.
- Added safe `hm_users.auth_user_id` linking to existing or newly created Supabase Auth users.
- Kept Streamlit login/Auth0 behavior unchanged.

## Required setup before UAT

Run this SQL once in Supabase SQL Editor:

`RUN_ONCE_SUPABASE_AUTH_PROVISIONING_SPRINT2A_2B_2C.sql`

Confirm Streamlit secrets contain:

```toml
SUPABASE_URL = "..."
SUPABASE_ANON_KEY = "..."
SUPABASE_SERVICE_ROLE_KEY = "..."
```

Optional:

```toml
SUPABASE_PASSWORD_RESET_REDIRECT_TO = "healthyme://reset-password/"
```

## Smoke test

1. Open Streamlit Admin as admin.
2. Open `Admin Supabase Auth Provisioning Workbench`.
3. Confirm configuration check is green.
4. Run single-member dry run.
5. Execute single-member provisioning after typing `PROVISION`.
6. Confirm `hm_users.auth_user_id` is populated.
7. Confirm audit row is visible.
8. Run batch dry run.
9. Execute batch only after dry run looks correct.
10. Confirm provisioned member can login through Flutter Supabase Auth.

## Non-scope

- No Streamlit admin Supabase login cutover.
- No Auth0 removal.
- No admin-role Supabase provisioning.
- No Flutter service-role usage.
