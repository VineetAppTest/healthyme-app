from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SUPPLEMENT_PAGE = ROOT / "pages" / "39_Admin_Supplement_Manager.py"
PROFILE_PAGE = ROOT / "pages" / "38_Admin_Recommendation_Profile_Builder.py"
REPOSITORY = ROOT / "components" / "supplement_repository.py"
SOURCE_BRIDGE = ROOT / "components" / "supplement_repository_source.py"


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_changed_python_files_compile():
    for path in [SUPPLEMENT_PAGE, PROFILE_PAGE, REPOSITORY, SOURCE_BRIDGE]:
        ast.parse(_text(path), filename=str(path))


def test_supplement_manager_is_repository_only():
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
        assert token not in text

    assert "Current Repository" in text
    assert "Add to Repository" in text
    assert "Member allocation is managed only through Recommendation Profile Builder" in text


def test_repository_migration_preserves_member_rows():
    text = _text(REPOSITORY)
    assert 'db.get("member_supplements", [])' in text
    assert 'db["member_supplements"]' not in text
    assert '"member_regimens_unchanged": True' in text


def test_profile_builder_installs_repository_source_before_modular_import():
    text = _text(PROFILE_PAGE)
    install_at = text.index("install_profile_builder_supplement_repository_source()")
    modular_import_at = text.index("from components.profile_builder_modular import")
    assert install_at < modular_import_at


def test_source_bridge_does_not_change_global_member_regimen_helpers():
    text = _text(SOURCE_BRIDGE)
    assert "contract.list_member_supplements = repository_rows" in text
    assert "components.db.list_member_supplements" not in text
    assert '"source_type": "supplement_repository"' in text
