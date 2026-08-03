from __future__ import annotations

import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "components" / "repository_exclusive_tabs_runtime.py"
BOOTSTRAP = ROOT / "components" / "__init__.py"


def text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class RepositoryExclusiveTabsRuntimeTests(unittest.TestCase):
    def test_runtime_and_bootstrap_compile(self):
        ast.parse(text(RUNTIME), filename=str(RUNTIME))
        ast.parse(text(BOOTSTRAP), filename=str(BOOTSTRAP))

    def test_runtime_is_limited_to_repository_pages(self):
        source = text(RUNTIME)
        self.assertIn("pages/15_Admin_Recipe_Manager.py", source)
        self.assertIn("pages/16_Admin_Exercise_Manager.py", source)
        self.assertIn("pages/39_Admin_Supplement_Manager.py", source)
        self.assertNotIn("pages/18_Daily_Log.py", source)

    def test_native_tabs_are_replaced_by_one_exclusive_selector(self):
        source = text(RUNTIME)
        self.assertIn("current_segmented_control", source)
        self.assertIn('options[0] != "Current Repository"', source)
        self.assertIn("_RepositorySection(", source)
        self.assertIn("active=selected == option", source)
        self.assertIn("st.tabs = tabs_with_exclusive_repository_section", source)

    def test_inactive_section_suppresses_widgets_and_repository_reads(self):
        source = text(RUNTIME)
        self.assertIn("_SUPPRESSED", source)
        self.assertIn('patch("load", empty_recipe_frame)', source)
        self.assertIn('patch("list_exercise_repository"', source)
        self.assertIn('"supplement_repository_counts"', source)
        self.assertIn('patch("list_supplement_repository"', source)
        self.assertIn("return [_NullBlock()", source)
        self.assertIn("return False", source)

    def test_disclosure_and_header_spacing_corrections_are_present(self):
        source = text(RUNTIME)
        self.assertIn("summary > :not(p):not(:has(p))", source)
        self.assertIn("color:transparent!important", source)
        self.assertIn("margin:.38rem 0 .38rem!important", source)
        self.assertIn("background:#F8F3E7!important", source)
        self.assertIn("border-left:3px solid #E3C98E!important", source)
        self.assertIn("font-size:.80rem!important", source)
        self.assertIn("min-height:58px!important", source)
        self.assertIn("hm-repository-exclusive-switch", source)

    def test_bootstrap_installs_runtime_after_layout_runtime(self):
        bootstrap = text(BOOTSTRAP)
        self.assertIn(
            "from components.repository_exclusive_tabs_runtime import (",
            bootstrap,
        )
        self.assertIn("install_repository_exclusive_tabs_runtime()", bootstrap)
        self.assertGreater(
            bootstrap.rfind("install_repository_exclusive_tabs_runtime()"),
            bootstrap.rfind("install_repository_layout_correction_runtime()"),
        )


if __name__ == "__main__":
    unittest.main()
