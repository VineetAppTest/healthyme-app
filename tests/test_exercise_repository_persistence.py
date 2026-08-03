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
        self.items = {
            "0": self._canonical_row("0", "Brisk Walking"),
            "1": self._canonical_row("1", "Cat-Cow Stretch"),
        }

        components_package = types.ModuleType("components")
        components_package.__path__ = [str(ROOT / "components")]
        store = types.ModuleType("components.content_repository_store")

        def list_repository_items(repository_type, active_only=True):
            self.assertEqual(repository_type, "exercise")
            rows = [copy.deepcopy(row) for row in self.items.values()]
            if active_only:
                rows = [row for row in rows if row.get("status") == "active"]
            rows.sort(key=lambda row: (row["display_name"].casefold(), row["source_id"]))
            return rows

        def get_repository_item(repository_type, source_id):
            self.assertEqual(repository_type, "exercise")
            row = self.items.get(str(source_id))
            return copy.deepcopy(row) if row else None

        def create_numeric_repository_item(
            repository_type,
            display_name,
            payload,
            *,
            status="active",
            actor_id="admin",
            source_system="healthyme",
        ):
            self.assertEqual(repository_type, "exercise")
            numeric_ids = [
                int(source_id)
                for source_id in self.items
                if str(source_id).isdigit()
            ]
            source_id = str(max(numeric_ids, default=-1) + 1)
            row = self._canonical_row(
                source_id,
                str(display_name),
                status=str(status),
                payload=dict(payload or {}),
                source_system=str(source_system),
                created_by=str(actor_id),
                updated_by=str(actor_id),
                legacy_reference="",
            )
            self.items[source_id] = row
            return copy.deepcopy(row)

        def save_repository_item(
            repository_type,
            source_id,
            display_name,
            payload,
            *,
            status="active",
            actor_id="admin",
            source_system="healthyme",
            legacy_reference="",
        ):
            self.assertEqual(repository_type, "exercise")
            clean_id = str(source_id)
            existing = self.items.get(clean_id)
            if not existing:
                raise ValueError("Exercise repository item was not found.")
            existing.update(
                {
                    "display_name": str(display_name),
                    "status": str(status),
                    "payload": copy.deepcopy(dict(payload or {})),
                    "source_system": str(source_system),
                    "legacy_reference": str(legacy_reference or ""),
                    "content_version": int(existing.get("content_version") or 1) + 1,
                    "updated_at": "2026-08-03T06:00:00+00:00",
                    "updated_by": str(actor_id),
                }
            )
            return copy.deepcopy(existing)

        def set_repository_item_status(
            repository_type,
            source_id,
            *,
            active,
            actor_id="admin",
        ):
            self.assertEqual(repository_type, "exercise")
            clean_id = str(source_id)
            existing = self.items.get(clean_id)
            if not existing:
                raise ValueError("Exercise repository item was not found.")
            existing["status"] = "active" if active else "inactive"
            existing["content_version"] = int(existing.get("content_version") or 1) + 1
            existing["updated_at"] = "2026-08-03T06:00:00+00:00"
            existing["updated_by"] = str(actor_id)
            return copy.deepcopy(existing)

        store.list_repository_items = list_repository_items
        store.get_repository_item = get_repository_item
        store.create_numeric_repository_item = create_numeric_repository_item
        store.save_repository_item = save_repository_item
        store.set_repository_item_status = set_repository_item_status

        self.previous_components = sys.modules.get("components")
        self.previous_store = sys.modules.get("components.content_repository_store")
        sys.modules["components"] = components_package
        sys.modules["components.content_repository_store"] = store

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
        if self.previous_store is None:
            sys.modules.pop("components.content_repository_store", None)
        else:
            sys.modules["components.content_repository_store"] = self.previous_store

    @staticmethod
    def _canonical_row(
        source_id,
        title,
        *,
        status="active",
        payload=None,
        source_system="exercise_repository",
        created_by="system",
        updated_by="system",
        legacy_reference=None,
    ):
        exercise_payload = {
            "title": str(title),
            "description": "",
            "category": "",
            "difficulty": "",
            "goal_tags": "",
            "condition_tags": "",
            "duration_or_reps": "",
            "hidden_calories_v96": "",
            "equipment": "",
            "image_url": "",
            "image_bucket": "",
            "image_path": "",
            "image_access_type": "public",
            "instructions": "",
            "benefits": "",
        }
        exercise_payload.update(copy.deepcopy(dict(payload or {})))
        exercise_payload["title"] = str(title)
        return {
            "id": f"uuid-{source_id}",
            "repository_type": "exercise",
            "source_id": str(source_id),
            "display_name": str(title),
            "status": str(status),
            "payload": exercise_payload,
            "content_version": 1,
            "source_system": str(source_system),
            "legacy_reference": (
                f"healthyme_app_state.data.exercises:{source_id}"
                if legacy_reference is None
                else str(legacy_reference)
            ),
            "created_at": "2026-08-01T00:00:00+00:00",
            "created_by": str(created_by),
            "updated_at": "2026-08-01T00:00:00+00:00",
            "updated_by": str(updated_by),
        }

    def test_backfill_preserves_legacy_numeric_ids(self):
        rows = self.module.list_exercise_repository(active_only=False)
        self.assertEqual([row["id"] for row in rows], ["0", "1"])
        self.assertEqual(
            rows[0]["legacy_reference"],
            "healthyme_app_state.data.exercises:0",
        )

    def test_add_uses_next_numeric_id_and_survives_canonical_read(self):
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
        self.assertIn("2", self.items)
        self.assertEqual(self.items["2"]["display_name"], "Jarvis Test Exercise")
        self.assertEqual(self.items["2"]["created_by"], "jarvis_admin")

    def test_duplicate_title_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "already exists"):
            self.module.add_exercise_repository_item(
                {"title": "brisk walking"}, actor_id="admin"
            )
        self.assertEqual(len(self.items), 2)

    def test_update_keeps_id_and_delete_inactivates_only_target(self):
        updated = self.module.update_exercise_repository_item(
            "1",
            {"title": "Cat-Cow Mobility", "difficulty": "Beginner"},
            actor_id="admin",
        )
        self.assertEqual(updated["id"], "1")
        self.assertEqual(updated["title"], "Cat-Cow Mobility")
        self.assertEqual(
            updated["legacy_reference"],
            "healthyme_app_state.data.exercises:1",
        )

        removed = self.module.delete_exercise_repository_item("1", actor_id="admin")
        self.assertEqual(removed["id"], "1")
        self.assertEqual(removed["status"], "inactive")
        self.assertEqual(set(self.items), {"0", "1"})
        active_ids = {
            row["id"]
            for row in self.module.list_exercise_repository(active_only=True)
        }
        self.assertEqual(active_ids, {"0"})

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
        titles = [row["display_name"] for row in self.items.values()]
        self.assertIn("Chair Squat", titles)
        self.assertIn("2", self.items)


if __name__ == "__main__":
    unittest.main()
