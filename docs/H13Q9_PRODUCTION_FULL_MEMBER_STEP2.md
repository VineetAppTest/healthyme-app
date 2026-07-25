# H13Q9 — Production Cutover Step 2: Full Member Application

## Objective
Connect the complete currently enabled HealthyMe Member application to the accepted H13Q8 production-parity native Supabase OIDC router, without changing live production and without removing the legacy Member authentication code yet.

## Accepted starting point
- Base branch: `h13q8-production-native-cutover-step1`
- Base build: `H13Q8-production-parity-native-router-v1`
- Accepted PR: #189
- Production rollback branch: `rollback-pre-native-auth-cutover-20260725`

## Step 2 branch and entry
- Branch: `h13q9-production-full-member-step2`
- Entry: `production_cutover/production_full_member_app.py`
- Build: `H13Q9-production-parity-full-member-v1`
- Immediate rollback entry: `production_cutover/production_parity_app.py`

## Implementation
The exact accepted full-Member runtime files from PR #183 are transplanted onto the production-based H13Q8 branch:
- `native_bridge/native_bridge_gate4_app.py`
- `native_bridge/native_bridge_full_member_app.py`
- `native_bridge/full_member_route_registry.py`
- `native_bridge/disabled_member_redirect.py`

The production entry applies only Step 2 build and rollback labels before executing the accepted runtime. The existing HealthyMe Member pages continue to run from their current `pages/*.py` files.

## Enabled Member scope
- Member Home
- Today's Plan
- Daily Log
- My Schedule
- My Weekly Plan
- My Profile
- LAF
- NSP Page 1
- NSP Page 2
- Submit / Status
- Body–Mind Connection
- Other current Member pages discovered by the accepted `require_member` registry rule

## Hidden and disabled Member scope
The following remain in source for possible future activation but are excluded from Member navigation and direct access:
- Recipe Repository and recipe-detail routes
- Exercise Repository and exercise-detail routes
- Member Supplements and supplement-detail routes

Direct access must return silently to Member Home without a technical modal.

## Deliberately retained during Step 2
Legacy Member auth files, custom marker support, durable-session code and legacy guards remain physically present for rollback. They must not act as the authentication source inside the H13Q9 entry. Removal happens only in Step 3 after Step 2 acceptance.

## Stop and rollback rule
Return the temporary Streamlit deployment to:
- Branch: `h13q8-production-native-cutover-step1`
- Entry: `production_cutover/production_parity_app.py`

Rollback immediately for native identity loss, repeated callback failure, routing loop, role crossover, logout failure, or failure across multiple unrelated Member pages before page code executes. An isolated page-specific failure remains on H13Q9 for diagnosis.

## Focused acceptance
1. `/Login` shows H13Q9 build and native identity absent.
2. Fresh Member login reaches the real Member Home.
3. Refresh and tab reopen preserve identity.
4. Today's Plan, My Schedule and My Weekly Plan open.
5. Daily Log loads and one controlled write persists.
6. LAF → NSP1 → NSP2 → Submit/Status and Body–Mind routes open.
7. Hidden Recipe, Exercise and Supplement URLs return silently to Member Home.
8. Logout from a downstream route returns to `/Login`; three refreshes remain logged out.
9. Fresh Admin login reaches the lightweight Admin shell; direct Member URLs correct to Admin.

## Excluded
- No live production deployment.
- No legacy Member-auth deletion.
- No real Admin/Nutritionist page migration.
- No unrelated backlog fixes.
