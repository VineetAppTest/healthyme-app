from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_FILE = ROOT / "components" / "meal_profile_builder_phase_b.py"
MODULAR_FILE = ROOT / "components" / "profile_builder_modular.py"
SETUP_FILE = ROOT / "components" / "member_plan_builder_setup.py"
MEALS_FILE = ROOT / "components" / "member_plan_builder_meals_compact.py"
EXERCISE_FILE = ROOT / "components" / "member_plan_builder_exercise.py"
SUPPLEMENT_FILE = ROOT / "components" / "member_plan_builder_supplement.py"
VIEW_FILE = ROOT / "components" / "member_plan_builder_view_compact.py"
PERFORMANCE_FILE = ROOT / "components" / "member_plan_builder_performance.py"
EXPANDER_FILE = ROOT / "components" / "member_plan_builder_expander_hygiene.py"
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
    def test_manifest_keeps_meal_write_boundary_and_five_task_navigation(self) -> None:
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
                "Exercise Allocation",
                "Supplement Allocation",
                "View Member Plan",
            ],
        )
        self.assertIn("separate top-level tasks", manifest["navigation_rule"])
        self.assertIn("consolidated active-plan read model", manifest["navigation_rule"])
        self.assertIn("cached", manifest["performance_rule"])

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

    def test_builder_lazy_loads_and_routes_five_distinct_tasks(self) -> None:
        source = MODULAR_FILE.read_text(encoding="utf-8")
        self.assertIn("load_member_plan_setup_options()", source)
        self.assertIn("load_member_plan_recipe_options()", source)
        self.assertIn("render_member_plan_setup(", source)
        self.assertIn("render_member_plan_meals_compact(", source)
        self.assertIn("render_member_plan_exercise()", source)
        self.assertIn("render_member_plan_supplement()", source)
        self.assertIn("render_view_member_plan_compact()", source)
        self.assertNotIn("render_member_plan_allocations()", source)
        setup_index = source.index('if section == "Profile Setup":')
        setup_load_index = source.index("load_member_plan_setup_options()", setup_index)
        meals_index = source.index('elif section == "Meal Structure":')
        recipe_load_index = source.index("load_member_plan_recipe_options()", meals_index)
        self.assertGreater(setup_load_index, setup_index)
        self.assertGreater(recipe_load_index, meals_index)

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

    def test_expanders_are_standardised_to_one_line_more_details(self) -> None:
        source = EXPANDER_FILE.read_text(encoding="utf-8")
        self.assertIn('text == "More setup details"', source)
        self.assertIn('text.startswith("More details —")', source)
        self.assertIn('label = "More details"', source)
        modular = MODULAR_FILE.read_text(encoding="utf-8")
        self.assertIn("white-space:nowrap", modular)
        self.assertIn("stVerticalBlockBorderWrapper", modular)

    def test_meals_use_fixed_compact_cards_portion_guidance_and_review(self) -> None:
        source = MEALS_FILE.read_text(encoding="utf-8")
        self.assertIn("for slot in MEAL_SLOTS", source)
        self.assertIn("with st.container(border=True):", source)
        self.assertIn('"Portion Guidance"', source)
        self.assertIn('with st.expander("More details"', source)
        self.assertIn('"Save Meal Plan"', source)
        self.assertIn("meal_review_rows", source)
        self.assertIn('"Publish & Allocate to Member"', source)
        self.assertIn('activate_profile(profile, "ACTIVATE")', source)
        self.assertNotIn('"Preview Meal Plan"', source)

    def test_exercise_and_supplement_are_separate_without_visible_allocation_ids(self) -> None:
        exercise = EXERCISE_FILE.read_text(encoding="utf-8")
        supplement = SUPPLEMENT_FILE.read_text(encoding="utf-8")
        self.assertIn('"Allocate Exercise"', exercise)
        self.assertIn('"Edit Exercise"', exercise)
        self.assertIn("save_exercise_member_allocation", exercise)
        self.assertIn("stop_exercise_member_allocation", exercise)
        self.assertNotIn('"Allocation ID"', exercise)
        self.assertIn('"Allocate Supplement"', supplement)
        self.assertIn('"Edit Supplement"', supplement)
        self.assertIn("save_supplement_member_allocation", supplement)
        self.assertIn("stop_supplement_member_allocation", supplement)
        self.assertNotIn('"Allocation ID"', supplement)
        self.assertTrue(EXERCISE_PAGE.is_file())
        self.assertTrue(SUPPLEMENT_PAGE.is_file())

    def test_view_member_plan_removes_scope_and_uses_consolidated_ssot(self) -> None:
        source = VIEW_FILE.read_text(encoding="utf-8")
        self.assertNotIn("Profile Scope", source)
        self.assertIn("build_current_member_plan", source)
        self.assertIn("model_profile_id != selected_id", source)
        self.assertIn("more than one active Meal Profile", source)
        self.assertIn('"Exercise Allocations"', source)
        self.assertIn('"Supplement Allocations"', source)
        self.assertIn('"Download Selected Member Plan"', source)
        self.assertIn('sheet_name="Legacy Profile Rows"', source)

    def test_source_contract_and_section_options_are_cached(self) -> None:
        source = PERFORMANCE_FILE.read_text(encoding="utf-8")
        self.assertIn("@st.cache_data(ttl=300", source)
        self.assertIn("_cached_source_contract", source)
        self.assertIn("load_member_plan_setup_options", source)
        self.assertIn("load_member_plan_recipe_options", source)
        self.assertIn("build_profile_builder_source_contract = _build_source_contract_cached", source)

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
