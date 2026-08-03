# Current Member Plan — Phase E

Date: 2026-08-04  
Issue: #360  
Follows: merged PR #379

## Decision

The Current Member Plan is a consolidated **read-only** member view. It does not create a new persistence authority and does not write, publish, backfill, auto-stop or replace any allocation.

## Source authorities

| Domain | Read authority | Excluded source |
|---|---|---|
| Meals | active Meal Profile (`hm_recommendation_profiles` + meal items only) | retained Profile Builder Exercise/Supplement rows |
| Exercises | `member_exercise_allocations` | Profile Builder Exercise rows |
| Supplements | `member_supplements` | Profile Builder Supplement rows |

The read model keeps source provenance through canonical `source_type + source_id` and frozen source snapshots.

## Production inventory

Read-only production verification before implementation returned:

- active recommendation profiles: 2;
- active-profile Meal items: 2;
- retained Profile Builder Exercise items: 2;
- retained Profile Builder Supplement items: 1;
- Exercise member buckets: 1;
- total Exercise allocations: 2;
- active Exercise allocations: 2;
- total Supplement allocations: 6;
- active Supplement allocations: 5.

No production row was inserted, updated or deleted during this inventory.

## Behaviour

### Current Member Plan

- Meals remain displayed as the active seven-day Meal Profile.
- Current and upcoming Exercise allocations are read from the independent Exercise authority.
- Current and upcoming Supplement allocations are read from the independent Supplement authority.
- Stopped allocations are excluded from the member-facing current plan.
- Active rows whose end date has already passed are hidden as `expired_pending_stop`; the page does not auto-stop or persist them.
- Nutrition Guidance remains sourced from the active Meal Profile.
- The page still renders Exercise or Supplement allocations when no Meal Profile is published.

### Today's Plan

- Today's Meals are the current-day slice of the active Meal Profile.
- Exercises and Supplements are the allocations in effect on the member's local date.
- Retained Profile Builder Exercise/Supplement items are never displayed.
- The existing Daily Log navigation remains unchanged.

## Privacy boundary

Repository `admin_notes` and generic repository `notes` are removed from the member-facing Supplement read model. Exercise member notes remain visible because they are owned by the Exercise member-allocation workflow.

## Write boundary

The Current Member Plan module:

- imports `load_state` only for read access to legacy-compatible Supplement rows;
- never imports or calls `save_state`;
- never calls Exercise or Supplement save/stop functions;
- never publishes `recommendation_shares`;
- never modifies repository definitions;
- never changes schema, RLS, RPCs, Auth, routing authority or Flutter;
- preserves all existing allocation and source IDs.

## Files

- `components/current_member_plan.py`
- `components/current_member_plan_view.py`
- `pages/36_Todays_Journey.py`
- `pages/37_Member_Plan.py`
- `tests/test_current_member_plan.py`
- `.github/workflows/current-member-plan-phase-e-validation.yml`

## Next controlled phase

After Phase E acceptance, run Streamlit production acceptance across:

1. Meal Profile Builder;
2. Exercise Member Allocation;
3. Supplement Member Allocation;
4. Current Member Plan;
5. Today's Plan;
6. existing Member/Admin regression routes.

Flutter implementation remains blocked until Streamlit production acceptance is complete.
