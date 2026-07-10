# H9A.10C Profile Builder Source Detail Pull + Snapshot Persistence

Scope:
- Adds the schema extension needed to preserve full source details selected in Recommendation Profile Builder.
- Expands source-backed labels so Recipe, Exercise and Supplement dropdowns show lightweight details, not only titles.
- Preserves full source snapshots after the H9A.10C SQL columns are present.
- Keeps admin override fields separate from source data.
- Preserves image references only; images are not loaded in normal admin editing.

Route impacted:
- `/Admin_Recommendation_Profile_Builder`

Schema file:
- `sql/h9a10c_profile_source_snapshot_columns.sql`

New item fields:
- `source_type`
- `source_id`
- `source_label`
- `source_snapshot`
- `source_image_url`
- `source_image_bucket`
- `source_image_path`
- `source_image_access_type`

Expected UX change:
- Recipe dropdown labels include meal type, portion, prep time, calories and image-reference availability where available.
- Exercise dropdown labels include category, difficulty, duration/reps, equipment and image-reference availability where available.
- Supplement dropdown labels include dosage, frequency and timing where available.

Expected save behaviour:
- Before SQL: draft save stays backward-compatible and saves legacy slim rows.
- After SQL: draft save also preserves source type, source id, clean source label, full source snapshot and image references.

Impact:
- Additive SQL only.
- No destructive migration.
- No Flutter changes.
- No member-facing display changes yet.

Acceptance checks:
1. Run `sql/h9a10c_profile_source_snapshot_columns.sql` in Supabase SQL Editor.
2. Open `/Admin_Recommendation_Profile_Builder`.
3. Confirm Profile Setup source caption says snapshot schema is ready.
4. Confirm Meals, Exercise and Supplements dropdowns show source details.
5. Save a draft with one row from each source type.
6. Confirm save message says source snapshots were preserved.
7. Confirm saved rows contain source metadata and source snapshot values.

Next sprint:
- H9A.10D — Member Recommendation Consumption Contract.
