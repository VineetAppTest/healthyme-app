from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAGES = {
    ROOT / "pages/15_Admin_Recipe_Manager.py": ("Add Recipe", "recipe_repository"),
    ROOT / "pages/16_Admin_Exercise_Manager.py": ("Add Exercise", "exercise_repository"),
    ROOT / "pages/39_Admin_Supplement_Manager.py": ("Add Supplement", "supplement_repository"),
}


def replace_once(text: str, old: str, new: str, *, label: str) -> str:
    if new in text:
        return text
    if old not in text:
        raise RuntimeError(f"Missing expected block: {label}")
    return text.replace(old, new, 1)


for path, (add_label, key) in PAGES.items():
    text = path.read_text(encoding="utf-8")
    text = replace_once(
        text,
        "    repository_inactive_panel,\n)",
        "    repository_inactive_panel,\n    render_repository_section_switch,\n)",
        label=f"{path.name} section-switch import",
    )
    text = replace_once(
        text,
        f'repository_tab, add_tab = st.tabs(["Current Repository", "{add_label}"])\n\nwith repository_tab:',
        f'section = render_repository_section_switch("{add_label}", key="{key}")\n\nif section == "repository":',
        label=f"{path.name} tabs",
    )
    text = replace_once(
        text,
        "\nwith add_tab:\n",
        "\nelse:\n",
        label=f"{path.name} Add branch",
    )
    if "st.tabs(" in text:
        raise RuntimeError(f"{path.name} still renders both tab bodies")
    path.write_text(text, encoding="utf-8")


consolidation = ROOT / "tests/test_repository_consolidation.py"
text = consolidation.read_text(encoding="utf-8")
old = '''    def test_each_page_exposes_only_repository_and_add_sections(self):
        self.assertIn('st.tabs(["Current Repository", "Add Recipe"])', self.recipe)
        self.assertIn('st.tabs(["Current Repository", "Add Exercise"])', self.exercise)
        self.assertIn('st.tabs(["Current Repository", "Add Supplement"])', self.supplement)
'''
new = '''    def test_each_page_exposes_only_repository_and_add_sections(self):
        self.assertIn('render_repository_section_switch("Add Recipe"', self.recipe)
        self.assertIn('render_repository_section_switch("Add Exercise"', self.exercise)
        self.assertIn('render_repository_section_switch("Add Supplement"', self.supplement)
        for source in (self.recipe, self.exercise, self.supplement):
            self.assertNotIn("st.tabs(", source)
            self.assertIn('if section == "repository":', source)
            self.assertIn("else:", source)
'''
text = replace_once(text, old, new, label="repository consolidation section contract")
consolidation.write_text(text, encoding="utf-8")


supplement_test = ROOT / "tests/test_supplement_repository_separation.py"
text = supplement_test.read_text(encoding="utf-8")
old = '''        self.assertIn(
            'repository_tab, add_tab = st.tabs(["Current Repository", "Add Supplement"])',
            text,
        )
        self.assertLess(text.index("with repository_tab:"), text.index("with add_tab:"))
'''
new = '''        self.assertIn('render_repository_section_switch("Add Supplement"', text)
        self.assertNotIn("st.tabs(", text)
        self.assertLess(text.index('if section == "repository":'), text.index("else:"))
'''
text = replace_once(text, old, new, label="supplement lazy section contract")
supplement_test.write_text(text, encoding="utf-8")


layout_test = ROOT / "tests/test_repository_layout_correction_runtime.py"
text = layout_test.read_text(encoding="utf-8")
old = '''    def test_add_and_edit_share_balanced_readable_dimensions(self):
        source = text(HELPER)
        self.assertIn("max-width:940px!important", source)
        self.assertIn("min-height:2.18rem!important", source)
        self.assertIn("min-height:68px!important", source)
        self.assertIn("font-size:.76rem!important", source)
        self.assertNotIn("min-height:1.72rem", source)
        self.assertNotIn("height:42px", source)
'''
new = '''    def test_add_and_edit_share_crisp_readable_dimensions(self):
        source = text(HELPER)
        self.assertIn("max-width:880px!important", source)
        self.assertIn("min-height:1.9rem!important", source)
        self.assertIn("min-height:52px!important", source)
        self.assertIn("font-size:.71rem!important", source)
        self.assertIn("button[kind=\\\"primary\\\"] *", source)

    def test_repository_sections_render_server_side_only(self):
        helper = text(HELPER)
        self.assertIn("def render_repository_section_switch", helper)
        self.assertIn('current not in {"repository", "add"}', helper)
        for page in PAGES:
            source = text(page)
            self.assertIn("render_repository_section_switch", source)
            self.assertNotIn("st.tabs(", source)
'''
text = replace_once(text, old, new, label="repository layout density contract")
layout_test.write_text(text, encoding="utf-8")


compact_test = ROOT / "tests/test_repository_compact_ui.py"
text = compact_test.read_text(encoding="utf-8")
old = '''    def test_add_and_edit_use_same_balanced_form_panel(self):
        helper = text(HELPER)
        self.assertIn("min-height:2.18rem!important", helper)
        self.assertIn("min-height:68px!important", helper)
        self.assertIn("font-size:.76rem!important", helper)
        self.assertNotIn("min-height:1.72rem", helper)
        self.assertNotIn("height:42px", helper)
'''
new = '''    def test_add_and_edit_use_same_crisp_form_panel(self):
        helper = text(HELPER)
        self.assertIn("min-height:1.9rem!important", helper)
        self.assertIn("min-height:52px!important", helper)
        self.assertIn("font-size:.71rem!important", helper)
        self.assertIn("Keep primary action copy visible", helper)
        self.assertIn("def render_repository_section_switch", helper)
'''
text = replace_once(text, old, new, label="repository compact density contract")
compact_test.write_text(text, encoding="utf-8")

print("Repository density and server-side section gating applied.")
