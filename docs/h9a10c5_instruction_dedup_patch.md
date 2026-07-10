# H9A.10C.5 Instruction De-duplication Patch

Follow-up patch after PR #92 was merged.

Issue observed:

- Exercise first row already has Instruction.
- Supplement first row already has Instruction.
- Pulled Source Details also showed Source Instructions.
- This created duplicate editable instruction fields.

Corrected behavior:

- Exercise source instructions auto-fill the first-row Instruction field when blank.
- Supplement source instructions auto-fill the first-row Instruction field when blank.
- Pulled Source Details no longer renders the duplicate Source Instructions editable field.
- Source snapshot still preserves the original repository/regimen instructions.
- Admin-edited first-row Instruction remains the final member-facing instruction.

No SQL.
No Flutter/member-facing code change.

Smoke check:

1. Open `/Admin_Recommendation_Profile_Builder`.
2. Go to Exercise Regime.
3. Select an Exercise.
4. Confirm first-row Instruction auto-fills where source instructions exist.
5. Confirm Pulled Source Details does not show Source Instructions.
6. Go to Supplement Regime.
7. Select a Supplement.
8. Confirm first-row Instruction auto-fills where source instructions exist.
9. Confirm Pulled Source Details does not show Source Instructions.
10. Save draft and confirm source snapshots remain preserved.
