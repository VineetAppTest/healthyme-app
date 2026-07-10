# H9A.9C Profile Builder UI Alignment Polish

Scope:

- Fixes Profile Builder top tab buttons by using short single-line tab labels and fixed-height styling.
- Keeps all final tabs accessible:
  - Setup
  - Meals
  - Exercise
  - Supplements
  - Preview
  - Publish
  - Active
- Fixes Load Draft and New Draft button alignment beside the saved draft dropdown.
- Fixes Clone Selected button alignment beside Clone From Existing Profile dropdown.
- Removes the empty bordered strip that appeared above draft loading on Profile Setup.
- Removes extra immediate rerun calls from New Draft / Load Draft / Clone Selected / Add Row interactions to reduce the visible two-second freeze effect.
- Updates Profile Builder visible version to:
  - `v100.35 · Profile Builder Tab Stability Polish`

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
2. Confirm version `v100.35 · Profile Builder Tab Stability Polish`.
3. Confirm top navigation buttons are equal width and equal height.
4. Confirm top navigation labels remain single-line and do not create taller/shorter buttons.
5. Confirm all seven tabs open: Setup, Meals, Exercise, Supplements, Preview, Publish and Active.
6. Confirm Load Draft and New Draft align with the saved draft dropdown.
7. Confirm Clone Selected aligns with Clone From Existing Profile dropdown.
8. Click New Draft and confirm the page does not visibly double-freeze or stall beyond the normal Streamlit refresh.
9. Confirm no empty bordered strip appears above draft loading.
10. Confirm Save Draft, Publish Control and Active Preview still work as before.
