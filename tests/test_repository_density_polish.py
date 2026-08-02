from __future__ import annotations

import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / "components" / "repository_page_ui.py"
PAGES = [
    ROOT / "pages" / "15_Admin_Recipe_Manager.py",
    ROOT / "pages" / "16_Admin_Exercise_Manager.py",
    ROOT / "pages" / "39_Admin_Supplement_Manager.py",
]


def text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class RepositoryDensityPolishTests(unittest.TestCase):
    def test_files_compile(self):
        ast.parse(text(HELPER), filename=str(HELPER))
        for path in PAGES:
            ast.parse(text(path), filename=str(path))

    def test_repository_rows_have_breathing_space(self):
        source = text(HELPER)
        self.assertIn(':has(.hm-repo-row)', source)
        self.assertIn(':has(.hm-sup-row)', source)
        self.assertIn('margin:0 0 .42rem!important', source)
        self.assertIn('align-items:center!important', source)

    def test_add_and_edit_keep_one_shared_panel(self):
        helper = text(HELPER)
        self.assertIn('def repository_form_panel()', helper)
        for path in PAGES:
            source = text(path)
            self.assertGreaterEqual(source.count('with repository_form_panel():'), 2)

    def test_form_is_crisp_but_readable(self):
        source = text(HELPER)
        for token in (
            'max-width:900px!important',
            'font-size:.64rem!important',
            'height:1.86rem!important',
            'height:52px!important',
            'min-height:2.05rem!important',
        ):
            self.assertIn(token, source)

    def test_save_button_text_is_forced_visible(self):
        source = text(HELPER)
        self.assertIn('div[data-testid="stFormSubmitButton"]>button p', source)
        self.assertIn('visibility:visible!important', source)
        self.assertIn('color:inherit!important', source)

    def test_repository_behaviour_is_untouched(self):
        recipe, exercise, supplement = (text(path) for path in PAGES)
        self.assertIn('_safe_delete_recipe', recipe)
        self.assertIn('set_exercise_repository_status', exercise)
        self.assertIn('set_supplement_repository_status', supplement)
        self.assertIn('clear_on_submit=True', supplement)


if __name__ == "__main__":
    unittest.main()
