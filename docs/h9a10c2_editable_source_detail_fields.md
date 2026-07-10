# H9A.10C.2 Editable Source Detail Fields

Intent:
- Club the dropdown label cleanup with editable source-detail UX.
- Keep Profile Builder rows compact.
- Show source details as a second compact row under the selected item, not concatenated into dropdown labels.

UX rule:
- Dropdowns show clean source names only.
- Pulled source details appear separately as editable fields.
- Existing admin override fields remain on the first row.
- Image references are shown as reference text only; images are not loaded in normal admin editing.

Persistence rule:
- Source snapshot persistence from H9A.10C remains active.
- Edited source-detail values are preserved inside source_snapshot as admin_source_overrides and effective top-level values.
- Original source snapshot is also retained inside source_original_snapshot.

No SQL change is required beyond the H9A.10C columns already run.

Smoke test:
1. Open /Admin_Recommendation_Profile_Builder.
2. Confirm Recipe / Exercise / Supplement dropdowns show clean names only.
3. Select a recipe and confirm Pulled Source Details appears below the row with editable recipe details.
4. Select an exercise and confirm Pulled Source Details appears below the row with editable exercise details.
5. Select a supplement and confirm Pulled Source Details appears below the row with editable supplement details.
6. Edit at least one pulled field and save the draft.
7. Verify Supabase source_snapshot contains source_original_snapshot and admin_source_overrides.
