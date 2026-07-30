from pathlib import Path


# Presentation-only regression coverage for Member Home and upload controls.
ROOT = Path(__file__).resolve().parents[1]
HOME_RUNTIME = ROOT / "components" / "member_home_side_by_side_runtime.py"
UPLOADER = ROOT / "components" / "file_uploader_presentation.py"
INIT = ROOT / "components" / "__init__.py"


def test_presentation_components_compile():
    for path in (HOME_RUNTIME, UPLOADER):
        compile(path.read_text(encoding="utf-8"), str(path), "exec")


def test_messages_use_the_same_native_expander_control_as_schedule():
    source = HOME_RUNTIME.read_text(encoding="utf-8")
    assert 'right.expander("Messages from Nutritionist", expanded=True)' in source
    assert "hm-messages-nutritionist-anchor-v4" in source
    assert 'return box.markdown' in source
    assert 'return box.button' in source
    assert "hm_member_home_messages_expanded" not in source
    assert "hm_member_home_messages_toggle" not in source


def test_schedule_and_messages_have_identical_pill_dimensions_and_alignment():
    source = HOME_RUNTIME.read_text(encoding="utf-8")
    assert 'current_columns([1, 1], gap="large")' in source
    assert 'return left.expander' in source
    assert 'align-items:flex-start' in source
    assert 'width:285px' in source
    assert 'min-height:2.12rem' in source
    assert 'height:2.12rem' in source
    assert '.hm-upcoming-schedule-anchor' in source
    assert '.hm-messages-nutritionist-anchor-v4' in source


def test_active_task_panel_is_visually_prioritised_without_rewriting_task_logic():
    source = HOME_RUNTIME.read_text(encoding="utf-8")
    assert 'stVerticalBlockBorderWrapper"]:has(.hm-v990-task-progress)' in source
    assert 'content:"Action required"' in source
    assert '.hm-v990-due-date' in source
    assert '.hm-v990-task-chip.pending' in source
    for forbidden in (
        "requested_pages =",
        "task_status_done_v96_2",
        "submitted_for_review",
        "switch_page(\"pages/04_NSP_Page1.py\")",
        "switch_page(\"pages/05_NSP_Page2.py\")",
    ):
        assert forbidden not in source


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
