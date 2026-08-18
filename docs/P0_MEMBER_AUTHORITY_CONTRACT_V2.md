# HealthyMe P0 Member Authority Contract v2

Date: 2026-08-18
Status: Approved correction before Native Member PR2 Today

## Problem

HealthyMe currently contains two generations of member planning logic. The consolidated Current Member Plan already treats Meal, Exercise and Supplement as separate authorities, while the Exercise Journal still derives prescribed Exercise rows from the older Recommendation Profile contract. Flutter also contains older reads that still treat Recommendation Profile Exercise/Supplement rows as active authority.

This correction freezes one contract for both web and native before the Today redesign continues.

## Authoritative sources

- Meal and Nutrition Guidance: active Meal Profile / published recommendation profile, limited to meal and guidance item types.
- Exercise: `member_exercise_allocations` only.
- Supplement: `member_supplements` only.
- Current Member Plan: read-only consolidation only; never a persistence authority.

Retained Recommendation Profile rows of type `exercise` or `supplement` are historical compatibility data. They are not future member-plan or journal assignment authority.

## Exercise effective-date rule

An Exercise allocation applies on a member date only when:

1. allocation status is `active`;
2. `start_date` is blank or `start_date <= selected_date`;
3. `end_date` is blank or `end_date >= selected_date`.

Reads are side-effect free. An expired allocation is not silently persisted as stopped during a member read.

## Exercise Journal identity

A new prescribed Exercise Journal row keeps the stable assignment identity:

- `member_id`
- `log_date`
- `allocation_id`

The accepted Journal also allows the member to add an extra actual Exercise that was not prescribed. Such a row must not fabricate an allocation or Recommendation Profile identity. It uses a journal-only stable `journal_entry_key` for that date instead.

`source_id`, when available, records the canonical Exercise Repository item chosen as the actual activity for traceability. Changing the actual activity does not change the Exercise allocation.

Legacy journal rows retain their existing Recommendation Profile identity:

- `profile_id`
- `day_number`
- `item_order`

Historical rows are not deleted, rewritten or matched to new allocations by Exercise name.

## Journal behaviour preserved

The accepted Exercise Journal remains an actual-behaviour surface. Timing, Activity, Duration / Sets, Remarks, Status and Completion Time remain member-editable where currently supported. A member changing the actual Activity does not change the underlying Exercise allocation: the journal row remains linked to the original `allocation_id`, while the selected actual activity/details are stored only in that journal row.

`+ Add Exercise`, `Remove Exercise`, saved-day/history and legacy saved days remain available.

## Member-safe fields

Internal/admin-only notes are not member content. In particular:

- assessment `admin_note` must not be rendered on Member Home;
- stored admin/internal notes remain preserved for admin workflows and audit/history;
- member communication must use a member-facing instruction/message field rather than an internal note.

## Compatibility and rollback

- Existing Recommendation Profile, Exercise allocation and Supplement allocation stores are preserved.
- Existing Exercise Journal rows and their identifiers are preserved.
- Existing legacy Exercise Journal uniqueness remains valid for legacy rows.
- Additive uniqueness is introduced for allocation-linked and journal-only new rows.
- Existing web Current Member Plan remains read-only and keeps the three-authority model.
- Flutter migration consumes the corrected contract after this web source-of-truth correction is validated.

## Explicitly out of scope

- PR2 Today UI/content redesign.
- Schedule timezone/reschedule-policy parity.
- Notification migration.
- Body-Mind and Reports/Progress migration.
- A wholesale backend normalization into new relational allocation tables.
- Destructive backfill of historical Exercise Journal rows.

## P0 acceptance

1. Web Current Member Plan and Web Exercise Journal use the same Exercise authority.
2. Exercise Journal shows only allocations effective for the selected date as assigned rows.
3. New prescribed Exercise Journal saves use `allocation_id`; extra actual Exercise rows use journal-only identity; old profile-linked history remains readable.
4. Exercise Journal writes cannot modify Exercise Repository, Recommendation Profile or Exercise allocation records.
5. `admin_note` is not exposed on Member Home.
6. Existing Meal, Supplement, journal history, auth/roles/RLS and schedule behaviour is unchanged.
