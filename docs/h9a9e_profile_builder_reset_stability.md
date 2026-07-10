# H9A.9E Profile Builder Reset Stability Polish

Scope:

- Follow-up after PR #83 smoke testing.
- Fixes `New Draft` so the saved draft dropdown is cleared back to `-- Select saved draft --`.
- Clears old loaded draft state, profile widget state, clone widget state, row state and validation state when starting a new draft.
- Moves New Draft, Load Draft, Clone Selected and Add Row actions to Streamlit callback style so actions are applied before the next page render.
- Keeps top tab labels short and single-line.
- Updates visible version to:
  - `v100.36 · Profile Builder Reset Stability Polish`

Route:

- `/Admin_Recommendation_Profile_Builder`

Impact:

- UI/state-management fix only.
- No SQL changes.
- No Flutter changes.
- No member-facing display change.
- No publish/activate logic change.
- No active preview contract change.

Smoke test:

1. Open `/Admin_Recommendation_Profile_Builder`.
2. Confirm version `v100.36 · Profile Builder Reset Stability Polish`.
3. Select an existing draft in `Load saved draft` and click `Load Draft`.
4. Confirm draft data loads.
5. Click `New Draft`.
6. Confirm `Load saved draft` resets to `-- Select saved draft --`.
7. Confirm profile fields clear.
8. Confirm old draft id is no longer shown.
9. Confirm row data does not carry over into the new blank draft.
10. Select a profile in `Clone From Existing Profile` and click `Clone Selected`.
11. Confirm clone completes and creates an unsaved `Copy of ...` draft.
12. Confirm any refresh/freeze is limited to the normal single Streamlit refresh and no double-stall behavior appears.
13. Confirm Load Draft / New Draft and Clone Selected remain aligned.
14. Confirm Publish and Active tabs still open normally.
