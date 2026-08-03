# Recommendation Profile Builder — Canonical Repository Contract

Status: Phase 1 contract freeze for issue #343  
Contract version: `2026-08-03-v1`

## Purpose

Recommendation Profile Builder currently reaches Recipe, Exercise and Supplement through different source paths and runtime adapters. This contract creates one stable boundary before the live Builder is migrated.

Phase 1 does **not** change the Builder UI, draft saving, publication, Active profiles or member consumption. It defines and tests the contract that those flows will use in the next phase.

## Common source format

Every repository item is normalised to the same envelope:

```text
contract_version
kind
source_type
source_id
identity_key
display_label
status
selectable
snapshot
```

### Identity rule

`source_id` is authoritative. `display_label` is presentation-only.

Example:

```text
exercise_repository:2 → display label "Mobility Flow"
exercise_repository:9 → display label "Mobility Flow"
```

Both records remain independently addressable even though their visible names match.

## Repository rules

| Repository | Current authority | ID rule | New selection rule |
|---|---|---|---|
| Recipe | `data/recipes.csv` compatibility repository | Numeric compatibility row ID; physical deletion and reindexing remain prohibited until durable Recipe migration | Active only |
| Exercise | Supabase-backed application state `exercises` | Persistent numeric repository ID | Active only |
| Supplement | Supabase-backed application state `supplement_repository` | Persistent `suprepo_*` repository ID | Active only |

## Snapshot rule

When a repository item is selected and saved into a recommendation, its content snapshot becomes historical evidence. Later repository edits or deactivation must not rewrite an already-saved recommendation snapshot.

A deactivated item:

- is excluded from new selections;
- remains resolvable by `source_id` when reviewing an existing profile;
- retains the saved snapshot that was attached to that profile.

## Supplement separation

The reusable Supplement Repository supplies:

- Supplement name
- Dosage default
- Frequency default
- Timing default
- Instructions
- Status

The new repository snapshot deliberately excludes:

- Member allocation
- Member-specific Start Date
- Member-specific End Date
- Admin Notes

Those values either belong to the member recommendation being created or are no longer part of the accepted repository UI.

## Contract API

`components/profile_builder_repository_contract.py` exposes:

- `canonical_repository_contract_manifest()`
- `normalise_profile_builder_repository_source(kind, row)`
- `list_profile_builder_repository_sources(kind, active_only=True)`
- `profile_builder_repository_source_by_id(kind, source_id, active_only=False)`

The live Profile Builder is not wired to these functions in Phase 1.

## Non-regression boundary

Phase 1 changes no:

- Profile Builder widget or page;
- draft, clone, module-save, Preview, Publish or Active operation;
- repository data or mutation path;
- authentication, role, routing or RLS rule;
- member-facing page.

## Next phase

Phase 2 will replace the existing mixed source chain inside Recommendation Profile Builder with this contract. It will migrate selection and source-detail lookup from visible labels to canonical IDs while keeping old saved profiles readable.
