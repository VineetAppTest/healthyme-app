# H13D — Browser Cookie Reload Handoff

## Deployed finding

After H13C deployment:

- Admin Dashboard refresh did not restore the Admin.
- Member Home refresh did not restore the Member.
- The Login page remained stuck on `Securing your HealthyMe session…` with a manual Retry button.

H13C is therefore not accepted.

## Root cause

The durable Supabase table is not the immediate failure point shown by the screenshot.
The browser-marker handoff still depended on asynchronous CookieManager read-back.
That component can rerun independently and its returned cookie dictionary is not a
reliable synchronous confirmation. The Login page therefore remained in the waiting
state and never reached a browser request in which `st.context.cookies` contained the
new marker.

Streamlit documents that `st.context.cookies` contains cookies sent in the initial
request. A normal script rerun does not create a new initial request.

## H13D correction

- Remove CookieManager `get_all` confirmation from the login handoff.
- After successful Supabase login and durable-row creation, render one browser script
  that writes the opaque marker.
- Attempt the write against both the component document and parent browser document.
- Perform one full parent-browser reload after the write.
- On the new initial request, `st.context.cookies` supplies the marker and H13C restores
  the durable Supabase session.
- Keep the existing Retry action only as an exceptional fallback.

## Database impact

No new SQL migration is required. Continue using:

`sql/h13c_streamlit_durable_auth_sessions.sql`

## Required smoke test

1. Sign in as Admin.
2. The `Securing your HealthyMe session…` screen should disappear automatically.
3. Refresh Admin Dashboard; the same Admin must remain signed in.
4. Sign out and sign in as Member.
5. Refresh Member Home; the same Member must remain signed in.
6. Refresh Daily Log and My Schedule.
7. Test Admin → logout → Member → logout → Admin.
8. Test logout → browser Back and direct protected URL.

## Acceptance rule

Do not accept H13D until the deployed Render build passes Admin Dashboard, Member
Home, Daily Log and My Schedule refresh without manual Retry.
