# HealthyMe Deployment Safety Notes

Before uploading to GitHub:
1. Keep the GitHub repository private.
2. Do not commit `data/db.json` if it contains real member data.
3. Commit `data/db_sample.json` only as a safe demo starter.
4. Do not commit `.streamlit/secrets.toml`.
5. Add real secrets in Streamlit Cloud under Manage app > Settings > Secrets.
6. For live use, move data from local JSON to Supabase/Google Sheets.

Recommended pilot stack:
- Private GitHub repo
- Streamlit Community Cloud
- Supabase Pro for live data
- App-level login enabled
- Forced password reset for users

This build still includes JSON persistence for local/demo testing. For live deployment, migrate storage to Supabase before using real member data.

## Supabase PostgreSQL persistence

This package includes Supabase persistence.

Required files:
- `components/storage_backend.py`
- `supabase_setup.sql`
- `SUPABASE_DEPLOYMENT_STEPS.md`

Live storage flow:

```text
Streamlit app
↓
components/db.py
↓
components/storage_backend.py
↓
Supabase PostgreSQL table: healthyme_app_state
```

If Supabase secrets are missing, the app falls back to local JSON for testing.