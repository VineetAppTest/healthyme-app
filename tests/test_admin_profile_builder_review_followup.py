from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class AdminProfileBuilderReviewFollowupTests(unittest.TestCase):
    def test_setup_more_details_uses_responsive_horizontal_wrapping(self):
        source = (ROOT / "components/member_plan_builder_setup.py").read_text()

        self.assertIn("mpb-setup-details-anchor", source)
        self.assertIn(
            "grid-template-columns:repeat(auto-fit,minmax(220px,1fr))",
            source,
        )
        self.assertIn("grid-template-columns:1fr!important", source)
        self.assertIn('row2 = st.columns(3, gap="small")', source)
        self.assertIn('note_col, change_col = st.columns(2, gap="small")', source)

    def test_recipe_more_details_uses_responsive_read_only_grid(self):
        source = (ROOT / "components/member_plan_builder_meals_compact.py").read_text()

        self.assertIn("mpb-recipe-detail-grid", source)
        self.assertIn(
            "grid-template-columns:repeat(auto-fit,minmax(180px,1fr))",
            source,
        )
        self.assertIn("mpb-recipe-detail-tile", source)
        self.assertNotIn('st.markdown(f"**{label}:** {safe(value)}")', source)
        self.assertIn('with st.expander("More details", expanded=False):', source)

    def test_publish_change_log_is_scoped_to_open_profile(self):
        export = (ROOT / "components/member_plan_builder_export.py").read_text()
        meals = (ROOT / "components/member_plan_builder_meals_compact.py").read_text()

        start = export.index("def load_profile_plan_events(")
        end = export.index("def build_member_plan_workbook(", start)
        block = export[start:end]
        self.assertIn('.eq("id", clean_profile_id)', block)
        self.assertIn('.eq("profile_id", clean_profile_id)', block)
        self.assertNotIn('.in_("profile_id"', block)
        self.assertIn("load_profile_plan_events(profile_id)", export)
        self.assertIn("load_profile_plan_events(selected_id)", export)
        self.assertIn("load_profile_plan_events.clear()", meals)
        self.assertNotIn("load_member_plan_events.clear()", meals)

    def test_exercise_duplicate_more_details_is_removed(self):
        source = (ROOT / "components/member_plan_builder_exercise.py").read_text()

        self.assertNotIn('st.expander("More details"', source)
        self.assertNotIn("mpb-exercise-more-details-anchor", source)
        self.assertNotIn("_render_exercise_polish_styles", source)
        self.assertIn("source_summary(", source)

    def test_exercise_frequency_and_timing_are_controlled_dropdowns(self):
        source = (ROOT / "components/member_plan_builder_exercise.py").read_text()
        allocation = (ROOT / "components/exercise_member_allocation.py").read_text()

        self.assertIn('selectbox(\n            "Frequency per week"', source)
        self.assertIn('selectbox(\n            "Timing"', source)
        self.assertIn("EXERCISE_FREQUENCY_OPTIONS", source)
        self.assertIn("EXERCISE_TIMING_OPTIONS", source)
        self.assertIn("EXERCISE_FREQUENCY_OPTIONS = tuple(range(1, 8))", allocation)
        for option in ("Morning", "Afternoon", "Evening", "Night", "As advised"):
            self.assertIn(f'"{option}"', allocation)

    def test_exercise_prescription_metadata_is_persisted_and_preserved(self):
        source = (ROOT / "components/exercise_member_allocation.py").read_text()
        view = (ROOT / "components/current_member_plan_view.py").read_text()

        self.assertIn('"frequency_per_week": frequency', source)
        self.assertIn('"timing": allocation_timing', source)
        self.assertIn(
            'frequency_per_week=allocation.get("frequency_per_week")',
            source,
        )
        self.assertIn('timing=allocation.get("timing")', source)
        self.assertIn('_chip("Frequency", _frequency_label(row.get("frequency_per_week")))', view)
        self.assertIn('_chip("Timing", row.get("timing"))', view)

    def test_scope_does_not_add_schema_auth_or_flutter_changes(self):
        files = (
            "components/member_plan_builder_setup.py",
            "components/member_plan_builder_meals_compact.py",
            "components/member_plan_builder_export.py",
            "components/member_plan_builder_exercise.py",
            "components/exercise_member_allocation.py",
            "components/current_member_plan_view.py",
        )
        combined = "\n".join((ROOT / path).read_text() for path in files)
        for forbidden in (
            "ALTER TABLE",
            "CREATE POLICY",
            "DROP POLICY",
            "auth.users",
            "flutter/",
        ):
            self.assertNotIn(forbidden, combined)


if __name__ == "__main__":
    unittest.main()
