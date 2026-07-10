# H9A.9D Profile Builder Tab Stability Follow-up

Scope:

- Follow-up to PR #81 after smoke test feedback.
- Fixes Profile Builder top navigation to avoid uneven button heights caused by wrapped labels.
- Uses short single-line labels for the top navigation while keeping all final sections available:
  - Setup
  - Meals
  - Exercise
  - Supplements
  - Preview
  - Publish
  - Active
- Uses fixed-height tab button styling.
- Removes extra immediate rerun calls from New Draft / Load Draft / Clone Selected / Add Row interactions to reduce visible freeze/double-refresh.
- Updates visible version to:
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
3. Confirm top buttons are equal height and single-line.
4. Confirm all seven sections open: Setup, Meals, Exercise, Supplements, Preview, Publish, Active.
5. Click New Draft and confirm there is no visible double-freeze beyond normal Streamlit refresh.
6. Confirm Load Draft / New Draft and Clone Selected remain aligned.
7. Confirm Save Draft, Publish Control and Active Preview still work.
