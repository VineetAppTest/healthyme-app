# H9A.9C Profile Builder UI Alignment Polish

Scope:

- Fixes Profile Builder top tab buttons so all tab buttons use equal column width and consistent height.
- Fixes Load Draft and New Draft button alignment beside the saved draft dropdown.
- Fixes Clone Selected button alignment beside Clone From Existing Profile dropdown.
- Removes the empty bordered strip that appeared above draft loading on Profile Setup.
- Updates Profile Builder visible version to:
  - `v100.34 · Profile Builder Alignment Polish`

Route:

- `/Admin_Recommendation_Profile_Builder`

Impact:

- UI-only fix.
- No SQL changes.
- No Flutter changes.
- No member-facing display change.
- No publish/activate logic change.
- No active preview contract change.

Smoke test:

1. Open `/Admin_Recommendation_Profile_Builder`.
2. Confirm version `v100.34 · Profile Builder Alignment Polish`.
3. Confirm top tab buttons are equal width and height.
4. Confirm Profile Setup, Meal Structure, Exercise Regime, Supplement Regime, Preview & Flow, Publish Control and Active Preview remain accessible.
5. Confirm Load Draft and New Draft buttons align with the saved draft dropdown.
6. Confirm Clone Selected aligns with Clone From Existing Profile dropdown.
7. Confirm no empty bordered strip appears above draft loading.
8. Confirm Save Draft, Publish Control and Active Preview still work as before.
