import copy
import importlib.util
import pathlib
import sys
import types
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "components" / "exercise_repository.py"


class ExerciseRepositoryPersistenceTests(unittest.TestCase):
    def setUp(self):
        self.state = {
            "exercises": [
                {
                    "id": "0",
                    "source_id": "0",
                    "title": "Brisk Walking",
                    "status": "active",
                },
                {
                    "id": "1",
                    "source_id": "1",
                    "title": "Cat-Cow Stretch",
                    "status": "active",
                },
            ],
            "exercise_repository_audit": [],
        }

        components_package = types.ModuleType("components")
        components_package.__path__ = [str(ROOT / "components")]
        backend = types.ModuleType("components.storage_backend")

        def load_state(force_refresh=False):
            return copy.deepcopy(self.state)

        def save_state(value):
            self.state = copy.deepcopy(value)

        backend.load_state = load_state
        backend.save_state = save_state
        backend.get_storage_status = lambda: {"mode": "SUPABASE"}
        backend.supabase_configured = lambda: True

        self.previous_components = sys.modules.get("components")
        self.previous_backend = sys.modules.get("components.storage_backend")
        sys.modules["components"] = components_package
        sys.modules["components.storage_backend"] = backend

        spec = importlib.util.spec_from_file_location(
            "exercise_repository_under_test", MODULE_PATH
        )
        self.module = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(self.module)
        self.module._clear_streamlit_data_cache = lambda: None

    def tearDown(self):
        if self.previous_components is None:
            sys.modules.pop("components", None)
        else:
            sys.modules["components"] = self.previous_components
        if self.previous_backend is None:
            sys.modules.pop("components.storage_backend", None)
        else:
            sys.modules["components.storage_backend"] = self.previous_backend

    def test_migration_preserves_legacy_numeric_ids(self):
        rows = self.module.list_exercise_repository(active_only=False)
        self.assertEqual([row["id"] for row in rows], ["0", "1"])
        self.assertTrue(self.state["exercise_repository_v1_migration"]["legacy_ids_preserved"])

    def test_add_uses_next_numeric_id_and_survives_fresh_read(self):
        row = self.module.add_exercise_repository_item(
            {
                "title": "Jarvis Test Exercise",
                "category": "Testing",
                "duration_or_reps": "1 controlled repetition",
                "status": "active",
            },
            actor_id="jarvis_admin",
        )
        self.assertEqual(row["id"], "2")
        stored = {item["id"]: item for item in self.state["exercises"]}
        self.assertIn("2", stored)
        self.assertEqual(stored["2"]["title"], "Jarvis Test Exercise")

    def test_duplicate_title_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "already exists"):
            self.module.add_exercise_repository_item(
                {"title": "brisk walking"}, actor_id="admin"
            )
        self.assertEqual(len(self.state["exercises"]), 2)

    def test_update_keeps_id_and_delete_removes_only_target(self):
        updated = self.module.update_exercise_repository_item(
            "1",
            {"title": "Cat-Cow Mobility", "difficulty": "Beginner"},
            actor_id="admin",
        )
        self.assertEqual(updated["id"], "1")
        self.assertEqual(updated["title"], "Cat-Cow Mobility")

        removed = self.module.delete_exercise_repository_item("1", actor_id="admin")
        self.assertEqual(removed["id"], "1")
        self.assertEqual([row["id"] for row in self.state["exercises"]], ["0"])

    def test_import_skips_duplicate_and_blank_rows(self):
        result = self.module.import_exercise_repository_items(
            [
                {"title": "Brisk Walking"},
                {"title": ""},
                {"title": "Chair Squat", "status": "active"},
            ],
            actor_id="admin",
        )
        self.assertEqual(result, {"imported": 1, "skipped": 2})
        titles = [row["title"] for row in self.state["exercises"]]
        self.assertIn("Chair Squat", titles)


if __name__ == "__main__":
    unittest.main()
