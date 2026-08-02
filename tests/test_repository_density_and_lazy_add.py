from __future__ import annotations

import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_UI = ROOT / "components" / "repository_page_ui.py"
WORKSPACE_UI = ROOT / "components" / "repository_workspace_common.py"
PAGES = {
    "recipe": ROOT / "pages" / "15_Admin_Recipe_Manager.py",
    "exercise": ROOT / "pages" / "16_Admin_Exercise_Manager.py",
    "supplement": ROOT / "pages" / "39_Admin_Supplement_Manager.py",
}
FORM_PAGES = {
    "recipe": ROOT / "pages" / "15A_Admin_Recipe_Form.py",
    "exercise": ROOT / "pages" / "16A_Admin_Exercise_Form.py",
    "supplement": ROOT / "pages" / "39A_Admin_Supplement_Form.py",
}


def text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class RepositoryDensityAndDedicatedWorkspaceTests(unittest.TestCase):
    def test_changed_python_files_compile(self):
        for path in [REPOSITORY_UI, WORKSPACE_UI, *PAGES.values(), *FORM_PAGES.values()]:
            ast.parse(text(path), filename=str(path))

    def test_repository_rows_keep_breathing_space(self):
        source = text(REPOSITORY_UI)
        self.assertIn(':has(.hm-repo-row)', source)
        self.assertIn(':has(.hm-sup-row)', source)
        self.assertIn('margin-bottom:.52rem!important', source)
        self.assertIn('margin:.34rem 0 .5rem!important', source)

    def test_workspace_form_density_is_balanced(self):
        source = text(WORKSPACE_UI)
        self.assertIn('max-width:960px!important', source)
        self.assertIn('min-height:2.12rem!important', source)
        self.assertIn('min-height:64px!important', source)
        self.assertIn('height:64px!important', source)
        self.assertIn('font-size:.74rem!important', source)

    def test_workspace_action_labels_cannot_be_hidden(self):
        source = text(WORKSPACE_UI)
        for token in (
            'button p{',
            'display:block!important',
            'visibility:visible!important',
            'opacity:1!important',
            'color:inherit!important',
        ):
            self.assertIn(token, source)

    def test_repository_add_and_edit_open_dedicated_routes(self):
        expected = {
            "recipe": ("15A_Admin_Recipe_Form.py", "hm_recipe_workspace_mode"),
            "exercise": ("16A_Admin_Exercise_Form.py", "hm_exercise_workspace_mode"),
            "supplement": ("39A_Admin_Supplement_Form.py", "hm_supplement_workspace_mode"),
        }
        for name, path in PAGES.items():
            source = text(path)
            route, mode_key = expected[name]
            self.assertIn(f'st.switch_page("pages/{route}")', source)
            self.assertIn(f'st.session_state["{mode_key}"] = "add"', source)
            self.assertIn(f'st.session_state["{mode_key}"] = "edit"', source)
            self.assertNotIn(f'hm_{name}_repository_add_open', source)

    def test_form_routes_execute_manager_in_workspace_mode(self):
        expected = {
            "recipe": ("_hm_recipe_workspace_embedded", "15_Admin_Recipe_Manager.py"),
            "exercise": ("_hm_exercise_workspace_embedded", "16_Admin_Exercise_Manager.py"),
            "supplement": ("_hm_supplement_workspace_embedded", "39_Admin_Supplement_Manager.py"),
        }
        for name, path in FORM_PAGES.items():
            source = text(path)
            flag, manager = expected[name]
            self.assertIn(f'st.session_state["{flag}"] = True', source)
            self.assertIn(manager, source)
            self.assertIn("runpy.run_path", source)
            self.assertIn(f'st.session_state.pop("{flag}", None)', source)

    def test_only_workspace_branch_renders_forms(self):
        for name, path in PAGES.items():
            source = text(path)
            self.assertIn(f'if st.session_state.get("_hm_{name}_workspace_embedded"):', source)
            self.assertIn("workspace_panel()", source)
            self.assertIn("st.stop()", source)
        self.assertIn('with st.form("hm_v1023a_add_supplement_form", clear_on_submit=True)', text(PAGES["supplement"]))

    def test_existing_safety_contracts_remain(self):
        recipe = text(PAGES["recipe"])
        exercise = text(PAGES["exercise"])
        supplement = text(PAGES["supplement"])
        self.assertIn("_safe_delete_recipe", recipe)
        self.assertIn("set_exercise_repository_status", exercise)
        self.assertIn("set_supplement_repository_status", supplement)
        for source in (recipe, exercise, supplement):
            self.assertIn("Historical references were retained.", source)


if __name__ == "__main__":
    unittest.main()
