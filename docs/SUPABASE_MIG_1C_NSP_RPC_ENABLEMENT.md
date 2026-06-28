# SUPABASE-MIG-1C — Flutter NSP RPC Enablement

## Status

Backend enablement completed in Supabase for NSP Page 1 and NSP Page 2 persistence.

## Purpose

Prepare the Supabase backend for Flutter NSP persistence so a later Flutter sprint can move NSP Page 1 and NSP Page 2 from session-only local state to Supabase-backed draft save, reload, and submit.

## RPCs installed

- `hm_flutter_get_nsp`
- `hm_flutter_save_nsp1_draft`
- `hm_flutter_save_nsp2_draft`
- `hm_flutter_submit_nsp1`
- `hm_flutter_submit_nsp2`

## Storage approach

NSP data is stored in `healthyme_app_state` with member-scoped keys:

- `flutter_nsp1_draft:<member user id>`
- `flutter_nsp2_draft:<member user id>`

Each record stores a JSON payload containing:

- responses
- status
- source
- updated timestamp
- submitted timestamp when submitted

## Workflow behavior

- NSP Page 1 submit sets `hm_workflow.nsp1_completed = true`.
- NSP Page 2 submit sets `hm_workflow.nsp2_completed = true`.
- Draft saves update workflow status without marking completion.

## RLS policies added

- `flutter_member_read_own_nsp_state`
- `flutter_member_insert_own_nsp_state`
- `flutter_member_update_own_nsp_state`

These policies restrict access to the authenticated active member's own NSP state records only.

## Non-scope

- No Streamlit change.
- No Auth0 change.
- No admin/report change.
- No final report generation change.
- No Flutter code change in this backend sprint.
- No Submit for Review persistence yet.

## Validation completed

- Confirmed five NSP RPC functions exist.
- Confirmed three NSP RLS policies exist.

## Next sprint

`FLUTTER-NSP-PERSIST-1` should wire NSP Page 1 and NSP Page 2 screens to these RPCs.
