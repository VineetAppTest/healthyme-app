from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAGES = (
    ROOT / "pages" / "15_Admin_Recipe_Manager.py",
    ROOT / "pages" / "16_Admin_Exercise_Manager.py",
    ROOT / "pages" / "39_Admin_Supplement_Manager.py",
)


def add_current_repository_heading() -> None:
    marker = (
        "# Do not build repository rows while Add is open. This keeps the run focused\n"
        "# on one large form and prevents hidden/background form rendering.\n"
        "if not add_open:\n"
    )
    replacement = marker + '    st.markdown("### Current Repository")\n'
    for path in PAGES:
        source = path.read_text(encoding="utf-8")
        if 'st.markdown("### Current Repository")' in source:
            continue
        if source.count(marker) != 1:
            raise RuntimeError(f"{path}: exact lazy repository marker is missing")
        source = source.replace(marker, replacement, 1)
        path.write_text(source, encoding="utf-8")


def update_repository_consolidation_test() -> None:
    path = ROOT / "tests" / "test_repository_consolidation.py"
    source = path.read_text(encoding="utf-8")
    old = '''    def test_each_page_exposes_only_repository_and_add_sections(self):
        self.assertIn('st.tabs(["Current Repository", "Add Recipe"])', self.recipe)
        self.assertIn('st.tabs(["Current Repository", "Add Exercise"])', self.exercise)
        self.assertIn('st.tabs(["Current Repository", "Add Supplement"])', self.supplement)
'''
    new = '''    def test_each_page_exposes_only_repository_and_add_sections(self):
        expected = (
            (self.recipe, "Recipe", "hm_recipe_repository_add_open"),
            (self.exercise, "Exercise", "hm_exercise_repository_add_open"),
            (self.supplement, "Supplement", "hm_supplement_repository_add_open"),
        )
        for source, item_name, state_key in expected:
            self.assertIn('st.markdown("### Current Repository")', source)
            self.assertIn(f'"Add {item_name}"', source)
            self.assertIn(state_key, source)
            self.assertIn("if add_open:", source)
            self.assertIn("if not add_open:", source)
            self.assertNotIn('st.tabs(["Current Repository"', source)
'''
    if old not in source:
        raise RuntimeError("Repository consolidation tab contract marker is missing")
    path.write_text(source.replace(old, new, 1), encoding="utf-8")


def update_supplement_test() -> None:
    path = ROOT / "tests" / "test_supplement_repository_separation.py"
    source = path.read_text(encoding="utf-8")
    old = '''        self.assertIn(
            'repository_tab, add_tab = st.tabs(["Current Repository", "Add Supplement"])',
            text,
        )
        self.assertLess(text.index("with repository_tab:"), text.index("with add_tab:"))
'''
    new = '''        self.assertIn('st.markdown("### Current Repository")', text)
        self.assertIn('"Add Supplement"', text)
        self.assertIn("hm_supplement_repository_add_open", text)
        self.assertIn("if add_open:", text)
        self.assertIn("if not add_open:", text)
        self.assertNotIn('st.tabs(["Current Repository"', text)
        self.assertNotIn("with repository_tab:", text)
        self.assertNotIn("with add_tab:", text)
'''
    if old not in source:
        raise RuntimeError("Supplement tab contract marker is missing")
    path.write_text(source.replace(old, new, 1), encoding="utf-8")


def strengthen_optimized_test() -> None:
    path = ROOT / "tests" / "test_optimized_inline_repository_forms.py"
    source = path.read_text(encoding="utf-8")
    old = '''            self.assertIn("if add_open:", source)
            self.assertIn("if not add_open:", source)
'''
    new = '''            self.assertIn("if add_open:", source)
            self.assertIn("if not add_open:", source)
            self.assertIn('st.markdown("### Current Repository")', source)
'''
    if old not in source:
        raise RuntimeError("Optimized inline test marker is missing")
    path.write_text(source.replace(old, new, 1), encoding="utf-8")


def main() -> None:
    add_current_repository_heading()
    update_repository_consolidation_test()
    update_supplement_test()
    strengthen_optimized_test()


if __name__ == "__main__":
    main()
