from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_FILE = ROOT / "components" / "meal_profile_builder_phase_b.py"
MODULAR_FILE = ROOT / "components" / "profile_builder_modular.py"
ALLOCATION_FILE = ROOT / "components" / "profile_builder_allocation_workspace.py"
WRITE_BOUNDARY_FILE = ROOT / "components" / "meal_profile_builder_write_boundary.py"
PAGE_FILE = ROOT / "pages" / "38_Admin_Recommendation_Profile_Builder.py"
DASHBOARD_FILE = ROOT / "pages" / "10_Admin_Dashboard.py"
EXERCISE_PAGE = ROOT / "pages" / "42_Admin_Exercise_Member_Allocation.py"
SUPPLEMENT_PAGE = ROOT / "pages" / "43_Admin_Supplement_Member_Allocation.py"
MODULES_FILE = ROOT / "components" / "pbm_modules.py"
PUBLISH_FILE = ROOT / "components" / "profile_publish_control_v2.py"
SETUP_FILE = ROOT / "components" / "pbm_setup.py"
DOC_FILE = ROOT / "docs" / "meal_profile_builder_phase_b_2026-08-04.md"

_SPEC = importlib.util.spec_from_file_location("meal_profile_builder_phase_b", CONTRACT_FILE)
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError("Unable to load Meal Profile Builder contract.")
contract = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(contract)


class MealProfileBuilderPhaseBTests(unittest.TestCase):
    def test_manifest_limits_live_builder_writes_to_meals(self) -> None:
        manifest = contract.meal_profile_builder_manifest()
        self.assertEqual(manifest["editable_item_types"], ["meal"])
        self.assertEqual(
            manifest["legacy_read_only_item_types"], ["exercise", "supplement"]
        )
        self.assertEqual(
            manifest["visible_sections"],
            [
                "Profile Setup",
                "Meal Structure",
                "Allocate Exercise & Supplement",
                "View Profiles",
            ],
        )
        self.assertIn("must not rewrite or delete", manifest["history_rule"])
        self.assertIn("Preview and Publish render inside Meal Structure", manifest["navigation_rule"])

    def test_item_split_preserves_legacy_rows_and_defensive_copies(self) -> None:
        rows = [
            {"item_type": "meal", "reference_label": "Breakfast"},
            {"item_type": "exercise", "reference_label": "Walk"},
            {"item_type": "supplement", "reference_label": "Vitamin"},
            {"item_type": "other", "reference_label": "Unknown"},
        ]
        grouped = contract.split_profile_items(rows)
        self.assertEqual(len(grouped["meal"]), 1)
        self.assertEqual(len(grouped["legacy_exercise"]), 1)
        self.assertEqual(len(grouped["legacy_supplement"]), 1)
        self.assertEqual(len(grouped["other"]), 1)
        grouped["legacy_exercise"][0]["reference_label"] = "Changed"
        self.assertEqual(rows[1]["reference_label"], "Walk")

    def test_live_navigation_has_four_compact_sections(self) -> None:
        source = MODULAR_FILE.read_text(encoding="utf-8")
        self.assertIn("MEAL_PROFILE_BUILDER_SECTIONS", source)
        self.assertIn("ALLOCATION_WORKSPACE_SECTION", source)
        self.assertIn("VIEW_PROFILES_SECTION", source)
        self.assertNotIn('render_module("exercise"', source)
        self.assertNotIn('render_module("supplement"', source)
        self.assertIn('render_module("meal", options)', source)
        self.assertIn('_render_meal_actions(can_publish)', source)
        self.assertIn('render_profile_builder_allocation_workspace()', source)
        self.assertNotIn('section == "Preview & End-to-End Flow"', source)
        self.assertNotIn('section == "Publish Control"', source)
        self.assertNotIn('section == "Active Profile Preview"', source)
        self.assertIn('"exercise": []', source)
        self.assertIn('"supplement": []', source)

    def test_preview_and_publish_are_meal_actions(self) -> None:
        source = MODULAR_FILE.read_text(encoding="utf-8")
        self.assertIn('"Preview Meal Plan"', source)
        self.assertIn('"Publish Meal Plan"', source)
        self.assertIn('pbm_meal_action_panel', source)
        meal_index = source.index('render_module("meal", options)')
        action_index = source.index('_render_meal_actions(can_publish)', meal_index)
        self.assertLess(meal_index, action_index)

    def test_allocation_workspace_routes_without_claiming_write_authority(self) -> None:
        source = ALLOCATION_FILE.read_text(encoding="utf-8")
        self.assertIn("assigned_member_id", source)
        self.assertIn("phase_c_member", source)
        self.assertIn("phase_d_member", source)
        self.assertIn("pages/42_Admin_Exercise_Member_Allocation.py", source)
        self.assertIn("pages/43_Admin_Supplement_Member_Allocation.py", source)
        for forbidden in (
            "save_exercise_member_allocation",
            "stop_exercise_member_allocation",
            "save_supplement_member_allocation",
            "stop_supplement_member_allocation",
            "save_state",
        ):
            self.assertNotIn(forbidden, source)
        self.assertTrue(EXERCISE_PAGE.is_file())
        self.assertTrue(SUPPLEMENT_PAGE.is_file())

    def test_dashboard_uses_profile_builder_as_allocation_entry(self) -> None:
        source = DASHBOARD_FILE.read_text(encoding="utf-8")
        self.assertIn('"Recommendation Profile Builder"', source)
        self.assertIn('"Exercises"', source)
        self.assertIn('"Supplements"', source)
        self.assertNotIn('nav_cell(\n            "Exercise Member Allocation"', source)
        self.assertNotIn('nav_cell(\n            "Supplement Member Allocation"', source)

    def test_stable_route_installs_write_boundary_before_renderer_import(self) -> None:
        source = PAGE_FILE.read_text(encoding="utf-8")
        install_index = source.index("install_meal_profile_builder_write_boundary()")
        import_index = source.index(
            "from components.profile_builder_modular import render_modular_profile_builder"
        )
        self.assertLess(install_index, import_index)
        self.assertIn('page_title="Meal Profile Builder"', source)
        self.assertIn('render_page_nav(\n        "Meal Profile Builder"', source)
        self.assertNotIn("install_profile_builder_supplement_repository_source", source)

    def test_write_boundary_rejects_non_meal_module_saves(self) -> None:
        source = WRITE_BOUNDARY_FILE.read_text(encoding="utf-8")
        self.assertIn("if not is_meal_profile_builder_editable_type(item_type)", source)
        self.assertIn("Meal Profile Builder can save Meal rows only", source)
        self.assertIn("_module_store.VALID_MODULES = set(MEAL_EDITABLE_ITEM_TYPES)", source)
        self.assertNotIn("delete()", source)
        self.assertNotIn("insert(", source)
        self.assertNotIn("update(", source)

    def test_existing_non_meal_rows_remain_readable_and_publishable(self) -> None:
        modular = MODULAR_FILE.read_text(encoding="utf-8")
        modules = MODULES_FILE.read_text(encoding="utf-8")
        publish = PUBLISH_FILE.read_text(encoding="utf-8")
        self.assertIn("legacy_exercise", modular)
        self.assertIn("legacy_supplement", modular)
        self.assertIn('elif kind == "exercise":', modules)
        self.assertIn('"Type": "Exercise"', modules)
        self.assertIn('"Type": "Supplement"', modules)
        self.assertIn('rows_ready = bool(items)', publish)
        self.assertIn('row.get("item_type") == "exercise"', publish)
        self.assertIn('row.get("item_type") == "supplement"', publish)

    def test_setup_and_meal_saves_do_not_claim_non_meal_ownership(self) -> None:
        page = PAGE_FILE.read_text(encoding="utf-8")
        modular = MODULAR_FILE.read_text(encoding="utf-8")
        setup = SETUP_FILE.read_text(encoding="utf-8")
        self.assertIn("existing stable route", page)
        self.assertIn("Meals are edited here", modular)
        self.assertIn("does not create, replace or delete Meal, Exercise or Supplement rows", setup)

    def test_documented_phase_order_and_safety_boundary(self) -> None:
        source = DOC_FILE.read_text(encoding="utf-8")
        for required in (
            "Independent Exercise Member Allocation",
            "Independent Supplement Member Allocation",
            "Current Member Plan consolidated read model",
            "No action in this phase deletes or rewrites existing Exercise or Supplement rows",
            "Supabase schema, RLS or RPC migration",
            "production data backfill or rewrite",
        ):
            self.assertIn(required, source)

    def test_contract_has_no_runtime_or_storage_dependency(self) -> None:
        source = CONTRACT_FILE.read_text(encoding="utf-8").lower()
        for forbidden in (
            "streamlit",
            "supabase",
            "load_state",
            "save_state",
            "hm_recommendation_profile_items",
        ):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
