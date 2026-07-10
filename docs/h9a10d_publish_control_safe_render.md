# H9A.10D Publish Control Safe Render

Follow-up after PR #99 was merged but the generic Streamlit error still appeared when selecting a specific draft in Publish Control.

## Why this patch exists

The previous fix guarded the render flow and normalised dataframe values. The remaining failure may still be triggered by Streamlit/PyArrow dataframe rendering or unsafe mixed row values before the page can show a friendly error.

## Scope

- Removes Streamlit dataframe rendering from Publish Control.
- Renders Current Active Profiles and draft review rows as string-only HTML tables.
- Escapes user/profile values before putting them into HTML blocks.
- Keeps the existing activation rules unchanged.
- Keeps the existing Supabase publish/update logic unchanged.

## Route

- `/Admin_Recommendation_Profile_Builder`
- Tab: `Publish Control`

## Smoke test

1. Open Recommendation Profile Builder.
2. Go to Publish Control.
3. Select the same draft/Profile Y that previously produced the generic Streamlit error.
4. Confirm the page stays open.
5. Confirm Selected Draft Review appears.
6. Expand Review recommendation rows before activation.
7. Confirm the rows render as a compact table.
8. Type `ACTIVATE` and publish only after the review screen is stable.

## Out of scope

- No SQL.
- No Flutter/member-facing change.
- No change to publish/activation business logic.
