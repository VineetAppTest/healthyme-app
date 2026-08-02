from __future__ import annotations

import ast
import importlib.util
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
            'div[data-testid="stElementContainer"]:has(style#hm-streamlit-toolbar-cleanup-v4)',
            self.toolbar_source,
        )
        self.assertIn("display: none !important", self.toolbar_source)
        self.assertIn("height: 0 !important", self.toolbar_source)

    def test_idle_reconnect_guard_targets_top_document_and_future_controls(self) -> None:
        expected_tokens = (
            "window.top || window",
            "doc.head || doc.documentElement",
            "__healthymeToolbarReconnectGuardV4",
            "MutationObserver",
            "observer.observe(doc.documentElement, { childList: true, subtree: true })",
            "previous.observer.disconnect()",
            "hostWindow.setTimeout(apply, delay)",
            "unsafe_allow_javascript=True",
        )
        for token in expected_tokens:
            self.assertIn(token, self.toolbar_source)

    def test_reconnect_guard_is_rendered_after_static_css(self) -> None:
        wrapper_start = self.toolbar_source.index("def set_page_config_without_owner_toolbar")
        css_call = self.toolbar_source.index("_render_global_toolbar_css()", wrapper_start)
        guard_call = self.toolbar_source.index("_render_toolbar_reconnect_guard()", wrapper_start)
        self.assertLess(css_call, guard_call)

    def test_every_page_config_call_renders_static_and_reconnect_guards(self) -> None:
        import streamlit as st

        spec = importlib.util.spec_from_file_location(
            "hm_toolbar_cleanup_runtime_contract",
            TOOLBAR,
        )
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)

        base_attr = module._BASE_CONFIG_ATTR
        had_base = hasattr(st, base_attr)
        previous_base = getattr(st, base_attr, None)
        previous_config = st.set_page_config
        previous_markdown = st.markdown
        previous_html = st.html
        calls = []

        def fake_config(*args, **kwargs):
            calls.append(("config", args, kwargs))
            return "configured"

        def fake_markdown(body, *args, **kwargs):
            calls.append(("markdown", body, kwargs))
            return "markdown"

        def fake_html(body, *args, **kwargs):
            calls.append(("html", body, kwargs))
            return "html"

        try:
            st.set_page_config = fake_config
            st.markdown = fake_markdown
            st.html = fake_html
            if hasattr(st, base_attr):
                delattr(st, base_attr)

            module.install_streamlit_toolbar_cleanup()
            self.assertEqual(st.set_page_config(page_title="HealthyMe"), "configured")
            self.assertEqual(st.set_page_config(page_title="HealthyMe again"), "configured")

            static_calls = [
                call for call in calls
                if call[0] == "markdown" and "hm-streamlit-toolbar-cleanup-v4" in call[1]
            ]
            reconnect_calls = [
                call for call in calls
                if call[0] == "html" and "hm-streamlit-toolbar-reconnect-guard-v4" in call[1]
            ]
            self.assertEqual(len(static_calls), 2)
            self.assertEqual(len(reconnect_calls), 2)
            for call in reconnect_calls:
                self.assertTrue(call[2].get("unsafe_allow_javascript"))
        finally:
            st.set_page_config = previous_config
            st.markdown = previous_markdown
            st.html = previous_html
            if had_base:
                setattr(st, base_attr, previous_base)
            elif hasattr(st, base_attr):
                delattr(st, base_attr)

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
