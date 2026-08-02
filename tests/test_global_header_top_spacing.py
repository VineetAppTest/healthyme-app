from __future__ import annotations

import ast
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
TOOLBAR = ROOT / "components" / "streamlit_toolbar_cleanup.py"
COMPONENT_BOOTSTRAP = ROOT / "components" / "__init__.py"


class GlobalHeaderTopSpacingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.toolbar_source = TOOLBAR.read_text(encoding="utf-8")
        cls.bootstrap_source = COMPONENT_BOOTSTRAP.read_text(encoding="utf-8")

    def test_changed_module_compiles(self) -> None:
        ast.parse(self.toolbar_source, filename=str(TOOLBAR))

    def test_normal_style_only_markup_uses_zero_height_renderer(self) -> None:
        self.assertIn("_STYLE_ONLY_MARKUP.fullmatch(body)", self.toolbar_source)
        self.assertIn("return html_renderer(body)", self.toolbar_source)
        self.assertIn("return current(body, *args, **kwargs)", self.toolbar_source)

    def test_zero_height_renderer_installs_before_page_config_wrapper(self) -> None:
        installer_at = self.toolbar_source.index("_install_zero_height_style_renderer()")
        page_config_at = self.toolbar_source.index("current = st.set_page_config")
        self.assertLess(installer_at, page_config_at)

    def test_owner_toolbar_css_uses_outer_global_renderer(self) -> None:
        self.assertIn("def _render_global_toolbar_css()", self.toolbar_source)
        self.assertIn(
            'getattr(st.markdown, "_hm_original_markdown", st.markdown)',
            self.toolbar_source,
        )
        self.assertIn("original_markdown(_TOOLBAR_CSS, unsafe_allow_html=True)", self.toolbar_source)
        self.assertIn("_render_global_toolbar_css()", self.toolbar_source)
        self.assertIn("install_streamlit_toolbar_cleanup()", self.bootstrap_source)

    def test_visible_owner_controls_are_suppressed(self) -> None:
        expected_selectors = (
            'button[aria-label="Share"]',
            'button[aria-label*="favorite" i]',
            'button[aria-label*="edit" i]',
            'button[aria-label*="more" i]',
            '[data-testid="stAppDeployButton"]',
            '[data-testid="stShareButton"]',
            '[data-testid="stFavoriteButton"]',
            '[data-testid="stEditButton"]',
            '[data-testid*="Toolbar"]',
        )
        for selector in expected_selectors:
            self.assertIn(selector, self.toolbar_source)

    def test_global_toolbar_stylesheet_does_not_restore_top_gap(self) -> None:
        self.assertIn(
            'div[data-testid="stElementContainer"]:has(style#hm-streamlit-toolbar-cleanup-v3)',
            self.toolbar_source,
        )
        self.assertIn("display: none !important", self.toolbar_source)
        self.assertIn("height: 0 !important", self.toolbar_source)

    def test_auth_and_navigation_are_not_modified(self) -> None:
        forbidden = (
            "logout_current_user",
            "st.switch_page",
            "st.session_state",
            "supabase",
            "require_admin",
            "require_member",
        )
        for token in forbidden:
            self.assertNotIn(token, self.toolbar_source)


if __name__ == "__main__":
    unittest.main()
