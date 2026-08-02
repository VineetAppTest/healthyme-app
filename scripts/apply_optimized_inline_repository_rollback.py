from __future__ import annotations

# One-time transformer. This comment intentionally retriggers the branch workflow.

import subprocess
import textwrap
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PRE_WORKSPACE_COMMIT = "ab1778d3e40cdb2af6c0e7a33f98ba4f5a821e46"

RESTORE_PATHS = [
    "pages/15_Admin_Recipe_Manager.py",
    "pages/16_Admin_Exercise_Manager.py",
    "pages/39_Admin_Supplement_Manager.py",
    "tests/test_exercise_journal_repository_fix_contract.py",
    "tests/test_repository_compact_ui.py",
    "tests/test_repository_density_and_lazy_add.py",
    "tests/test_supplement_repository_separation.py",
]

REMOVE_PATHS = [
    ".github/workflows/dedicated-repository-workspaces-validation.yml",
    "components/repository_workspace_common.py",
    "pages/15A_Admin_Recipe_Form.py",
    "pages/16A_Admin_Exercise_Form.py",
    "pages/39A_Admin_Supplement_Form.py",
    "tests/test_dedicated_repository_workspaces.py",
]

PAGES = {
    "Recipe": ROOT / "pages" / "15_Admin_Recipe_Manager.py",
    "Exercise": ROOT / "pages" / "16_Admin_Exercise_Manager.py",
    "Supplement": ROOT / "pages" / "39_Admin_Supplement_Manager.py",
}


def run(*args: str) -> None:
    subprocess.run(args, cwd=ROOT, check=True)


def restore_pre_workspace_files() -> None:
    run("git", "checkout", PRE_WORKSPACE_COMMIT, "--", *RESTORE_PATHS)
    for relative_path in REMOVE_PATHS:
        path = ROOT / relative_path
        if path.exists():
            path.unlink()


def replace_tabs_with_strict_lazy_inline(path: Path, item_name: str) -> None:
    source = path.read_text(encoding="utf-8")
    tab_marker = (
        f'repository_tab, add_tab = st.tabs(["Current Repository", "Add {item_name}"])'
    )
    if tab_marker not in source:
        raise RuntimeError(f"{path}: repository tab marker is missing")

    start = source.index(tab_marker)
    repository_marker = "\n\nwith repository_tab:\n"
    add_marker = "\nwith add_tab:\n"
    nav_marker = "\nrender_page_nav(\n"

    repository_start = source.index(repository_marker, start)
    add_start = source.index(add_marker, repository_start)
    nav_start = source.index(nav_marker, add_start)

    repository_body = textwrap.dedent(
        source[repository_start + len(repository_marker) : add_start]
    ).rstrip()
    add_body = textwrap.dedent(source[add_start + len(add_marker) : nav_start]).rstrip()

    replacement = (
        add_body
        + "\n\n# Do not build repository rows while Add is open. This keeps the run focused\n"
        + "# on one large form and prevents hidden/background form rendering.\n"
        + "if not add_open:\n"
        + textwrap.indent(repository_body, "    ")
        + "\n"
    )
    source = source[:start] + replacement + source[nav_start:]

    forbidden = (
        "repository_workspace_common",
        f"pages/{path.stem.split('_Admin_')[0]}A_",
        "_workspace_embedded",
        "st.tabs([\"Current Repository\"",
        "with repository_tab:",
        "with add_tab:",
    )
    for token in forbidden:
        if token in source:
            raise RuntimeError(f"{path}: forbidden dedicated/tab token remains: {token}")

    required = (
        "if add_open:",
        "if not add_open:",
        "repository_form_panel()",
        f'hm_{item_name.lower()}_repository_add_open',
        f'st.session_state["hm_{item_name.lower()}_repository_add_open"] = False',
    )
    for token in required:
        if token not in source:
            raise RuntimeError(f"{path}: optimized inline token missing: {token}")

    path.write_text(source, encoding="utf-8")


def write_validation_contract() -> None:
    test_path = ROOT / "tests" / "test_optimized_inline_repository_forms.py"
    test_path.write_text(
        '''from __future__ import annotations

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
''',
        encoding="utf-8",
    )

    workflow_path = ROOT / ".github" / "workflows" / "optimized-inline-repository-forms-validation.yml"
    workflow_path.write_text(
        '''name: Optimized inline repository forms validation

on:
  pull_request:
    paths:
      - pages/15_Admin_Recipe_Manager.py
      - pages/16_Admin_Exercise_Manager.py
      - pages/39_Admin_Supplement_Manager.py
      - components/repository_page_ui.py
      - tests/test_optimized_inline_repository_forms.py
      - tests/test_repository_density_and_lazy_add.py
      - tests/test_repository_compact_ui.py
      - tests/test_supplement_repository_separation.py
      - tests/test_exercise_journal_repository_fix_contract.py
      - .github/workflows/optimized-inline-repository-forms-validation.yml

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Compile repository pages
        run: |
          python -m py_compile \\
            pages/15_Admin_Recipe_Manager.py \\
            pages/16_Admin_Exercise_Manager.py \\
            pages/39_Admin_Supplement_Manager.py \\
            components/repository_page_ui.py
      - name: Run optimized inline contracts
        run: |
          python -m unittest tests.test_optimized_inline_repository_forms -v
          python -m unittest tests.test_repository_density_and_lazy_add -v
          python -m unittest tests.test_repository_compact_ui -v
          python -m unittest tests.test_supplement_repository_separation -v
          python -m unittest tests.test_exercise_journal_repository_fix_contract -v
''',
        encoding="utf-8",
    )


def main() -> None:
    restore_pre_workspace_files()
    for item_name, page_path in PAGES.items():
        replace_tabs_with_strict_lazy_inline(page_path, item_name)
    write_validation_contract()


if __name__ == "__main__":
    main()
