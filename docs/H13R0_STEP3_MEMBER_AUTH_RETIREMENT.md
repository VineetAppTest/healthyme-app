# H13R0 Step 3 — Legacy Member Authentication Retirement

## Rollback

- Accepted rollback PR: #191
- Rollback branch: `h13q9-production-full-member-step2`
- Rollback build: `H13Q9-production-parity-full-member-v1`
- Production baseline rollback remains: `rollback-pre-native-auth-cutover-20260725`

## Objective

Make native Streamlit identity (`st.user`) plus HealthyMe role resolution the only active authentication authority for the Member runtime.

## Retired for the Member runtime

- Supabase email/password login form
- durable Supabase session restoration
- custom browser session marker
- CookieManager/localStorage restoration
- Session State as the authentication authority
- legacy `require_member` restoration path
- keepalive/reload authentication workaround
- legacy Member logout and remote password-session clearing

## Retained temporarily

The source files supporting the current Admin/Auth0 and rollback paths remain physically present until Step 4 and final cleanup. They are not called by the H13R0 Member runtime.

## Implementation

- `components/native_member_auth.py` installs the native Member guard, logout, utility bar and disabled keepalive adapters once at startup.
- `production_cutover/production_native_member_auth_only_app.py` runs the accepted H13Q9 full-Member application with build marker `H13R0-production-native-member-auth-only-v1`.
- The real Member pages and database contracts remain unchanged.
- The lightweight Admin regression route remains available to verify role isolation; the real Admin migration remains Step 4.

## Stop rule

Rollback to PR #191 for any of the following:

- native identity loss on refresh or tab reopen
- repeated OAuth callback failure
- Member/Admin role crossover
- routing loop
- logout failure
- failure across multiple unrelated Member pages before page code executes

## Acceptance

- clean logged-out Login page shows H13R0 retirement diagnostics
- fresh Member login reaches real Member Home
- refresh and tab-reopen persistence
- representative read route
- one controlled Daily Log write and refresh
- hidden-route redirect
- downstream Member logout and logged-out persistence
- fresh Admin login and Member-route blocking
