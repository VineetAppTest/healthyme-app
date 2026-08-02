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


def text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class RepositoryCompactUiTests(unittest.TestCase):
    def test_pages_compile(self):
        for path in PAGES.values():
            ast.parse(text(path), filename=str(path))

    def test_repository_actions_are_compact_and_inline(self):
        for path in PAGES.values():
            source = text(path)
            self.assertIn('st.columns([5.8, 0.72, 0.82], gap="small")', source)
            self.assertIn('"Edit",', source)
            self.assertIn('"Delete",', source)
            self.assertIn('border-radius:999px!important', source)
            self.assertIn('white-space:nowrap!important', source)

    def test_edit_disclosures_are_single_line_plus_minus_controls(self):
        for name, path in PAGES.items():
            source = text(path)
            self.assertIn(f'with st.expander(f"Edit {name} ·', source)
            self.assertIn('summary:before{content:"+"', source)
            self.assertIn('details[open] summary:before{content:"−"', source)
            self.assertIn('summary p{white-space:nowrap!important', source)

    def test_edit_panels_are_compact_and_structured(self):
        recipe = text(PAGES["Recipe"])
        exercise = text(PAGES["Exercise"])
        supplement = text(PAGES["Supplement"])

        for source in (recipe, exercise, supplement):
            self.assertIn('div[data-testid="stExpander"] textarea{min-height:68px!important;}', source)
            self.assertIn('gap="small"', source)
            self.assertIn('"Save Changes",', source)
            self.assertIn('"Close",', source)

        self.assertIn('st.markdown("#### Nutrition")', recipe)
        self.assertIn('st.markdown("#### Preparation")', recipe)
        self.assertIn('detail_left, detail_right = st.columns(2, gap="small")', exercise)
        self.assertIn('basic_name, basic_dose, basic_frequency = st.columns(3, gap="small")', supplement)

    def test_inactive_repository_uses_same_disclosure_pattern(self):
        for path in PAGES.values():
            source = text(path)
            self.assertIn('with st.expander(f"Inactive Repository Items (', source)
            self.assertIn('summary:before{content:"+"', source)
            self.assertIn('details[open] summary:before{content:"−"', source)

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
