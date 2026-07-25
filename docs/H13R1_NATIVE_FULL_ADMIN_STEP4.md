# H13R1 Step 4 — Native full Admin application

## Objective

Connect the real HealthyMe Admin application to the accepted native Supabase OIDC identity and central role router while preserving the fully accepted Member runtime from Step 3.

## Branch and rollback

- Step 4 branch: `h13r1-native-full-admin-step4`
- Step 4 entry: `production_cutover/production_native_full_app.py`
- Step 4 build: `H13R1-production-native-full-app-v1`
- Immediate rollback PR: #192
- Immediate rollback branch: `h13r0-retire-legacy-member-auth-step3`
- Immediate rollback entry: `production_cutover/production_native_member_auth_only_app.py`
- Immediate rollback build: `H13R0-production-native-member-auth-only-v1`
- Production baseline rollback remains: `rollback-pre-native-auth-cutover-20260725`

## Active identity flow

`st.login("supabaseoidc")` → Streamlit callback → `st.user` → HealthyMe role resolution → central hidden router → native Member/Admin guard → real application page

## Included

- Accepted full Member route registry and native Member guard from Step 3.
- Real Admin Dashboard at `/Admin_Dashboard`.
- All current Dashboard-linked Admin pages.
- Automatic discovery of additional production pages that call/import `require_admin` or use the Admin filename contract.
- Native Admin guard backed only by `st.user` and HealthyMe role resolution.
- Native logout on real Admin pages.
- Role-aware utility bar.
- Legacy Admin keepalive disabled during native execution.
- Admin direct Member-route correction and Member direct Admin-route correction.
- Existing database and UI contracts remain unchanged.

## Authorization boundary

Current production authorization is preserved:

- `admin` and `super_admin`: full Admin application.
- `member`: Member application only.
- `nutritionist` and `practitioner`: not silently promoted to Admin. The current role model identifies these as future staff roles without full Admin access.

## Not deleted in Step 4

Legacy Auth0/Admin source remains physically available for rollback and final cleanup. The Step 4 runtime does not invoke it for native Admin authentication.

## Temporary deployment

- Repository: `VineetAppTest/healthyme-app`
- Branch: `h13r1-native-full-admin-step4`
- Main file: `production_cutover/production_native_full_app.py`
- Subdomain: `healthyme-native-role-bridge`
- Python: 3.11
- Secrets: reuse the accepted native Supabase OIDC Secrets without modification.

## Mandatory acceptance

### Logged out

- Correct H13R1 build on `/Login`.
- Native identity absent.
- Native Member/Admin guards installed.
- Auth0 restore inactive.
- No custom marker, durable auth session or legacy keepalive.

### Admin

- Fresh Admin login reaches the real Admin Dashboard.
- Dashboard refresh 5/5.
- Direct Dashboard after tab close/reopen.
- Representative Dashboard routes render: Review, Evaluation Status, User Manager, Recommendation Profile Builder, Daily Logs, Scheduling and Database.
- At least one safe Admin write/edit workflow saves and survives refresh.
- Direct Member route corrects to Admin Dashboard.
- Native logout and logged-out refresh 3/3.

### Member regression

- Fresh Member login reaches the accepted real Member Home.
- Refresh and tab reopen persistence.
- Representative read route and Daily Log write still pass.
- Direct Admin route corrects to Member Home.
- Native logout remains clean.

## Stop rule

Rollback immediately to PR #192 for identity loss, repeated callback failure, role crossover, routing loops, logout failure, or failure across multiple unrelated Admin pages before their page code executes.

Do not change the live HealthyMe production app in Step 4.
