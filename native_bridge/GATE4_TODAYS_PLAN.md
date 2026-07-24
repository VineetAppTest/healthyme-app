# H13Q6 Gate 4 — Native real Today's Plan

## Accepted baseline

Gate 4 is stacked directly on the accepted Gate 3 branch and retains:

- Supabase OIDC through `st.login("supabaseoidc")`
- Streamlit native `st.user` as the authentication authority
- HealthyMe role lookup through `resolve_app_user(email, sub)`
- central hidden `st.navigation` routing
- root-hosted one-time Supabase authorization UI
- real `pages/02_Member_Home.py`
- native `st.logout()`

## Gate 4 change

Gate 4 connects exactly one downstream Member page:

```text
pages/36_Todays_Journey.py
```

Native protected URL:

```text
/Todays_Plan
```

The real page continues to use its existing recommendation data and rendering logic:

- today's recommendation day
- meals
- supplements
- exercises
- nutrition guidance
- existing empty states

## Navigation boundary

- Member Home → Today's Plan is enabled.
- Direct `/Todays_Plan` is enabled for a resolved Member.
- Today's Plan → Member Home is enabled through the Gate 4 bottom navigation.
- `Log today's activity` remains blocked because Daily Log is outside Gate 4.
- Every other downstream Member route remains blocked.

## Authentication boundary

During the isolated Gate 4 execution only, the native router:

1. resolves the Member from native `st.user`;
2. derives the existing application context with `apply_app_user_to_session` on every run;
3. bypasses the legacy page-level Member guard because the central router has already authorized the route;
4. replaces legacy logout with native `st.logout()`;
5. replaces legacy return navigation with the registered native Member Home route;
6. ignores duplicate page configuration owned by the embedded legacy page.

Application Session State remains a derived compatibility context, not the authentication source.

## Explicitly excluded

- Daily Log integration
- My Schedule integration
- My Weekly Plan integration
- task-form integration
- real Admin Dashboard
- production deployment or `main` cutover
- legacy page guard or keepalive restoration
- custom browser marker, durable auth session, CookieManager or localStorage
- retry, sleep or browser reload workarounds
- Flutter or Admin Lite

## Build

```text
H13Q6-native-gate4-real-todays-plan-v1
```

## Mandatory acceptance

Member:

1. `/Login` shows the Gate 4 build.
2. Fresh Member login reaches the real Member Home.
3. Clicking Today's Plan reaches `/Todays_Plan` and renders the real page.
4. Refresh `/Todays_Plan` five times.
5. Close and reopen direct `/Todays_Plan`.
6. Back to Member Home returns to `/Member_Home`.
7. Direct `/Todays_Plan` while logged out returns to `/Login`.
8. `Log today's activity` is safely blocked without logout or Page-not-found.
9. Wrong-role Admin access corrects to `/Admin_Dashboard`.
10. Native logout returns to `/Login` and logged-out refresh remains stable.

Admin regression:

1. Fresh Admin login reaches the lightweight `/Admin_Dashboard`.
2. Direct `/Todays_Plan` corrects to `/Admin_Dashboard`.
3. One Admin refresh succeeds.
4. Logout returns to `/Login`.

Do not connect another downstream page or production cutover until this gate passes.
