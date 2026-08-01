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

    def test_style_only_markup_uses_zero_height_renderer(self) -> None:
        self.assertIn("_STYLE_ONLY_MARKUP.fullmatch(body)", self.toolbar_source)
        self.assertIn("return html_renderer(body)", self.toolbar_source)
        self.assertIn("return current(body, *args, **kwargs)", self.toolbar_source)

    def test_zero_height_renderer_installs_before_page_config_wrapper(self) -> None:
        installer_at = self.toolbar_source.index("_install_zero_height_style_renderer()")
        page_config_at = self.toolbar_source.index("current = st.set_page_config")
        self.assertLess(installer_at, page_config_at)

    def test_toolbar_css_uses_shared_style_renderer(self) -> None:
        self.assertIn("st.markdown(_TOOLBAR_CSS, unsafe_allow_html=True)", self.toolbar_source)
        self.assertIn("install_streamlit_toolbar_cleanup()", self.bootstrap_source)

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
