from __future__ import annotations

import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
STATUS = ROOT / "supabase" / "migrations" / "20260803152500_users_workflow_gate2_status_contract.sql"
AUDIT = ROOT / "supabase" / "migrations" / "20260803152600_users_workflow_gate2_audit_tables.sql"
USER = ROOT / "supabase" / "migrations" / "20260803152700_users_workflow_gate2_user_contract.sql"
WORKFLOW = ROOT / "supabase" / "migrations" / "20260803152800_users_workflow_gate2_workflow_contract.sql"
DOC = ROOT / "docs" / "users_workflow_gate2_contract_foundation_2026-08-03.md"


class UsersWorkflowGate2ContractFoundationTests(unittest.TestCase):
    def test_canonical_status_function_and_triggers(self) -> None:
        source = STATUS.read_text(encoding="utf-8")
        self.assertIn("create or replace function public.hm_derive_workflow_status", source)
        self.assertIn("when coalesce(p_final_report_ready, false) then 'finalized'", source)
        self.assertIn("when coalesce(p_admin_completed, false) then 'admin_completed'", source)
        self.assertIn("when coalesce(p_submitted_for_review, false) then 'submitted'", source)
        self.assertIn("then 'in_progress'", source)
        self.assertIn("else 'not_started'", source)
        self.assertIn("hm_workflow_canonical_status_insert", source)
        self.assertIn("hm_workflow_canonical_status_update", source)
        self.assertIn("before update of laf_completed", source)
        self.assertIn("workflow_status", source)

    def test_flutter_internal_helpers_delegate_to_canonical_status(self) -> None:
        source = STATUS.read_text(encoding="utf-8")
        for helper in (
            "public.hm_flutter_nsp_workflow_status",
            "public.hm_flutter_workflow_status",
            "public.hm_flutter_update_state_workflow",
        ):
            self.assertIn(helper, source)
        self.assertGreaterEqual(source.count("public.hm_derive_workflow_status("), 4)
        self.assertIn("set search_path = ''", source)
        self.assertNotIn("update public.healthyme_app_state", source.lower())

    def test_internal_status_surface_is_not_client_executable(self) -> None:
        source = STATUS.read_text(encoding="utf-8")
        signatures = (
            "public.hm_derive_workflow_status(boolean, boolean, boolean, boolean, boolean, boolean)",
            "public.hm_flutter_nsp_workflow_status(boolean, boolean, boolean, boolean, boolean, boolean)",
            "public.hm_flutter_workflow_status(jsonb)",
            "public.hm_flutter_update_state_workflow(jsonb, text, boolean, boolean, boolean)",
            "public.hm_workflow_apply_canonical_status()",
        )
        for signature in signatures:
            with self.subTest(signature=signature):
                self.assertIn(f"revoke all on function {signature}", source)
                self.assertIn("from public, anon, authenticated;", source)
                self.assertIn(f"grant execute on function {signature}", source)

    def test_audit_tables_are_forced_rls_and_append_only(self) -> None:
        source = AUDIT.read_text(encoding="utf-8")
        for table in (
            "public.hm_domain_write_requests",
            "public.hm_user_events",
            "public.hm_workflow_events",
        ):
            with self.subTest(table=table):
                self.assertIn(f"create table if not exists {table}", source)
                self.assertIn(f"alter table {table} enable row level security;", source)
                self.assertIn(f"alter table {table} force row level security;", source)
                self.assertIn(f"revoke all on table {table} from public, anon, authenticated;", source)
                self.assertIn(f"grant select on table {table} to service_role;", source)
        self.assertIn("create or replace function public.hm_reject_append_only_mutation()", source)
        self.assertEqual(source.count("before update or delete"), 3)
        self.assertNotIn("insert into public.hm_user_events", source.lower())
        self.assertNotIn("insert into public.hm_workflow_events", source.lower())

    def test_user_contract_is_transactional_idempotent_and_redacted(self) -> None:
        source = USER.read_text(encoding="utf-8")
        self.assertIn("create or replace function public.hm_admin_upsert_user", source)
        self.assertIn("security definer", source)
        self.assertIn("set search_path = ''", source)
        self.assertIn("pg_catalog.pg_advisory_xact_lock", source)
        self.assertIn("from public.hm_domain_write_requests", source)
        self.assertIn("idempotent_replay", source)
        self.assertIn("row(", source)
        self.assertIn("is distinct from row(", source)
        self.assertIn("v_saved := v_existing", source)
        self.assertIn("v_after_full - 'password_hash'", source)
        self.assertIn("v_before_full - 'password_hash'", source)
        self.assertIn("insert into public.hm_user_events", source)
        self.assertIn("insert into public.hm_domain_write_requests", source)
        signature = "public.hm_admin_upsert_user(text, text, jsonb, text, text, text, jsonb)"
        self.assertIn(f"revoke all on function {signature}", source)
        self.assertIn(f"grant execute on function {signature}", source)
        self.assertIn("to service_role;", source)

    def test_workflow_contract_cannot_accept_caller_status(self) -> None:
        source = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("create or replace function public.hm_admin_upsert_workflow", source)
        self.assertIn("security definer", source)
        self.assertIn("set search_path = ''", source)
        self.assertIn("pg_catalog.pg_advisory_xact_lock", source)
        self.assertIn("Workflow User does not exist", source)
        allowed_section = source[source.index("where key not in (") : source.index(");", source.index("where key not in ("))]
        self.assertNotIn("workflow_status", allowed_section)
        self.assertIn("insert into public.hm_workflow_events", source)
        self.assertIn("insert into public.hm_domain_write_requests", source)
        self.assertIn("v_saved := v_existing", source)
        self.assertNotIn("set workflow_status", source.lower())
        signature = "public.hm_admin_upsert_workflow(text, text, jsonb, text, text, text, jsonb)"
        self.assertIn(f"revoke all on function {signature}", source)
        self.assertIn(f"grant execute on function {signature}", source)
        self.assertIn("to service_role;", source)

    def test_foundation_does_not_cut_application_writers_over(self) -> None:
        combined = "\n".join(
            path.read_text(encoding="utf-8")
            for path in (STATUS, AUDIT, USER, WORKFLOW)
        ).lower()
        for forbidden in (
            "update public.healthyme_app_state",
            "delete from public.healthyme_app_state",
            "delete from public.hm_users",
            "delete from public.hm_workflow",
            "truncate public.hm_users",
            "truncate public.hm_workflow",
        ):
            self.assertNotIn(forbidden, combined)

    def test_document_records_deployment_verification_and_next_gate(self) -> None:
        source = DOC.read_text(encoding="utf-8")
        for required in (
            "20260803095743_users_workflow_gate2_status_contract",
            "20260803095808_users_workflow_gate2_audit_tables",
            "20260803100039_users_workflow_gate2_user_contract",
            "20260803100249_users_workflow_gate2_workflow_contract",
            "Workflow status mismatches: `0`",
            "persisted User events after tests: `0`",
            "User no-op: no event and unchanged `updated_at`",
            "Workflow no-op: no event and unchanged `updated_at`",
            "Gate 2 does not",
            "Gate 3 can cut over **User writes only**",
        ):
            self.assertIn(required, source)


if __name__ == "__main__":
    unittest.main()
