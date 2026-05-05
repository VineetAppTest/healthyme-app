# HealthyMe — Layman Steps to Connect Supabase and Check Connection

This guide follows the same safe method used in the Salary Management System.

## Golden rule

```text
Do not add Streamlit secrets before running the Supabase SQL setup.
```

If secrets are added first and the table does not exist, the app may not find the database.  
This build has safe fallback, but follow the sequence below.

---

# Part A — Connect Supabase

## Step 1 — Create Supabase project

1. Open Supabase.
2. Click **New Project**.
3. Select your organization.
4. Give project name, for example:

```text
healthyme-app
```

5. Set a strong database password.
6. Select region close to India if available.
7. Click **Create Project**.
8. Wait until project is ready.

---

## Step 2 — Run SQL setup

1. Open Supabase project.
2. Go to **SQL Editor**.
3. Open the file from this package:

```text
supabase_setup.sql
```

4. Copy the full SQL.
5. Paste it in SQL Editor.
6. Click **Run**.

This creates the table:

```text
healthyme_app_state
```

---

## Step 3 — Get Supabase keys

1. Go to Supabase project.
2. Open **Project Settings**.
3. Open **API**.
4. Copy:
   - Project URL
   - service_role key

Use service role key only inside Streamlit Secrets.  
Do not paste it in Python code or GitHub.

---

## Step 4 — Add Streamlit secrets

1. Open Streamlit Cloud.
2. Open your HealthyMe app.
3. Click **Manage app**.
4. Open **Settings**.
5. Open **Secrets**.
6. Add:

```toml
SUPABASE_URL = "https://your-project-id.supabase.co"
SUPABASE_SERVICE_ROLE_KEY = "your-service-role-key"
APP_SECRET_KEY = "some-long-random-value"
```

7. Save.
8. Reboot the app.

---

# Part B — Check if Supabase is connected

## Step 1 — Login as admin

Open the app and login as admin.

## Step 2 — Open Database Status

Go to:

```text
Admin Dashboard → Database Status
```

## Step 3 — Check expected status

If connected, you should see:

```text
Database Mode: SUPABASE
Supabase Secrets: Present
Connection: Connected
Fallback: Inactive
```

If not connected, you will see:

```text
Database Mode: LOCAL_FALLBACK
Connection: Not Connected
Fallback: Active
```

This means the app is working but data is not live-persistent on Streamlit Cloud.

---

# Part C — Reboot test

This is the most important test.

1. Go to Admin Dashboard.
2. Click **Create Users**.
3. Create a test member:

```text
Supabase Test Member
```

4. Go to Streamlit Cloud.
5. Click **Manage app**.
6. Click **Reboot app**.
7. Login again.
8. Check if the test member is still visible.

Result:

```text
Member still visible = Supabase persistence is working.
Member missing = app is still local fallback or Supabase save failed.
```

---

# Part D — Safe migration

Before pushing data to Supabase:

1. Go to Admin Dashboard.
2. Open **Database Status**.
3. Click **Download Current Database Backup**.
4. Save the file safely.
5. Then click **Push Local Data to Supabase** only if you intentionally want the local/demo database to become the Supabase database.

---

# Part E — Demo Mode

This package includes:

```text
Admin Dashboard → Demo Mode
```

Use this to auto-fill:
- LAF
- NSP Page 1
- NSP Page 2

Demo Mode is only for testing and client walkthroughs.  
Do not use it for real client/member records.

---

# Troubleshooting

## If Database Status says LOCAL_FALLBACK

Check:

1. Did you run `supabase_setup.sql`?
2. Did you add Streamlit Secrets correctly?
3. Is `SUPABASE_URL` correct?
4. Is `SUPABASE_SERVICE_ROLE_KEY` correct?
5. Did you reboot Streamlit app after adding secrets?

## If app still works but warning is shown

That is good. It means the no-crash fallback is working.

But for live use, the warning must be resolved and Database Mode should show:

```text
SUPABASE
```