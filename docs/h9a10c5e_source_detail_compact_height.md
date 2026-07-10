# H9A.10C.5E — Source Detail Compact Height Alignment

## Purpose

Correct the source-detail field height behavior after smoke-test feedback.

The requested visual rule is:

- Exercise source-detail second row fields must match the compact height of the Category/Difficulty/Duration fields.
- Supplement source-detail fields must match the compact height of the first-row Supplement controls.

## Scope

Route:

- `/Admin_Recommendation_Profile_Builder`

Changed behavior:

- Exercise Pulled Source Details remains two rows:
  - Row 1: Category | Difficulty | Duration/Reps
  - Row 2: Equipment | Benefits | Image Reference
- Equipment, Benefits and Image Reference now render as compact text-input height.
- Supplement Pulled Source Details remains one row:
  - Source Timing | Admin Notes
- Source Timing and Admin Notes now render as compact text-input height.
- Meal long-form fields continue to use larger text areas where appropriate.

## Not changed

- No SQL change.
- No Flutter/member-facing change.
- No source snapshot schema change.
- No change to source instruction mapping into the first-row Instruction field.

## Smoke test

1. Open `/Admin_Recommendation_Profile_Builder`.
2. Go to Exercise Regime.
3. Select an exercise.
4. Confirm Equipment, Benefits and Image Reference are the same height as Category.
5. Go to Supplement Regime.
6. Select a supplement.
7. Confirm Source Timing and Admin Notes are the same height as the first-row Supplement field.
