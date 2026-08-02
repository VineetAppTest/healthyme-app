from __future__ import annotations

import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
UI = ROOT / "components" / "repository_page_ui.py"
PAGES = {
    "recipe": ROOT / "pages" / "15_Admin_Recipe_Manager.py",
    "exercise": ROOT / "pages" / "16_Admin_Exercise_Manager.py",
    "supplement": ROOT / "pages" / "39_Admin_Supplement_Manager.py",
}


def text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class RepositoryDensityAndLazyAddTests(unittest.TestCase):
    def test_changed_python_files_compile(self):
        for path in [UI, *PAGES.values()]:
            ast.parse(text(path), filename=str(path))

    def test_repository_rows_have_breathing_space(self):
        source = text(UI)
        self.assertIn(':has(.hm-repo-row)', source)
        self.assertIn(':has(.hm-sup-row)', source)
        self.assertIn('margin-bottom:.52rem!important', source)
        self.assertIn('margin:.34rem 0 .5rem!important', source)

    def test_form_density_is_crisp_but_readable(self):
        source = text(UI)
        self.assertIn('max-width:980px!important', source)
        self.assertIn('gap:.2rem!important', source)
        self.assertIn('min-height:1.9rem!important', source)
        self.assertIn('min-height:52px!important', source)
        self.assertIn('height:52px!important', source)
        self.assertIn('font-size:.66rem!important', source)

    def test_action_labels_cannot_be_hidden(self):
        source = text(UI)
        for token in (
            'button p{',
            'display:block!important',
            'visibility:visible!important',
            'opacity:1!important',
            'color:inherit!important',
        ):
            self.assertIn(token, source)

    def test_add_forms_render_only_when_opened(self):
        expected = {
            "recipe": "hm_recipe_repository_add_open",
            "exercise": "hm_exercise_repository_add_open",
            "supplement": "hm_supplement_repository_add_open",
        }
        for name, path in PAGES.items():
            source = text(path)
            state_key = expected[name]
            self.assertIn(f'get("{state_key}", False)', source)
            self.assertIn(f'st.session_state["{state_key}"] = not add_open', source)
            self.assertIn('if add_open:', source)
            self.assertNotIn(f'st.subheader("Add {name.title()}")', source)

    def test_opening_edit_closes_add(self):
        for name, path in PAGES.items():
            source = text(path)
            self.assertIn(
                f'st.session_state["hm_{name}_repository_add_open"] = False',
                source,
            )

    def test_existing_safety_contracts_remain(self):
        recipe = text(PAGES["recipe"])
        exercise = text(PAGES["exercise"])
        supplement = text(PAGES["supplement"])
        self.assertIn("_safe_delete_recipe", recipe)
        self.assertIn("set_exercise_repository_status", exercise)
        self.assertIn("set_supplement_repository_status", supplement)
        self.assertIn(
            'with st.form("hm_v1023a_add_supplement_form", clear_on_submit=True)',
            supplement,
        )
        for source in (recipe, exercise, supplement):
            self.assertIn("repository_form_panel()", source)
            self.assertIn("Historical references were retained.", source)


if __name__ == "__main__":
    unittest.main()
