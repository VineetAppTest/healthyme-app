# H9A.10C.3 Render Source Detail Rows

Follow-up after PR #89 smoke test showed that the clean dropdown label check did not pass and the second Pulled Source Details row was not visible for Meals, Exercise or Supplements.

Scope:

- Renders Pulled Source Details explicitly inside the Recommendation Profile Builder page, directly below each selected Recipe / Exercise / Supplement row.
- Keeps first row compact and familiar:
  - Meal: Recipe | Portion | Instruction
  - Exercise: Exercise | Time of Day | Intensity | Instruction
  - Supplement: Supplement | Frequency | Timeline | Dosage | Instruction
- Keeps dropdown labels clean: name only.
- Records edited source-detail values into session override state.
- Persists original source snapshot plus admin-edited source overrides through the existing H9A.10C source snapshot columns.
- Removes reliance on monkey-patching Streamlit buttons for source-detail rendering.

Expected version:

- `v100.37 · Editable Source Detail Fields`

Route:

- `/Admin_Recommendation_Profile_Builder`

No new SQL.
No Flutter change.
No member-facing change.

Smoke test:

1. Open `/Admin_Recommendation_Profile_Builder`.
2. Confirm version `v100.37 · Editable Source Detail Fields`.
3. Confirm Recipe / Exercise / Supplement dropdowns show clean names only.
4. In Meals, select a recipe and confirm Pulled Source Details appears below the row.
5. In Exercise, select an exercise and confirm Pulled Source Details appears below the row.
6. In Supplements, select a supplement and confirm Pulled Source Details appears below the row.
7. Edit one source-detail field and save draft.
8. Confirm saved `source_snapshot` contains `source_original_snapshot` and `admin_source_overrides`.
