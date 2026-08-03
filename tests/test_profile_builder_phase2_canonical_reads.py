from __future__ import annotations

import copy
import unittest
from pathlib import Path
from unittest.mock import patch

from components import profile_builder_canonical_sources as canonical
from components import profile_builder_canonical_repository_runtime as runtime
from components import profile_builder_module_store
from components import profile_builder_module_store_canonical
from components.pbm_core import SOURCE_FIELDS


ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "pages" / "38_Admin_Recommendation_Profile_Builder.py"
MODULAR = ROOT / "components" / "profile_builder_modular.py"
ROWS = ROOT / "components" / "pbm_rows.py"


def source(
    kind: str,
    source_id: str,
    label: str,
    *,
    status: str = "active",
    **snapshot_values,
):
    source_type = {
        "recipe": "recipe_repository",
        "exercise": "exercise_repository",
        "supplement": "supplement_repository",
    }[kind]
    snapshot = {
        "contract_version": "2026-08-03-v1",
        "source_type": source_type,
        "source_id": source_id,
        "title": label,
        "status": status,
        **snapshot_values,
    }
    if kind == "supplement":
        snapshot["supplement_name"] = label
    return {
        "contract_version": "2026-08-03-v1",
        "kind": kind,
        "source_type": source_type,
        "source_id": source_id,
        "identity_key": f"{source_type}:{source_id}",
        "display_label": label,
        "status": status,
        "selectable": status == "active",
        "snapshot": snapshot,
    }


class ProfileBuilderPhase2CanonicalReadsTests(unittest.TestCase):
    def test_phase2_source_loader_never_uses_mock_repository_fallbacks(self):
        recipe = source("recipe", "1", "Recipe One")
        supplement = source("supplement", "suprepo_1", "Supplement One")

        def repository_rows(kind, *, active_only=True):
            if kind == "recipe":
                return [recipe]
            if kind == "exercise":
                raise RuntimeError("exercise store unavailable")
            return [supplement]

        with (
            patch.object(
                canonical,
                "list_profile_builder_repository_sources",
                side_effect=repository_rows,
            ),
            patch.object(
                canonical,
                "check_profile_builder_store",
                return_value={"ok": False},
            ),
        ):
            sources, options, message = canonical.load_profile_builder_phase2_sources()

        self.assertEqual(sources["recipe"], ["Recipe One"])
        self.assertEqual(sources["exercise"], [])
        self.assertEqual(sources["supplement"], ["Supplement One"])
        self.assertEqual(options["exercise"], [])
        self.assertIn("exercise=unavailable", message)
        self.assertNotIn("Brisk Walking", sources["exercise"])

    def test_duplicate_visible_names_remain_distinct_by_source_id(self):
        options = [
            canonical._option_from_source(source("exercise", "2", "Mobility Flow")),
            canonical._option_from_source(source("exercise", "9", "Mobility Flow")),
        ]
        labels = canonical.source_option_labels(options)

        self.assertEqual({option["option_id"] for option in options}, {"2", "9"})
        self.assertEqual(labels["2"], "Mobility Flow · ID 2")
        self.assertEqual(labels["9"], "Mobility Flow · ID 9")

    def test_loaded_saved_snapshot_is_not_replaced_during_render(self):
        saved_snapshot = {
            "contract_version": "2026-08-03-v1",
            "source_type": "exercise_repository",
            "source_id": "7",
            "title": "Original Mobility",
            "benefits": "Historical benefit",
            "status": "active",
        }
        row = {
            "item_type": "exercise",
            "source_id": "7",
            "source_type": "exercise_repository",
            "reference_label": "Original Mobility",
            "source_snapshot": copy.deepcopy(saved_snapshot),
            "source_admin_overrides": {"benefits": "Member-specific context"},
        }
        active_option = canonical._option_from_source(
            source(
                "exercise",
                "7",
                "Renamed Mobility",
                benefits="Current repository benefit",
            )
        )

        row_options = canonical.source_options_for_row(
            "exercise",
            row,
            [active_option],
        )
        selected = canonical.current_source_option_id(
            "exercise",
            row,
            row_options,
        )
        changed, snapshot = canonical.apply_source_selection(
            "exercise",
            row,
            selected,
            row_options,
        )

        self.assertFalse(changed)
        self.assertTrue(selected.startswith("saved:exercise:"))
        self.assertEqual(snapshot["benefits"], "Historical benefit")
        self.assertEqual(row["reference_label"], "Original Mobility")
        self.assertEqual(row["source_snapshot"], saved_snapshot)
        self.assertEqual(
            row["source_admin_overrides"],
            {"benefits": "Member-specific context"},
        )

        changed, refreshed = canonical.apply_source_selection(
            "exercise",
            row,
            "7",
            row_options,
        )
        self.assertTrue(changed)
        self.assertEqual(refreshed["benefits"], "Current repository benefit")
        self.assertEqual(row["reference_label"], "Renamed Mobility")
        self.assertEqual(row["source_option_id"], "7")
        self.assertEqual(row["source_admin_overrides"], {})

    def test_legacy_label_only_row_backfills_only_when_unambiguous(self):
        one_match = source("recipe", "4", "Balanced Bowl")
        row = {
            "item_type": "meal",
            "reference_label": "Balanced Bowl",
            "source_snapshot": {},
        }
        with patch.object(
            canonical,
            "list_profile_builder_repository_sources",
            return_value=[one_match],
        ):
            canonical.prepare_row_source("meal", row)

        self.assertEqual(row["source_id"], "4")
        self.assertEqual(row["source_type"], "recipe_repository")
        self.assertEqual(row["source_snapshot"]["title"], "Balanced Bowl")
        self.assertTrue(row["source_option_id"].startswith("saved:recipe:"))

        ambiguous = {
            "item_type": "exercise",
            "reference_label": "Repeated Name",
            "source_snapshot": {},
        }
        with patch.object(
            canonical,
            "list_profile_builder_repository_sources",
            return_value=[
                source("exercise", "3", "Repeated Name"),
                source("exercise", "8", "Repeated Name"),
            ],
        ):
            canonical.prepare_row_source("exercise", ambiguous)

        self.assertEqual(ambiguous["source_id"], "")
        self.assertTrue(
            ambiguous["source_option_id"].startswith("legacy:exercise:")
        )

    def test_saved_inactive_or_removed_source_remains_available(self):
        row = {
            "item_type": "supplement",
            "source_id": "suprepo_old",
            "source_type": "supplement_repository",
            "reference_label": "Historical Supplement",
            "source_snapshot": {
                "contract_version": "2026-08-03-v1",
                "source_type": "supplement_repository",
                "source_id": "suprepo_old",
                "title": "Historical Supplement",
                "supplement_name": "Historical Supplement",
                "dosage": "1 tablet",
                "status": "inactive",
            },
        }
        with patch.object(
            canonical,
            "profile_builder_repository_source_by_id",
            return_value=None,
        ):
            options = canonical.source_options_for_row(
                "supplement",
                row,
                [],
            )
        labels = canonical.source_option_labels(options)
        selected = canonical.current_source_option_id(
            "supplement",
            row,
            options,
        )

        self.assertEqual(len(options), 1)
        self.assertTrue(selected.startswith("saved:supplement:"))
        self.assertIn("Inactive saved source", labels[selected])
        self.assertEqual(
            canonical.source_snapshot_for_row("supplement", row)["dosage"],
            "1 tablet",
        )

    def test_canonical_storage_payload_uses_row_id_and_saved_snapshot(self):
        row = {
            "item_type": "exercise",
            "source_id": "11",
            "source_type": "exercise_repository",
            "source_contract_version": "2026-08-03-v1",
            "reference_label": "Strength Basics",
            "source_snapshot": {
                "contract_version": "2026-08-03-v1",
                "source_type": "exercise_repository",
                "source_id": "11",
                "title": "Strength Basics",
                "difficulty": "Beginner",
                "image": {"image_url": "https://example.test/strength.png"},
                "status": "active",
            },
            "source_admin_overrides": {"difficulty": "Intermediate"},
        }
        payload = canonical.source_storage_payload_for_row("exercise", row)

        self.assertEqual(payload["source_id"], "11")
        self.assertEqual(payload["source_type"], "exercise_repository")
        self.assertEqual(payload["source_label"], "Strength Basics")
        self.assertEqual(
            payload["source_snapshot"]["difficulty"],
            "Intermediate",
        )
        self.assertEqual(
            payload["source_snapshot"]["source_original_snapshot"]["difficulty"],
            "Beginner",
        )
        self.assertEqual(
            payload["source_image_url"],
            "https://example.test/strength.png",
        )

    def test_supplement_source_details_do_not_restore_admin_notes(self):
        fields = [field for field, _label, _type in SOURCE_FIELDS["supplement"]]
        self.assertEqual(fields, ["timing", "instructions"])
        self.assertNotIn("admin_notes", fields)

    def test_runtime_wires_canonical_module_store(self):
        runtime._INSTALLED = False
        runtime.install_profile_builder_canonical_repository_runtime()
        self.assertIs(
            profile_builder_module_store._normalise_item_rows,
            profile_builder_module_store_canonical._normalise_item_rows,
        )
        self.assertIs(
            profile_builder_module_store.save_profile_module,
            profile_builder_module_store_canonical.save_profile_module,
        )

    def test_production_page_installs_phase2_before_modular_import(self):
        page_source = PAGE.read_text(encoding="utf-8")
        install_at = page_source.index(
            "install_profile_builder_canonical_repository_runtime()"
        )
        modular_at = page_source.index(
            "from components.profile_builder_modular import"
        )
        self.assertLess(install_at, modular_at)
        self.assertNotIn(
            "install_profile_builder_supplement_repository_source",
            page_source,
        )

        modular_source = MODULAR.read_text(encoding="utf-8")
        self.assertIn("load_profile_builder_phase2_sources", modular_source)
        self.assertIn('"recipe_sources"', modular_source)
        self.assertIn('"exercise_sources"', modular_source)
        self.assertIn('"supplement_sources"', modular_source)

        row_source = ROWS.read_text(encoding="utf-8")
        self.assertIn('widget_key(row, "source_option_id")', row_source)
        self.assertNotIn(
            'widget_key(row, "reference_label")',
            row_source,
        )


if __name__ == "__main__":
    unittest.main()
