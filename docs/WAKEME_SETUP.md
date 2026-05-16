# WakeMe Setup - v18 Sturdy Version

This version applies the key learnings from the Salary Management System issue:

1. Do not rely on one fragile secret expression.
2. Show diagnostics in the workflow logs.
3. Use manual trigger for testing.
4. Support both GitHub secret and GitHub variable.
5. Add cache-busting to avoid stale responses.
6. Retry multiple times because a sleeping Streamlit app can need more than one hit.
7. Add an extra safety cron around 10:00 AM IST.

## Files added/updated

- `.github/workflows/wakeme.yml`
- `scripts/wakeme.py`
- `docs/WAKEME_SETUP.md`

## Required setup

Set a GitHub repository secret:

Name:

`WAKEME_URLS`

Value:

`https://your-healthyme-app.streamlit.app`

Multiple URLs:

`https://app1.streamlit.app,https://app2.streamlit.app`

## Manual test

1. GitHub repo → Actions
2. Open **WakeMe - Keep HealthyMe Warm**
3. Click **Run workflow**
4. Optional: paste the URL in `target_urls`
5. Check logs

Successful log should show:

- `Secret WAKEME_URLS configured: YES`
- `WakeMe completed successfully for all targets`

## If manual works but schedule does not

Check:

- Workflow file is committed to the default branch.
- GitHub Actions is enabled.
- Scheduled workflows are not disabled.
- GitHub cron is UTC and best-effort, so delay is possible.

## Time note

10:00 AM IST = 04:30 UTC.

The workflow includes:
- every 10 minutes: `*/10 * * * *`
- extra 10 AM IST safety run: `30 4 * * *`
