# HealthyMe Auth0 Provisioning Setup Guide

Goal:

```text
Admin creates user once in HealthyMe
↓
HealthyMe creates role record in Supabase
↓
HealthyMe creates/finds user in Auth0
↓
Auth0 sends password setup/reset email
↓
User logs in through Auth0
```

The HealthyMe admin does not need to open Auth0.

---

## Part 1 — Create Auth0 Machine-to-Machine app

1. Open Auth0 Dashboard.
2. Go to **Applications → Applications**.
3. Click **Create Application**.
4. Name it:

```text
HealthyMe Management API Provisioner
```

5. Choose:

```text
Machine to Machine Applications
```

6. Select API:

```text
Auth0 Management API
```

7. Authorize the app.

---

## Part 2 — Give permissions

For the Machine-to-Machine app, grant these Auth0 Management API permissions:

```text
read:users
create:users
update:users
```

Optional but useful later:

```text
create:user_tickets
```

This build creates/finds users and triggers Auth0 password setup/reset email through the Auth0 database connection.

---

## Part 3 — Confirm database connection name

In Auth0, go to:

```text
Authentication → Database
```

Most Auth0 tenants use:

```text
Username-Password-Authentication
```

Use that value for:

```text
AUTH0_CONNECTION
```

---

## Part 4 — Update Streamlit Secrets

In Streamlit Cloud → Manage app → Settings → Secrets, keep your existing Supabase and OIDC login settings, and add:

```toml
# Auth0 Management API provisioning
AUTH0_DOMAIN = "dev-xxxx.us.auth0.com"
AUTH0_M2M_CLIENT_ID = "machine-to-machine-client-id"
AUTH0_M2M_CLIENT_SECRET = "machine-to-machine-client-secret"
AUTH0_AUDIENCE = "https://dev-xxxx.us.auth0.com/api/v2/"
AUTH0_CONNECTION = "Username-Password-Authentication"
AUTH0_APP_CLIENT_ID = "regular-web-app-client-id-used-for-login"
```

Important:
- `AUTH0_M2M_CLIENT_ID` and `AUTH0_M2M_CLIENT_SECRET` come from the Machine-to-Machine app.
- `AUTH0_APP_CLIENT_ID` comes from the Regular Web Application used for login.
- `AUTH0_DOMAIN` should not include `https://`.

---

## Part 5 — Admin workflow after setup

Admin goes to:

```text
Admin Dashboard → Create Users
```

Then:
1. Enters name.
2. Enters email.
3. Chooses member/admin section.
4. Clicks create.

HealthyMe will:
1. Create the user/role in Supabase.
2. Check Auth0 for that email.
3. If missing, create Auth0 user.
4. Trigger password setup/reset email.

---

## Testing

Create a test user:

```text
test.member@example.com
```

Expected message:

```text
Member created in HealthyMe and Auth0 provisioning completed.
```

Then the user should receive Auth0 password setup/reset email.

If no email is received:
1. Check Auth0 email templates/provider.
2. Check password change email is enabled.
3. Check Auth0 tenant logs.
4. Check Streamlit app message for provisioning error.

---

## Important security notes

- Do not expose M2M secrets to normal users.
- Keep M2M secrets only in Streamlit Secrets.
- Do not commit `.streamlit/secrets.toml` to GitHub.
- HealthyMe stores roles in Supabase; Auth0 stores identity/password/session.