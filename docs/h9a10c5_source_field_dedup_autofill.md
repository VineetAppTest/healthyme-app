# H9A.10C.5 Source Field De-duplication and Auto-fill

Scope:

- Removes duplicate source-detail fields from the Recommendation Profile Builder UX.
- Exercise row now uses `Exercise | Time of Day | Instruction`; first-row `Intensity` is removed because repository `Difficulty` is the source-backed equivalent.
- Exercise Pulled Source Details now opens immediately when the Exercise is selected.
- Meal Source Portion is no longer shown as a separate Pulled Source Detail field; source portion auto-fills the first-row Portion field.
- Supplement Source Frequency and Source Dosage are no longer shown as duplicate Pulled Source Detail fields; they auto-fill first-row Frequency and Dosage.
- Supplement Source Timing is retained as context and helps populate Timeline where possible.
- Supplement source Start Date and End Date are shown only as read-only regimen context, not editable recommendation fields.
- Existing H9A.10C source snapshot persistence remains unchanged.

Version:

- `v100.38 · Source Field De-duplication and Auto-fill`

Route:

- `/Admin_Recommendation_Profile_Builder`

No new SQL.
No Flutter change.
No member-facing change.

Smoke test:

1. Open `/Admin_Recommendation_Profile_Builder`.
2. Confirm version `v100.38 · Source Field De-duplication and Auto-fill`.
3. Meals: select a recipe and confirm Portion auto-fills if source portion exists.
4. Meals: confirm Pulled Source Details does not show Source Portion as a duplicate field.
5. Exercise: select an exercise and confirm Pulled Source Details appears immediately, before selecting Time of Day.
6. Exercise: confirm first row is Exercise | Time of Day | Instruction; no Intensity field.
7. Exercise: confirm Difficulty appears in Pulled Source Details.
8. Supplements: select a supplement and confirm Frequency/Dosage auto-fill where source values exist.
9. Supplements: confirm Pulled Source Details does not duplicate Source Frequency or Source Dosage.
10. Supplements: confirm source Start Date/End Date are read-only context only.
11. Save draft and confirm source snapshots are still preserved.
