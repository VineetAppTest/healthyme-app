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
        runtime.st = self.fake_st

    def tearDown(self):
        runtime.st = self.original_runtime_st
        ui_common.topbar = self.original_topbar

    def test_member_home_collapses_hidden_wrappers_and_hero_gap(self):
        calls = []

        def base_topbar(title, *args, **kwargs):
            calls.append(title)

        ui_common.topbar = base_topbar

        runtime.install_member_home_global_header_runtime()
        ui_common.topbar("Member Home", "Member subtitle", "Member experience")

        self.assertEqual(calls, ["Member Home"])
        rendered_css = "\n".join(self.fake_st.markdown_calls)
        self.assertIn("hm-member-home-global-header-v3", rendered_css)
        self.assertIn("hm-member-identity-pill", rendered_css)
        self.assertIn("hm-top-profile-anchor", rendered_css)
        self.assertIn("hm-top-logout-anchor", rendered_css)
        self.assertIn(
            'div[data-testid="stElementContainer"]:has(.hm-top-profile-anchor)',
            rendered_css,
        )
        self.assertIn(
            'div[data-testid="stElementContainer"]:has(.hm-top-logout-anchor)',
            rendered_css,
        )
        self.assertIn(
            'div[data-testid="column"] > div[data-testid="stVerticalBlock"]:has(.hm-top-profile-anchor)',
            rendered_css,
        )
        self.assertIn("gap:0!important", rendered_css)
        self.assertIn("min-height:2.46rem", rendered_css)
        self.assertIn(
            'div[data-testid="stElementContainer"]:has(.hero-shell)',
            rendered_css,
        )
        self.assertIn("margin-top:-.72rem!important", rendered_css)
        self.assertNotIn("min-height:2.84rem", rendered_css)

    def test_other_pages_keep_their_existing_header_sequence(self):
        calls = []

        def base_topbar(title, *args, **kwargs):
            calls.append(title)

        ui_common.topbar = base_topbar

        runtime.install_member_home_global_header_runtime()
        ui_common.topbar("Daily Log", "Capture updates", "Member tracker")

        self.assertEqual(calls, ["Daily Log"])
        self.assertEqual(self.fake_st.markdown_calls, [])

    def test_installer_is_idempotent(self):
        calls = []

        def base_topbar(title, *args, **kwargs):
            calls.append(title)

        ui_common.topbar = base_topbar

        runtime.install_member_home_global_header_runtime()
        installed = ui_common.topbar
        runtime.install_member_home_global_header_runtime()

        self.assertIs(ui_common.topbar, installed)
        ui_common.topbar("Member Home")
        self.assertEqual(calls, ["Member Home"])


if __name__ == "__main__":
    unittest.main()
