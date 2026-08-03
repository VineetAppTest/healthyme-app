# Content Repository persistence standardisation

Issue: #347

## Accepted business architecture

Content creation and maintenance remains separate from Member Planning:

```text
Content Repositories
├── Recipe Repository
├── Exercise Repository
└── Supplement Repository
```

This work standardises only the persistence behind those three repositories. It does not restructure Meal Profile Builder, Member Allocations or Current Member Plan.

## Current authorities

| Repository | Current write authority | Current ID pattern |
|---|---|---|
| Recipe | `data/recipes.csv` | CSV row-position compatibility IDs (`0`, `1`, …) |
| Exercise | `healthyme_app_state.data.exercises` | Stable numeric text IDs (`0`, `1`, …) |
| Supplement | `healthyme_app_state.data.supplement_repository` | Stable master IDs (`suprepo_*`) |

Exercise and Supplement are persisted in Supabase today, but as collections inside one shared JSON application-state row. Recipe remains page-owned CSV persistence.

## Target authority

All three repository types use `public.hm_content_repository_items`.

Identity is the composite:

```text
(repository_type, source_id)
```

This allows Recipe `0` and Exercise `0` to remain distinct without renumbering either. Display names are never identity.

### Common envelope

- `repository_type`: `recipe`, `exercise` or `supplement`
- `source_id`: existing stable/compatibility ID
- `display_name`: current visible title/name
- `status`: `active` or `inactive`
- `payload`: type-specific fields
- `content_version`: database-managed version number
- `source_system` and `legacy_reference`: migration traceability
- created/updated timestamps and actors

### Audit

`public.hm_content_repository_events` is append-only from the application perspective. Database triggers create `created`, `updated`, `deactivated` and `reactivated` events. Physical delete is not granted to the application service role.

### Access

Both tables have Row Level Security enabled. `anon` and `authenticated` receive no table privileges. The server-side Streamlit backend uses `service_role`; browser and member clients do not receive direct access.

## Delivery sequence

### Phase A — Foundation

- Create the canonical tables, constraints, indexes, RLS and audit triggers.
- Add one common Python store with fresh-read verification after every write.
- Add a dry-run-first migration planner.
- Keep all live repository pages on their current authorities.

### Phase B — Controlled cutover

1. Run dry-run inventory and capture counts/checksums.
2. Backfill all three types without changing IDs.
3. Compare source and destination identity/checksum evidence.
4. Switch one repository at a time to canonical reads and writes.
5. Test Add, Edit, Deactivate, Reactivate and refresh persistence after each switch.

Recommended switch order:

1. Exercise — already has stable numeric IDs and write verification.
2. Supplement — already has stable `suprepo_*` master IDs.
3. Recipe — requires the most careful compatibility migration from CSV row positions.

### Phase C — Legacy retirement

- Stop writes to Recipe CSV and repository collections inside `healthyme_app_state`.
- Keep compatibility reads only for the agreed observation period.
- Remove old adapters after repository, historical-plan and member-plan smoke tests pass.

## Historical-plan rule

Repository edits never rewrite existing recommendation snapshots. Existing rows in `hm_recommendation_profile_items.source_snapshot` remain the historical truth for saved plans. Deactivation only removes a repository item from future selection.

## Rollback boundary

Until each repository is accepted after cutover, its legacy authority remains readable and unchanged. Phase A makes no production-page change and performs no automatic backfill.
