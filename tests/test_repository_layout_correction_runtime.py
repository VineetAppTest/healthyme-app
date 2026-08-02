from __future__ import annotations

import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / "components/repository_page_ui.py"
BOOTSTRAP = ROOT / "components/__init__.py"
PAGES = [
    ROOT / "pages/15_Admin_Recipe_Manager.py",
    ROOT / "pages/16_Admin_Exercise_Manager.py",
    ROOT / "pages/39_Admin_Supplement_Manager.py",
]


def text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class RepositoryDirectPageUiTests(unittest.TestCase):
    def test_helper_bootstrap_and_pages_compile(self):
        for path in [HELPER, BOOTSTRAP, *PAGES]:
            ast.parse(text(path), filename=str(path))

    def test_repository_pages_do_not_use_streamlit_expanders(self):
        for page in PAGES:
            source = text(page)
            self.assertNotIn("st.expander", source, page.name)
            self.assertIn("render_repository_disclosure", source, page.name)
            self.assertGreaterEqual(source.count("repository_form_panel()"), 2, page.name)
            self.assertIn("repository_inactive_panel()", source, page.name)

    def test_disclosure_is_page_owned_and_has_one_inline_symbol(self):
        source = text(HELPER)
        self.assertIn('symbol = "⊖" if is_open else "⊕"', source)
        self.assertIn('f"{symbol}  {label}"', source)
        self.assertNotIn("st.expander", source)

    def test_repository_rows_have_breathing_space(self):
        source = text(HELPER)
        self.assertIn(':has(.hm-repo-row)', source)
        self.assertIn(':has(.hm-sup-row)', source)
        self.assertIn('margin-bottom:.52rem!important', source)
        self.assertIn('margin:.46rem 0 .22rem!important', source)

    def test_add_and_edit_share_compact_readable_dimensions(self):
        source = text(HELPER)
        self.assertIn("max-width:940px!important", source)
        self.assertIn("min-height:2rem!important", source)
        self.assertIn("min-height:54px!important", source)
        self.assertIn("font-size:.75rem!important", source)
        self.assertNotIn("min-height:1.72rem", source)
        self.assertNotIn("height:42px", source)

    def test_approved_sections_are_directly_rendered(self):
        recipe, exercise, supplement = [text(page) for page in PAGES]
        for heading in ("#### Core Details", "#### Nutrition", "#### Preparation", "#### Image"):
            self.assertIn(heading, recipe)
        for heading in ("#### Core Fields", "#### Guidance / Benefits", "#### Tags", "#### Image"):
            self.assertIn(heading, exercise)
        for heading in ("#### Basic Details", "#### Timing", "#### Instructions"):
            self.assertGreaterEqual(supplement.count(heading), 2)

    def test_legacy_repository_layout_runtime_is_not_installed(self):
        bootstrap = text(BOOTSTRAP)
        self.assertNotIn("install_repository_layout_correction_runtime", bootstrap)


if __name__ == "__main__":
    unittest.main()
