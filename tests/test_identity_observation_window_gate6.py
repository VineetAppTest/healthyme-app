from __future__ import annotations

import json
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
MIGRATION = ROOT / "supabase" / "migrations" / "20260803175000_identity_observation_window_gate6.sql"
COMPONENT = ROOT / "components" / "identity_projection_observation.py"
STORAGE = ROOT / "components" / "storage_backend.py"
ROLE_MODEL = ROOT / "components" / "admin_role_model.py"
GUARDS = ROOT / "components" / "guards.py"
APP = ROOT / "app.py"
DATABASE_STATUS = ROOT / "pages" / "28_Admin_Database_Status.py"
DOC = ROOT / "docs" / "identity_observation_window_gate6_2026-08-03.md"
EVIDENCE = ROOT / "docs" / "evidence" / "identity_gate6_static_evidence_2026-08-03.json"


class IdentityObservationWindowGate6Tests(unittest.TestCase):
    def test_window_contract_is_read_only_and_service_role_only(self) -> None:
        source = MIGRATION.read_text(encoding="utf-8")
        self.assertIn("create or replace function public.hm_identity_observation_window_status", source)
        self.assertIn("language sql", source.lower())
        self.assertIn("stable", source.lower())
        self.assertIn("security definer", source.lower())
        self.assertIn("set search_path = ''", source)
        self.assertNotIn("insert into", source.lower())
        self.assertNotIn("update public.", source.lower())
        self.assertNotIn("delete from", source.lower())
        self.assertIn("from public, anon, authenticated", source.lower())
        self.assertIn("to service_role", source.lower())

    def test_window_contract_exposes_all_retirement_blockers(self) -> None:
        source = MIGRATION.read_text(encoding="utf-8")
        for required in (
            "insufficient_observation_count",
            "insufficient_observation_span",
            "active_member_auth_email_fallback_remains",
            "active_member_missing_canonical_workflow",
            "flutter_rpc_anon_execution_remains",
            "flutter_authenticated_rpc_access_missing",
            "flutter_shared_workflow_fallback_remains",
            "automated_retirement_preconditions_ready",
            "database_observation_ready",
        ):
            self.assertIn(required, source)
        self.assertIn("hm_flutter_get_laf", source)
        self.assertIn("hm_flutter_get_nsp", source)
        self.assertIn("#> array[''workflow'''", source)

    def test_component_exposes_window_status_without_claiming_manual_smoke(self) -> None:
        source = COMPONENT.read_text(encoding="utf-8")
        self.assertIn('WINDOW_STATUS_RPC = "hm_identity_observation_window_status"', source)
        self.assertIn("def get_identity_observation_window_status(", source)
        self.assertIn("minimum_observations: int = 3", source)
        self.assertIn("minimum_span_minutes: int = 60", source)
        self.assertIn("signed-in Streamlit and Flutter device smoke evidence", source)
        self.assertIn("automated_retirement_preconditions_ready", source)

    def test_streamlit_identity_and_route_authority_remain_fail_closed(self) -> None:
        storage = STORAGE.read_text(encoding="utf-8")
        role_model = ROLE_MODEL.read_text(encoding="utf-8")
        guards = GUARDS.read_text(encoding="utf-8")
        app = APP.read_text(encoding="utf-8")

        self.assertIn("def _strip_noncanonical_identity", storage)
        self.assertIn('db["users"] = []', storage)
        self.assertIn('db["workflow"] = {}', storage)
        self.assertIn("identity_fail_closed=True", storage)
        self.assertIn("The role model resolves authorization only from canonical `hm_users`", role_model)
        self.assertNotIn("from components.db import find_user_by_email", role_model)
        self.assertNotIn("Loaded user from legacy local store", role_model)
        self.assertIn('restore_any_login("admin")', guards)
        self.assertIn("current_user_is_admin()", guards)
        self.assertIn('restore_any_login("member")', guards)
        self.assertIn("current_user_is_member()", guards)
        self.assertIn("native_bridge", app)

    def test_database_status_shows_readiness_without_retirement_action(self) -> None:
        source = DATABASE_STATUS.read_text(encoding="utf-8")
        self.assertIn("get_identity_observation_window_status", source)
        self.assertIn('st.subheader("Gate 6 observation window")', source)
        self.assertIn("Automated Readiness", source)
        self.assertIn("flutter_shared_workflow_fallback_functions", source)
        self.assertIn("manual route/device evidence", source)
        self.assertNotIn("Retire Shared Projection", source)
        self.assertNotIn("Freeze Shared Projection", source)

    def test_cross_repository_manifest_is_exact_and_does_not_overclaim(self) -> None:
        evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
        self.assertEqual(
            "bf54ed509b61a3fe6526afdab705fd1365da190d",
            evidence["healthyme_app"]["revision"],
        )
        self.assertEqual(
            "a2de87cb37bea2dfecacbbb04cf03069f505077a",
            evidence["flutter_member"]["revision"],
        )
        flutter_paths = {
            item["path"]: item for item in evidence["flutter_member"]["contracts"]
        }
        self.assertEqual(
            "71aa4ece9ae020cbe355b13ad21c03185f6cb627",
            flutter_paths["lib/repositories/member_repository.dart"]["blob_sha"],
        )
        self.assertEqual(
            "b100ae6e66e1bc8f0457310e44dd9841281929e5",
            flutter_paths["lib/repositories/laf_repository.dart"]["blob_sha"],
        )
        self.assertEqual(
            "ee18476f5ef5dd93f4e9fb11bb351997460b079a",
            flutter_paths["lib/repositories/nsp_repository.dart"]["blob_sha"],
        )
        checkpoint = evidence["production_database_checkpoint"]
        self.assertEqual(3, checkpoint["observation_count"])
        self.assertEqual(3, checkpoint["healthy_observation_count"])
        self.assertEqual(0, checkpoint["repair_count"])
        self.assertEqual(28.25, checkpoint["observation_span_minutes"])
        self.assertEqual(
            ["hm_flutter_get_laf", "hm_flutter_get_nsp"],
            checkpoint["flutter_shared_workflow_fallback_functions"],
        )
        self.assertEqual(
            [
                "insufficient_observation_span",
                "active_member_auth_email_fallback_remains",
                "flutter_shared_workflow_fallback_remains",
            ],
            checkpoint["automated_blockers"],
        )
        self.assertEqual(
            {"pending"}, set(evidence["signed_in_smoke_evidence"].values())
        )
        self.assertFalse(evidence["decision"]["projection_retirement_ready"])

    def test_document_records_current_evidence_and_safety_boundary(self) -> None:
        source = DOC.read_text(encoding="utf-8")
        for required in (
            "Three genuine healthy production observations",
            "approximately `28.25` minutes",
            "active members still using controlled email fallback: `1`",
            "hm_flutter_get_laf()",
            "hm_flutter_get_nsp()",
            "The observation-count blocker has cleared",
            "insufficient_observation_span",
            "signed-in browser or Android-device smoke",
            "Projection retirement is still not approved",
            "Sessions, password retirement and default-Admin redesign remain separate batches",
        ):
            self.assertIn(required, source)


if __name__ == "__main__":
    unittest.main()
