from __future__ import annotations

import unittest

from components import member_home_global_header_runtime as runtime
from components import ui_common


class _FakeStreamlit:
    def __init__(self):
        self.markdown_calls = []

    def markdown(self, body, *args, **kwargs):
        self.markdown_calls.append(str(body))


class MemberHomeGlobalHeaderRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.fake_st = _FakeStreamlit()
        self.original_runtime_st = runtime.st
        self.original_topbar = ui_common.topbar
        self.original_utility = ui_common.utility_logout_bar
        runtime.st = self.fake_st

    def tearDown(self):
        runtime.st = self.original_runtime_st
        ui_common.topbar = self.original_topbar
        ui_common.utility_logout_bar = self.original_utility

    def test_member_home_replaces_local_row_with_shared_global_header(self):
        events = []

        def base_topbar(title, *args, **kwargs):
            events.append(("topbar", title))

        def shared_utility():
            events.append(("utility", None))

        ui_common.topbar = base_topbar
        ui_common.utility_logout_bar = shared_utility

        runtime.install_member_home_global_header_runtime()
        ui_common.topbar("Member Home", "Member subtitle", "Member experience")

        self.assertEqual(
            events,
            [("utility", None), ("topbar", "Member Home")],
        )
        rendered_css = "\n".join(self.fake_st.markdown_calls)
        self.assertIn("hm-member-home-global-header-v1", rendered_css)
        self.assertIn("hm-member-identity-pill", rendered_css)
        self.assertIn("display:none", rendered_css)
        self.assertIn(".utility-bar", rendered_css)
        self.assertIn(".hero-shell", rendered_css)

    def test_other_pages_keep_their_existing_header_sequence(self):
        events = []

        def base_topbar(title, *args, **kwargs):
            events.append(("topbar", title))

        def shared_utility():
            events.append(("utility", None))

        ui_common.topbar = base_topbar
        ui_common.utility_logout_bar = shared_utility

        runtime.install_member_home_global_header_runtime()
        ui_common.topbar("Daily Log", "Capture updates", "Member tracker")

        self.assertEqual(events, [("topbar", "Daily Log")])
        self.assertEqual(self.fake_st.markdown_calls, [])

    def test_installer_is_idempotent(self):
        calls = []

        def base_topbar(title, *args, **kwargs):
            calls.append(title)

        ui_common.topbar = base_topbar
        ui_common.utility_logout_bar = lambda: None

        runtime.install_member_home_global_header_runtime()
        installed = ui_common.topbar
        runtime.install_member_home_global_header_runtime()

        self.assertIs(ui_common.topbar, installed)
        ui_common.topbar("Member Home")
        self.assertEqual(calls, ["Member Home"])


if __name__ == "__main__":
    unittest.main()
