# SUPABASE-MIG-1A — Flutter LAF Supabase Migration

Purpose: move Flutter Member LAF from session-only draft behavior toward Supabase-backed load, save draft, and submit.

Current Flutter app already calls three LAF RPC names:
- hm_flutter_get_laf
- hm_flutter_save_laf_draft
- hm_flutter_submit_laf

Current Supabase finding:
- Relevant tables found: hm_users, hm_workflow, healthyme_app_state.
- No hm_flutter RPC functions are currently installed.

Target behavior:
1. Supabase Auth confirms the user identity.
2. HealthyMe hm_users confirms the signed-in email is an active member.
3. LAF draft responses are saved for that member.
4. LAF submit marks the member workflow LAF step as completed.
5. Streamlit admin, Auth0, reporting, and final report generation remain unchanged.

Recommended storage approach:
- Store Flutter LAF draft data in healthyme_app_state.
- Use a member-scoped key format: flutter_laf_draft:<member user id>.
- Store responses, status, source, and updated timestamp in the data JSON.

Non-scope:
- No Streamlit auth migration.
- No Auth0 removal.
- No Practitioner Lite.
- No report generation change.
- No NSP persistence in this sprint.
- No admin-page change.

Validation checklist:
- Login as approved member in Flutter.
- Open LAF.
- Save Draft.
- Close and reopen app.
- Reopen LAF and confirm values reload.
- Submit LAF.
- Confirm NSP Page 1 unlock remains correct.
- Confirm hm_workflow marks LAF completed for that member.
