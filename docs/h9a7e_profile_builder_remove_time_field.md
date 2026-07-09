# H9A.7E Profile Builder Regime Time Field Removal

Scope:

- Removes the separate Time input field from Exercise Regime rows.
- Removes the separate Time input field from Supplement Regime rows.
- Keeps Exercise Regime grouped only by:
  - Morning
  - Afternoon
  - Evening
  - Night / As advised
- Keeps Supplement Regime grouped only by:
  - Before Breakfast
  - After Breakfast
  - Before Lunch
  - After Lunch
  - Before Dinner
  - After Dinner
  - Before Bed
- Removes Time from the preview table.
- Updates version to `v100.28 · Profile Builder Regime Time Field Removal`.
- Keeps the V2 page as the direct implementation page with no fallback route.
- Keeps draft save/load, clone, validation, preview, cross-section buffering.
- No SQL changes.
- No publish, activate, member-facing, or Flutter changes.

Smoke test route:

`/Admin_Recommendation_Profile_Builder_Mockup_V2`

Expected version:

`v100.28 · Profile Builder Regime Time Field Removal`
