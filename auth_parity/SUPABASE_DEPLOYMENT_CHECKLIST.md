# H13Q1 Supabase OIDC comparison deployment

Use a second temporary Streamlit app. Do not replace or modify the accepted Auth0 baseline deployment.

## Streamlit deployment

- Repository: `VineetAppTest/healthyme-app`
- Branch: `h13q1-native-oidc-provider-parity`
- Main file: `auth_parity/auth_parity_app.py`
- Python: 3.11
- Suggested app URL: `healthyme-identity-parity-b`
- Exact callback URL: `https://healthyme-identity-parity-b.streamlit.app/oauth2callback`
- Exact consent page URL: `https://healthyme-identity-parity-b.streamlit.app/OAuth_Consent`

## Streamlit Secrets template

```toml
AUTH_TEST_PROVIDER = "supabaseoidc"
SUPABASE_URL = "https://arptwzvlugxrqtvbrmtl.supabase.co"
SUPABASE_ANON_KEY = "<supabase-publishable-or-anon-key>"

[auth]
redirect_uri = "https://healthyme-identity-parity-b.streamlit.app/oauth2callback"
cookie_secret = "<new-long-random-secret-created-only-for-this-temp-app>"

[auth.supabaseoidc]
client_id = "<supabase-oauth-client-id>"
client_secret = "<supabase-oauth-client-secret>"
server_metadata_url = "https://arptwzvlugxrqtvbrmtl.supabase.co/auth/v1/.well-known/openid-configuration"
client_kwargs = { scope = "openid email profile", prompt = "login" }
```

Never commit or share the actual secret values.

## Supabase dashboard

1. Authentication > OAuth Server: enabled.
2. Authorization Path: `/OAuth_Consent`.
3. Authentication > URL Configuration > Site URL: `https://healthyme-identity-parity-b.streamlit.app` for this isolated comparison window.
4. Authentication > OAuth Apps: create or update a confidential client.
5. OAuth client Redirect URI: exact `https://healthyme-identity-parity-b.streamlit.app/oauth2callback`.
6. Project JWT signing key must be asymmetric for OIDC ID-token issuance.

The Site URL plus Authorization Path must resolve to:

`https://healthyme-identity-parity-b.streamlit.app/OAuth_Consent`

## Smoke test

1. Build marker shown: `H13Q1-native-oidc-provider-parity-v1`.
2. Click Continue with Supabase OIDC.
3. Sign in on the consent page and approve access.
4. Native identity, email claim and subject claim are Present.
5. Refresh 10 consecutive times.
6. Close and reopen the app URL.
7. Logout.
8. Refresh the logged-out page 3 times.

PR #177 remains Draft and unmerged until the result is recorded. Production H13R1 and Flutter remain untouched.
