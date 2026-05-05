# HealthyMe Build 2 — Users + Workflow Normalized Tables Guide

This build starts the Supabase normalization safely.

## What is migrated now

Only these high-traffic areas:

```text
Users
Workflow/status
```

New Supabase tables:

```text
hm_users
hm_workflow
```

## What is not migrated yet

These remain in the existing JSONB app state for now:

```text
LAF responses
NSP responses
Admin assessments
Reports
Questions
Body-Mind responses
Recipes/exercises
Daily logs
```

This keeps risk low.

## Step-by-step implementation

### Step 1 — Upload the build

Upload/push this build to GitHub and wait for Streamlit to redeploy.

### Step 2 — Run SQL in Supabase

Open:

```text
supabase_normalized_users_workflow.sql
```

Copy the full SQL.

In Supabase:

```text
Supabase Dashboard → SQL Editor → New Query → Paste → Run
```

This creates:

```text
hm_users
hm_workflow
```

### Step 3 — Reboot Streamlit

Go to:

```text
Streamlit → Manage app → Reboot
```

### Step 4 — Open Database Status

In HealthyMe:

```text
Admin Dashboard → Database Status
```

Find:

```text
Normalized Users + Workflow Tables
```

Click:

```text
Check Normalized Tables
```

Expected:

```text
ok: true
hm_users: true
hm_workflow: true
```

### Step 5 — Migrate users/workflow

Click:

```text
Migrate Users + Workflow to Normalized Tables
```

Expected success:

```text
Migrated/synced X users and X workflow records to normalized tables.
```

### Step 6 — Test

1. Login as admin.
2. Open Admin Dashboard.
3. Check member count.
4. Create a new test member.
5. Open Supabase Table Editor and check `hm_users`.
6. The new user should appear in `hm_users`.
7. Open `hm_workflow`; the user should have a workflow row.

## Safety behavior

If the normalized tables are missing or fail:

```text
App falls back to the existing JSONB app state.
```

The app should not crash.

## Why this is faster

Earlier, the app relied mainly on:

```text
healthyme_app_state JSONB
```

This means users/workflow were inside one big object.

Now, high-traffic data can come from:

```text
hm_users
hm_workflow
```

This prepares the app for faster dashboard, login authorization, and access management.