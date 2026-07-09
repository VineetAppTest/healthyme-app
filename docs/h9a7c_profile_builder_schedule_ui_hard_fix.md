# H9A.7C Profile Builder Schedule UI Hard Fix

Scope:

- Adds V5 Profile Builder implementation and routes the existing V2 direct URL to V5.
- Forces the visible Exercise Regime slots to:
  - Morning
  - Afternoon
  - Evening
  - Night / As advised
- Forces the visible Supplement Regime slots to:
  - Before Breakfast
  - After Breakfast
  - Before Lunch
  - After Lunch
  - Before Dinner
  - After Dinner
  - Before Bed
- Removes the information message above the day buttons: `Select day to edit / Row 1: Day 1 to Day 4...`.
- Maintains draft save/load, clone, validation, preview, cross-section buffering, and time selectors.
- Uses schema marker `v100.26` to clear stale Streamlit schedule keys.
- No SQL changes.
- No publish, activate, member-facing, or Flutter changes.

Smoke test route:

`/Admin_Recommendation_Profile_Builder_Mockup_V2`

Expected version:

`v100.26 · Profile Builder Schedule UI Hard Fix`
