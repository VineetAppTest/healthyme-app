# H13Q8 — Production Native Auth Cutover Step 1

## Objective
Move the accepted Supabase OIDC and native Streamlit identity architecture from the temporary H13Q7 validation app into a production-parity HealthyMe branch without changing live production.

## Production baseline and rollback
- Production source branch: `main`
- Baseline commit: `331df6ad84d0c5e425a479cc037141c597c769ae`
- Protected rollback branch: `rollback-pre-native-auth-cutover-20260725`
- Cutover branch: `h13q8-production-native-cutover-step1`

No live production deployment or Secret change is permitted in Step 1.

## Accepted source of truth
- H13Q7 branch: `h13q7-full-member-native-integration`
- H13Q7 PR: #183
- Accepted capabilities:
  - `st.login("supabaseoidc")`
  - native `st.user` identity persistence
  - HealthyMe role lookup using email and subject claim
  - central Member/Admin route selection and wrong-role correction
  - real Member Home and enabled Member pages
  - controlled Daily Log write
  - direct-route, refresh, tab-reopen and logout persistence
  - hidden Recipe, Exercise and Supplements routes redirected to Member Home

## Step 1 scope
1. Preserve the production baseline and rollback branch.
2. Create the production-cutover branch from the exact production baseline.
3. Inventory current production auth dependencies before changing them:
   - `app.py`
   - `pages/01_Login.py`
   - `components/guards.py`
   - `components/auth_session.py`
   - `components/supabase_auth_session.py`
   - role-resolution modules
4. Bring across only the accepted native identity, role-resolution and protected-routing architecture from H13Q7.
5. Add a temporary production-parity entry point for Streamlit Community Cloud deployment.
6. Keep current Member and Admin legacy auth code available as rollback-only code during Steps 1–2.
7. Do not remove old session restoration, browser marker, CookieManager or legacy guards in this step.

## Production-parity deployment rule
Deploy this branch to a new temporary Streamlit app. Do not change the live HealthyMe production app URL or production branch.

## Step 1 acceptance
- Temporary production-parity app starts successfully.
- Native login reaches HealthyMe role resolution.
- Member and Admin are routed to the correct protected shell.
- No production database schema change is required.
- Current `main` remains untouched.
- Rollback branch resolves to the original production baseline.

## Six-step migration sequence
1. Production cutover branch and parity shell.
2. Connect full Member application behind native identity.
3. Retire legacy Member auth after Member acceptance.
4. Connect the real Admin/Nutritionist application behind native identity.
5. Controlled live production cutover with immediate rollback readiness.
6. Stabilization, monitoring and final legacy-auth cleanup.

## Stop rule
Return to `rollback-pre-native-auth-cutover-20260725` if there is identity loss, repeated callback failure, role crossover, routing loop, logout failure or multiple unrelated pages failing before page code executes.

## Team readiness after migration
The team must be ready to begin the already identified backlog immediately after migration stabilization. Current tracked examples include:
- Admin/Nutritionist cannot edit existing allocated or unallocated recommendation profiles (#186).
- Daily Log and other date-sensitive pages require explicit member-local timezone handling (#184).
- Scheduling and other practitioner/member time exchanges must show both parties’ local date, time and timezone (#185).
- Remaining Member UI, schedule, Daily Log and profile-builder corrections already recorded in the project backlog.

Authentication migration remains the priority until Step 6 is accepted. Backlog fixes must not be mixed into cutover PRs unless they directly block authentication acceptance.
