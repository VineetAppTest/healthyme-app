# H9A.10A / H9A.10B Repository Source Alignment + Source Selection Contract

Scope completed in this PR:

## H9A.10A — Repository-to-Profile Builder Source Alignment

- Adds a contract-first diagnostic page before member recommendation consumption is built.
- Compares the actual source repositories against what the current Recommendation Profile Builder captures.
- Checks Recipe, Exercise, active Supplement Regimen, image reference availability, and field-level information not preserved by the older Profile Builder flow.
- Adds System Tools entry: `Profile Source Alignment`.
- Adds route: `/Admin_Profile_Source_Alignment`.
- Adds visible diagnostic page version: `v100.37 · Repository Source Alignment`.

## H9A.10B — Profile Builder Source Selection Contract

- Updates `load_profile_builder_sources()` so Profile Builder dropdowns no longer rely only on `hm_recommendation_master_options` for recommendation items.
- Recipe dropdown now prefers active rows from the Recipe Repository.
- Exercise dropdown now prefers active rows from the Exercise Repository.
- Supplement dropdown is augmented from active member supplement regimen names when available.
- Profile/demographic dropdowns such as age band, health concern and diet type continue to use Profile Builder master data.
- Draft save/load behavior remains backward compatible.
- No SQL migration is required for this step.

Impact:

- Admin/Profile Builder source improvement only.
- No SQL changes.
- No Flutter changes.
- No member-facing display changes.
- No publish/activate logic change.

Next step after acceptance:

- H9A.10C — Member Recommendation Consumption Contract.

Smoke check:

1. Open `/Admin_Recommendation_Profile_Builder`.
2. Go to Meal Structure and confirm Recipe dropdown shows actual active Recipe Repository items where available.
3. Go to Exercise Regime and confirm Exercise dropdown shows actual active Exercise Repository items where available.
4. Go to Supplement Regime and confirm Supplement dropdown includes active regimen names where available.
5. Open Admin Dashboard > System Tools > Profile Source Alignment.
6. Confirm `/Admin_Profile_Source_Alignment` opens and shows coverage/missing-field diagnostics.
7. Confirm no member-facing page is changed.
