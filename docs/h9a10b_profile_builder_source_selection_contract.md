# H9A.10B Profile Builder Source Selection Contract

Scope:

- Moves Profile Builder dropdown sourcing away from label-only master data for the three recommendation domains.
- Recipe dropdown now prefers active Recipe Repository rows.
- Exercise dropdown now prefers active Exercise Repository rows.
- Supplement dropdown now prefers unique names from active supplement regimen rows.
- Preserves age band, health concern and diet type behaviour from Profile Builder master data.
- Adds a source contract helper that builds immutable source snapshots for:
  - recipe repository items
  - exercise repository items
  - active supplement regimen items
- Preserves image references in the contract helper as references only:
  - `image_url`
  - `image_bucket`
  - `image_path`
  - `image_access_type`
- Does not load heavy images in normal admin editing.

Route impacted:

- `/Admin_Recommendation_Profile_Builder`

Expected visible behaviour:

- On Profile Setup, the dropdown source caption should mention source-backed Recipe / Exercise / Supplement options.
- Meal Structure recipe dropdown should reflect active Recipe Repository titles.
- Exercise Regime exercise dropdown should reflect active Exercise Repository titles.
- Supplement Regime supplement dropdown should reflect active supplement regimen names where available.

Important contract position:

- This is source-selection alignment, not member-facing consumption yet.
- Existing admin override fields remain unchanged:
  - meal portion/instruction
  - exercise time of day/intensity/instruction
  - supplement frequency/timeline/dosage/instruction
- Existing draft save/publish schema remains unchanged in this sprint.
- No SQL changes.
- No Flutter changes.
- No member-facing display changes.

Next sprint:

- H9A.10C — Profile Builder Source Snapshot Persistence
  - Persist source type/source id/source snapshot at draft/publish time.
  - Keep image references as references only.
  - Keep admin override fields separate from source snapshot.

Then:

- H9A.10D — Member Recommendation Consumption Contract
