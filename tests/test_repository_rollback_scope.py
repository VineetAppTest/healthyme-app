from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class RepositoryRollbackScopeTests(unittest.TestCase):
    def test_late_repository_ui_layers_are_absent(self):
        for relative in (
            "components/repository_create_form_success.py",
            "components/repository_layout_correction_runtime.py",
            "components/repository_page_ui.py",
            "tests/test_optimized_inline_repository_forms.py",
            "tests/test_repository_compact_ui.py",
            "tests/test_repository_create_form_success.py",
            "tests/test_repository_density_and_lazy_add.py",
            "tests/test_repository_layout_correction_runtime.py",
        ):
            self.assertFalse((ROOT / relative).exists(), relative)

    def test_pr327_repository_pages_remain(self):
        for relative in (
            "pages/15_Admin_Recipe_Manager.py",
            "pages/16_Admin_Exercise_Manager.py",
            "pages/39_Admin_Supplement_Manager.py",
        ):
            self.assertTrue((ROOT / relative).exists(), relative)


if __name__ == "__main__":
    unittest.main()
