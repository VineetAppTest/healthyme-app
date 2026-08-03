# Supplement Member Allocation — Phase D

Date: 2026-08-04  
Issue: #360

## Outcome

Phase D establishes an independent Admin workflow for member-specific Supplement
allocation while preserving the existing `member_supplements` authority and every
legacy allocation ID.

The workflow:

- allows new allocations only from active canonical Supplement repository items;
- writes only `member_supplements`, existing supplement audit logs and member notifications;
- stores canonical `source_type = supplement_repository` and `source_id`;
- freezes member-facing source snapshots without repository `admin_notes`;
- owns dosage, frequency, timing, instructions, dates and allocation lifecycle;
- preserves stopped and historical rows instead of replacing or deleting them;
- blocks stale allocation IDs and canonical source-identity changes;
- clears the Add form only after a confirmed save.

## Legacy compatibility mapping

Existing `member_supplements` rows did not contain a canonical `source_id`.
Phase D resolves them without changing allocation IDs using this order:

1. retain an already persisted canonical `source_id`;
2. match the allocation ID to the repository item's `legacy_source_id`;
3. use one unique, case-insensitive exact Supplement name match;
4. leave the row readable but unmapped when no unique match exists;
5. require an Admin-selected active canonical source before an unmapped active row can be edited.

A safe compatibility match is persisted when the row is next updated, stopped or
auto-stopped. Read-only listing alone does not rewrite production data.

## Production inventory validation

Read-only production checks found six legacy allocations and five active canonical
Supplement repository items.

- Five allocations have a direct repository `legacy_source_id` match.
- The second Potassium allocation maps uniquely by exact Supplement name.
- All six can therefore receive a canonical source reference without replacing their IDs.

No production row was changed during inventory validation.

## Routes

- Repository ownership: `pages/39_Admin_Supplement_Manager.py`
- Member allocation ownership: `pages/43_Admin_Supplement_Member_Allocation.py`
- Exercise member allocation remains separate at `pages/42_Admin_Exercise_Member_Allocation.py`
- The Admin Dashboard exposes both independent allocation routes.

## Safety boundary

This phase does not:

- modify Supplement repository definitions;
- write or publish `recommendation_shares`;
- implement Current Member Plan persistence;
- change Supabase schema, RLS, RPCs or Auth;
- replace existing allocation IDs or historical rows;
- modify Flutter.

## Next phase

Consolidated read-only Current Member Plan across Meal, Exercise and Supplement
sources, with no new persistence authority.
