from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOME_RUNTIME = ROOT / "components" / "member_home_side_by_side_runtime.py"
UPLOADER = ROOT / "components" / "file_uploader_presentation.py"
INIT = ROOT / "components" / "__init__.py"


def test_presentation_components_compile():
    for path in (HOME_RUNTIME, UPLOADER):
        compile(path.read_text(encoding="utf-8"), str(path), "exec")


def test_messages_have_a_persistent_expand_collapse_control():
    source = HOME_RUNTIME.read_text(encoding="utf-8")
    assert "hm_member_home_messages_expanded" in source
    assert "Messages from Nutritionist" in source
    assert "not open_now" in source
    assert 'right.button(' in source
    assert 'return right.markdown' in source
    assert 'return right.button' in source


def test_schedule_and_messages_share_real_aligned_columns():
    source = HOME_RUNTIME.read_text(encoding="utf-8")
    assert 'current_columns([1, 1], gap="large")' in source
    assert 'return left.expander' in source
    assert 'align-items:flex-start' in source
    assert 'width:285px' in source


def test_uploader_icon_font_and_button_layout_are_restored():
    source = UPLOADER.read_text(encoding="utf-8")
    assert '[data-testid="stFileUploader"] [data-testid="stIconMaterial"]' in source
    assert 'Material Symbols Rounded' in source
    assert 'font-feature-settings:"liga"' in source
    assert 'display:inline-flex' in source
    assert 'white-space:nowrap' in source
    assert 'return current(*args, **kwargs)' in source


def test_uploader_cleanup_is_installed_before_admin_widget_isolation():
    source = INIT.read_text(encoding="utf-8")
    assert "install_file_uploader_presentation" in source
    assert source.index("install_file_uploader_presentation()") < source.index(
        "install_admin_content_form_cleanup()"
    )


def test_presentation_patch_does_not_modify_business_contracts():
    source = HOME_RUNTIME.read_text(encoding="utf-8") + UPLOADER.read_text(encoding="utf-8")
    for forbidden in (
        "list_upcoming_member_schedules",
        "mark_member_message_read",
        "schedule_status",
        "session_counted",
        "package_usage",
        "authorization_id",
        "require_member",
        "require_admin",
        "supabase",
    ):
        assert forbidden not in source
