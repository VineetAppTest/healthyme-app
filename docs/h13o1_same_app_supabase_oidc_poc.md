# H13O1 — Same-app Supabase OIDC proof of concept

## Objective

Test whether HealthyMe can remain on Streamlit Community Cloud while Supabase remains the identity source and Streamlit owns the persistent browser identity cookie.

This is an isolated proof of concept. The working H13R1 production login on `main` is not changed.

## Test architecture

`Temporary Streamlit branch app → st.login("supabase_oidc") → Supabase OAuth Server → same-app OAuth consent page → Streamlit callback → st.user → HealthyMe role resolution`

The OIDC identity is resolved against `hm_users` using the Supabase `sub` claim first and email as fallback.

## Included in this branch

- `supabase_oidc_poc` authentication mode.
- Branch-only OIDC login page.
- Same-app `/OAuth_Consent` Streamlit page.
- Supabase OIDC identity-to-role mapping.
- Native Streamlit OIDC logout.
- Safe secrets template with placeholders only.

## Critical constraints

1. Supabase OAuth 2.1 Server is currently beta.
2. OpenID Connect ID tokens require an asymmetric Supabase JWT signing key such as RS256 or ES256.
3. OAuth redirect URIs require an exact match.
4. Supabase combines its Site URL with the Authorization Path. The current Site URL must therefore be recorded before the PoC and restored after the test window if changed.
5. No production Streamlit secrets should be changed for this PoC.
6. No Supabase service-role key or OAuth client secret may be pasted into GitHub, screenshots, or chat.

## Temporary Streamlit deployment

Create a separate temporary Community Cloud app using:

- Repository: `VineetAppTest/healthyme-app`
- Branch: `h13o1-supabase-oidc-poc`
- Main file: `app.py`
- Suggested temporary subdomain: `healthyme-oidc-poc`

The callback will then be:

`https://healthyme-oidc-poc.streamlit.app/oauth2callback`

Use the exact deployed URL if Community Cloud assigns a different subdomain.

## Streamlit secrets

Copy `.streamlit/secrets.h13o1.example.toml` into the temporary app's Secrets box and replace placeholders locally.

Generate the Streamlit cookie secret locally:

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

Do not reuse the gateway signing secret or any Supabase key.

## Supabase dashboard preparation

Perform these steps only during a controlled PoC window:

1. Record the current values under Authentication → URL Configuration.
2. Confirm an asymmetric JWT signing key is active. Do not rotate production signing keys casually; follow the Supabase migration process and verify existing clients.
3. Enable Authentication → OAuth Server.
4. Set Authorization Path to:

   `/OAuth_Consent`

5. For the PoC window, set Site URL to the temporary Streamlit app root:

   `https://healthyme-oidc-poc.streamlit.app`

6. Register a confidential OAuth client named `HealthyMe Streamlit OIDC PoC`.
7. Set its exact redirect URI to:

   `https://healthyme-oidc-poc.streamlit.app/oauth2callback`

8. Copy the client ID and one-time client secret directly into the temporary Streamlit app secrets.

After testing, restore the original Site URL and review whether the OAuth Server should remain enabled.

## Consent page behavior

The consent page runs Supabase password authentication in the browser using the publishable/anon key. It does not send the password to the Streamlit Python process and does not persist the Supabase session in browser storage.

The page then retrieves the OAuth request details, displays the requested scopes, and calls Supabase approve/deny authorization methods. The resulting redirect returns to Streamlit's native callback.

## Mandatory smoke test

1. Open the temporary app and start Supabase OIDC login.
2. Sign in as Admin and approve access.
3. Confirm Admin Dashboard opens.
4. Refresh Admin Dashboard and one more protected Admin page.
5. Log out and confirm a protected URL requires login.
6. Sign in as Member and approve access.
7. Refresh Member Home, Daily Log, and My Schedule.
8. Run Admin → logout → Member → logout → Admin.
9. Record visible login time and refresh restoration time.
10. Confirm production H13R1 login/logout still works separately.

## Acceptance boundary

H13O1 is not accepted until both roles survive refresh and logout clears the Streamlit identity session. The PoC must remain unmerged until the deployed test passes.

## Rollback

- Delete the temporary Streamlit app.
- Restore the original Supabase Site URL and Authorization Path.
- Revoke/delete the PoC OAuth client.
- Keep production `main` on H13R1.
