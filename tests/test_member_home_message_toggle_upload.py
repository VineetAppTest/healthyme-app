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
    assert "hm-messages-nutritionist-anchor-v5" in source
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
    assert '.hm-messages-nutritionist-anchor-v5' in source
    assert 'summary+div' in source
    assert 'border:0!important' in source


def test_home_gap_and_message_card_match_schedule_presentation():
    source = HOME_RUNTIME.read_text(encoding="utf-8")
    assert '.hero-shell{margin-bottom:.20rem!important;}' in source
    assert 'margin:-1.05rem 0 .82rem 0' in source
    assert '.hm-b13-message-card' in source
    assert 'border-radius:18px!important' in source
    assert 'padding:.80rem .95rem!important' in source
    assert 'background:linear-gradient(180deg,#FFFDF8 0%,#FFF9EC 100%)' in source


def test_task_due_state_uses_india_date_and_distinct_green_red_styles():
    source = HOME_RUNTIME.read_text(encoding="utf-8")
    assert 'ZoneInfo("Asia/Kolkata")' in source
    assert 'due_date < today' in source
    assert 'hm-task-before-due' in source
    assert 'hm-task-overdue' in source
    assert '#22C55E' in source
    assert '#DC2626' in source
    assert 'font-size:.90rem' in source
    assert 'font-size:.84rem' in source


def test_completed_nsp_buttons_are_relabelled_and_disabled_without_data_writes():
    source = HOME_RUNTIME.read_text(encoding="utf-8")
    assert '"nsp1_completed", "NSP Page 1 Completed"' in source
    assert '"nsp2_completed", "NSP Page 2 Completed"' in source
    assert 'kwargs["disabled"] = True' in source
    assert '_member_home_frame("_render_task_progress")' in source
    for forbidden in (
        "update(",
        "insert(",
        "delete(",
        "upsert(",
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
