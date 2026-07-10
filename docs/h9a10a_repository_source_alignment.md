# H9A.10A / H9A.10B Repository Source Alignment + Source Selection Contract

Scope completed in this PR:

## H9A.10A — Repository-to-Profile Builder Source Alignment

- Adds a contract-first diagnostic page before member recommendation consumption is built.
- Compares the actual source repositories against what the current Recommendation Profile Builder captures.
- Checks:
  - Recipe repository active rows vs Profile Builder recipe dropdown labels.
  - Exercise repository active rows vs Profile Builder exercise dropdown labels.
  - Active supplement regimen names vs Profile Builder supplement dropdown labels.
  - Recipe and exercise image reference availability.
  - Field-level information currently not preserved by Profile Builder.
- Adds System Tools entry:
  - `Profile Source Alignment`
- Adds route:
  - `/Admin_Profile_Source_Alignment`
- Adds visible diagnostic page version:
  - `v100.37 · Repository Source Alignment`

## H9A.10B — Profile Builder Source Selection Contract

- Updates `load_profile_builder_sources()` so Profile Builder dropdowns no longer rely only on `hm_recommendation_master_options` for recommendation items.
- Recipe dropdown now prefers active rows from the Recipe Repository.
- Exercise dropdown now prefers active rows from the Exercise Repository.
- Supplement dropdown is augmented from active member supplement regimen names when available.
- Profile/demographic dropdowns such as age band, health concern and diet type continue to use Profile Builder master data.
- Draft save/load behavior remains backward compatible.
- No SQL migration is required for this step.

Important finding confirmed:

- The old Profile Builder captured slim recommendation rows.
- Recipe and exercise repositories contain richer data than the Profile Builder currently preserved.
- Images should be preserved by reference for member consumption, but do not need to render in normal admin editing.
- Supplement regimen is member-specific and should be pulled from active member supplement rows where relevant instead of re-entered manually.

Impact:

- Admin/Profile Builder source improvement only.
- No SQL changes.
- No Flutter changes.
- No member-facing display changes.
- No publish/activate logic change.

Next step after acceptance:

- H9A.10C — Member Recommendation Consumption Contract
  - Resolve selected recipe/exercise/supplement names into full member-facing details.
  - Preserve image references for member web / Flutter.
  - Decide what is shown on member side vs hidden from normal admin editing.

Smoke check:

1. Open `/Admin_Recommendation_Profile_Builder`.
2. Go to Meal Structure.
3. Confirm Recipe dropdown shows actual active Recipe Repository items where available.
4. Go to Exercise Regime.
5. Confirm Exercise dropdown shows actual active Exercise Repository items where available.
6. Go to Supplement Regime.
7. Confirm Supplement dropdown includes active regimen names where available.
8. Open Admin Dashboard > System Tools > Profile Source Alignment.
9. Confirm `/Admin_Profile_Source_Alignment` opens and shows coverage/missing-field diagnostics.
10. Confirm no member-facing page is changed.
