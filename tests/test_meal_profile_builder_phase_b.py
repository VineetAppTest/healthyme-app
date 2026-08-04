from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_FILE = ROOT / "components" / "meal_profile_builder_phase_b.py"
MODULAR_FILE = ROOT / "components" / "profile_builder_modular.py"
SETUP_FILE = ROOT / "components" / "member_plan_builder_setup.py"
MEALS_FILE = ROOT / "components" / "member_plan_builder_meals.py"
ALLOCATION_FILE = ROOT / "components" / "member_plan_builder_allocations.py"
EXPORT_FILE = ROOT / "components" / "member_plan_builder_export.py"
WRITE_BOUNDARY_FILE = ROOT / "components" / "meal_profile_builder_write_boundary.py"
PAGE_FILE = ROOT / "pages" / "38_Admin_Recommendation_Profile_Builder.py"
DASHBOARD_FILE = ROOT / "pages" / "10_Admin_Dashboard.py"
EXERCISE_PAGE = ROOT / "pages" / "42_Admin_Exercise_Member_Allocation.py"
SUPPLEMENT_PAGE = ROOT / "pages" / "43_Admin_Supplement_Member_Allocation.py"

_SPEC = importlib.util.spec_from_file_location(
    "meal_profile_builder_phase_b",
    CONTRACT_FILE,
)
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError("Unable to load Member Plan Builder contract.")
contract = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(contract)


class MealProfileBuilderPhaseBTests(unittest.TestCase):
    def test_manifest_keeps_meal_write_boundary_and_final_navigation(self) -> None:
        manifest = contract.meal_profile_builder_manifest()
        self.assertEqual(manifest["editable_item_types"], ["meal"])
        self.assertEqual(
            manifest["legacy_read_only_item_types"],
            ["exercise", "supplement"],
        )
        self.assertEqual(
            manifest["visible_sections"],
            [
                "Profile Setup",
                "Meal Structure",
                "Allocate Exercise & Supplement",
                "View Member Plan",
            ],
        )
        self.assertIn("auto-loads", manifest["navigation_rule"])
        self.assertIn("Excel download", manifest["navigation_rule"])

    def test_item_split_preserves_legacy_rows_and_defensive_copies(self) -> None:
        rows = [
            {"item_type": "meal", "reference_label": "Breakfast"},
            {"item_type": "exercise", "reference_label": "Walk"},
            {"item_type": "supplement", "reference_label": "Vitamin"},
        ]
        grouped = contract.split_profile_items(rows)
        self.assertEqual(len(grouped["meal"]), 1)
        self.assertEqual(len(grouped["legacy_exercise"]), 1)
        self.assertEqual(len(grouped["legacy_supplement"]), 1)
        grouped["legacy_exercise"][0]["reference_label"] = "Changed"
        self.assertEqual(rows[1]["reference_label"], "Walk")

    def test_builder_has_four_task_based_sections(self) -> None:
        source = MODULAR_FILE.read_text(encoding="utf-8")
        self.assertIn("MEAL_PROFILE_BUILDER_SECTIONS", source)
        self.assertIn("render_member_plan_setup(options)", source)
        self.assertIn("render_member_plan_meals(options[\"recipe\"], can_publish)", source)
        self.assertIn("render_member_plan_allocations()", source)
        self.assertIn("render_view_member_plan()", source)
        self.assertNotIn("render_profile_builder_allocation_workspace", source)
        self.assertNotIn("render_module(", source)
        self.assertNotIn("render_profile_publish_control", source)

    def test_setup_auto_loads_and_clones_complete_meal_plan(self) -> None:
        source = SETUP_FILE.read_text(encoding="utf-8")
        self.assertIn("_handle_plan_selection(selected_id)", source)
        self.assertIn("load_selected(selected_id, shell_only=False)", source)
        self.assertNotIn('"Load Profile"', source)
        self.assertIn('"Clone Complete Plan"', source)
        self.assertIn('if clean(row.get("item_type")).lower() == "meal"', source)
        self.assertIn("save_profile_module(", source)

    def test_setup_selector_is_compact_aligned_and_state_safe(self) -> None:
        source = SETUP_FILE.read_text(encoding="utf-8")
        self.assertNotIn(
            "Select a plan and it loads automatically. Keep only the information needed",
            source,
        )
        self.assertIn('label_visibility="collapsed"', source)
        self.assertIn('vertical_alignment="bottom"', source)
        self.assertIn("_queue_plan_selector(profile_id)", source)
        self.assertIn("_queue_plan_selector(new_id)", source)
        self.assertIn("_apply_queued_plan_selector(selector_options, loaded_id)", source)
        apply_at = source.index("_apply_queued_plan_selector(selector_options, loaded_id)")
        widget_at = source.index("selected_id = select_col.selectbox(")
        self.assertLess(apply_at, widget_at)
        handler = source[
            source.index("def _handle_plan_selection") : source.index(
                "def _clone_complete_plan"
            )
        ]
        self.assertNotIn("st.session_state[_SELECTOR_KEY] =", handler)

    def test_meals_use_fixed_slots_portion_guidance_review_and_direct_publish(self) -> None:
        source = MEALS_FILE.read_text(encoding="utf-8")
        self.assertIn("for slot in MEAL_SLOTS", source)
        self.assertIn('"Portion Guidance"', source)
        self.assertIn('source_snapshot("meal", selected_recipe)', source)
        self.assertIn('"More details', source)
        self.assertIn('"Save Meal Plan"', source)
        self.assertIn("meal_review_rows", source)
        self.assertIn('"Publish & Allocate to Member"', source)
        self.assertIn('activate_profile(profile, "ACTIVATE")', source)
        self.assertNotIn('"Preview Meal Plan"', source)

    def test_allocations_render_one_selected_route_and_keep_independent_stores(self) -> None:
        source = ALLOCATION_FILE.read_text(encoding="utf-8")
        self.assertIn('allocation_type = st.radio(', source)
        self.assertIn('["Exercise", "Supplement"]', source)
        self.assertIn('if allocation_type == "Exercise":', source)
        self.assertIn("_render_exercise(member_id)", source)
        self.assertIn("_render_supplement(member_id)", source)
        self.assertNotIn('st.tabs(["Exercise", "Supplement"])', source)
        exercise_branch = source[source.index('if allocation_type == "Exercise":') :]
        self.assertIn(
            'if allocation_type == "Exercise":\n        _render_exercise(member_id)\n    else:\n        _render_supplement(member_id)',
            exercise_branch,
        )
        self.assertIn("save_exercise_member_allocation", source)
        self.assertIn("stop_exercise_member_allocation", source)
        self.assertIn("save_supplement_member_allocation", source)
        self.assertIn("stop_supplement_member_allocation", source)
        self.assertNotIn("st.switch_page", source)
        self.assertTrue(EXERCISE_PAGE.is_file())
        self.assertTrue(SUPPLEMENT_PAGE.is_file())

    def test_publish_log_and_view_download_are_detailed_excel_files(self) -> None:
        source = EXPORT_FILE.read_text(encoding="utf-8")
        self.assertIn('"Change Log"', source)
        self.assertIn('"Seven Day Meals"', source)
        self.assertIn("pd.ExcelWriter", source)
        self.assertIn('"Download Detailed Plan & Change Log"', source)
        self.assertIn('"Download Selected Member Plan"', source)
        self.assertIn("render_view_profiles()", source)

    def test_dashboard_uses_member_plan_builder_as_single_entry(self) -> None:
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
        self.assertIn('page_title="Member Plan Builder"', source)
        self.assertIn('render_page_nav(\n        "Member Plan Builder"', source)

    def test_write_boundary_still_rejects_non_meal_profile_saves(self) -> None:
        source = WRITE_BOUNDARY_FILE.read_text(encoding="utf-8")
        self.assertIn("if not is_meal_profile_builder_editable_type(item_type)", source)
        self.assertIn("Meal Profile Builder can save Meal rows only", source)
        self.assertNotIn("insert(", source)
        self.assertNotIn("update(", source)


if __name__ == "__main__":
    unittest.main()
