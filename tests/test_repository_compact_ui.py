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
FORM_PAGES = {
    "Recipe": ROOT / "pages" / "15A_Admin_Recipe_Form.py",
    "Exercise": ROOT / "pages" / "16A_Admin_Exercise_Form.py",
    "Supplement": ROOT / "pages" / "39A_Admin_Supplement_Form.py",
}
REPOSITORY_HELPER = ROOT / "components" / "repository_page_ui.py"
WORKSPACE_HELPER = ROOT / "components" / "repository_workspace_common.py"


def text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class RepositoryCompactUiTests(unittest.TestCase):
    def test_pages_and_helpers_compile(self):
        for path in [*PAGES.values(), *FORM_PAGES.values(), REPOSITORY_HELPER, WORKSPACE_HELPER]:
            ast.parse(text(path), filename=str(path))

    def test_repository_actions_are_compact_and_inline(self):
        for path in PAGES.values():
            source = text(path)
            self.assertIn('st.columns([5.8, 0.72, 0.82], gap="small")', source)
            self.assertIn('"Edit",', source)
            self.assertIn('"Delete",', source)
            self.assertIn('border-radius:999px!important', source)
            self.assertIn('white-space:nowrap!important', source)

    def test_inactive_disclosures_remain_page_owned(self):
        helper = text(REPOSITORY_HELPER)
        self.assertIn('symbol = "⊖" if is_open else "⊕"', helper)
        self.assertIn('f"{symbol}  {label}"', helper)
        self.assertNotIn("st.expander", helper)
        for path in PAGES.values():
            source = text(path)
            self.assertIn('f"Inactive Repository Items (', source)
            self.assertIn("render_repository_disclosure", source)
            self.assertIn("repository_inactive_panel()", source)
            self.assertNotIn("st.expander", source)

    def test_add_and_edit_share_dedicated_workspace_panel(self):
        helper = text(WORKSPACE_HELPER)
        self.assertIn("min-height:2.12rem!important", helper)
        self.assertIn("min-height:64px!important", helper)
        self.assertIn("height:64px!important", helper)
        self.assertIn("font-size:.76rem!important", helper)
        for name, path in PAGES.items():
            source = text(path)
            self.assertIn("workspace_panel()", source)
            self.assertIn('"Save Changes"', source)
            self.assertIn(f'"Add {name}"', source)
            self.assertIn(f'pages/{FORM_PAGES[name].name}', source)

        recipe = text(PAGES["Recipe"])
        exercise = text(PAGES["Exercise"])
        supplement = text(PAGES["Supplement"])
        self.assertIn('st.markdown("#### Nutrition")', recipe)
        self.assertIn('st.markdown("#### Preparation")', recipe)
        self.assertIn('st.markdown("#### Guidance / Benefits")', exercise)
        self.assertIn('st.markdown("#### Tags")', exercise)
        self.assertGreaterEqual(supplement.count('st.markdown("#### Basic Details")'), 2)
        self.assertGreaterEqual(supplement.count('st.markdown("#### Timing")'), 2)
        self.assertGreaterEqual(supplement.count('st.markdown("#### Instructions")'), 2)

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
