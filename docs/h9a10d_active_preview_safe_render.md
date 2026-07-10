# H9A.10D Active Preview Safe Render

## Context

After PR #100, Publish Control used safe HTML tables instead of Streamlit dataframe rendering.

Smoke testing then showed a similar generic Streamlit `Oh no` page when selecting the member email in Active Profile Preview after a profile was published.

## Scope

This patch applies the same safe-rendering principle to Active Profile Preview.

Changes:

1. Removes Streamlit dataframe rendering from day-wise Active Profile Preview.
2. Renders day-wise rows through escaped, string-only HTML tables.
3. Adds a guard around Active Profile Preview rendering so errors are shown in-page.
4. Escapes profile/member text before HTML rendering.
5. Uses safe integer parsing for day/order values.
6. Builds the raw member contract only when raw payload view is requested.

## Route

- `/Admin_Recommendation_Profile_Builder`
- Tab: `Active Profile Preview`

## Smoke test

1. Merge and deploy this PR.
2. Open `/Admin_Recommendation_Profile_Builder`.
3. Go to `Active Profile Preview`.
4. Select the same member email that previously crashed.
5. Confirm the generic Streamlit `Oh no` page does not appear.
6. Confirm Active Profile Summary appears.
7. Confirm Day-wise Member Consumption Preview renders rows as compact tables.

## Not changed

- No SQL.
- No Flutter/member-facing UI change.
- No publish/activation logic change.
- No source snapshot persistence change.
