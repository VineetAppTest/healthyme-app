# Meal Profile Builder meals-only cutover — Phase B

Date: 2026-08-04  
Issue: #360  
Follows: merged PR #361

## Decision

The existing stable route `pages/38_Admin_Recommendation_Profile_Builder.py` becomes the live **Meal Profile Builder** without changing its registered route.

The workflow owns:

- Profile Setup;
- Meal Structure;
- Recipe source selection and immutable meal source snapshots;
- Preview, Publish, Active Profile Preview and View Profiles.

It no longer owns new Exercise or Supplement editing.

## Live section change

Visible builder sections are now:

1. Profile Setup
2. Meal Structure
3. Preview
4. Publish — Admin/Super Admin only
5. Active
6. View Profiles

Exercise Regime and Supplement Regime are removed from live navigation and cannot be restored through stale session state.

## Write boundary

The page installs a fail-closed Meal Profile Builder write boundary before the modular renderer imports its module save function.

- `meal` rows may be saved through the existing verified module contract.
- `exercise` and `supplement` module-save attempts are rejected.
- Setup saves continue to update profile-level fields only.
- Meal saves continue to replace only `item_type = meal` rows.
- No action in this phase deletes or rewrites existing Exercise or Supplement rows.

## Existing profile compatibility

Existing Draft and Active profiles continue to load all persisted recommendation rows.

- Meal rows remain editable.
- Existing Exercise rows remain loaded for Preview/Publish and are read-only in Meal Profile Builder.
- Existing Supplement rows remain loaded for Preview/Publish and are read-only in Meal Profile Builder.
- Publish eligibility continues to recognise retained profile rows so historical combined profiles remain publishable.
- View Profiles and Active Profile Preview remain read-only full-plan views.
- Existing profile IDs, allocation, status, source snapshots and event history remain unchanged.

## Repository boundary

- Recipe sources remain available to Meal Structure.
- Exercise and Supplement repository sources are intentionally not supplied to new builder rows.
- Canonical Content Repository IDs and payloads are unchanged.
- No repository record is inserted, updated, deactivated or deleted by this phase.

## Safety boundary

This phase includes no:

- Supabase schema, RLS or RPC migration;
- production data backfill or rewrite;
- authentication, session or central routing change;
- Exercise member-allocation implementation;
- Supplement member-allocation implementation;
- Current Member Plan persistence implementation;
- Flutter change.

## Next controlled phases

1. Independent Exercise Member Allocation.
2. Independent Supplement Member Allocation with legacy `source_id` compatibility mapping.
3. Current Member Plan consolidated read model.
