from __future__ import annotations

import importlib.util
import pathlib
import sys
import types
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "components" / "daily_log_widget_route_preservation.py"
PENDING_KEY = "_hm_h13r9e_pending_rerun_path"


class DailyLogWidgetRoutePreservationTests(unittest.TestCase):
    def setUp(self):
        self.calls = []
        self.fake_streamlit = types.ModuleType("streamlit")
        self.fake_streamlit.session_state = {}

        def make_widget(name):
            def widget(*args, **kwargs):
                self.calls.append((name, args, kwargs))
                return f"{name}-result"

            return widget

        for widget_name in (
            "button",
            "checkbox",
            "date_input",
            "multiselect",
            "number_input",
            "radio",
            "selectbox",
            "slider",
            "text_area",
            "text_input",
            "time_input",
            "toggle",
        ):
            setattr(self.fake_streamlit, widget_name, make_widget(widget_name))

        self.previous_streamlit = sys.modules.get("streamlit")
        sys.modules["streamlit"] = self.fake_streamlit
        spec = importlib.util.spec_from_file_location(
            "hm_daily_log_widget_route_preservation_test_runtime",
            RUNTIME,
        )
        self.runtime = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(self.runtime)
        self.runtime.install_daily_log_widget_route_preservation()

    def tearDown(self):
        if self.previous_streamlit is None:
            sys.modules.pop("streamlit", None)
        else:
            sys.modules["streamlit"] = self.previous_streamlit

    def _last_kwargs(self):
        return self.calls[-1][2]

    def test_status_dropdown_stages_daily_log_before_existing_callback(self):
        callback_calls = []

        def existing_callback(value, *, source):
            callback_calls.append((value, source, self.fake_streamlit.session_state.get(PENDING_KEY)))

        result = self.fake_streamlit.selectbox(
            "Status",
            ["Not Started", "In Progress", "Completed", "Skipped"],
            key="hm_daily_log_exercise_profile_1_2026_08_02_1_status",
            on_change=existing_callback,
            args=("In Progress",),
            kwargs={"source": "status"},
        )

        self.assertEqual(result, "selectbox-result")
        forwarded = self._last_kwargs()
        self.assertNotEqual(forwarded["on_change"], existing_callback)
        self.assertNotIn("args", forwarded)
        self.assertNotIn("kwargs", forwarded)

        forwarded["on_change"]()
        self.assertEqual(
            self.fake_streamlit.session_state[PENDING_KEY],
            "Daily_Log",
        )
        self.assertEqual(
            callback_calls,
            [("In Progress", "status", "Daily_Log")],
        )

    def test_activity_timing_and_text_fields_receive_route_callbacks(self):
        widget_cases = (
            ("selectbox", "hm_daily_log_exercise_profile_1_activity", "on_change"),
            ("selectbox", "hm_daily_log_exercise_profile_1_timing", "on_change"),
            ("text_input", "hm_daily_log_exercise_profile_1_remarks", "on_change"),
            ("date_input", "hm_daily_log_exercise_date", "on_change"),
        )

        for widget_name, key, callback_name in widget_cases:
            self.fake_streamlit.session_state.clear()
            getattr(self.fake_streamlit, widget_name)("Field", key=key)
            callback = self._last_kwargs()[callback_name]
            callback()
            self.assertEqual(
                self.fake_streamlit.session_state[PENDING_KEY],
                "Daily_Log",
                msg=f"{widget_name}:{key} did not preserve Daily Log",
            )

    def test_save_add_remove_and_saved_day_buttons_preserve_route(self):
        keys = (
            "hm_daily_log_exercise_profile_1_save",
            "hm_daily_log_exercise_add_2026_08_02",
            "hm_daily_log_exercise_remove_2026_08_02",
            "hm_h9a4c_load_2026-08-02",
        )
        for key in keys:
            self.fake_streamlit.session_state.clear()
            self.fake_streamlit.button("Action", key=key)
            self._last_kwargs()["on_click"]()
            self.assertEqual(
                self.fake_streamlit.session_state[PENDING_KEY],
                "Daily_Log",
                msg=f"button:{key} did not preserve Daily Log",
            )

    def test_journal_selector_preserves_route_and_original_selection_callback(self):
        selected = []

        def activate(label):
            selected.append(label)

        self.fake_streamlit.button(
            "Exercise Journal",
            key="hm_daily_log_exercise_journal_selector",
            on_click=activate,
            args=("Exercise Journal",),
        )
        self._last_kwargs()["on_click"]()

        self.assertEqual(selected, ["Exercise Journal"])
        self.assertEqual(
            self.fake_streamlit.session_state[PENDING_KEY],
            "Daily_Log",
        )

    def test_unrelated_navigation_control_is_not_modified(self):
        original_callback = lambda: None
        self.fake_streamlit.button(
            "Dashboard",
            key="hm_page_nav_dashboard_daily_log",
            on_click=original_callback,
        )
        forwarded = self._last_kwargs()
        self.assertIs(forwarded["on_click"], original_callback)
        self.assertNotIn(PENDING_KEY, self.fake_streamlit.session_state)

    def test_installation_is_idempotent(self):
        first_selectbox = self.fake_streamlit.selectbox
        self.runtime.install_daily_log_widget_route_preservation()
        self.assertIs(self.fake_streamlit.selectbox, first_selectbox)


if __name__ == "__main__":
    unittest.main()
