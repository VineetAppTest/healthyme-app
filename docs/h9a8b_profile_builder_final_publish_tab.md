# H9A.8B Profile Builder Final Publish Tab

Scope:

- Moves Publish Control into the normal Recommendation Profile Builder flow.
- Removes the standalone publish-control route.
- Removes `Mockup_V2` from the final Profile Builder route.
- New final route:
  - `/Admin_Recommendation_Profile_Builder`
- Version:
  - `v100.32 · Profile Builder Final Publish Tab`

Final tabs:

- Profile Setup
- Meal Structure
- Exercise Regime
- Supplement Regime
- Preview & End-to-End Flow
- Publish Control

Preserved accepted Profile Beta Structure:

- Exercise Regime: `Exercise | Time of Day | Intensity | Instruction`
- Supplement Regime: `Supplement | Frequency | Timeline | Dosage | Instruction`
- Exercise and Supplement dropdowns continue to load from Profile Builder repository/master data.
- Timeline remains a multiselect and validates against Frequency.

Publish Control behavior:

- Select saved draft.
- Validate draft status, member assignment and recommendation rows.
- Require typed confirmation: `ACTIVATE`.
- Activate selected profile.
- Replace previous active profile for the same member.
- Write activation/replacement event history.

Removed routes:

- `/Admin_Recommendation_Profile_Builder_Mockup_V2`
- `/Admin_Profile_Publish_Control`

No SQL changes. No Flutter changes. No member-facing display change.

Smoke test:

1. Open `/Admin_Recommendation_Profile_Builder`.
2. Confirm version `v100.32 · Profile Builder Final Publish Tab`.
3. Confirm all six tabs are visible.
4. Confirm Profile Setup can load/save draft.
5. Confirm Exercise Regime remains row-based.
6. Confirm Supplement Regime remains row-based with Frequency/Timeline validation.
7. Confirm Preview & End-to-End Flow works.
8. Open Publish Control tab.
9. Select a saved draft and activate with `ACTIVATE`.
10. Confirm previous standalone publish route is removed.
11. Confirm old Mockup V2 route is removed.
