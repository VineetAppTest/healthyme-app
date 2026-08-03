# Exercise Repository canonical cutover gate — 2026-08-03

## Status

**Jarvis gate: PASS**

PR #351 is ready for review as the Exercise Repository read/write cutover under issue #347.

The application cutover is not live until PR #351 is merged. The supporting server-side numeric-ID RPC has been applied safely in advance.

## Supabase migration

- Version: `20260803052220`
- Name: `create_numeric_content_repository_item_rpc`
- Function: `public.hm_create_numeric_content_repository_item(text,text,jsonb,text,text,text)`

Effective execution permissions:

- `service_role`: allowed
- `anon`: denied
- `authenticated`: denied

The function uses a PostgreSQL advisory transaction lock per repository type and allocates the next numeric `source_id` atomically.

## Installed RPC rehearsal

A rollback-only production transaction created a temporary Exercise through the installed RPC and verified:

- allocated source ID: `3`
- content version: `1`
- created audit events: `1`
- audit actor: `system:jarvis_installed_rpc_test`
- legacy Exercise app-state count during test: `3`

The transaction was rolled back.

Post-rollback production state:

- canonical items: `10`
- canonical events: `10`
- canonical Exercise items: `3`
- canonical Exercise source IDs: `0,1,2`
- legacy Exercise app-state rows: `3`

No test record or test audit event remains.

## Application authority after merge

`components/exercise_repository.py` will use the standard Content Repository exclusively:

- reads: `list_repository_items("exercise")`
- creates: `create_numeric_repository_item(...)`
- updates: `save_repository_item(...)`
- deactivate/reactivate: `set_repository_item_status(...)`

It will no longer read or write `healthyme_app_state.data.exercises`.

The old app-state data remains unchanged as rollback evidence, but it is not a live Exercise Repository authority after merge.

## Compatibility checks

The public Exercise Repository API and legacy flattened row shape remain compatible with:

- Admin Exercise Repository page
- Member Exercise Repository CSV compatibility shim
- Recommendation/Profile Builder source reads
- Exercise Journal and related runtime bootstrap

Delete remains a safe inactive-status transition. Existing IDs and `legacy_reference` values are preserved.

## Regression validation

All exact-code-head checks passed:

- Content repository standardization validation
- Repository layout correction validation
- Exercise Journal and Repository Fix Validation
- Profile Builder repository contract validation
- Form reset closure audit v2

The initial failures were limited to retired app-state test fixtures and one literal `None` normalization assertion. Tests were migrated to the canonical store; no production fallback was added.
