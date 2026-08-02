from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAGES = {
    "recipe": ROOT / "pages/15_Admin_Recipe_Manager.py",
    "exercise": ROOT / "pages/16_Admin_Exercise_Manager.py",
    "supplement": ROOT / "pages/39_Admin_Supplement_Manager.py",
}
BOOTSTRAP = ROOT / "components/__init__.py"
TEST = ROOT / "tests/test_repository_layout_correction_runtime.py"

IMPORT_BLOCK = """from components.repository_page_ui import (
    inject_repository_page_ui,
    render_repository_disclosure,
    repository_form_panel,
    repository_inactive_panel,
)
"""


def must_replace(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise RuntimeError(f"Missing expected block: {label}")
    return text.replace(old, new, 1)


def add_import_and_init(text: str, anchor: str) -> str:
    if IMPORT_BLOCK not in text:
        text = must_replace(text, anchor, anchor + IMPORT_BLOCK, "repository page UI import")
    if "inject_repository_page_ui()" not in text:
        text = must_replace(
            text,
            "utility_logout_bar()\n",
            "utility_logout_bar()\ninject_repository_page_ui()\n",
            "repository page UI init",
        )
    return text


def replace_inactive_block(text: str, count_expr: str, state_key: str, button_key: str) -> str:
    marker = f'    with st.expander(f"Inactive Repository Items ({{{count_expr}}})"):'
    start = text.find(marker)
    if start < 0:
        raise RuntimeError(f"Missing inactive block: {count_expr}")
    end = text.find("\nwith add_tab:", start)
    if end < 0:
        raise RuntimeError("Missing add tab after inactive block")
    block = text[start:end]
    body_lines = block.splitlines()[1:]
    indented_body = "\n".join("    " + line for line in body_lines)
    replacement = f'''    inactive_open = bool(st.session_state.get("{state_key}", False))
    if render_repository_disclosure(
        f"Inactive Repository Items ({{{count_expr}}})",
        is_open=inactive_open,
        key="{button_key}",
    ):
        st.session_state["{state_key}"] = not inactive_open
        st.rerun()
    if inactive_open:
        with repository_inactive_panel():
{indented_body}'''
    return text[:start] + replacement + text[end:]


def wrap_add_tab(text: str) -> str:
    start = text.find("with add_tab:\n")
    if start < 0:
        raise RuntimeError("Missing add tab")
    end = text.find("\nrender_page_nav(", start)
    if end < 0:
        raise RuntimeError("Missing page navigation after add tab")
    block = text[start:end]
    lines = block.splitlines()
    body = "\n".join("    " + line for line in lines[1:])
    replacement = "with add_tab:\n    with repository_form_panel():\n" + body
    return text[:start] + replacement + text[end:]


def transform_recipe(text: str) -> str:
    text = add_import_and_init(
        text,
        "from components.storage_assets import upload_content_image\n",
    )
    text = text.replace('st.markdown("#### Core details")', 'st.markdown("#### Core Details")')
    text = must_replace(
        text,
        '                with st.expander(f"Edit Recipe · {title}", expanded=True):',
        '''                if render_repository_disclosure(
                    f"Edit Recipe · {title}",
                    is_open=True,
                    key=f"recipe_repo_edit_disclosure_{index}",
                ):
                    st.session_state.pop("hm_recipe_repository_edit_index", None)
                    st.rerun()
                with repository_form_panel():''',
        "recipe edit disclosure",
    )
    text = replace_inactive_block(
        text,
        "len(inactive_df)",
        "hm_recipe_repository_inactive_open",
        "recipe_repo_inactive_disclosure",
    )
    return wrap_add_tab(text)


def transform_exercise(text: str) -> str:
    text = add_import_and_init(
        text,
        "from components.storage_assets import upload_content_image\n",
    )
    text = text.replace('st.markdown("#### Core display fields")', 'st.markdown("#### Core Fields")')
    text = must_replace(
        text,
        "    description = st.text_area(\n",
        '    st.markdown("#### Guidance / Benefits")\n    description = st.text_area(\n',
        "exercise guidance heading",
    )
    text = must_replace(
        text,
        "    goal_col, condition_col = st.columns(2, gap=\"small\")\n",
        '    st.markdown("#### Tags")\n    goal_col, condition_col = st.columns(2, gap="small")\n',
        "exercise tags heading",
    )
    text = must_replace(
        text,
        '            with st.expander(f"Edit Exercise · {title}", expanded=True):',
        '''            if render_repository_disclosure(
                f"Edit Exercise · {title}",
                is_open=True,
                key=f"exercise_repo_edit_disclosure_{exercise_id}",
            ):
                st.session_state.pop("hm_exercise_repository_edit_id", None)
                st.rerun()
            with repository_form_panel():''',
        "exercise edit disclosure",
    )
    text = replace_inactive_block(
        text,
        "len(inactive_rows)",
        "hm_exercise_repository_inactive_open",
        "exercise_repo_inactive_disclosure",
    )
    return wrap_add_tab(text)


def transform_supplement(text: str) -> str:
    text = add_import_and_init(
        text,
        "from components.supplement_repository import (\n",
    )
    # The supplement import anchor is a multiline import. Reposition the helper block
    # after that import if the simple insertion landed inside it.
    broken = "from components.supplement_repository import (\n" + IMPORT_BLOCK
    if broken in text:
        text = text.replace(broken, "from components.supplement_repository import (\n", 1)
        anchor = ")\nfrom components.ui_common import (\n"
        text = must_replace(text, anchor, ")\n" + IMPORT_BLOCK + "from components.ui_common import (\n", "supplement helper import")

    text = must_replace(
        text,
        '            with st.expander(f"Edit Supplement · {name}", expanded=True):',
        '''            if render_repository_disclosure(
                f"Edit Supplement · {name}",
                is_open=True,
                key=f"supplement_repo_edit_disclosure_{supplement_id}",
            ):
                st.session_state.pop("hm_supplement_repository_edit_id", None)
                st.rerun()
            with repository_form_panel():''',
        "supplement edit disclosure",
    )
    text = must_replace(
        text,
        "                basic_name, basic_dose, basic_frequency = st.columns(3, gap=\"small\")\n",
        '                st.markdown("#### Basic Details")\n                basic_name, basic_dose, basic_frequency = st.columns(3, gap="small")\n',
        "supplement edit basic heading",
    )
    text = must_replace(
        text,
        "                timing_col, custom_col = st.columns([1.35, 1], gap=\"small\")\n",
        '                st.markdown("#### Timing")\n                timing_col, custom_col = st.columns([1.35, 1], gap="small")\n',
        "supplement edit timing heading",
    )
    text = must_replace(
        text,
        "                edit_instructions = st.text_area(\n",
        '                st.markdown("#### Instructions")\n                edit_instructions = st.text_area(\n',
        "supplement edit instructions heading",
    )
    text = replace_inactive_block(
        text,
        "len(inactive_rows)",
        "hm_supplement_repository_inactive_open",
        "supplement_repo_inactive_disclosure",
    )
    text = must_replace(
        text,
        '    with st.form("hm_v1023a_add_supplement_form", clear_on_submit=True):\n        name = st.text_input(\n',
        '    with st.form("hm_v1023a_add_supplement_form", clear_on_submit=True):\n        st.markdown("#### Basic Details")\n        name = st.text_input(\n',
        "supplement add basic heading",
    )
    text = must_replace(
        text,
        "        timing_options = st.multiselect(\n",
        '        st.markdown("#### Timing")\n        timing_options = st.multiselect(\n',
        "supplement add timing heading",
    )
    text = must_replace(
        text,
        "        instructions = st.text_area(\n",
        '        st.markdown("#### Instructions")\n        instructions = st.text_area(\n',
        "supplement add instructions heading",
    )
    return wrap_add_tab(text)


def transform_bootstrap(text: str) -> str:
    text = text.replace(
        "from components.repository_layout_correction_runtime import (\n    install_repository_layout_correction_runtime,\n)\n",
        "",
    )
    text = text.replace(
        "\n# Repository presentation is page-scoped and outermost so it can override legacy\n# card widths, native disclosure markers and form spacing without changing writes.\ninstall_repository_layout_correction_runtime()",
        "",
    )
    return text


TEST_CONTENT = '''from __future__ import annotations

import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / "components/repository_page_ui.py"
BOOTSTRAP = ROOT / "components/__init__.py"
PAGES = [
    ROOT / "pages/15_Admin_Recipe_Manager.py",
    ROOT / "pages/16_Admin_Exercise_Manager.py",
    ROOT / "pages/39_Admin_Supplement_Manager.py",
]


def text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class RepositoryDirectPageUiTests(unittest.TestCase):
    def test_helper_bootstrap_and_pages_compile(self):
        for path in [HELPER, BOOTSTRAP, *PAGES]:
            ast.parse(text(path), filename=str(path))

    def test_repository_pages_do_not_use_streamlit_expanders(self):
        for page in PAGES:
            source = text(page)
            self.assertNotIn("st.expander", source, page.name)
            self.assertIn("render_repository_disclosure", source, page.name)
            self.assertGreaterEqual(source.count("repository_form_panel()"), 2, page.name)
            self.assertIn("repository_inactive_panel()", source, page.name)

    def test_disclosure_is_page_owned_and_has_one_inline_symbol(self):
        source = text(HELPER)
        self.assertIn('symbol = "⊖" if is_open else "⊕"', source)
        self.assertIn('f"{symbol}  {label}"', source)
        self.assertNotIn("st.expander", source)

    def test_add_and_edit_share_balanced_readable_dimensions(self):
        source = text(HELPER)
        self.assertIn("max-width:940px!important", source)
        self.assertIn("min-height:2.18rem!important", source)
        self.assertIn("min-height:68px!important", source)
        self.assertIn("font-size:.76rem!important", source)
        self.assertNotIn("min-height:1.72rem", source)
        self.assertNotIn("height:42px", source)

    def test_approved_sections_are_directly_rendered(self):
        recipe, exercise, supplement = [text(page) for page in PAGES]
        for heading in ("#### Core Details", "#### Nutrition", "#### Preparation", "#### Image"):
            self.assertIn(heading, recipe)
        for heading in ("#### Core Fields", "#### Guidance / Benefits", "#### Tags", "#### Image"):
            self.assertIn(heading, exercise)
        for heading in ("#### Basic Details", "#### Timing", "#### Instructions"):
            self.assertGreaterEqual(supplement.count(heading), 2)

    def test_legacy_repository_layout_runtime_is_not_installed(self):
        bootstrap = text(BOOTSTRAP)
        self.assertNotIn("install_repository_layout_correction_runtime", bootstrap)


if __name__ == "__main__":
    unittest.main()
'''


def main() -> None:
    transforms = {
        "recipe": transform_recipe,
        "exercise": transform_exercise,
        "supplement": transform_supplement,
    }
    for name, path in PAGES.items():
        source = path.read_text(encoding="utf-8")
        path.write_text(transforms[name](source), encoding="utf-8")

    BOOTSTRAP.write_text(
        transform_bootstrap(BOOTSTRAP.read_text(encoding="utf-8")),
        encoding="utf-8",
    )
    TEST.write_text(TEST_CONTENT, encoding="utf-8")


if __name__ == "__main__":
    main()
