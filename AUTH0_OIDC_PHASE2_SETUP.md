# HealthyMe Phase 2 — Auth0 / OIDC Setup Guide

This build removes all temporary session hacks:
- no `hm_token` in URL
- no custom browser token logic
- no custom email/password app login for active authentication

Authentication is handled by:
```text
Auth0 / OIDC + Streamlit native st.login()
```

Authorization is handled by:
```text
HealthyMe users table in Supabase
```

## Architecture

```text
User opens HealthyMe
↓
Clicks Continue with Auth0
↓
Auth0 authenticates user
↓
Streamlit receives OIDC identity in st.user
↓
HealthyMe checks st.user.email in users table
↓
If role = admin → Admin Dashboard
If role = member → Member Home
If email not registered → blocked
```

## Auth0 app type

Create this in Auth0:

```text
Regular Web Application
```

Do not choose SPA.

## Auth0 URLs

In Auth0 Application settings, add:

### Allowed Callback URLs
```text
https://your-streamlit-app-url/oauth2callback
```

For local testing:
```text
http://localhost:8501/oauth2callback
```

### Allowed Logout URLs
```text
https://your-streamlit-app-url
```

For local testing:
```text
http://localhost:8501
```

### Allowed Web Origins
```text
https://your-streamlit-app-url
```

For local testing:
```text
http://localhost:8501
```

## Streamlit Secrets

In Streamlit Cloud → Manage app → Settings → Secrets, add:

```toml
SUPABASE_URL = "https://your-project-id.supabase.co"
SUPABASE_SERVICE_ROLE_KEY = "your-service-role-key"

[auth]
redirect_uri = "https://your-streamlit-app-url/oauth2callback"
cookie_secret = "replace-with-strong-random-cookie-secret"
client_id = "replace-with-auth0-client-id"
client_secret = "replace-with-auth0-client-secret"
server_metadata_url = "https://YOUR_AUTH0_DOMAIN/.well-known/openid-configuration"
```

`YOUR_AUTH0_DOMAIN` usually looks like:

```text
dev-xxxxxx.us.auth0.com
```

## User access rule

Auth0 login alone is not enough.

The email must also exist in HealthyMe:

```text
Admin Dashboard → Create Users
```

Create the user with the same email used in Auth0.

## Test checklist

1. Open app.
2. Click Continue with Auth0.
3. Login with an authorized Auth0 user.
4. User lands on Admin Dashboard or Member Home.
5. Refresh browser.
6. User should stay logged in because Streamlit OIDC cookie handles session.
7. Copy URL and open in another browser/incognito.
8. It should not carry a session.
9. Logout.
10. User should be logged out from the app.

## Important

If login fails with `state validation failed` or callback errors:
- Confirm Streamlit app URL is final and stable.
- Confirm callback URL exactly ends with `/oauth2callback`.
- Confirm Auth0 application type is Regular Web Application.
- Confirm Streamlit Secrets `[auth].redirect_uri` exactly matches Auth0 callback URL.
- Reboot Streamlit app after changing secrets.