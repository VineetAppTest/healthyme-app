from __future__ import annotations

import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAGES = {
    "recipe": ROOT / "pages" / "15_Admin_Recipe_Manager.py",
    "exercise": ROOT / "pages" / "16_Admin_Exercise_Manager.py",
    "supplement": ROOT / "pages" / "39_Admin_Supplement_Manager.py",
}
DEDICATED_PATHS = (
    ROOT / "components" / "repository_workspace_common.py",
    ROOT / "pages" / "15A_Admin_Recipe_Form.py",
    ROOT / "pages" / "16A_Admin_Exercise_Form.py",
    ROOT / "pages" / "39A_Admin_Supplement_Form.py",
)


def text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class OptimizedInlineRepositoryFormTests(unittest.TestCase):
    def test_repository_pages_compile(self):
        for path in PAGES.values():
            ast.parse(text(path), filename=str(path))

    def test_dedicated_workspace_architecture_is_removed(self):
        for path in DEDICATED_PATHS:
            self.assertFalse(path.exists(), path)
        for source_path in PAGES.values():
            source = text(source_path)
            self.assertNotIn("repository_workspace_common", source)
            self.assertNotIn("_workspace_embedded", source)
            self.assertNotIn("15A_Admin_Recipe_Form", source)
            self.assertNotIn("16A_Admin_Exercise_Form", source)
            self.assertNotIn("39A_Admin_Supplement_Form", source)

    def test_tabs_cannot_render_hidden_add_forms(self):
        for source_path in PAGES.values():
            source = text(source_path)
            self.assertNotIn('st.tabs(["Current Repository"', source)
            self.assertNotIn("with repository_tab:", source)
            self.assertNotIn("with add_tab:", source)
            self.assertIn("if add_open:", source)
            self.assertIn("if not add_open:", source)

    def test_add_and_edit_are_mutually_exclusive(self):
        for name, source_path in PAGES.items():
            source = text(source_path)
            add_key = f"hm_{name}_repository_add_open"
            self.assertIn(f'get("{add_key}", False)', source)
            self.assertIn(f'st.session_state["{add_key}"] = not add_open', source)
            self.assertIn(f'st.session_state["{add_key}"] = False', source)
            self.assertIn("repository_form_panel()", source)

    def test_edit_remains_inline_below_selected_item(self):
        for source_path in PAGES.values():
            source = text(source_path)
            self.assertIn('"Edit",', source)
            self.assertIn("render_repository_disclosure(", source)
            self.assertIn("Save Changes", source)
            self.assertIn("repository_edit_", source)

    def test_safe_delete_and_save_contracts_remain(self):
        recipe = text(PAGES["recipe"])
        exercise = text(PAGES["exercise"])
        supplement = text(PAGES["supplement"])
        self.assertIn("_safe_delete_recipe", recipe)
        self.assertIn("set_exercise_repository_status", exercise)
        self.assertIn("set_supplement_repository_status", supplement)
        self.assertIn("Historical references were retained.", recipe)
        self.assertIn("Historical references were retained.", exercise)
        self.assertIn("Historical references were retained.", supplement)


if __name__ == "__main__":
    unittest.main()
