# WakeMe / Keep-Awake Setup

This build includes:

- `.github/workflows/wakeme.yml`
- `scripts/wakeme.py`

The workflow pings the deployed HealthyMe app every 10 minutes.

## Why this version is safer

This workflow does not use `actions/checkout` or `actions/setup-python`, so it avoids Node-action deprecation warnings.

## Required setup after uploading to GitHub

1. Open your GitHub repository.
2. Go to **Settings**.
3. Go to **Secrets and variables**.
4. Open **Actions**.
5. Add a new **Repository secret**:
   - Name: `WAKEME_URLS`
   - Value: your deployed app URL, for example:
     `https://your-healthyme-app.streamlit.app`

For multiple URLs, use comma separation:

`https://app1.streamlit.app,https://app2.streamlit.app`

## Manual test

1. Go to GitHub repo.
2. Click **Actions**.
3. Select **WakeMe - Keep HealthyMe Warm**.
4. Click **Run workflow**.
5. Check logs for HTTP response.
