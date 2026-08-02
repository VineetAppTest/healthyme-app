from __future__ import annotations

import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANAGERS = {
    "recipe": ROOT / "pages" / "15_Admin_Recipe_Manager.py",
    "exercise": ROOT / "pages" / "16_Admin_Exercise_Manager.py",
    "supplement": ROOT / "pages" / "39_Admin_Supplement_Manager.py",
}
ENTRIES = {
    "recipe": ROOT / "pages" / "15A_Admin_Recipe_Form.py",
    "exercise": ROOT / "pages" / "16A_Admin_Exercise_Form.py",
    "supplement": ROOT / "pages" / "39A_Admin_Supplement_Form.py",
}
WORKSPACE = ROOT / "components" / "repository_workspace_common.py"


def text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class DedicatedRepositoryWorkspaceTests(unittest.TestCase):
    def test_all_workspace_sources_compile(self):
        for path in [WORKSPACE, *MANAGERS.values(), *ENTRIES.values()]:
            ast.parse(text(path), filename=str(path))

    def test_repository_routes_are_lightweight_entry_points(self):
        routes = {
            "recipe": "15A_Admin_Recipe_Form.py",
            "exercise": "16A_Admin_Exercise_Form.py",
            "supplement": "39A_Admin_Supplement_Form.py",
        }
        for name, manager in MANAGERS.items():
            source = text(manager)
            self.assertIn(f'pages/{routes[name]}', source)
            self.assertIn(f'hm_{name}_workspace_mode', source)
            self.assertIn(f'hm_{name}_workspace_id', source)
            self.assertNotIn(f'hm_{name}_repository_add_open', source)

    def test_entry_routes_reuse_manager_source(self):
        managers = {
            "recipe": "15_Admin_Recipe_Manager.py",
            "exercise": "16_Admin_Exercise_Manager.py",
            "supplement": "39_Admin_Supplement_Manager.py",
        }
        for name, entry in ENTRIES.items():
            source = text(entry)
            self.assertIn("runpy.run_path", source)
            self.assertIn(managers[name], source)
            self.assertIn(f'_hm_{name}_workspace_embedded', source)

    def test_manager_workspace_branch_stops_before_repository_render(self):
        for name, manager in MANAGERS.items():
            source = text(manager)
            branch = f'if st.session_state.get("_hm_{name}_workspace_embedded"):'
            self.assertIn(branch, source)
            branch_at = source.index(branch)
            stop_at = source.index("st.stop()", branch_at)
            repository_at = source.index("repository_tab, add_tab = st.tabs", stop_at)
            self.assertLess(stop_at, repository_at)

    def test_add_success_clears_or_uses_clear_on_submit(self):
        recipe = text(MANAGERS["recipe"])
        exercise = text(MANAGERS["exercise"])
        supplement = text(MANAGERS["supplement"])
        self.assertIn('clear_widget_prefix(prefix)', recipe)
        self.assertIn('Recipe saved successfully. The form has been cleared.', recipe)
        self.assertIn('clear_widget_prefix(prefix)', exercise)
        self.assertIn('Exercise saved successfully. The form has been cleared.', exercise)
        self.assertIn('clear_on_submit=True', supplement)
        self.assertIn('Supplement saved successfully. The form has been cleared.', supplement)

    def test_edit_success_returns_to_repository(self):
        expected = {
            "recipe": "pages/15_Admin_Recipe_Manager.py",
            "exercise": "pages/16_Admin_Exercise_Manager.py",
            "supplement": "pages/39_Admin_Supplement_Manager.py",
        }
        for name, manager in MANAGERS.items():
            source = text(manager)
            self.assertIn('"Save Changes"', source)
            self.assertIn(f'st.switch_page("{expected[name]}")', source)
            self.assertIn(f'clear_workspace("{name}")', source)

    def test_safe_delete_logic_is_unchanged(self):
        recipe = text(MANAGERS["recipe"])
        exercise = text(MANAGERS["exercise"])
        supplement = text(MANAGERS["supplement"])
        self.assertIn("_safe_delete_recipe", recipe)
        self.assertIn("set_exercise_repository_status", exercise)
        self.assertIn("set_supplement_repository_status", supplement)
        for source in (recipe, exercise, supplement):
            self.assertIn("Historical references were retained.", source)


if __name__ == "__main__":
    unittest.main()
