from __future__ import annotations

import ast
import json
import pathlib
import unittest
from typing import Any, Dict, List, Optional, Tuple


ROOT = pathlib.Path(__file__).resolve().parents[1]
MIGRATION = ROOT / "supabase" / "migrations" / "20260803165000_workflow_gate4_identity_state_commit.sql"
NORMALIZED = ROOT / "components" / "normalized_store.py"
STORAGE = ROOT / "components" / "storage_backend.py"
DOC = ROOT / "docs" / "workflow_gate4_write_cutover_2026-08-03.md"


def _isolated_functions(path: pathlib.Path, names: tuple[str, ...]):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    nodes = [
        item
        for item in tree.body
        if isinstance(item, (ast.FunctionDef, ast.Assign, ast.AnnAssign))
        and (
            not isinstance(item, ast.FunctionDef)
            or item.name in names
        )
    ]
    selected = []
    for item in nodes:
        if isinstance(item, ast.FunctionDef):
            selected.append(item)
            continue
        targets = []
        if isinstance(item, ast.Assign):
            targets = [target.id for target in item.targets if isinstance(target, ast.Name)]
        elif isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
            targets = [item.target.id]
        if any(target in {"WORKFLOW_CANONICAL_FIELDS"} for target in targets):
            selected.append(item)
    module = ast.Module(body=selected, type_ignores=[])
    ast.fix_missing_locations(module)
    namespace = {
        "Any": Any,
        "Dict": Dict,
        "List": List,
        "Optional": Optional,
        "Tuple": Tuple,
        "json": json,
    }
    exec(compile(module, str(path), "exec"), namespace)
    return namespace


class WorkflowGate4WriteCutoverTests(unittest.TestCase):
    def test_database_contract_is_atomic_idempotent_and_service_role_only(self) -> None:
        source = MIGRATION.read_text(encoding="utf-8")
        self.assertIn("create or replace function public.hm_admin_commit_identity_and_state", source)
        self.assertIn("security definer", source.lower())
        self.assertIn("set search_path = ''", source)
        self.assertIn("pg_advisory_xact_lock", source)
        self.assertIn("public.hm_admin_upsert_user(", source)
        self.assertIn("public.hm_admin_upsert_workflow(", source)
        self.assertLess(
            source.index("public.hm_admin_upsert_user("),
            source.index("public.hm_admin_upsert_workflow("),
        )
        self.assertIn("insert into public.healthyme_app_state", source)
        self.assertIn("'identity_state_commit'", source)
        signature = (
            "public.hm_admin_commit_identity_and_state(\n"
            "  text, text, jsonb, jsonb, jsonb, text, text, text, jsonb\n"
            ")"
        )
        self.assertIn("from public, anon, authenticated;", source.lower())
        self.assertIn(f"grant execute on function {signature}".lower(), source.lower())
        self.assertIn("to service_role", source.lower())

    def test_direct_service_role_workflow_writes_are_audited(self) -> None:
        source = MIGRATION.read_text(encoding="utf-8")
        self.assertIn("create or replace function public.hm_capture_direct_workflow_event()", source)
        self.assertIn("if current_user <> 'service_role'", source)
        self.assertIn("'service_role_direct'", source)
        self.assertIn("create trigger hm_workflow_capture_direct_event", source)
        self.assertIn("after insert or update on public.hm_workflow", source.lower())

    def test_workflow_patch_uses_only_canonical_lifecycle_fields(self) -> None:
        namespace = _isolated_functions(
            NORMALIZED,
            ("_workflow_base", "_canonical_workflow_patch"),
        )
        patch = namespace["_canonical_workflow_patch"](
            {
                "laf_completed": True,
                "nsp1_completed": True,
                "nsp2_completed": False,
                "submitted_for_review": False,
                "admin_completed": False,
                "final_report_ready": False,
                "workflow_status": "incorrect-client-value",
                "body_mind_activation_requested": True,
                "body_mind_unlocked": True,
            }
        )
        self.assertEqual(
            {
                "laf_completed",
                "nsp1_completed",
                "nsp2_completed",
                "submitted_for_review",
                "admin_completed",
                "final_report_ready",
            },
            set(patch),
        )
        self.assertNotIn("workflow_status", patch)
        self.assertNotIn("body_mind_activation_requested", patch)
        self.assertNotIn("body_mind_unlocked", patch)

    def test_projection_helper_keeps_one_workflow_per_user_and_shared_fields(self) -> None:
        namespace = _isolated_functions(
            NORMALIZED,
            ("_workflow_base", "ensure_workflow_projection"),
        )
        db = {
            "users": [{"id": "member1"}, {"id": "admin1"}],
            "workflow": {
                "member1": {
                    "laf_completed": True,
                    "body_mind_unlocked": True,
                    "workflow_status": "stale",
                }
            },
        }
        result = namespace["ensure_workflow_projection"](db)
        self.assertEqual({"member1", "admin1"}, set(result["workflow"]))
        self.assertTrue(result["workflow"]["member1"]["body_mind_unlocked"])
        self.assertEqual("in_progress", result["workflow"]["member1"]["workflow_status"])
        self.assertEqual("not_started", result["workflow"]["admin1"]["workflow_status"])

    def test_normalized_store_uses_combined_contract_without_direct_workflow_upsert(self) -> None:
        source = NORMALIZED.read_text(encoding="utf-8")
        self.assertIn("def commit_identity_and_state(", source)
        self.assertIn('client.rpc("hm_admin_commit_identity_and_state"', source)
        self.assertIn("def _changed_workflow_entries(", source)
        self.assertIn("def _canonical_workflow_patch(", source)
        self.assertIn("def sync_workflow_to_normalized(", source)
        self.assertIn("workflow_compatibility_sync", source)
        self.assertNotIn('.table("hm_workflow").upsert(', source)

    def test_storage_selects_fail_closed_combined_identity_path(self) -> None:
        source = STORAGE.read_text(encoding="utf-8")
        self.assertIn("commit_identity_and_state", source)
        self.assertIn("ensure_workflow_projection", source)
        self.assertIn("users_changed = _users_projection_changed(previous, db)", source)
        self.assertIn("workflow_changed = _workflow_projection_changed(previous, db)", source)
        self.assertIn("identity_changed = users_changed or workflow_changed", source)
        self.assertIn("if identity_changed and not configured:", source)
        self.assertIn("local User/Workflow fallback is disabled", source)
        self.assertIn("force_state_commit=True", source)
        self.assertIn("raise RuntimeError(identity_commit_message)", source)
        self.assertNotIn("sync_workflow_to_normalized", source)

    def test_workflow_change_detection_covers_shared_only_side_effect_fields(self) -> None:
        namespace = _isolated_functions(STORAGE, ("_workflow_projection_changed",))
        changed = namespace["_workflow_projection_changed"]
        before = {
            "workflow": {
                "u1": {
                    "laf_completed": True,
                    "body_mind_unlocked": False,
                }
            }
        }
        after = {
            "workflow": {
                "u1": {
                    "laf_completed": True,
                    "body_mind_unlocked": True,
                }
            }
        }
        self.assertTrue(changed(before, after))
        self.assertFalse(changed(after, after))

    def test_local_push_preserves_both_canonical_identity_projections(self) -> None:
        source = STORAGE.read_text(encoding="utf-8")
        self.assertIn("canonical identity data could not be loaded", source)
        self.assertIn('local_state["users"] = canonical_users', source)
        self.assertIn('local_state["workflow"] = canonical_workflow', source)
        self.assertIn("canonical Users and Workflow were preserved", source)

    def test_document_records_production_evidence_and_exclusions(self) -> None:
        source = DOC.read_text(encoding="utf-8")
        for required in (
            "canonical Workflow rows: `15`",
            "shared Workflow rows: `15`",
            "Workflow field mismatches: `0`",
            "Workflow status mismatches: `0`",
            "persisted Workflow events: `0`",
            "direct Workflow audit trigger: present",
            "Existing Flutter Workflow functions are unchanged by this gate",
            "Session migration, password retirement and default-Admin redesign separate",
        ):
            self.assertIn(required, source)


if __name__ == "__main__":
    unittest.main()
