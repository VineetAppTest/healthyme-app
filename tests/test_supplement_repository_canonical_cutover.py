from __future__ import annotations

import pathlib
import unittest
from unittest import mock

import components.supplement_repository as repository


ROOT = pathlib.Path(__file__).resolve().parents[1]
SUPPLEMENT = ROOT / "components" / "supplement_repository.py"


def canonical_row(
    source_id: str = "suprepo_2ceffd32",
    *,
    name: str = "Omega-3",
    status: str = "active",
    version: int = 1,
) -> dict:
    return {
        "id": "internal-uuid",
        "repository_type": "supplement",
        "source_id": source_id,
        "display_name": name,
        "status": status,
        "payload": {
            "supplement_name": name,
            "title": name,
            "dosage": "1 capsule",
            "frequency": "Once",
            "timing": "With Food",
            "instructions": "Take with water",
            "admin_notes": "historical internal note",
            "legacy_source_id": "legacy-supplement-1",
        },
        "content_version": version,
        "source_system": "supplement_repository",
        "legacy_reference": "healthyme_app_state.data.supplement_repository:1",
        "created_at": "2026-08-02T13:30:35+00:00",
        "created_by": "system:content_repository_backfill",
        "updated_at": "2026-08-03T05:30:00+00:00",
        "updated_by": "admin_vineet",
    }


class SupplementRepositoryCanonicalCutoverTests(unittest.TestCase):
    def test_repository_has_no_app_state_or_member_regimen_authority(self) -> None:
        source = SUPPLEMENT.read_text(encoding="utf-8")
        self.assertNotIn("load_db", source)
        self.assertNotIn("save_db", source)
        self.assertNotIn("member_supplements", source)
        self.assertNotIn("supplement_repository_v1_migration", source)
        self.assertIn("list_repository_items", source)
        self.assertIn("save_repository_item", source)
        self.assertIn("set_repository_item_status", source)

    def test_list_flattens_canonical_envelope_to_legacy_shape(self) -> None:
        with mock.patch.object(
            repository,
            "list_repository_items",
            return_value=[canonical_row()],
        ) as list_items:
            rows = repository.list_supplement_repository(active_only=False)

        list_items.assert_called_once_with("supplement", active_only=False)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["id"], "suprepo_2ceffd32")
        self.assertEqual(rows[0]["source_id"], "suprepo_2ceffd32")
        self.assertEqual(rows[0]["supplement_name"], "Omega-3")
        self.assertEqual(rows[0]["status"], "Active")
        self.assertEqual(rows[0]["content_version"], 1)
        self.assertEqual(
            rows[0]["legacy_reference"],
            "healthyme_app_state.data.supplement_repository:1",
        )
        self.assertEqual(rows[0]["admin_notes"], "historical internal note")

    def test_add_uses_suprepo_identity_and_verified_canonical_write(self) -> None:
        created = canonical_row("suprepo_a1b2c3d4", name="Vitamin D")
        with mock.patch.object(
            repository,
            "list_supplement_repository",
            return_value=[repository._from_canonical(canonical_row())],
        ), mock.patch.object(
            repository,
            "_new_source_id",
            return_value="suprepo_a1b2c3d4",
        ), mock.patch.object(
            repository,
            "save_repository_item",
            return_value=created,
        ) as save_item, mock.patch.object(
            repository,
            "_clear_streamlit_data_cache",
        ):
            result = repository.add_supplement_repository_item(
                {
                    "supplement_name": "Vitamin D",
                    "dosage": "1 tablet",
                    "frequency": "Once",
                    "timing": "Morning",
                },
                actor_id="admin_vineet",
            )

        args, kwargs = save_item.call_args
        self.assertEqual(args[0:3], ("supplement", "suprepo_a1b2c3d4", "Vitamin D"))
        self.assertEqual(args[3]["supplement_name"], "Vitamin D")
        self.assertEqual(args[3]["title"], "Vitamin D")
        self.assertEqual(kwargs["status"], "active")
        self.assertEqual(kwargs["actor_id"], "admin_vineet")
        self.assertEqual(kwargs["source_system"], "supplement_repository")
        self.assertEqual(result["id"], "suprepo_a1b2c3d4")

    def test_update_preserves_identity_legacy_reference_and_hidden_notes(self) -> None:
        before = canonical_row()
        after = canonical_row(name="Omega-3 Advanced", version=2)
        with mock.patch.object(
            repository,
            "get_repository_item",
            return_value=before,
        ), mock.patch.object(
            repository,
            "list_supplement_repository",
            return_value=[repository._from_canonical(before)],
        ), mock.patch.object(
            repository,
            "save_repository_item",
            return_value=after,
        ) as save_item, mock.patch.object(
            repository,
            "_clear_streamlit_data_cache",
        ):
            result = repository.update_supplement_repository_item(
                "suprepo_2ceffd32",
                {
                    "supplement_name": "Omega-3 Advanced",
                    "dosage": "2 capsules",
                },
                actor_id="admin_vineet",
            )

        args, kwargs = save_item.call_args
        self.assertEqual(
            args[0:3],
            ("supplement", "suprepo_2ceffd32", "Omega-3 Advanced"),
        )
        self.assertEqual(args[3]["dosage"], "2 capsules")
        self.assertEqual(args[3]["admin_notes"], "historical internal note")
        self.assertEqual(
            kwargs["legacy_reference"],
            "healthyme_app_state.data.supplement_repository:1",
        )
        self.assertEqual(result["id"], "suprepo_2ceffd32")
        self.assertEqual(result["content_version"], 2)

    def test_status_change_is_reversible_and_never_deletes(self) -> None:
        inactive = canonical_row(status="inactive", version=2)
        with mock.patch.object(
            repository,
            "set_repository_item_status",
            return_value=inactive,
        ) as set_status, mock.patch.object(
            repository,
            "_clear_streamlit_data_cache",
        ):
            result = repository.set_supplement_repository_status(
                "suprepo_2ceffd32",
                False,
                actor_id="admin_vineet",
            )

        set_status.assert_called_once_with(
            "supplement",
            "suprepo_2ceffd32",
            active=False,
            actor_id="admin_vineet",
        )
        self.assertEqual(result["status"], "Inactive")
        self.assertNotIn("delete", SUPPLEMENT.read_text(encoding="utf-8").lower())

    def test_duplicate_name_is_rejected_before_write(self) -> None:
        existing = repository._from_canonical(canonical_row())
        with mock.patch.object(
            repository,
            "list_supplement_repository",
            return_value=[existing],
        ), mock.patch.object(repository, "save_repository_item") as save_item:
            with self.assertRaisesRegex(ValueError, "already exists"):
                repository.add_supplement_repository_item(
                    {"supplement_name": "omega-3"},
                    actor_id="admin",
                )

        save_item.assert_not_called()


if __name__ == "__main__":
    unittest.main()
