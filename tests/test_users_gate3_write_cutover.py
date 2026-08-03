from __future__ import annotations

import ast
import json
import pathlib
import unittest
from typing import Any, Dict, Optional


ROOT = pathlib.Path(__file__).resolve().parents[1]
MIGRATION = ROOT / "supabase" / "migrations" / "20260803161100_users_gate3_transactional_state_commit.sql"
NORMALIZED = ROOT / "components" / "normalized_store.py"
STORAGE = ROOT / "components" / "storage_backend.py"
DOC = ROOT / "docs" / "users_gate3_write_cutover_2026-08-03.md"
GATE4_DOC = ROOT / "docs" / "workflow_gate4_write_cutover_2026-08-03.md"


def _isolated_function(path: pathlib.Path, function_name: str):
    """Compile one pure helper without importing the Streamlit components package."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    node = next(
        item for item in tree.body if isinstance(item, ast.FunctionDef) and item.name == function_name
    )
    module = ast.Module(body=[node], type_ignores=[])
    ast.fix_missing_locations(module)
    namespace = {
        "Any": Any,
        "Dict": Dict,
        "Optional": Optional,
        "json": json,
    }
    exec(compile(module, str(path), "exec"), namespace)
    return namespace[function_name]


class UsersGate3WriteCutoverTests(unittest.TestCase):
    def test_database_contract_is_transactional_and_service_role_only(self) -> None:
        source = MIGRATION.read_text(encoding="utf-8")
        self.assertIn("create or replace function public.hm_admin_commit_users_and_state", source)
        self.assertIn("security definer", source.lower())
        self.assertIn("set search_path = ''", source)
        self.assertIn("pg_advisory_xact_lock", source)
        self.assertIn("public.hm_admin_upsert_user(", source)
        self.assertIn("insert into public.healthyme_app_state", source)
        self.assertIn("'user_state_commit'", source)
        signature = (
            "public.hm_admin_commit_users_and_state(text, text, jsonb, jsonb, "
            "text, text, text, jsonb)"
        )
        self.assertIn("from public, anon, authenticated;", source.lower())
        self.assertIn(f"grant execute on function {signature}".lower(), source.lower())
        self.assertIn("to service_role", source.lower())

    def test_direct_service_role_writes_are_audited_without_password_values(self) -> None:
        source = MIGRATION.read_text(encoding="utf-8")
        self.assertIn("create or replace function public.hm_capture_direct_user_event()", source)
        self.assertIn("if current_user <> 'service_role'", source)
        self.assertIn("to_jsonb(old) - 'password_hash'", source)
        self.assertIn("to_jsonb(new) - 'password_hash'", source)
        self.assertIn("'service_role_direct'", source)
        self.assertIn("create trigger hm_users_capture_direct_event", source)

    def test_normalized_store_retains_gate3_contract_and_auth_linkage_protection(self) -> None:
        source = NORMALIZED.read_text(encoding="utf-8")
        self.assertIn("def commit_users_and_state(", source)
        self.assertIn('client.rpc("hm_admin_commit_users_and_state"', source)
        self.assertIn("SUPABASE_SERVICE_ROLE_KEY is required for canonical User writes", source)
        self.assertIn('if "auth_user_id" in user:', source)
        self.assertIn('if "auth_migrated_at" in user:', source)
        self.assertIn("def sync_workflow_to_normalized(", source)
        self.assertIn("def sync_users_workflow_to_normalized(", source)
        self.assertIn("manual_users_workflow_sync", source)

    def test_shared_only_user_fields_do_not_enter_canonical_patch(self) -> None:
        canonical_user_patch = _isolated_function(NORMALIZED, "_canonical_user_patch")
        patch = canonical_user_patch(
            {
                "id": "u1",
                "name": "Member",
                "email": " MEMBER@EXAMPLE.COM ",
                "password_hash": "hash",
                "role": "MEMBER",
                "must_reset_password": False,
                "is_active": True,
                "auth_provider": "AUTH0",
                "auth0_user_id": "legacy|123",
                "auth0_email_verified": True,
            }
        )
        self.assertEqual("member@example.com", patch["email"])
        self.assertEqual("member", patch["role"])
        self.assertEqual("auth0", patch["auth_provider"])
        self.assertNotIn("auth0_user_id", patch)
        self.assertNotIn("auth0_email_verified", patch)
        self.assertNotIn("auth_user_id", patch)
        self.assertNotIn("auth_migrated_at", patch)

    def test_gate4_supersedes_storage_selection_without_weakening_user_fail_closed(self) -> None:
        source = STORAGE.read_text(encoding="utf-8")
        self.assertIn("commit_identity_and_state", source)
        self.assertIn("users_changed = _users_projection_changed(previous, db)", source)
        self.assertIn("workflow_changed = _workflow_projection_changed(previous, db)", source)
        self.assertIn("identity_changed = users_changed or workflow_changed", source)
        self.assertIn("if identity_changed and not configured:", source)
        self.assertIn("local User/Workflow fallback is disabled", source)
        self.assertIn("force_state_commit=True", source)
        self.assertIn("raise RuntimeError(identity_commit_message)", source)
        self.assertNotIn("sync_workflow_to_normalized", source)

    def test_projection_change_detection_covers_shared_only_user_metadata(self) -> None:
        users_projection_changed = _isolated_function(STORAGE, "_users_projection_changed")
        before = {"users": [{"id": "u1", "name": "A", "auth0_user_id": ""}]}
        after = {"users": [{"id": "u1", "name": "A", "auth0_user_id": "legacy|1"}]}
        self.assertTrue(users_projection_changed(before, after))
        self.assertFalse(users_projection_changed(after, after))

    def test_local_push_cannot_replace_canonical_identity(self) -> None:
        source = STORAGE.read_text(encoding="utf-8")
        self.assertIn("canonical identity data could not be loaded", source)
        self.assertIn('local_state["users"] = canonical_users', source)
        self.assertIn('local_state["workflow"] = canonical_workflow', source)
        self.assertIn("canonical Users and Workflow were preserved", source)

    def test_gate3_document_remains_historical_and_gate4_records_supersession(self) -> None:
        source = DOC.read_text(encoding="utf-8")
        for required in (
            "canonical Users: `15`",
            "shared User rows: `15`",
            "missing shared identities: `0`",
            "persisted User events: `0`",
            "direct User audit trigger: present",
            "Workflow remains on its existing dedicated synchronization path",
            "Gate 4 may cut over **Workflow writes only**",
        ):
            self.assertIn(required, source)
        gate4 = GATE4_DOC.read_text(encoding="utf-8")
        self.assertIn("Gate 4 cuts over the **Streamlit/shared-state Workflow write authority**", gate4)
        self.assertIn("combined User + Workflow + state transactional contract", gate4)


if __name__ == "__main__":
    unittest.main()
