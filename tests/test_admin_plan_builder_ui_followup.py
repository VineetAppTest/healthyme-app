from __future__ import annotations

import ast
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class AdminPlanBuilderUiFollowupTests(unittest.TestCase):
    def _source(self, path: str) -> str:
        text = (ROOT / path).read_text()
        ast.parse(text)
        return text

    def test_meal_more_details_use_responsive_wrapping(self):
        source = self._source("components/member_plan_builder_meals_compact.py")
        self.assertIn("mpb-responsive-details", source)
        self.assertIn("display:flex;flex-wrap:wrap", source)
        self.assertIn("mpb-responsive-detail-wide", source)
        self.assertIn('"Ingredients", "Preparation", "Repository Instructions"', source)

    def test_publish_log_is_scoped_to_open_profile(self):
        source = self._source("components/member_plan_builder_export.py")
        self.assertIn("def load_profile_plan_events(profile_id: str)", source)
        self.assertIn('.eq("profile_id", clean_profile_id)', source)
        self.assertIn("load_profile_plan_events(profile_id)", source)
        render_start = source.index("def render_publish_log_and_download")
        render_end = source.index("def render_view_member_plan", render_start)
        render_block = source[render_start:render_end]
        self.assertNotIn("load_member_plan_events", render_block)
        self.assertIn('profile_id = clean(profile.get("id"))', render_block)

    def test_exercise_removes_duplicate_summary_and_wraps_details(self):
        source = self._source("components/member_plan_builder_exercise.py")
        start = source.index("def _render_source_details")
        end = source.index("def _render_add_exercise", start)
        detail_block = source[start:end]
        self.assertNotIn("source_summary(", detail_block)
        self.assertIn("mpb-exercise-detail-wrap", detail_block)
        self.assertIn("mpb-exercise-detail-wide", source)
        self.assertIn("flex-wrap:wrap", source)

    def test_supplement_removes_duplicate_details_and_uses_approved_dropdowns(self):
        source = self._source("components/member_plan_builder_supplement.py")
        self.assertNotIn("def _render_source_details", source)
        self.assertNotIn('st.expander("More details"', source)
        for option in (
            "Once",
            "Ten times",
            "Morning",
            "Before Bed",
            "After Meals",
        ):
            self.assertIn(f'"{option}"', source)
        self.assertGreaterEqual(source.count('.selectbox(\n            "Frequency"'), 2)
        self.assertGreaterEqual(source.count('.selectbox(\n            "Timing"'), 2)
        self.assertIn("_options_with_current", source)

    def test_scope_does_not_touch_auth_schema_or_member_surfaces(self):
        workflow = (ROOT / ".github/workflows/admin-plan-builder-ui-followup-validation.yml").read_text()
        for forbidden in (
            "components/auth",
            "supabase/migrations",
            "pages/02_Member_Home.py",
            "flutter/",
        ):
            self.assertNotIn(forbidden, workflow)


if __name__ == "__main__":
    unittest.main()
