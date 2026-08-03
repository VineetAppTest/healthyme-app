from __future__ import annotations

import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
IDENTITY_MIGRATION = ROOT / "supabase" / "migrations" / "20260803144800_harden_flutter_workflow_rpc_permissions.sql"
RPC_GRANTS_MIGRATION = ROOT / "supabase" / "migrations" / "20260803145200_restrict_flutter_member_rpc_execution.sql"
DOC = ROOT / "docs" / "flutter_workflow_rpc_permission_hardening_gate1_2026-08-03.md"


class FlutterWorkflowRpcPermissionHardeningGate1Tests(unittest.TestCase):
    def test_identity_helper_is_fail_closed_and_fixed_path(self) -> None:
        source = IDENTITY_MIGRATION.read_text(encoding="utf-8")
        self.assertIn("create or replace function public.hm_flutter_current_member_id()", source)
        self.assertIn("security definer", source)
        self.assertIn("set search_path = ''", source)
        self.assertIn("u.auth_user_id = v_auth_user_id", source)
        self.assertIn("u.auth_user_id is null", source)
        self.assertIn("and lower(u.email) = v_email", source)
        self.assertNotIn("or lower(u.email) = v_email", source)
        self.assertIn("errcode = '28000'", source)
        self.assertIn("errcode = '42501'", source)
        self.assertIn("errcode = '21000'", source)

    def test_workflow_helper_self_resolves_before_write(self) -> None:
        source = IDENTITY_MIGRATION.read_text(encoding="utf-8")
        resolver = "v_authenticated_member_id := public.hm_flutter_current_member_id();"
        guard = "p_member_id <> v_authenticated_member_id"
        write = "insert into public.hm_workflow"
        self.assertIn(resolver, source)
        self.assertIn(guard, source)
        self.assertIn("Workflow updates are limited to the current authenticated HealthyMe member.", source)
        self.assertLess(source.index(resolver), source.index(guard))
        self.assertLess(source.index(guard), source.index(write))
        self.assertIn("where user_id = v_authenticated_member_id", source)
        self.assertIn("v_authenticated_member_id,", source)

    def test_internal_helper_is_not_client_executable(self) -> None:
        source = IDENTITY_MIGRATION.read_text(encoding="utf-8")
        signature = "public.hm_flutter_upsert_nsp_workflow(text, boolean, boolean, boolean)"
        for role in ("PUBLIC", "anon", "authenticated"):
            self.assertIn(f"revoke all on function {signature} from {role};", source)
        self.assertNotIn(f"grant execute on function {signature} to authenticated;", source)

    def test_identity_helper_is_authenticated_only(self) -> None:
        source = IDENTITY_MIGRATION.read_text(encoding="utf-8")
        signature = "public.hm_flutter_current_member_id()"
        for role in ("PUBLIC", "anon", "authenticated"):
            self.assertIn(f"revoke all on function {signature} from {role};", source)
        self.assertIn(f"grant execute on function {signature} to authenticated;", source)

    def test_complete_flutter_identity_and_nsp_surface_is_restricted(self) -> None:
        source = RPC_GRANTS_MIGRATION.read_text(encoding="utf-8")
        signatures = (
            "public.hm_flutter_link_current_member_auth_user()",
            "public.hm_flutter_get_nsp()",
            "public.hm_flutter_save_nsp1_draft(jsonb)",
            "public.hm_flutter_submit_nsp1(jsonb)",
            "public.hm_flutter_save_nsp2_draft(jsonb)",
            "public.hm_flutter_submit_nsp2(jsonb)",
            "public.hm_flutter_submit_assessment_review()",
        )
        for signature in signatures:
            with self.subTest(signature=signature):
                for role in ("PUBLIC", "anon", "authenticated"):
                    self.assertIn(f"revoke all on function {signature} from {role};", source)
                self.assertIn(f"grant execute on function {signature} to authenticated;", source)

    def test_gate_does_not_change_shared_state_or_flutter_payloads(self) -> None:
        combined = "\n".join(
            path.read_text(encoding="utf-8")
            for path in (IDENTITY_MIGRATION, RPC_GRANTS_MIGRATION)
        )
        for forbidden in (
            "update public.healthyme_app_state",
            "delete from public.healthyme_app_state",
            "delete from public.hm_users",
            "delete from public.hm_workflow",
            "drop function public.hm_flutter_get_nsp",
            "drop function public.hm_flutter_submit_nsp1",
            "drop function public.hm_flutter_submit_nsp2",
        ):
            self.assertNotIn(forbidden, combined.lower())

    def test_document_records_production_and_next_gate(self) -> None:
        source = DOC.read_text(encoding="utf-8")
        for required in (
            "20260803092801_harden_flutter_workflow_rpc_permissions",
            "20260803093059_restrict_flutter_member_rpc_execution",
            "anon execute: false for all nine Gate 1 functions",
            "production row counts remain 15 Users and 15 Workflow rows",
            "a different member ID is rejected before mutation",
            "Gate 2 may create the canonical contract foundation",
            "This gate does not",
        ):
            self.assertIn(required, source)


if __name__ == "__main__":
    unittest.main()
