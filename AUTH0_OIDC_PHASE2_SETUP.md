# HealthyMe Phase 2 — Auth0 / OIDC Named Provider Setup

This hotfix uses:
```text
streamlit==1.52.2
st.login("auth0")
[auth.auth0]
```

This is to reduce Streamlit/Authlib state mismatch issues seen with generic/default provider setup.

## Streamlit Secrets

In Streamlit Cloud → Manage app → Settings → Secrets:

```toml
SUPABASE_URL = "https://your-project-id.supabase.co"
SUPABASE_SERVICE_ROLE_KEY = "your-service-role-key"

[auth]
redirect_uri = "https://healthymeappbyankita.streamlit.app/~/+/oauth2callback"
cookie_secret = "one-fixed-long-random-cookie-secret-do-not-change"

[auth.auth0]
client_id = "your-auth0-client-id"
client_secret = "your-auth0-client-secret"
server_metadata_url = "https://YOUR_AUTH0_DOMAIN/.well-known/openid-configuration"
client_kwargs = { prompt = "login" }
```

## Auth0 settings

Application type:

```text
Regular Web Application
```

Allowed Callback URLs:

```text
https://healthymeappbyankita.streamlit.app/~/+/oauth2callback,
https://healthymeappbyankita.streamlit.app/oauth2callback
```

Allowed Logout URLs:

```text
https://healthymeappbyankita.streamlit.app
```

Allowed Web Origins:

```text
https://healthymeappbyankita.streamlit.app
```

## Mandatory clean test sequence

1. Save Streamlit Secrets.
2. Save Auth0 Application settings.
3. Reboot Streamlit app.
4. Clear browser cookies/site data for `healthymeappbyankita.streamlit.app`.
5. Start from app home URL only:

```text
https://healthymeappbyankita.streamlit.app
```

Do not retry from a callback URL containing `code=` and `state=`.

## If MismatchingStateError still happens

Then the next recommendation is not more Streamlit-native OIDC tweaking.

Move Auth0 to either:
1. Custom OAuth flow using Auth0 SDK/Authlib directly, or
2. Deploy on Render instead of Streamlit Community Cloud for more stable callback/cookie control.

The app architecture remains:
```text
Auth0 = identity
HealthyMe users table = role authorization
Supabase = app data
```

## Version compatibility fix

This build pins:

```text
streamlit==1.52.2
authlib==1.6.5
```

This avoids the known `400: 'NoneType' object does not support item assignment` Authlib/Streamlit login issue.
