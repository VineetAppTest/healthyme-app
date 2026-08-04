from __future__ import annotations

import unittest
from pathlib import Path

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

    def test_member_home_runtime_only_sizes_controls_and_mobile_row(self):
        calls = []

        def base_topbar(title, *args, **kwargs):
            calls.append(title)

        ui_common.topbar = base_topbar

        runtime.install_member_home_global_header_runtime()
        ui_common.topbar("Member Home", "Member subtitle", "Member experience")

        self.assertEqual(calls, ["Member Home"])
        rendered_css = "\n".join(self.fake_st.markdown_calls)
        self.assertIn("hm-member-home-global-header-v6", rendered_css)
        self.assertIn("hm-member-identity-pill", rendered_css)
        self.assertIn("hm-top-profile-anchor", rendered_css)
        self.assertIn("hm-top-logout-anchor", rendered_css)
        self.assertIn("@media(max-width:760px)", rendered_css)
        self.assertIn(
            "grid-template-columns:minmax(0,1fr) 2.55rem 4.65rem!important",
            rendered_css,
        )
        self.assertIn("text-overflow:ellipsis!important", rendered_css)
        self.assertNotIn("block-container:has", rendered_css)
        self.assertNotIn(".hero-shell", rendered_css)
        self.assertNotIn("margin-top:-", rendered_css)

    def test_member_home_page_uses_one_structural_header_shell(self):
        source = Path("pages/02_Member_Home.py").read_text()

        self.assertIn("hm-member-home-local-style-v3", source)
        self.assertIn("hm-member-home-root-anchor", source)
        self.assertIn("with st.container():", source)
        self.assertIn("padding-top:.55rem!important", source)
        self.assertIn("gap:.28rem!important", source)
        self.assertNotIn("html body .block-container{padding-top:0", source)
        self.assertNotIn("margin:0 0 .52rem 0!important", source)

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
