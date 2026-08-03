from __future__ import annotations

import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
MIGRATION = ROOT / "supabase" / "migrations" / "20260803161100_users_gate3_transactional_state_commit.sql"
NORMALIZED = ROOT / "components" / "normalized_store.py"
STORAGE = ROOT / "components" / "storage_backend.py"
DOC = ROOT / "docs" / "users_gate3_write_cutover_2026-08-03.md"


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

    def test_normalized_store_uses_canonical_contract_and_preserves_auth_linkage(self) -> None:
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
        import components.normalized_store as store

        patch = store._canonical_user_patch(
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

    def test_storage_selects_fail_closed_user_path_and_workflow_only_sync(self) -> None:
        source = STORAGE.read_text(encoding="utf-8")
        self.assertIn("commit_users_and_state", source)
        self.assertIn("sync_workflow_to_normalized", source)
        self.assertNotIn("sync_users_workflow_to_normalized", source)
        self.assertIn("users_changed = _users_projection_changed(previous, db)", source)
        self.assertIn("force_state_commit=True", source)
        self.assertIn("raise RuntimeError(user_commit_message)", source)
        self.assertIn("Canonical User write rejected; state was not saved.", source)

    def test_projection_change_detection_covers_shared_only_metadata(self) -> None:
        import components.storage_backend as storage

        before = {"users": [{"id": "u1", "name": "A", "auth0_user_id": ""}]}
        after = {"users": [{"id": "u1", "name": "A", "auth0_user_id": "legacy|1"}]}
        self.assertTrue(storage._users_projection_changed(before, after))
        self.assertFalse(storage._users_projection_changed(after, after))

    def test_local_push_cannot_replace_canonical_users(self) -> None:
        source = STORAGE.read_text(encoding="utf-8")
        self.assertIn("Local push blocked because canonical Users could not be loaded", source)
        self.assertIn('local_state["users"] = canonical_users', source)
        self.assertIn("canonical Users were preserved", source)

    def test_document_records_production_evidence_and_scope(self) -> None:
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


if __name__ == "__main__":
    unittest.main()
