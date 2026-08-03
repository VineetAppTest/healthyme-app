from __future__ import annotations

import pathlib
import unittest
from unittest import mock

import components.exercise_repository as repository


ROOT = pathlib.Path(__file__).resolve().parents[1]
STORE = ROOT / "components" / "content_repository_store.py"
EXERCISE = ROOT / "components" / "exercise_repository.py"
RPC_MIGRATION = (
    ROOT
    / "supabase"
    / "migrations"
    / "20260803104500_create_numeric_content_repository_item_rpc.sql"
)


def canonical_row(
    source_id: str = "2",
    *,
    title: str = "Stretches",
    status: str = "active",
    version: int = 1,
) -> dict:
    return {
        "id": "internal-uuid",
        "repository_type": "exercise",
        "source_id": source_id,
        "display_name": title,
        "status": status,
        "payload": {
            "title": title,
            "description": "Gentle mobility",
            "category": "Mobility",
            "difficulty": "Beginner",
            "goal_tags": "general",
            "condition_tags": "general",
            "duration_or_reps": "10 reps",
            "hidden_calories_v96": "",
            "equipment": "Mat",
            "image_url": "",
            "image_bucket": "",
            "image_path": "",
            "image_access_type": "public",
            "instructions": "Move slowly",
            "benefits": "Mobility",
        },
        "content_version": version,
        "source_system": "exercise_repository",
        "legacy_reference": "healthyme_app_state.data.exercises:2",
        "created_at": "2026-08-02T13:30:35+00:00",
        "created_by": "admin_vineet",
        "updated_at": "2026-08-03T05:30:00+00:00",
        "updated_by": "admin_vineet",
    }


class ExerciseRepositoryCanonicalCutoverTests(unittest.TestCase):
    def test_repository_has_no_app_state_read_or_write_authority(self) -> None:
        source = EXERCISE.read_text(encoding="utf-8")
        self.assertNotIn("load_state", source)
        self.assertNotIn("save_state", source)
        self.assertNotIn("healthyme_app_state", source)
        self.assertIn("list_repository_items", source)
        self.assertIn("save_repository_item", source)
        self.assertIn("set_repository_item_status", source)
        self.assertIn("create_numeric_repository_item", source)

    def test_list_flattens_canonical_envelope_to_legacy_shape(self) -> None:
        with mock.patch.object(
            repository,
            "list_repository_items",
            return_value=[canonical_row()],
        ) as list_items:
            rows = repository.list_exercise_repository(active_only=False)

        list_items.assert_called_once_with("exercise", active_only=False)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["id"], "2")
        self.assertEqual(rows[0]["source_id"], "2")
        self.assertEqual(rows[0]["resource_type"], "exercises")
        self.assertEqual(rows[0]["title"], "Stretches")
        self.assertEqual(rows[0]["content_version"], 1)
        self.assertEqual(
            rows[0]["legacy_reference"],
            "healthyme_app_state.data.exercises:2",
        )

    def test_add_uses_atomic_numeric_rpc_and_fresh_verified_result(self) -> None:
        created = canonical_row("3", title="New Exercise")
        with mock.patch.object(
            repository,
            "list_exercise_repository",
            return_value=[repository._from_canonical(canonical_row())],
        ), mock.patch.object(
            repository,
            "create_numeric_repository_item",
            return_value=created,
        ) as create_item, mock.patch.object(
            repository,
            "_clear_streamlit_data_cache",
        ):
            result = repository.add_exercise_repository_item(
                {
                    "title": "New Exercise",
                    "category": "Strength",
                    "status": "active",
                },
                actor_id="admin_vineet",
            )

        args, kwargs = create_item.call_args
        self.assertEqual(args[0], "exercise")
        self.assertEqual(args[1], "New Exercise")
        self.assertEqual(args[2]["title"], "New Exercise")
        self.assertEqual(kwargs["actor_id"], "admin_vineet")
        self.assertEqual(kwargs["source_system"], "exercise_repository")
        self.assertEqual(result["id"], "3")

    def test_update_keeps_source_id_and_legacy_reference(self) -> None:
        before = canonical_row()
        after = canonical_row(title="Updated Stretches", version=2)
        with mock.patch.object(
            repository,
            "get_repository_item",
            return_value=before,
        ), mock.patch.object(
            repository,
            "list_exercise_repository",
            return_value=[repository._from_canonical(before)],
        ), mock.patch.object(
            repository,
            "save_repository_item",
            return_value=after,
        ) as save_item, mock.patch.object(
            repository,
            "_clear_streamlit_data_cache",
        ):
            result = repository.update_exercise_repository_item(
                "2",
                {"title": "Updated Stretches", "equipment": "None"},
                actor_id="admin_vineet",
            )

        args, kwargs = save_item.call_args
        self.assertEqual(args[0:3], ("exercise", "2", "Updated Stretches"))
        self.assertEqual(args[3]["equipment"], "None")
        self.assertEqual(
            kwargs["legacy_reference"],
            "healthyme_app_state.data.exercises:2",
        )
        self.assertEqual(result["id"], "2")
        self.assertEqual(result["content_version"], 2)

    def test_delete_is_an_inactive_status_transition(self) -> None:
        inactive = canonical_row(status="inactive", version=2)
        with mock.patch.object(
            repository,
            "set_repository_item_status",
            return_value=inactive,
        ) as set_status, mock.patch.object(
            repository,
            "_clear_streamlit_data_cache",
        ):
            result = repository.delete_exercise_repository_item(
                "2",
                actor_id="admin_vineet",
            )

        set_status.assert_called_once_with(
            "exercise",
            "2",
            active=False,
            actor_id="admin_vineet",
        )
        self.assertEqual(result["status"], "inactive")

    def test_numeric_creation_rpc_is_atomic_and_server_only(self) -> None:
        sql = RPC_MIGRATION.read_text(encoding="utf-8")
        store = STORE.read_text(encoding="utf-8")

        self.assertIn("pg_advisory_xact_lock", sql)
        self.assertIn("max(source_id::bigint)", sql)
        self.assertIn("returns setof public.hm_content_repository_items", sql)
        self.assertIn("security invoker", sql.lower())
        self.assertIn(
            "from public, anon, authenticated, service_role",
            sql,
        )
        self.assertIn("to service_role", sql)
        self.assertIn('NUMERIC_CREATE_RPC = "hm_create_numeric_content_repository_item"', store)
        self.assertIn("return _verified_item(kind, source_id, expected)", store)


if __name__ == "__main__":
    unittest.main()
