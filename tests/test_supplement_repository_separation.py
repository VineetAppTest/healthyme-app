from __future__ import annotations

import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SUPPLEMENT_PAGE = ROOT / "pages" / "39_Admin_Supplement_Manager.py"
PROFILE_PAGE = ROOT / "pages" / "38_Admin_Recommendation_Profile_Builder.py"
REPOSITORY = ROOT / "components" / "supplement_repository.py"
SOURCE_BRIDGE = ROOT / "components" / "supplement_repository_source.py"


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class SupplementRepositorySeparationTests(unittest.TestCase):
    def test_changed_python_files_compile(self):
        for path in [SUPPLEMENT_PAGE, PROFILE_PAGE, REPOSITORY, SOURCE_BRIDGE]:
            ast.parse(_text(path), filename=str(path))

    def test_supplement_manager_is_repository_only(self):
        text = _text(SUPPLEMENT_PAGE)
        forbidden = [
            'st.selectbox("Select Member"',
            "add_member_supplement",
            "list_member_supplements",
            "stop_member_supplement",
            "update_member_supplement",
            "supplement_regimen_counts",
            "Add & Publish to Member",
            "published to this member",
        ]
        for token in forbidden:
            self.assertNotIn(token, text)

        self.assertIn("Current Repository", text)
        self.assertIn("Add to Repository", text)

    def test_requested_repository_ui_polish_is_present(self):
        text = _text(SUPPLEMENT_PAGE)
        self.assertNotIn(
            "Member allocation is managed only through Recommendation Profile Builder. This page creates and maintains reusable supplement definitions and does not publish directly to any member.",
            text,
        )
        self.assertNotIn("hm-sup-boundary", text)
        self.assertNotIn("hm-sup-card", text)
        self.assertIn("hm-sup-list-details", text)
        self.assertIn("hm-sup-list-divider", text)
        self.assertIn('add_column, repository_column = st.columns([0.78, 1.22]', text)
        self.assertLess(text.index("with add_column:"), text.index("with repository_column:"))
        self.assertIn('f"Expand — Inactive Repository Items ({counts[\'inactive\']})"', text)
        self.assertIn('f"Close — Inactive Repository Items ({counts[\'inactive\']})"', text)
        self.assertNotIn("with st.expander", text)

    def test_repository_actions_remain_available(self):
        text = _text(SUPPLEMENT_PAGE)
        for token in (
            'st.button("Edit"',
            'st.button("Deactivate"',
            'st.button("Reactivate"',
            "update_supplement_repository_item(",
            "set_supplement_repository_status(",
        ):
            self.assertIn(token, text)

    def test_repository_migration_preserves_member_rows(self):
        text = _text(REPOSITORY)
        self.assertIn('db.get("member_supplements", [])', text)
        self.assertNotIn('db["member_supplements"]', text)
        self.assertIn('"member_regimens_unchanged": True', text)

    def test_profile_builder_installs_repository_source_before_modular_import(self):
        text = _text(PROFILE_PAGE)
        install_at = text.index("install_profile_builder_supplement_repository_source()")
        modular_import_at = text.index("from components.profile_builder_modular import")
        self.assertLess(install_at, modular_import_at)

    def test_source_bridge_does_not_change_global_member_regimen_helpers(self):
        text = _text(SOURCE_BRIDGE)
        self.assertIn("contract.list_member_supplements = repository_rows", text)
        self.assertNotIn("components.db.list_member_supplements", text)
        self.assertIn('"source_type": "supplement_repository"', text)


if __name__ == "__main__":
    unittest.main()
