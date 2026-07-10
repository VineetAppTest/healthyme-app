# H9A.10C.5C Direct Source Detail Layout Render Fix

Follow-up after PR #94 was merged but the Exercise and Supplement source-detail layout did not reflect in the live page.

Root cause:

- The earlier layout patch was applied only once at module level.
- Streamlit reruns the Profile Builder page and recreates page-level functions on interactions.
- After a rerun, the page could revert to the original source-detail renderer.

Correction:

- Reapply the source-detail render override whenever the current Profile Builder page function has not been patched.
- Keep the layout contract explicit:
  - Exercise row 1: Category | Difficulty | Duration/Reps
  - Exercise row 2: Equipment | Benefits | Image Reference
  - Supplement row: Source Timing | Admin Notes
- Keep Source Instructions connected to the first-row Instruction field.
- Do not repeat Source Instructions in Pulled Source Details.
- Preserve existing H9A.10C source snapshot storage.

Route:

- `/Admin_Recommendation_Profile_Builder`

No SQL.
No Flutter/member-facing change.

Smoke test:

1. Open `/Admin_Recommendation_Profile_Builder` after merge/deploy.
2. Go to Exercise Regime.
3. Select an exercise.
4. Confirm Pulled Source Details appears as two rows of three fields:
   - Category | Difficulty | Duration/Reps
   - Equipment | Benefits | Image Reference
5. Go to Supplement Regime.
6. Select a supplement.
7. Confirm Pulled Source Details appears as one row of two fields:
   - Source Timing | Admin Notes
8. Confirm Source Instructions is not repeated below and first-row Instruction remains populated/editable where source instruction exists.
