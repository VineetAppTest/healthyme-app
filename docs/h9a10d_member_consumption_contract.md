# H9A.10D — Member Recommendation Consumption Contract

## Purpose

This sprint moves the active profile preview from a slim row preview to a member-consumption contract review.

The goal is to confirm that the member-facing layer can consume the recommendation profile without losing the repository/regimen context captured in H9A.10C.

## Scope

- Active Profile Preview now loads source metadata and source snapshots from `hm_recommendation_profile_items` where the H9A.10C columns exist.
- The preview remains backward-compatible with legacy slim rows if source snapshot columns are unavailable.
- The active member contract now includes:
  - final admin row values,
  - source metadata,
  - source snapshot context,
  - admin source overrides,
  - image references as references only.
- No image is loaded in this admin preview.
- No Flutter/member-facing display is changed in this sprint.

## Member-ready row logic

### Meal

Member-facing contract includes:

- meal slot,
- recipe name,
- final portion,
- final instruction,
- meal type,
- diet type,
- prep time,
- calories,
- ingredients,
- steps,
- image reference.

### Exercise

Member-facing contract includes:

- time of day,
- exercise name,
- final instruction,
- category,
- difficulty,
- duration/reps,
- equipment,
- benefits,
- image reference.

### Supplement

Member-facing contract includes:

- supplement name,
- final frequency,
- final dosage,
- final timeline,
- final instruction,
- source timing,
- admin notes,
- source start/end context.

## Admin preview route

`/Admin_Recommendation_Profile_Builder`

Tab:

`Active Profile Preview`

## Acceptance checks

1. Publish/activate a profile with one meal, one exercise and one supplement.
2. Open Active Profile Preview.
3. Confirm the summary card shows source-backed rows count.
4. Confirm the day-wise table shows Source Context and Image Reference columns.
5. Confirm row values show final admin-edited values, not only raw repository labels.
6. Confirm raw payload contains `profile` and `days` with member-ready items.
7. Confirm no image is loaded in admin preview.

## No changes

- No SQL.
- No Flutter.
- No member-facing UI change.
- No publish/activation logic change.
