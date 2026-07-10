# H9A.10D Publish Control Crash Guard

## Context

During H9A.10D smoke testing, selecting a draft profile in Publish Control caused the generic Streamlit error screen.

The Publish Control path should not take down the whole page when a specific draft row has an unexpected data shape or when Streamlit/PyArrow has trouble rendering a mixed-type table.

## Scope

This follow-up patch updates `components/profile_publish_control.py`.

Changes:

- Adds a top-level guard around Publish Control rendering.
- Converts active-profile and recommendation-review tables to string-normalised pandas dataframes before calling `st.dataframe`.
- Keeps activation logic unchanged.
- Keeps Supabase table/schema unchanged.
- Keeps member-facing Flutter/UI unchanged.
- Keeps source snapshot/member consumption contract work unchanged.

## Expected behavior

When a draft profile is selected in Publish Control:

1. The page should not show the generic Streamlit crash screen.
2. Draft review should load if profile and item rows are readable.
3. Any unexpected issue should show as a human-readable error inside Publish Control.
4. Current active profile table should still render.
5. Recommendation rows should still render inside the review expander.
6. Activation should still require member assignment, item rows and `ACTIVATE` confirmation.

## Smoke test

Route:

`/Admin_Recommendation_Profile_Builder`

Tab:

`Publish Control`

Steps:

1. Open Publish Control.
2. Select the same draft profile that previously crashed, for example Profile Y.
3. Confirm no generic Streamlit error page appears.
4. Confirm Selected Draft Review appears.
5. Expand Review recommendation rows before activation.
6. Confirm rows render in a table.
7. Type `ACTIVATE` only if the profile is ready and activation is intended.
8. Publish/activate and confirm success message.

## Notes

This is an admin hardening patch only. No SQL and no Flutter/member-facing change.
