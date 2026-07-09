# H9A.7D Profile Builder No-Fallback UI Implementation

Scope:

- Makes `/Admin_Recommendation_Profile_Builder_Mockup_V2` the direct implementation page.
- Removes the V2-to-V5 switch-page fallback route.
- Deletes the temporary V5 Profile Builder route file.
- Exercise Regime renders only:
  - Morning
  - Afternoon
  - Evening
  - Night / As advised
- Supplement Regime renders only:
  - Before Breakfast
  - After Breakfast
  - Before Lunch
  - After Lunch
  - Before Dinner
  - After Dinner
  - Before Bed
- Removes the information message above the day buttons: `Select day to edit / Row 1: Day 1 to Day 4...`.
- Removes silent slot mapping. If a saved draft contains old/unsupported slot names, those rows are preserved and a warning is shown rather than silently mapping them into the new structure.
- Keeps draft save/load, clone, validation, preview, cross-section buffering and time selectors.
- No SQL changes.
- No publish, activate, member-facing or Flutter changes.

Smoke test route:

`/Admin_Recommendation_Profile_Builder_Mockup_V2`

Expected version:

`v100.27 · Profile Builder Direct Schedule Fix`
