from pathlib import Path


# Presentation-only regression coverage for Member Home and upload controls.
ROOT = Path(__file__).resolve().parents[1]
HOME_RUNTIME = ROOT / "components" / "member_home_side_by_side_runtime.py"
HOME_PAGE = ROOT / "pages" / "02_Member_Home.py"
PRESENTATION = ROOT / "components" / "member_home_schedule_presentation.py"
UPLOADER = ROOT / "components" / "file_uploader_presentation.py"
INIT = ROOT / "components" / "__init__.py"


def test_presentation_components_compile():
    for path in (HOME_RUNTIME, PRESENTATION, UPLOADER):
        compile(path.read_text(encoding="utf-8"), str(path), "exec")


def test_messages_and_consultations_use_separate_native_expanders():
    page = HOME_PAGE.read_text(encoding="utf-8")
    assert 'with st.expander("Message from Nutritionist", expanded=True)' in page
    assert 'f"Upcoming Consultation ({len(upcoming_schedules)})"' in page
    assert "hm-message-pill-anchor" in page
    assert "hm-upcoming-schedule-anchor" in page
    assert "hm_member_home_messages_toggle" not in page


def test_schedule_and_messages_share_compact_pill_contract():
    source = PRESENTATION.read_text(encoding="utf-8")
    assert ':has(.hm-upcoming-schedule-anchor)' in source
    assert ':has(.hm-message-pill-anchor)' in source
    assert 'min-height:2.12rem!important' in source
    assert 'width:max-content!important' in source
    assert 'min-width:15.5rem!important' in source
    assert 'justify-content:flex-start!important' in source
    assert 'text-align:left!important' in source
    assert 'width:fit-content!important;max-width:100%!important;min-width:0!important' not in source
    assert 'summary + div' in source
    assert 'border:0!important' in source


def test_home_cards_use_three_by_two_grids_without_relocation_runtime():
    page = HOME_PAGE.read_text(encoding="utf-8")
    runtime = HOME_RUNTIME.read_text(encoding="utf-8")
    assert 'range(0, len(upcoming_schedules), 3)' in page
    assert 'range(0, len(unique_messages), 3)' in page
    assert page.count('st.columns(3, gap="small")') >= 2
    assert 'without relocating page sections' in runtime
    assert 'return left.expander' not in runtime
    assert 'return right.expander' not in runtime


def test_task_due_state_uses_india_date_and_distinct_green_red_styles():
    source = HOME_RUNTIME.read_text(encoding="utf-8")
    styles = (ROOT / "components" / "member_task_pending_age.py").read_text(
        encoding="utf-8"
    )
    assert 'ZoneInfo("Asia/Kolkata")' in source
    assert 'due_date < today' in source
    assert 'hm-task-before-due' in source
    assert 'hm-task-overdue' in source
    assert '#22C55E' in styles
    assert '#DC2626' in styles


def test_completed_nsp_buttons_are_relabelled_and_disabled_without_data_writes():
    source = HOME_RUNTIME.read_text(encoding="utf-8")
    assert '"nsp1_completed", "NSP Page 1 Done"' in source
    assert '"nsp2_completed", "NSP Page 2 Done"' in source
    assert 'kwargs["disabled"] = True' in source
    assert '_member_home_frame("_render_task_progress")' in source
    for forbidden in (
        "update(",
        "insert(",
        "delete(",
        "upsert(",
        'switch_page("pages/04_NSP_Page1.py")',
        'switch_page("pages/05_NSP_Page2.py")',
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


def test_presentation_patch_does_not_modify_auth_or_package_contracts():
    source = PRESENTATION.read_text(encoding="utf-8") + UPLOADER.read_text(encoding="utf-8")
    for forbidden in (
        "session_counted =",
        "package_usage",
        "authorization_id",
        "require_admin",
        "supabase",
    ):
        assert forbidden not in source
