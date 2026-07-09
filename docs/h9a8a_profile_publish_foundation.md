# H9A.8A Profile Builder Publish Foundation

Scope:

- Adds a new admin publish-control page.
- New route:
  - `/Admin_Profile_Publish_Control`
- Version:
  - `v100.31 · Profile Builder Publish Foundation`
- Allows admin to select a saved draft profile and activate it for its assigned member.
- Requires the draft to have:
  - draft status
  - assigned member
  - at least one recommendation row
- Requires typed confirmation: `ACTIVATE`.
- When a profile is activated, any previous active profile for the same member is marked `replaced`.
- Writes event history:
  - `profile_activated`
  - `profile_replaced` for previous active profile(s)
- Shows current active profiles.
- Shows selected draft readiness and row counts before activation.
- Keeps member-facing display unwired in this sprint.

No SQL changes are included. Existing `hm_recommendation_profiles`, `hm_recommendation_profile_items`, and `hm_recommendation_profile_events` tables are reused.

Smoke test:

1. Open `/Admin_Profile_Publish_Control`.
2. Confirm version `v100.31 · Profile Builder Publish Foundation` is visible.
3. Confirm current active profiles table loads or shows empty-state message.
4. Select a saved draft with member assignment.
5. Confirm draft readiness panel shows Profile, Member, Status, Start Date, and row counts.
6. Confirm activation is blocked if member assignment or rows are missing.
7. Type `ACTIVATE`.
8. Click `Publish / Activate Profile`.
9. Confirm success message.
10. Refresh and confirm the profile appears under current active profiles.
11. If the member already had an active profile, confirm the previous active profile is replaced.
12. Confirm there is no member-facing display in this sprint.
