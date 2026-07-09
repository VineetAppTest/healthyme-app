# H9A.7B Profile Builder Session Reset Hotfix

Scope:

- Adds a route-level hard reset for stale Profile Builder Streamlit session keys.
- Reset is triggered only when the schedule schema marker changes to `v100.25`.
- Clears stale meal/exercise/supplement widget keys, row count buffers, preview day keys and action-message keys.
- Forces the active section back to Profile Setup after reset.
- This is intended to remove old Exercise/Supplement slot state after the schedule alignment change.
- No SQL changes.
- No publish, activate, member-facing, or Flutter changes.

Smoke test:

1. Open `/Admin_Recommendation_Profile_Builder_Mockup_V2` after merge/deploy.
2. Confirm page opens cleanly on Profile Setup.
3. Click New Draft.
4. Go to Exercise Regime and confirm slots are Morning, Afternoon, Evening, Night / As advised.
5. Go to Supplement Regime and confirm slots are Before Breakfast, After Breakfast, Before Lunch, After Lunch, Before Dinner, After Dinner, Before Bed.
6. Confirm save/load still works.
