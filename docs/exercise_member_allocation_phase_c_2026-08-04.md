# Exercise Member Allocation — Phase C

Date: 2026-08-04  
Issue: #360

## Outcome

Phase C establishes an independent Admin workflow for member-specific Exercise
allocation.

The workflow:

- reads only active canonical Exercise repository sources for new allocations;
- writes only `member_exercise_allocations`;
- stores canonical `source_type = exercise_repository` and `source_id`;
- keeps the legacy-compatible `exercise_id`;
- preserves allocation IDs during edits;
- preserves stopped and historical rows instead of deleting them;
- freezes a member-facing source snapshot at allocation creation;
- owns dates, instructions, notes and allocation status.

## Route

`pages/42_Admin_Exercise_Member_Allocation.py`

## Safety boundary

This phase does not:

- modify the Exercise repository;
- change Supabase schema, RLS or RPCs;
- write `recommendation_shares`;
- implement Supplement allocation;
- implement Current Member Plan;
- change authentication or central routing;
- modify Flutter.

## Compatibility

Existing rows that contain `exercise_id` but not `source_id` are read as
`exercise_repository:<exercise_id>`. Existing IDs are retained. Inactive
repository sources cannot be used for a new allocation, but historical
allocations linked to those sources remain readable.

## Next phase

Independent Supplement Member Allocation with compatibility mapping for legacy
`member_supplements` rows.
