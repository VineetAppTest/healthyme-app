from __future__ import annotations

from pathlib import Path


TEST = Path("tests/test_member_home_schedule_presentation.py")
source = TEST.read_text()

old = '''    def test_member_home_header_renders_before_slow_workflow_reads(self):
        source = (ROOT / "pages/02_Member_Home.py").read_text()
        self.assertIn("hm-member-home-local-style-v2", source)
        self.assertIn("padding-top:0!important", source)
        render_start = source.index(
            "# Render the local spacing override and first visible controls"
        )
        workflow_read = source.index("get_workflow(user_id)")
        self.assertLess(render_start, workflow_read)
        self.assertLess(source.index("\\n_render_member_home_css()\\n"), workflow_read)
        self.assertLess(source.index("\\n_render_member_utility_bar()\\n"), workflow_read)
        self.assertLess(source.index('topbar(\\n    "Member Home"'), workflow_read)
        self.assertEqual(source.count("\\n_render_member_home_css()\\n"), 1)
        self.assertEqual(source.count("\\n_render_member_utility_bar()\\n"), 1)
'''
new = '''    def test_member_home_header_renders_before_slow_workflow_reads(self):
        source = (ROOT / "pages/02_Member_Home.py").read_text()
        self.assertIn("hm-member-home-local-style-v3", source)
        self.assertIn("hm-member-home-root-anchor", source)
        self.assertIn("padding-top:.55rem!important", source)
        self.assertIn("gap:.28rem!important", source)
        self.assertNotIn("html body .block-container{padding-top:0", source)
        render_start = source.index(
            "# Render one structural header shell before slower page reads"
        )
        workflow_read = source.index("get_workflow(user_id)")
        self.assertLess(render_start, workflow_read)
        shell_start = source.index("with st.container():", render_start)
        self.assertLess(shell_start, workflow_read)
        self.assertLess(source.index("    _render_member_home_css()", shell_start), workflow_read)
        self.assertLess(source.index("    _render_member_utility_bar()", shell_start), workflow_read)
        self.assertLess(source.index('    topbar(\\n        "Member Home"', shell_start), workflow_read)
        self.assertEqual(source.count("    _render_member_home_css()"), 1)
        self.assertEqual(source.count("    _render_member_utility_bar()"), 1)
'''

if source.count(old) != 1:
    raise RuntimeError("Expected one stale Member Home schedule header contract")
TEST.write_text(source.replace(old, new, 1))
