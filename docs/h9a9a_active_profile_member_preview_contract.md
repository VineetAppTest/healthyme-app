# H9A.9A Active Profile Member Preview Contract

Scope:

- Adds admin-side Active Profile Preview inside the final Recommendation Profile Builder page.
- Route remains:
  - `/Admin_Recommendation_Profile_Builder`
- Version:
  - `v100.33 · Active Profile Member Preview Contract`
- Adds tab:
  - `Active Profile Preview`
- Allows admin to select a member.
- Pulls that member's active recommendation profile from `hm_recommendation_profiles`.
- Pulls active profile rows from `hm_recommendation_profile_items`.
- Shows active profile summary.
- Shows Day 1 to Day 7 member preview.
- Shows meal, exercise and supplement rows as saved in the active profile contract.
- Validates basic contract readiness:
  - active profile exists
  - profile status is active
  - member assignment exists
  - recommendation rows exist
  - row counts by meal/exercise/supplement
  - missing day coverage
  - supplement frequency vs timeline count

Diagnostic placement:

- Raw active profile contract payload is removed from the normal Active Preview tab.
- Raw payload is available only in System Tools via:
  - `/Admin_Active_Profile_Contract_Diagnostics`
- Admin Dashboard now exposes this under System Tools as:
  - `Active Profile Contract Diagnostics`

Impact:

- Admin-only preview.
- No SQL changes.
- No Flutter changes.
- No member-facing display change.
- Publish/Activate behavior remains unchanged.

Smoke test:

1. Open `/Admin_Recommendation_Profile_Builder`.
2. Confirm version `v100.33 · Active Profile Member Preview Contract`.
3. Confirm tab `Active Preview` is visible.
4. Open `Active Preview`.
5. Select a member with an active recommendation profile.
6. Confirm profile summary is visible.
7. Confirm row counts for Meal, Exercise, Supplement and Total rows.
8. Confirm Day 1 to Day 7 tabs render.
9. Confirm meal, exercise and supplement rows display exactly from the active profile.
10. Confirm raw contract payload is not shown in normal Active Preview.
11. Open Admin Dashboard > System Tools > Active Profile Contract Diagnostics.
12. Confirm raw contract payload is available only there.
13. Confirm a member without active profile shows a clear empty-state message.
14. Confirm no Flutter/member-facing page is changed.
