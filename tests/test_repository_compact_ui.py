from __future__ import annotations

import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAGES = {
    "Recipe": ROOT / "pages" / "15_Admin_Recipe_Manager.py",
    "Exercise": ROOT / "pages" / "16_Admin_Exercise_Manager.py",
    "Supplement": ROOT / "pages" / "39_Admin_Supplement_Manager.py",
}
HELPER = ROOT / "components" / "repository_page_ui.py"


def text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class RepositoryCompactUiTests(unittest.TestCase):
    def test_pages_and_helper_compile(self):
        for path in [*PAGES.values(), HELPER]:
            ast.parse(text(path), filename=str(path))

    def test_repository_actions_are_compact_and_inline(self):
        for path in PAGES.values():
            source = text(path)
            self.assertIn('st.columns([5.8, 0.72, 0.82], gap="small")', source)
            self.assertIn('"Edit",', source)
            self.assertIn('"Delete",', source)
            self.assertIn('border-radius:999px!important', source)
            self.assertIn('white-space:nowrap!important', source)

    def test_edit_disclosures_are_page_owned_single_controls(self):
        helper = text(HELPER)
        self.assertIn('symbol = "⊖" if is_open else "⊕"', helper)
        self.assertIn('f"{symbol}  {label}"', helper)
        self.assertNotIn("st.expander", helper)

        for name, path in PAGES.items():
            source = text(path)
            self.assertIn(f'f"Edit {name} ·', source)
            self.assertIn("render_repository_disclosure", source)
            self.assertNotIn("st.expander", source)

    def test_add_and_edit_use_same_crisp_form_panel(self):
        helper = text(HELPER)
        self.assertIn("min-height:1.9rem!important", helper)
        self.assertIn("min-height:52px!important", helper)
        self.assertIn("height:52px!important", helper)
        self.assertIn("font-size:.7rem!important", helper)
        self.assertIn("font-size:.66rem!important", helper)
        self.assertNotIn("min-height:1.72rem", helper)
        self.assertNotIn("height:42px", helper)

        recipe = text(PAGES["Recipe"])
        exercise = text(PAGES["Exercise"])
        supplement = text(PAGES["Supplement"])
        for source in (recipe, exercise, supplement):
            self.assertGreaterEqual(source.count("repository_form_panel()"), 2)
            self.assertIn('gap="small"', source)
            self.assertIn('"Save Changes",', source)
            self.assertIn('"Close",', source)

        self.assertIn('st.markdown("#### Nutrition")', recipe)
        self.assertIn('st.markdown("#### Preparation")', recipe)
        self.assertIn('st.markdown("#### Guidance / Benefits")', exercise)
        self.assertIn('st.markdown("#### Tags")', exercise)
        self.assertGreaterEqual(supplement.count('st.markdown("#### Basic Details")'), 2)
        self.assertGreaterEqual(supplement.count('st.markdown("#### Timing")'), 2)
        self.assertGreaterEqual(supplement.count('st.markdown("#### Instructions")'), 2)

    def test_inactive_repository_uses_direct_disclosure_pattern(self):
        for path in PAGES.values():
            source = text(path)
            self.assertIn('f"Inactive Repository Items (', source)
            self.assertIn("render_repository_disclosure", source)
            self.assertIn("repository_inactive_panel()", source)
            self.assertNotIn("st.expander", source)

    def test_safe_delete_and_form_hygiene_remain(self):
        recipe = text(PAGES["Recipe"])
        exercise = text(PAGES["Exercise"])
        supplement = text(PAGES["Supplement"])

        self.assertIn("_safe_delete_recipe", recipe)
        self.assertNotIn("df.drop(", recipe)
        self.assertNotIn("reset_index", recipe)
        self.assertIn("set_exercise_repository_status", exercise)
        self.assertIn("set_supplement_repository_status", supplement)
        self.assertIn('with st.form("hm_v1023a_add_supplement_form", clear_on_submit=True)', supplement)
        self.assertIn('key="hm_v1023a_add_frequency"', supplement)


if __name__ == "__main__":
    unittest.main()
