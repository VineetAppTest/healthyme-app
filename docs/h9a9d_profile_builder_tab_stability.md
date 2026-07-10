# H9A.9D Profile Builder Tab Stability Follow-up

Scope:

- Follow-up to PR #81 smoke-test feedback.
- Makes top Profile Builder navigation buttons equal height with fixed-height styling.
- Uses short single-line labels to prevent wrapped labels from changing button height:
  - Setup
  - Meals
  - Exercise
  - Supplements
  - Preview
  - Publish
  - Active
- Removes extra immediate rerun calls from New Draft, Load Draft, Clone Selected and Add Row interactions.
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
5. Click New Draft and confirm it refreshes normally.
6. Confirm Load Draft / New Draft and Clone Selected remain aligned.
7. Confirm Save Draft, Publish Control and Active Preview still work.
