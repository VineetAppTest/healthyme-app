# H13Q5 Gate 3 — Native identity to real Member Home

## Accepted baseline

Gate 3 is stacked on the accepted Gate 2 branch and retains:

- Supabase OIDC through `st.login("supabaseoidc")`
- Streamlit native `st.user` as the authentication authority
- HealthyMe role lookup through `resolve_app_user(email, sub)`
- central hidden `st.navigation` routing
- root-hosted one-time Supabase authorization UI
- native `st.logout()`

## Gate 3 change

For a resolved **Member** role, the router now executes the existing real page:

```text
pages/02_Member_Home.py
```

The page continues to load its existing HealthyMe data and presentation:

- member identity row
- Member Home header
- workflow and current assessment instance
- messages from the nutritionist
- upcoming schedules
- progress/status cards
- Your next steps
- Personalized content and Daily tools

## Authentication boundary

The existing Member Home currently expects legacy application Session State and calls legacy page-level authentication helpers. During the isolated Gate 3 run only, the router:

1. resolves the Member from native `st.user`;
2. re-derives the existing application context with `apply_app_user_to_session` on every run;
3. bypasses `require_member()` because the central router has already authorized the Member route;
4. disables the old keepalive guard;
5. replaces legacy logout with `st.logout()`;
6. ignores the page's duplicate `st.set_page_config` call;
7. blocks navigation to downstream legacy Member pages until later gates.

Application Session State is therefore a **derived compatibility context**, not the authentication source.

## Explicitly excluded

- real Admin Dashboard
- production deployment or `main` cutover
- downstream Member page integration
- legacy Member page guard
- legacy keepalive/session restoration
- custom browser marker `hm_supabase_sid_v2`
- durable authentication session table
- CookieManager or localStorage
- retry, sleep or browser reload workaround
- Flutter or Admin Lite

## Build

```text
H13Q5-native-gate3-real-member-home-v1
```

## Mandatory acceptance

Run Member first:

1. `/Login` shows the Gate 3 build.
2. Fresh Member OIDC login finishes on `/Member_Home`.
3. The real Member Home renders the correct member-specific data.
4. Refresh `/Member_Home` five times.
5. Close and reopen the direct `/Member_Home` URL.
6. Root routes back to `/Member_Home`.
7. Wrong-role `/Admin_Dashboard` corrects to `/Member_Home`.
8. A downstream Member button is safely blocked without Page-not-found or logout.
9. Logout returns to `/Login`.
10. Refresh logged-out `/Login` three times.

Admin regression only:

1. Fresh Admin login still finishes on the lightweight `/Admin_Dashboard` route.
2. One refresh succeeds.
3. Logout returns to `/Login`.

Do not connect any downstream Member page or the real Admin Dashboard until this gate passes.
