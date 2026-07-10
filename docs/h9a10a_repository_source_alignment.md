# H9A.10A Repository-to-Profile Builder Source Alignment

Purpose:

- Contract-first diagnostic before member recommendation consumption.
- Checks whether Recipe, Exercise and Supplement source information is fully available to the Profile Builder.
- Confirms whether Profile Builder currently pulls complete repository details or only dropdown labels.

Scope:

- Adds a System Tools diagnostic page:
  - `/Admin_Profile_Source_Alignment`
- Adds Admin Dashboard > System Tools button:
  - `Profile Source Alignment`
- Adds reusable diagnostic component:
  - `components/profile_source_alignment.py`
- Version:
  - `v100.37 · Repository Source Alignment`

What the diagnostic checks:

- Recipe Repository active rows vs Profile Builder recipe dropdown values.
- Exercise Repository active rows vs Profile Builder exercise dropdown values.
- Active Supplement regimen names vs Profile Builder supplement dropdown values.
- Source fields currently not preserved by Profile Builder.
- Image reference availability in Recipe and Exercise repositories.
- Recommended member consumption contract direction.

Current finding expected from the diagnostic:

- Profile Builder is not yet a full source-aligned contract.
- Recipe rows are currently captured mostly as label / portion / instruction.
- Exercise rows are currently captured mostly as label / time / intensity / instruction.
- Supplement rows are currently captured mostly as label / timing / dosage-frequency / instruction.
- Repository images and richer metadata should be preserved in the member contract but not necessarily rendered in normal admin editing.

Impact:

- Diagnostic/admin-only change.
- No SQL changes.
- No Flutter changes.
- No member-facing display change.
- No Profile Builder save/publish behavior change.

Smoke test:

1. Open Admin Dashboard.
2. Go to System Tools.
3. Confirm `Profile Source Alignment` button is visible.
4. Click it.
5. Confirm `/Admin_Profile_Source_Alignment` opens.
6. Confirm version `v100.37 · Repository Source Alignment`.
7. Confirm source count cards render for Recipe, Exercise, Supplement and missing labels.
8. Confirm Coverage Assessment table renders.
9. Confirm Dropdown Alignment Check table renders.
10. Confirm Recommended Member Consumption Contract block is visible.
11. Confirm no Profile Builder save/publish behavior is changed.
12. Confirm no member-facing page is changed.
