# H9A.10C.5B Source Detail Layout Polish

Follow-up after smoke-test screenshots for the source-detail rows.

Scope:

- Exercise Pulled Source Details uses a compact 2 x 3 layout:
  - Row 1: Category | Difficulty | Duration/Reps
  - Row 2: Equipment | Benefits | Image Reference
- Equipment moves from the crowded first row to the second row.
- Supplement Pulled Source Details uses a compact 1 x 2 layout:
  - Source Timing | Admin Notes
- Source Instructions stays connected to the first-row Instruction field and is not repeated below.
- Keeps existing H9A.10C source snapshot storage unchanged.

Route:

- `/Admin_Recommendation_Profile_Builder`

No new SQL.
No Flutter/member-facing change.

Smoke test:

1. Open Recommendation Profile Builder.
2. Select an exercise.
3. Confirm Exercise source details render as 2 rows of 3 fields with Equipment on row 2.
4. Select a supplement.
5. Confirm Supplement source details render as Source Timing and Admin Notes in one row.
6. Save draft and confirm source snapshots remain preserved.
