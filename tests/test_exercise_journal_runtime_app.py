import pathlib
import tempfile
import unittest

from streamlit.testing.v1 import AppTest


ROOT = pathlib.Path(__file__).resolve().parents[1]
RUNTIME_PATH = ROOT / "components" / "member_daily_log_native_tab_persistence.py"


class ExerciseJournalRuntimeAppTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

    def _app(self):
        script = f'''
import importlib.util
import streamlit as st

spec = importlib.util.spec_from_file_location(
    "member_daily_log_exclusive_runtime_app_test",
    {str(RUNTIME_PATH)!r},
)
runtime = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runtime)
runtime.install_member_daily_log_native_tab_persistence()


def _render_food_journal(user_id):
    st.text("FOOD_PANEL_VISIBLE")
    st.selectbox("Food status", ["Not recorded", "Recorded"], key="food_status")


def _render_exercise_journal(user_id):
    st.text("EXERCISE_PANEL_VISIBLE")
    st.selectbox("Exercise status", ["Planned", "Completed"], key="exercise_status")
    if st.button("Save Progress", key="exercise_save_progress"):
        # Reproduce an explicit save/load pipeline that removes the public
        # page-scoped selector before calling st.rerun().
        st.session_state.pop("hm_daily_log_active_journal", None)
        st.rerun()


def _render_supplement_journal(user_id):
    st.text("SUPPLEMENT_PANEL_VISIBLE")


food_tab, exercise_tab, supplement_tab = st.tabs(
    ["Food Journal", "Exercise Journal", "Supplement Journal"]
)
with food_tab:
    _render_food_journal("member-1")
with exercise_tab:
    _render_exercise_journal("member-1")
with supplement_tab:
    _render_supplement_journal("member-1")
'''
        pages_dir = pathlib.Path(self.temp_dir.name) / "pages"
        pages_dir.mkdir(parents=True, exist_ok=True)
        page_path = pages_dir / "18_Daily_Log.py"
        page_path.write_text(script, encoding="utf-8")
        return AppTest.from_file(str(page_path), default_timeout=10).run()

    @staticmethod
    def _text_values(app):
        return [element.value for element in app.text]

    @staticmethod
    def _button(app, label):
        for button in app.button:
            if button.label == label:
                return button
        raise AssertionError(f"Button not found: {label}")

    def _assert_exercise_only(self, app):
        self.assertIn("EXERCISE_PANEL_VISIBLE", self._text_values(app))
        self.assertNotIn("FOOD_PANEL_VISIBLE", self._text_values(app))
        self.assertNotIn("SUPPLEMENT_PANEL_VISIBLE", self._text_values(app))
        self.assertEqual([box.label for box in app.selectbox], ["Exercise status"])

    def test_exercise_selection_survives_dropdown_and_explicit_save_reruns(self):
        app = self._app()
        self.assertIn("FOOD_PANEL_VISIBLE", self._text_values(app))
        self.assertNotIn("EXERCISE_PANEL_VISIBLE", self._text_values(app))
        self.assertEqual([box.label for box in app.selectbox], ["Food status"])

        app = self._button(app, "Exercise Journal").click().run()
        self._assert_exercise_only(app)

        app = app.selectbox[0].select("Completed").run()
        self._assert_exercise_only(app)
        self.assertEqual(app.selectbox[0].value, "Completed")

        app = self._button(app, "Save Progress").click().run()
        self._assert_exercise_only(app)
        self.assertEqual(app.selectbox[0].value, "Completed")


if __name__ == "__main__":
    unittest.main()
