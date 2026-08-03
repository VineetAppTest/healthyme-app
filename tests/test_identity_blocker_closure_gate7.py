from __future__ import annotations

import json
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
MIGRATION = ROOT / "supabase" / "migrations" / "20260803183000_identity_blocker_closure_gate7.sql"
COMPONENT = ROOT / "components" / "identity_projection_observation.py"
DATABASE_STATUS = ROOT / "pages" / "28_Admin_Database_Status.py"
DOC = ROOT / "docs" / "identity_blocker_closure_gate7_2026-08-03.md"
EVIDENCE = ROOT / "docs" / "evidence" / "identity_gate7_fallback_closure_evidence_2026-08-03.json"


def _section(source: str, start: str, end: str) -> str:
    start_index = source.index(start)
    end_index = source.index(end, start_index)
    return source[start_index:end_index]


class IdentityBlockerClosureGate7Tests(unittest.TestCase):
    def test_auth_link_uses_existing_atomic_contract_and_no_raw_user_update(self) -> None:
        source = MIGRATION.read_text(encoding="utf-8")
        self.assertIn("exact unique Auth email match", source)
        self.assertIn("public.hm_admin_commit_identity_and_state(", source)
        self.assertIn("'identity-gate7-auth-link'", source)
        self.assertIn("'auth_provider', 'supabase'", source)
        self.assertIn("'auth_user_id', v_auth_user_id::text", source)
        self.assertIn("'auth_migrated_at', v_migrated_at::text", source)
        self.assertNotIn("update public.hm_users", source.lower())
        self.assertNotIn("insert into public.hm_users", source.lower())

    def test_current_member_resolution_is_auth_user_id_only(self) -> None:
        source = MIGRATION.read_text(encoding="utf-8")
        section = _section(
            source,
            "create or replace function public.hm_flutter_current_member_id()",
            "create or replace function public.hm_flutter_get_laf()",
        ).lower()
        self.assertIn("v_auth_user_id uuid := auth.uid()", section)
        self.assertIn("u.auth_user_id = v_auth_user_id", section)
        self.assertIn("linked by auth user id", section)
        self.assertNotIn("auth.jwt", section)
        self.assertNotIn("email", section)

    def test_laf_keeps_responses_but_requires_canonical_workflow(self) -> None:
        source = MIGRATION.read_text(encoding="utf-8")
        section = _section(
            source,
            "create or replace function public.hm_flutter_get_laf()",
            "create or replace function public.hm_flutter_get_nsp()",
        ).lower()
        self.assertIn("array['laf_responses', v_user_id]", section)
        self.assertIn("from public.hm_workflow", section)
        self.assertIn("canonical workflow is missing", section)
        self.assertNotIn("array['workflow'", section)

    def test_nsp_keeps_response_payloads_but_requires_canonical_workflow(self) -> None:
        source = MIGRATION.read_text(encoding="utf-8")
        section = _section(
            source,
            "create or replace function public.hm_flutter_get_nsp()",
            "revoke execute on function public.hm_flutter_current_member_id()",
        ).lower()
        self.assertIn("array['nsp1_responses', v_member_id]", section)
        self.assertIn("array['nsp2_responses', v_member_id]", section)
        self.assertIn("from public.hm_workflow", section)
        self.assertIn("canonical workflow is missing", section)
        self.assertNotIn("v_state_workflow", section)
        self.assertNotIn("array['workflow'", section)

    def test_identity_rls_is_consolidated_to_auth_id_and_direct_writes_are_retired(self) -> None:
        source = MIGRATION.read_text(encoding="utf-8")
        for removed in (
            "flutter_member_read_own_hm_users",
            "hm_users_member_select_self",
            "hm_users_member_select_self_auth_id_or_email",
            "flutter_member_read_own_hm_workflow",
            "hm_workflow_member_select_self",
            "hm_workflow_member_select_self_auth_id_or_email",
            "flutter_member_insert_own_hm_workflow",
            "flutter_member_update_own_hm_workflow",
        ):
            self.assertIn(f"drop policy if exists {removed}", source.lower())
        self.assertIn("create policy hm_users_member_select_self_auth_user_id", source)
        self.assertIn("create policy hm_workflow_member_select_self_auth_user_id", source)
        self.assertGreaterEqual(source.count("(select auth.uid())"), 2)
        self.assertIn(
            "revoke all on table public.hm_users, public.hm_workflow from anon",
            source.lower(),
        )
        self.assertIn(
            "revoke insert, update, delete, truncate, references, trigger",
            source.lower(),
        )
        self.assertIn(
            "grant select on table public.hm_users, public.hm_workflow to authenticated",
            source.lower(),
        )

    def test_closure_contract_is_read_only_service_role_only_and_complete(self) -> None:
        source = MIGRATION.read_text(encoding="utf-8")
        section = source[source.index("create or replace function public.hm_identity_fallback_closure_status()") :]
        self.assertIn("language sql", section.lower())
        self.assertIn("stable", section.lower())
        self.assertIn("security definer", section.lower())
        self.assertIn("set search_path = ''", section)
        for field in (
            "active_members_missing_auth_user_id",
            "active_members_missing_workflow",
            "current_member_id_uses_email_fallback",
            "flutter_shared_workflow_fallback_functions",
            "email_fallback_policies",
            "direct_workflow_write_policies",
            "anon_privilege_count",
            "authenticated_nonselect_privilege_count",
            "blockers",
        ):
            self.assertIn(field, section)
        self.assertIn("from public, anon, authenticated", section.lower())
        self.assertIn("to service_role", section.lower())
        self.assertNotIn("update public.", section.lower())
        self.assertNotIn("delete from", section.lower())

    def test_migration_records_healthy_observation_without_repair(self) -> None:
        source = MIGRATION.read_text(encoding="utf-8")
        self.assertIn("'identity-gate7-post-closure-observation'", source)
        self.assertIn("'identity_gate7_post_closure'", source)
        call = source[source.index("select public.hm_admin_observe_identity_projection(") :]
        self.assertIn("false", call.lower())

    def test_component_and_admin_page_expose_gate7_status(self) -> None:
        component = COMPONENT.read_text(encoding="utf-8")
        page = DATABASE_STATUS.read_text(encoding="utf-8")
        self.assertIn('CLOSURE_STATUS_RPC = "hm_identity_fallback_closure_status"', component)
        self.assertIn("def get_identity_fallback_closure_status(", component)
        self.assertIn("Identity fallback closure is complete", component)
        self.assertIn("get_identity_fallback_closure_status", page)
        self.assertIn('st.subheader("Gate 7 identity fallback closure")', page)
        self.assertIn("Auth-ID Linked", page)
        self.assertIn("Direct Writes", page)
        self.assertIn("Signed-in Streamlit route checks and Flutter device smoke", page)
        self.assertNotIn("Retire Shared Projection", page)

    def test_evidence_records_completed_database_window_without_manual_smoke_claim(self) -> None:
        evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
        closure = evidence["production_closure"]
        window = evidence["observation_window_checkpoint"]
        self.assertTrue(closure["closed"])
        self.assertEqual(7, closure["active_member_count"])
        self.assertEqual(0, closure["active_members_missing_auth_user_id"])
        self.assertEqual(0, closure["active_members_missing_workflow"])
        self.assertFalse(closure["current_member_id_uses_email_fallback"])
        self.assertEqual([], closure["flutter_shared_workflow_fallback_functions"])
        self.assertEqual([], closure["email_fallback_policies"])
        self.assertEqual([], closure["direct_workflow_write_policies"])
        self.assertEqual(5, window["observation_count"])
        self.assertEqual(5, window["healthy_observation_count"])
        self.assertEqual(0, window["repair_count"])
        self.assertGreaterEqual(window["span_minutes"], 60)
        self.assertTrue(window["database_observation_ready"])
        self.assertTrue(window["automated_retirement_preconditions_ready"])
        self.assertEqual([], window["remaining_automated_blockers"])
        self.assertEqual(
            {"pending"}, set(evidence["signed_in_smoke_evidence"].values())
        )
        self.assertFalse(evidence["decision"]["projection_retirement_approved"])

    def test_document_records_completion_and_safety_boundary(self) -> None:
        source = DOC.read_text(encoding="utf-8")
        for required in (
            "active members with `auth_user_id`: `7`",
            "active members using email fallback: `0`",
            "closure: `true`",
            "observations: `5`",
            "span: approximately `63.19` minutes",
            "database observation ready: `true`",
            "automated retirement preconditions ready: `true`",
            "Automated readiness remains evidence only",
            "Still pending and not represented by static or SQL verification",
            "does **not** retire the shared Users or Workflow projection",
            "Sessions, password retirement and default-Admin redesign remain separate batches",
        ):
            self.assertIn(required, source)


if __name__ == "__main__":
    unittest.main()
