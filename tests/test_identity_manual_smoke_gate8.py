from __future__ import annotations

import json
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
MIGRATION = ROOT / "supabase" / "migrations" / "20260803184500_identity_manual_smoke_gate8.sql"
HARDEN_GRANTS = ROOT / "supabase" / "migrations" / "20260803185000_identity_manual_smoke_gate8_harden_service_role_grants.sql"
CONTRACT_ONLY = ROOT / "supabase" / "migrations" / "20260803185500_identity_manual_smoke_gate8_contract_only_writes.sql"
COMPONENT = ROOT / "components" / "identity_projection_observation.py"
PAGE = ROOT / "pages" / "28_Admin_Database_Status.py"
DOC = ROOT / "docs" / "identity_manual_smoke_gate8_2026-08-03.md"
EVIDENCE = ROOT / "docs" / "evidence" / "identity_gate8_manual_smoke_baseline_2026-08-03.json"


class IdentityManualSmokeGate8Tests(unittest.TestCase):
    def test_evidence_table_is_private_and_constrained(self) -> None:
        source = MIGRATION.read_text(encoding="utf-8")
        harden = HARDEN_GRANTS.read_text(encoding="utf-8")
        contract_only = CONTRACT_ONLY.read_text(encoding="utf-8")
        self.assertIn("create table if not exists public.hm_identity_manual_smoke_evidence", source)
        self.assertIn("alter table public.hm_identity_manual_smoke_evidence enable row level security", source)
        self.assertIn("revoke all on table public.hm_identity_manual_smoke_evidence from public, anon, authenticated", source)
        self.assertIn("evidence_bundle in ('streamlit_admin', 'streamlit_member', 'flutter_member')", source)
        self.assertIn("status in ('pass', 'fail')", source)
        self.assertIn("request_id text not null unique", source)
        self.assertIn("request_payload jsonb not null", source)
        self.assertIn("revoke all on table public.hm_identity_manual_smoke_evidence from public, anon, authenticated", harden)
        self.assertIn("revoke all on table public.hm_identity_manual_smoke_evidence from service_role", contract_only)
        self.assertIn("grant select on table public.hm_identity_manual_smoke_evidence to service_role", contract_only)
        self.assertNotIn("grant insert", contract_only.lower())

    def test_record_contract_requires_every_bundle_step_for_a_pass(self) -> None:
        source = MIGRATION.read_text(encoding="utf-8")
        self.assertIn("create or replace function public.hm_admin_record_identity_smoke_evidence", source)
        self.assertIn("array['login', 'refresh_persistence', 'admin_protected_route', 'logout']", source)
        self.assertIn("array['login', 'refresh_persistence', 'member_protected_route', 'logout']", source)
        self.assertIn("array['login', 'dashboard', 'laf', 'nsp', 'submit_for_review']", source)
        self.assertIn("A passing smoke record requires every mandatory step to pass", source)
        self.assertIn("request_id has already been used with a different smoke evidence payload", source)
        self.assertIn("'idempotent_replay', true", source)
        signature = (
            "public.hm_admin_record_identity_smoke_evidence(\n"
            "  text, text, text, text, text, text, jsonb, text, text, text, text, timestamptz, jsonb\n"
            ")"
        )
        self.assertIn("from public, anon, authenticated", source.lower())
        self.assertIn(f"grant execute on function {signature}".lower(), source.lower())
        self.assertIn("to service_role", source.lower())

    def test_readiness_aggregates_all_gates_but_never_approves_retirement(self) -> None:
        source = MIGRATION.read_text(encoding="utf-8")
        self.assertIn("create or replace function public.hm_identity_projection_retirement_readiness", source)
        self.assertIn("public.hm_identity_observation_window_status", source)
        self.assertIn("public.hm_identity_fallback_closure_status", source)
        self.assertIn("smoke.passing_bundle_count = 3 as manual_smoke_ready", source)
        self.assertIn("rollback_projection_ready", source)
        self.assertIn("'ready_for_retirement_decision'", source)
        self.assertIn("'projection_retirement_approved', false", source)
        self.assertIn("streamlit_admin_smoke_missing", source)
        self.assertIn("streamlit_member_smoke_missing", source)
        self.assertIn("flutter_member_smoke_missing", source)
        self.assertIn("evidence_max_age_hours", source)
        self.assertIn("Download and retain the complete current database backup before retirement", source)

    def test_python_adapter_preserves_genuine_evidence_boundary(self) -> None:
        source = COMPONENT.read_text(encoding="utf-8")
        for required in (
            "SMOKE_RECORD_RPC = \"hm_admin_record_identity_smoke_evidence\"",
            "RETIREMENT_READINESS_RPC = \"hm_identity_projection_retirement_readiness\"",
            "SMOKE_BUNDLE_CHECKLISTS",
            "def identity_smoke_checklist_for_bundle",
            "def get_identity_projection_retirement_readiness",
            "def record_identity_smoke_evidence",
            "Every mandatory checklist step must pass before recording a passing bundle",
            "genuine_signed_in_evidence_required",
            "Projection retirement still requires a separate explicit decision and PR",
        ):
            self.assertIn(required, source)

    def test_admin_page_records_evidence_but_has_no_retirement_action(self) -> None:
        source = PAGE.read_text(encoding="utf-8")
        for required in (
            "Gate 8 retirement-decision evidence",
            "Record Signed-in Smoke Evidence",
            "I completed these checks in the selected environment using the referenced build",
            "Static tests, SQL probes and screenshots without an authenticated end-to-end run do not qualify",
            "projection_retirement_approved",
            "Retirement is never automatic",
            "Download and retain the complete database backup",
        ):
            self.assertIn(required, source)
        self.assertNotIn('st.button("Retire', source)
        self.assertNotIn('st.form_submit_button("Retire', source)
        self.assertNotIn("delete from public.healthyme_app_state", source.lower())

    def test_document_freezes_manual_and_rollback_boundaries(self) -> None:
        source = DOC.read_text(encoding="utf-8")
        for required in (
            "It does **not** retire, freeze, delete or stop updating",
            "A `pass` record is rejected unless every mandatory checklist value",
            "Default evidence age limit",
            "projection retirement approved: `false`",
            "No temporary smoke evidence persisted",
            "direct table `INSERT`: denied",
            "The page contains no projection-retirement action",
            "static tests or SQL probes as signed-in UI/device smoke",
            "Sessions, password retirement and default-Admin redesign remain separate batches",
        ):
            self.assertIn(required, source)

    def test_machine_evidence_keeps_manual_smoke_missing(self) -> None:
        evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
        self.assertTrue(evidence["automated_evidence"]["automated_ready"])
        self.assertTrue(evidence["automated_evidence"]["fallback_closure_ready"])
        self.assertTrue(evidence["automated_evidence"]["rollback_projection_ready"])
        self.assertEqual(0, evidence["manual_smoke_baseline"]["persisted_evidence_rows"])
        self.assertEqual(0, evidence["manual_smoke_baseline"]["passing_bundle_count"])
        self.assertFalse(evidence["manual_smoke_baseline"]["manual_smoke_ready"])
        self.assertFalse(evidence["current_decision"]["ready_for_retirement_decision"])
        self.assertFalse(evidence["current_decision"]["projection_retirement_approved"])
        self.assertEqual(
            {
                "flutter_member_smoke_missing",
                "streamlit_admin_smoke_missing",
                "streamlit_member_smoke_missing",
            },
            set(evidence["current_decision"]["blockers"]),
        )
        self.assertTrue(evidence["rolled_back_sequential_probe"]["ready_for_retirement_decision_inside_transaction"])
        self.assertFalse(evidence["rolled_back_sequential_probe"]["projection_retirement_approved_inside_transaction"])
        self.assertEqual(0, evidence["rolled_back_sequential_probe"]["rows_after_rollback"])
        self.assertFalse(evidence["safety_boundary"]["projection_retired"])


if __name__ == "__main__":
    unittest.main()
