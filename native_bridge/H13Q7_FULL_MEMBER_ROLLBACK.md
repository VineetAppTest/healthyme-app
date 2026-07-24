# H13Q7 — Consolidated full Member integration

## Purpose

This branch consolidates the former Gates 5, 6 and 7 into one temporary deployment while preserving the accepted Gate 4 deployment as the hard rollback point.

## Consolidated build

- Branch: `h13q7-full-member-native-integration`
- Entry file: `native_bridge/native_bridge_full_member_app.py`
- Build: `H13Q7-native-full-member-app-v1`

## Hard rollback point

- Branch: `h13q6-gate4-native-real-todays-plan`
- Entry file: `native_bridge/native_bridge_gate4_app.py`
- Build: `H13Q6-native-gate4-real-todays-plan-v1`
- Accepted PR: `#182`

Rollback requires only redeploying the temporary Streamlit app from the Gate 4 branch and entry file. Do not change Supabase OAuth client settings, callback URLs, Site URL or Streamlit Secrets.

## Internal checkpoints

1. **Checkpoint A — read routes**
   - My Profile
   - Recipe Repository
   - Exercise Repository
   - My Schedule
   - Member/Weekly Plan
   - Member Supplements

2. **Checkpoint B — interactive/write routes**
   - LAF
   - NSP Page 1
   - NSP Page 2
   - Submit / Status
   - Daily Log
   - Body Mind Connection

3. **Checkpoint C — remaining current Member routes**
   - Any additional page in `pages/` that currently uses `require_member`
   - Login and Admin files are excluded
   - Member Home and Today's Plan remain supplied by the accepted Gate 4 layer

4. **Checkpoint D — regression and rollback**
   - Member and Admin role protection
   - Direct URL, refresh, tab reopen and root routing
   - Native logout and logged-out refresh stability
   - Page-level diagnostic boundary for an isolated compatibility failure

## Mandatory smoke-test order

1. Logged-out `/Login` shows the H13Q7 build and native identity absent.
2. Fresh Member login reaches the real Member Home.
3. Test read routes first: Weekly Plan and My Schedule.
4. Test Daily Log load, save validation and one controlled write.
5. Test LAF/NSP/Body Mind/Submit Status navigation without changing accepted member data unless the test explicitly requires it.
6. Test direct URLs and five refreshes on one read route and one write route.
7. Test return navigation to Member Home.
8. Test logout from a downstream page and three logged-out refreshes.
9. Test Admin login and direct Member-route correction to the lightweight Admin Dashboard.

## Stop and rollback conditions

Rollback immediately to Gate 4 when any of the following affects more than one route:

- native identity disappears on refresh;
- logout does not clear native identity;
- Admin can render a real Member page;
- Member is routed to Admin;
- root routing enters a loop;
- the OAuth callback repeatedly fails;
- multiple unrelated pages fail before their own page code is reached.

A failure isolated to one page should remain on the H13Q7 branch for diagnosis; do not roll back the entire deployment unless the native identity or central routing layer regresses.
