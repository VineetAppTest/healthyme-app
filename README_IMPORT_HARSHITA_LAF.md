# One-Time Backend Import — Harshita Sajjanhar LAF

## Purpose

This one-time import creates/updates the HealthyMe backend member record for Harshita Sajjanhar and populates the Lifestyle Assessment Form (LAF) only.

It follows the same operational route used for the Shweta Mishra import, but scope is intentionally limited to LAF.

## Files to upload to GitHub

Upload these files to the deployed branch:

| File | GitHub location |
|---|---|
| `33_Admin_One_Time_Import_Harshita.py` | `pages/` |
| `import_harshita_laf_backend.py` | `scripts/` |
| `README_IMPORT_HARSHITA_LAF.md` | repo root |

## Direct URL after deployment

After Streamlit redeploys, open:

```text
https://healthymeappbyankita.streamlit.app/Admin_One_Time_Import_Harshita
```

Streamlit usually drops the numeric page prefix from the URL slug.

## Import details

- Member name: Harshita Sajjanhar
- Email: harshita@gmail.com
- Temporary password reference: Password@123
- Member active: Yes
- LAF form date: 2026-01-24
- LAF signed/client statement date: 2026-01-28
- Scope: LAF only

## What this import does

- Creates/updates the app/backend member record.
- Creates/updates the profile record.
- Fills `laf_responses` for Harshita Sajjanhar.
- Marks `laf_completed` as true.
- Keeps NSP Page 1 and NSP Page 2 incomplete.
- Does not create NSP scores.
- Does not fill Digestive, Intestinal, Immune, Glandular, or Musculoskeletal subforms.
- Does not generate final report.
- Does not unlock Body-Mind.

## Auth0 note

This import does not create an Auth0 user. Auth0 must be created or updated manually.

Auth0 and HealthyMe backend should use the same email:

1. Auth0 user email/login
2. HealthyMe backend/app member email

## Cleanup after successful import

After confirming the import succeeded, delete this file from GitHub:

```text
pages/33_Admin_One_Time_Import_Harshita.py
```

Optional cleanup after verification:

```text
scripts/import_harshita_laf_backend.py
README_IMPORT_HARSHITA_LAF.md
```
