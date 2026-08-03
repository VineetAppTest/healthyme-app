from __future__ import annotations

import ast
import pathlib
import unittest
from typing import Any, Dict, Optional


ROOT = pathlib.Path(__file__).resolve().parents[1]
MIGRATION = ROOT / "supabase" / "migrations" / "20260803172500_identity_projection_observation_gate5a6a.sql"
STORAGE = ROOT / "components" / "storage_backend.py"
ROLE_MODEL = ROOT / "components" / "admin_role_model.py"
OBSERVATION = ROOT / "components" / "identity_projection_observation.py"
STATUS_PAGE = ROOT / "pages" / "28_Admin_Database_Status.py"
DOC = ROOT / "docs" / "identity_read_observation_gate5a6a_2026-08-03.md"


def _isolated_function(path: pathlib.Path, function_name: str):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    node = next(
        item for item in tree.body
        if isinstance(item, ast.FunctionDef) and item.name == function_name
    )
    module = ast.Module(body=[node], type_ignores=[])
    ast.fix_missing_locations(module)
    namespace = {"Any": Any, "Dict": Dict, "Optional": Optional}
    exec(compile(module, str(path), "exec"), namespace)
    return namespace[function_name]


class IdentityReadObservationGateTests(unittest.TestCase):
    def test_snapshot_and_observation_contracts_are_service_role_only(self) -> None:
        source = MIGRATION.read_text(encoding="utf-8")
        self.assertIn("create or replace function public.hm_identity_projection_snapshot()", source)
        self.assertIn("create or replace function public.hm_admin_observe_identity_projection(", source)
        self.assertIn("security definer", source.lower())
        self.assertIn("set search_path = ''", source)
        self.assertIn("from public, anon, authenticated", source.lower())
        self.assertIn("to service_role", source.lower())
        self.assertIn("alter table public.hm_identity_projection_observations enable row level security", source.lower())

    def test_observation_defaults_to_dry_run_and_repair_is_explicit(self) -> None:
        source = MIGRATION.read_text(encoding="utf-8")
        self.assertIn("p_apply_repair boolean default false", source)
        self.assertIn("if p_apply_repair and not", source.lower())
        self.assertIn("repair_applied", source)
        self.assertIn("idempotent_replay", source)
        self.assertIn("pg_advisory_xact_lock", source)

    def test_repair_updates_only_shared_projection(self) -> None:
        source = MIGRATION.read_text(encoding="utf-8").lower()
        self.assertIn("update public.healthyme_app_state", source)
        self.assertNotIn("update public.hm_users", source)
        self.assertNotIn("update public.hm_workflow", source)
        self.assertIn("coalesce(s.row_data, '{}'::jsonb)", source)
        self.assertIn("coalesce(v_state #> array['workflow', c.user_id], '{}'::jsonb)", source)

    def test_snapshot_detects_missing_orphan_duplicate_and_field_drift(self) -> None:
        source = MIGRATION.read_text(encoding="utf-8")
        for required in (
            "missing_shared_user_ids",
            "orphan_shared_user_ids",
            "duplicate_shared_user_ids",
            "user_mismatches",
            "missing_shared_workflow_ids",
            "orphan_shared_workflow_ids",
            "workflow_mismatches",
            "'healthy'",
        ):
            self.assertIn(required, source)

    def test_storage_strips_local_identity_and_records_fail_closed_status(self) -> None:
        source = STORAGE.read_text(encoding="utf-8")
        self.assertIn("def _strip_noncanonical_identity", source)
        self.assertIn('db["users"] = []', source)
        self.assertIn('db["workflow"] = {}', source)
        self.assertIn("identity_authority_available=False", source)
        self.assertIn("identity_fail_closed=True", source)
        self.assertIn("local Users and Workflow were removed fail-closed", source)

        strip_identity = _isolated_function(STORAGE, "_strip_noncanonical_identity")
        state = {
            "users": [{"id": "legacy"}],
            "workflow": {"legacy": {"laf_completed": True}},
            "profiles": {"legacy": {"full_name": "Preserved non-identity data"}},
        }
        result = strip_identity(state)
        self.assertEqual([], result["users"])
        self.assertEqual({}, result["workflow"])
        self.assertIn("legacy", result["profiles"])

    def test_role_resolution_has_no_shared_or_local_user_fallback(self) -> None:
        source = ROLE_MODEL.read_text(encoding="utf-8")
        self.assertNotIn("from components.db import find_user_by_email", source)
        self.assertNotIn("Loaded user from legacy local store", source)
        self.assertNotIn("local_user =", source)
        self.assertIn("Failure never falls back to shared JSON or local files", source)
        self.assertIn("Loaded user from canonical hm_users", source)

    def test_observation_adapter_requires_service_role_and_explicit_repair_flag(self) -> None:
        source = OBSERVATION.read_text(encoding="utf-8")
        self.assertIn("SUPABASE_SERVICE_ROLE_KEY", source)
        self.assertIn("def get_identity_projection_snapshot", source)
        self.assertIn("def observe_identity_projection", source)
        self.assertIn("apply_repair: bool = False", source)
        self.assertIn('"p_apply_repair": bool(apply_repair)', source)
        self.assertIn("canonical Users and Workflow", source)

    def test_database_status_replaces_bulk_migration_with_observe_and_repair(self) -> None:
        source = STATUS_PAGE.read_text(encoding="utf-8")
        self.assertIn("Record Projection Observation", source)
        self.assertIn("Repair Shared Projection from Canonical", source)
        self.assertIn("Confirm canonical projection repair", source)
        self.assertNotIn("Migrate Users + Workflow to Normalized Tables", source)
        self.assertNotIn("sync_users_workflow_to_normalized", source)

    def test_document_records_baseline_and_exclusions(self) -> None:
        source = DOC.read_text(encoding="utf-8")
        for required in (
            "canonical Users: `15`",
            "shared Users: `15`",
            "canonical Workflow rows: `15`",
            "shared Workflow rows: `15`",
            "snapshot health: `true`",
            "No automatic repair runs during application load or save",
            "does not retire the compatibility projection",
            "Sessions, password retirement and default-Admin redesign remain separate workstreams",
        ):
            self.assertIn(required, source)


if __name__ == "__main__":
    unittest.main()
