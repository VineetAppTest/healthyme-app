from __future__ import annotations

import contextlib
import pathlib
import types
import unittest

from components import admin_exercise_repair_runtime as admin_runtime
from components import member_daily_log_native_tab_persistence as member_runtime


ROOT = pathlib.Path(__file__).resolve().parents[1]
BOOTSTRAP = ROOT / "components" / "__init__.py"


class _Context:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False


class ExerciseLiveRepairTests(unittest.TestCase):
    def test_bootstrap_retires_second_server_side_daily_log_wrapper(self):
        source = BOOTSTRAP.read_text(encoding="utf-8")
        self.assertNotIn("install_member_daily_log_section_runtime", source)
        self.assertIn("install_admin_exercise_repair_runtime()", source)
        self.assertIn("install_member_daily_log_native_tab_persistence()", source)
        self.assertLess(
            source.index("install_admin_exercise_repair_runtime()"),
            source.index("install_member_daily_log_native_tab_persistence()"),
        )

    def test_member_daily_log_bypasses_legacy_wrappers_only_for_journal_tabs(self):
        calls = []

        def native_tabs(labels, *args, **kwargs):
            calls.append(("native", tuple(labels)))
            return [contextlib.nullcontext() for _ in labels]

        def legacy_tabs(labels, *args, **kwargs):
            calls.append(("legacy", tuple(labels)))
            return native_tabs(labels, *args, **kwargs)

        legacy_tabs.__wrapped__ = native_tabs

        def admin_tabs(labels, *args, **kwargs):
            calls.append(("admin", tuple(labels)))
            return legacy_tabs(labels, *args, **kwargs)

        admin_tabs.__wrapped__ = legacy_tabs

        html_calls = []
        fake_st = types.SimpleNamespace(
            tabs=admin_tabs,
            html=lambda body, **kwargs: html_calls.append((body, kwargs)),
        )
        original_st = member_runtime.st
        original_page_check = member_runtime._page_in_stack
        try:
            member_runtime.st = fake_st
            member_runtime._page_in_stack = lambda: True
            member_runtime.install_member_daily_log_native_tab_persistence()

            result = fake_st.tabs(["Food Journal", "Exercise Journal"])
            self.assertEqual(len(result), 2)
            self.assertEqual(calls[0][0], "native")
            self.assertTrue(html_calls)
            script = html_calls[0][0]
            self.assertIn("sessionStorage", script)
            self.assertIn("MutationObserver", script)
            self.assertIn("Exercise Journal", script)

            calls.clear()
            fake_st.tabs(["One", "Two"])
            self.assertEqual(calls[0][0], "admin")
        finally:
            member_runtime.st = original_st
            member_runtime._page_in_stack = original_page_check

    def test_admin_success_survives_rerun_and_blank_field_is_not_rendered(self):
        rendered_success = []
        text_calls = []

        def base_tabs(labels, *args, **kwargs):
            return [_Context() for _ in labels]

        def base_success(body, *args, **kwargs):
            rendered_success.append(str(body))

        def base_text_input(label, *args, **kwargs):
            text_calls.append((label, kwargs.get("key")))
            return kwargs.get("value", "")

        markdown_calls = []
        fake_st = types.SimpleNamespace(
            tabs=base_tabs,
            success=base_success,
            text_input=base_text_input,
            markdown=lambda body, **kwargs: markdown_calls.append(str(body)),
            session_state={},
        )
        original_st = admin_runtime.st
        original_page_check = admin_runtime._page_in_stack
        try:
            admin_runtime.st = fake_st
            admin_runtime._page_in_stack = lambda: True
            admin_runtime.install_admin_exercise_repair_runtime()

            fake_st.success("Exercise saved.")
            self.assertEqual(rendered_success, [])
            self.assertEqual(
                fake_st.session_state[admin_runtime._SECTION_STATE],
                "Add Exercise",
            )

            contexts = fake_st.tabs(list(admin_runtime._LABELS))
            with contexts[1]:
                pass
            self.assertTrue(any("Exercise saved." in body for body in markdown_calls))
            self.assertNotIn(admin_runtime._FLASH_KEY, fake_st.session_state)

            hidden_value = fake_st.text_input(
                "",
                value="125",
                key="new_exercise_v93_hidden_calories_v96",
            )
            self.assertEqual(hidden_value, "125")
            self.assertEqual(text_calls, [])

            visible_value = fake_st.text_input(
                "Difficulty",
                value="Beginner",
                key="new_exercise_v93_difficulty",
            )
            self.assertEqual(visible_value, "Beginner")
            self.assertEqual(text_calls, [("Difficulty", "new_exercise_v93_difficulty")])
        finally:
            admin_runtime.st = original_st
            admin_runtime._page_in_stack = original_page_check


if __name__ == "__main__":
    unittest.main()
