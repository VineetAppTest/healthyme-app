# Streamlit Member Planning production acceptance

Date: 2026-08-04  
Issue: #360  
Baseline: merged PR #380 / `c558a82d7f0ce31a8dc34849788d50273d314f4d`

## Purpose

Validate the complete Streamlit Member Planning journey after the ownership separation:

1. Meal Profile Builder;
2. independent Exercise Member Allocation;
3. independent Supplement Member Allocation;
4. consolidated read-only Current Member Plan;
5. Today's Plan;
6. existing Member and Admin route stability.

This phase does not start Flutter development. Flutter remains blocked until the live Streamlit acceptance walkthrough is explicitly accepted.

## Accepted navigation correction

The Meal Profile Builder top-level navigation is reduced to:

- Setup;
- Meals;
- Allocate Exercise & Supplement;
- View Profiles.

Preview and Publish are actions inside Meals rather than separate top-level tabs. Active Profile is not a separate tab because active and historical profiles are available through View Profiles.

The allocation tab is intentionally compact. It carries the selected member context into the existing focused Exercise or Supplement allocation route. It does not duplicate the full allocation forms and does not merge their persistence authorities.

The Admin Dashboard retains:

- Exercises repository;
- Supplements repository;
- Recommendation Profile Builder.

The duplicate Exercise Member Allocation and Supplement Member Allocation Dashboard buttons are removed. Their registered routes remain available through the Profile Builder allocation workspace.

## Ownership boundary

| Domain | Write authority | Streamlit entry |
|---|---|---|
| Meal profile | Recommendation profile tables / Meal rows only | Meal Profile Builder → Meals |
| Exercise allocation | `member_exercise_allocations` | Meal Profile Builder → Allocate Exercise & Supplement → Allocate Exercise |
| Supplement allocation | `member_supplements` | Meal Profile Builder → Allocate Exercise & Supplement → Allocate Supplement |
| Current Member Plan | Read-only consolidated model | Member Current Member Plan / Today's Plan |

The compact workspace imports no Exercise or Supplement save/stop function and does not call `save_state`.

## Automated acceptance

The acceptance workflow must:

- compile the Profile Builder, allocation workspace, Dashboard, independent allocation pages, Current Member Plan and Today's Plan files;
- run the Profile Builder navigation and write-boundary suite;
- run Exercise and Supplement allocation regressions;
- run Current Member Plan regressions;
- run the Member Planning separation contract;
- run form-reset and authority-trace guards triggered by the changed paths.

## Live Streamlit walkthrough

### Admin

1. Login and reach Admin Dashboard without technical build labels or route errors.
2. Open Exercises and Supplements repository pages and confirm repository management remains unchanged.
3. Open Recommendation Profile Builder.
4. Confirm only Setup, Meals, Allocate Exercise & Supplement and View Profiles appear at the top level.
5. Load an existing profile and confirm its member assignment and Meal rows hydrate correctly.
6. Save Setup and confirm the same Profile ID is retained.
7. Open Meals and confirm Preview Meal Plan and Publish Meal Plan appear below the Meal workflow.
8. Preview the loaded Meal plan.
9. Publish with an Admin/Super Admin account and confirm the existing publish rules remain active.
10. Open Allocate Exercise & Supplement and confirm the assigned member is shown.
11. Open Exercise allocation, create or update an allocation, and confirm the allocation ID and source identity are retained.
12. Open Supplement allocation, create or update an allocation, and confirm legacy/current IDs and source mapping remain intact.
13. Confirm View Profiles shows Draft, Active and historical visibility without a separate Active tab.

### Member

1. Login and reach Member Home.
2. Open Current Member Plan.
3. Confirm Meals come from the active Meal Profile.
4. Confirm Exercises come from independent Exercise allocations only.
5. Confirm Supplements come from independent Supplement allocations only.
6. Confirm retained Exercise/Supplement Profile Builder rows are not duplicated in the member plan.
7. Confirm repository `admin_notes` are not shown.
8. Open Today's Plan and confirm the same authority split for the member-local date.
9. Confirm Daily Log navigation remains available.

## Explicit non-scope

This phase makes no:

- Supabase schema, RLS or RPC change;
- Auth or role-model change;
- repository-data change;
- allocation-store migration;
- recommendation-share redesign;
- Current Member Plan write path;
- Flutter change;
- production data backfill or rewrite.

## Exit rule

Automated checks make the branch ready for live acceptance. Issue #360 can move to Flutter only after the Admin and Member walkthrough above is explicitly accepted and any identified Streamlit regressions are closed.
