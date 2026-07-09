# H9A.8A Profile Builder Publish Foundation

Superseded route note:

- The standalone route `/Admin_Profile_Publish_Control` was smoke-tested successfully.
- Publish Control has now been moved into the final Recommendation Profile Builder page.
- Current final route: `/Admin_Recommendation_Profile_Builder`.
- Current implementation version: `v100.32 · Profile Builder Final Publish Tab`.

Publish Control behavior remains:

- Select saved draft.
- Validate draft status, member assignment and recommendation rows.
- Require typed confirmation: `ACTIVATE`.
- Activate selected profile.
- Replace previous active profile for the same member.
- Write activation/replacement event history.

Latest integrated implementation is documented in `docs/h9a8b_profile_builder_final_publish_tab.md`.
