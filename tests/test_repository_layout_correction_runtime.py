from __future__ import annotations

import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "components" / "repository_layout_correction_runtime.py"
BOOTSTRAP = ROOT / "components" / "__init__.py"


def text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class RepositoryLayoutCorrectionRuntimeTests(unittest.TestCase):
    def test_runtime_and_bootstrap_compile(self):
        ast.parse(text(RUNTIME), filename=str(RUNTIME))
        ast.parse(text(BOOTSTRAP), filename=str(BOOTSTRAP))

    def test_runtime_is_limited_to_three_repository_pages(self):
        source = text(RUNTIME)
        self.assertIn("pages/15_Admin_Recipe_Manager.py", source)
        self.assertIn("pages/16_Admin_Exercise_Manager.py", source)
        self.assertIn("pages/39_Admin_Supplement_Manager.py", source)
        self.assertNotIn("pages/18_Daily_Log.py", source)

    def test_repository_cards_are_sharper_and_vertically_aligned(self):
        source = text(RUNTIME)
        self.assertIn("align-items:center!important", source)
        self.assertIn("max-width:900px!important", source)
        self.assertIn("flex:0 1 60%!important", source)
        self.assertIn("flex:0 0 70px!important", source)
        self.assertIn("flex:0 0 78px!important", source)
        self.assertIn("min-height:2.18rem!important", source)
        self.assertIn("padding:.3rem .52rem!important", source)

    def test_native_disclosure_glyph_wrapper_is_removed(self):
        source = text(RUNTIME)
        self.assertIn("summary::-webkit-details-marker{display:none!important;}", source)
        self.assertIn('summary::marker{content:""!important;display:none!important;}', source)
        self.assertIn('summary [data-testid="stExpanderToggleIcon"]', source)
        self.assertIn("summary>span:first-child", source)
        self.assertIn("summary>div:first-child:has(svg)", source)
        self.assertIn("overflow:visible!important", source)
        self.assertIn("text-overflow:clip!important", source)

    def test_add_and_edit_forms_use_approved_sections(self):
        source = text(RUNTIME)
        for heading in (
            "#### Core Details",
            "#### Core Fields",
            "#### Guidance / Benefits",
            "#### Tags",
            "#### Basic Details",
            "#### Timing",
            "#### Instructions",
        ):
            self.assertIn(heading, source)

    def test_add_and_edit_forms_are_materially_more_compact(self):
        source = text(RUNTIME)
        self.assertIn('div[data-baseweb="tab-panel"]{', source)
        self.assertIn("max-width:940px!important", source)
        self.assertIn("gap:.16rem!important", source)
        self.assertIn("font-size:.62rem!important", source)
        self.assertIn("min-height:1.72rem!important", source)
        self.assertIn("min-height:42px!important", source)
        self.assertIn("height:42px!important", source)
        self.assertIn("padding:.42rem .52rem!important", source)
        self.assertIn('border-left:3px solid #D4A72C!important', source)
        self.assertIn('[data-testid="stFileUploaderDropzone"]', source)

    def test_runtime_is_installed_outermost(self):
        bootstrap = text(BOOTSTRAP)
        self.assertIn(
            "from components.repository_layout_correction_runtime import (",
            bootstrap,
        )
        self.assertIn("install_repository_layout_correction_runtime()", bootstrap)
        self.assertGreater(
            bootstrap.rfind("install_repository_layout_correction_runtime()"),
            bootstrap.rfind("install_member_home_global_header_runtime()"),
        )


if __name__ == "__main__":
    unittest.main()
