# HealthyMe Supabase PostgreSQL Deployment Steps

This build supports persistent storage using Supabase PostgreSQL.

## What changed

The app no longer needs to depend on `data/db.json` for live use.  
When Supabase secrets are configured, the app stores all HealthyMe app state in this PostgreSQL table:

```text
public.healthyme_app_state
```

The app still has a local JSON fallback for laptop testing only.

## Step 1 — Create Supabase project

1. Go to Supabase.
2. Create a new project.
3. Choose a strong database password.
4. Wait for the project to be ready.

## Step 2 — Run the SQL setup

1. Open Supabase Dashboard.
2. Go to SQL Editor.
3. Open the file from this package:

```text
supabase_setup.sql
```

4. Copy-paste the full SQL.
5. Click Run.

This creates the table:

```text
healthyme_app_state
```

## Step 3 — Add Streamlit Secrets

In Streamlit Cloud:

1. Open your app.
2. Click Manage app.
3. Go to Settings.
4. Open Secrets.
5. Add:

```toml
SUPABASE_URL = "https://your-project-id.supabase.co"
SUPABASE_SERVICE_ROLE_KEY = "your-service-role-key"
APP_SECRET_KEY = "some-long-random-value"
```

Use the **service role key**, not the anon key, because this MVP app writes server-side state.

## Step 4 — Deploy / reboot app

1. Push the updated package to GitHub.
2. Reboot the Streamlit app.
3. On first run, the app will seed Supabase from local demo/sample data.
4. From then onward, the live data will persist in Supabase.

## Important

For real use:
- Keep GitHub private.
- Do not commit real `data/db.json`.
- Keep `.streamlit/secrets.toml` out of GitHub.
- Add secrets only in Streamlit Cloud settings.
- Supabase Pro is recommended before storing real client data.

## Local testing

If Supabase secrets are not configured, the app falls back to:

```text
data/db.json
```

This is only for local demo/testing.