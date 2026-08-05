from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SETUP = ROOT / "components" / "member_plan_builder_setup.py"


class MemberPlanSetupRuntimeFixTests(unittest.TestCase):
    def test_setup_file_compiles(self):
        compile(SETUP.read_text(encoding="utf-8"), str(SETUP), "exec")

    def test_selector_changes_are_deferred_until_before_widget_creation(self):
        source = SETUP.read_text(encoding="utf-8")
        self.assertIn('st.session_state[_SELECTOR_NEXT_KEY] = plan_id', source)
        apply_at = source.index("_apply_queued_plan_selector(selector_options, loaded_id)")
        widget_at = source.index("selected_id = select_col.selectbox(")
        self.assertLess(apply_at, widget_at)
        handler = source[
            source.index("def _handle_plan_selection") : source.index(
            "def _clone_meal_profile"
            )
        ]
        self.assertNotIn("st.session_state[_SELECTOR_KEY] =", handler)

    def test_setup_header_and_control_row_are_compact(self):
        source = SETUP.read_text(encoding="utf-8")
        self.assertNotIn(
            "Select a plan and it loads automatically. Keep only the information needed",
            source,
        )
        self.assertIn('label_visibility="collapsed"', source)
        self.assertIn('vertical_alignment="bottom"', source)


if __name__ == "__main__":
    unittest.main()
