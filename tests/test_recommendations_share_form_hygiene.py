from pathlib import Path
import py_compile


ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "components" / "recommendations_share_form_hygiene.py"
INIT = ROOT / "components" / "__init__.py"
PAGE = ROOT / "pages" / "35_Admin_Recommendations_Share.py"


def test_runtime_and_page_compile():
    for path in (COMPONENT, INIT, PAGE):
        py_compile.compile(str(path), doraise=True)


def test_member_scoping_and_success_only_reload():
    source = COMPONENT.read_text(encoding="utf-8")
    assert '_WIDGET_PREFIX = "hm_v1024_"' in source
    assert '_MEMBER_SELECTOR_KEY = "hm_v1024_rec_member"' in source
    assert 'member_id = str(frame.f_locals.get("member_id")' in source
    assert 'f"{text}__member_{scope}__v{_version(scope)}"' in source
    assert 'text == "Draft saved."' in source
    assert 'text.startswith("Recommendations shared.")' in source
    assert source.count("_advance(scope)") == 1


def test_existing_rerun_is_reused_without_database_changes():
    source = COMPONENT.read_text(encoding="utf-8")
    page = PAGE.read_text(encoding="utf-8")
    assert "st.rerun()" not in source
    assert "st.rerun()" in page
    for forbidden in (
        "save_recommendation_share(",
        "get_latest_recommendation_share(",
        "list_members(",
        ".table(",
    ):
        assert forbidden not in source
