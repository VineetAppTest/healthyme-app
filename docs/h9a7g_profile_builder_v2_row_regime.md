# H9A.7G Profile Builder V2 Row-Based Regime

Scope:

- Updates the default `/Admin_Recommendation_Profile_Builder_Mockup_V2` page.
- Removes the separate B4 comparison page.
- Removes the B4 comparison documentation.
- Updates version to `v100.30 · Profile Builder V2 Row-Based Regime`.

Exercise Regime fields:

- Exercise
- Time of Day
- Intensity
- Instruction

Exercise is loaded from the Profile Builder repository/master-data dropdown. Time of Day options are:

- Morning
- Afternoon
- Evening
- Night / As advised

Supplement Regime fields:

- Supplement
- Frequency
- Timeline
- Dosage
- Instruction

Supplement is loaded from the Profile Builder repository/master-data dropdown. Frequency is a number. Timeline is a multiselect from:

- Before Breakfast
- After Breakfast
- Before Lunch
- After Lunch
- Before Dinner
- After Dinner
- Before Bed

Timeline selection is validated against the frequency number.

No SQL changes. No Flutter changes. No publish, activate, or member-facing changes.

Smoke test:

1. Open `/Admin_Recommendation_Profile_Builder_Mockup_V2`.
2. Confirm version `v100.30 · Profile Builder V2 Row-Based Regime`.
3. Go to Exercise Regime.
4. Confirm fields are `Exercise | Time of Day | Intensity | Instruction`.
5. Confirm Exercise is a dropdown from repository/master data.
6. Confirm Time of Day options are Morning, Afternoon, Evening, Night / As advised.
7. Go to Supplement Regime.
8. Confirm fields are `Supplement | Frequency | Timeline | Dosage | Instruction`.
9. Confirm Supplement is a dropdown from repository/master data.
10. Confirm Frequency is numeric.
11. Confirm Timeline is a multiselect and validates against Frequency.
12. Confirm the separate B4 route is removed.
