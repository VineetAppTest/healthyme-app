from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "components" / "member_saved_days_home_cleanup.py"
INIT = ROOT / "components" / "__init__.py"
CONFIG = ROOT / ".streamlit" / "config.toml"
MEMBER_HOME = ROOT / "pages" / "02_Member_Home.py"
DAILY_LOG = ROOT / "pages" / "18_Daily_Log.py"


def test_cleanup_component_compiles():
    compile(COMPONENT.read_text(encoding="utf-8"), str(COMPONENT), "exec")


def test_saved_days_is_fixed_to_seven_days_and_meals_only():
    source = COMPONENT.read_text(encoding="utf-8")
    assert "today - dt.timedelta(days=6)" in source
    assert "_STRUCTURED_MEALS" in source
    assert "Breakfast" in source and "Dinner" in source and "Bedtime" in source
    assert "water_litres" not in source
    assert "poop_rounds" not in source
    assert "Member Notes" not in source


def test_saved_days_buttons_do_not_reload_the_food_form():
    source = COMPONENT.read_text(encoding="utf-8")
    assert "_SAVED_BUTTON_PREFIX = \"hm_h9a4c_load_\"" in source
    assert "button_with_static_saved_summary" in source
    assert "return False" in source
    assert "st.session_state[\"hm_food_journal_date\"]" not in source


def test_member_home_kpis_are_suppressed_only_on_member_home():
    source = COMPONENT.read_text(encoding="utf-8")
    assert "stat_grid_without_member_home" in source
    assert "_is_member_home_frame(caller)" in source
    assert "return current_stat_grid(*args, **kwargs)" in source
    assert "stat_grid(" in MEMBER_HOME.read_text(encoding="utf-8")


def test_messages_and_schedule_receive_balanced_desktop_columns():
    source = COMPONENT.read_text(encoding="utf-8")
    assert ".hm-b13-message-shell{float:right" in source
    assert "stExpander\"]:has(.hm-upcoming-schedule-anchor){float:left" in source
    assert "width:47%" in source
    assert "clear:both" in source


def test_streamlit_toolbar_is_minimized_without_auth_changes():
    config = CONFIG.read_text(encoding="utf-8")
    assert 'toolbarMode = "minimal"' in config
    assert "authorization_id" not in config
    assert "logout" not in config.lower()


def test_cleanup_is_installed_after_prior_member_runtime_layers():
    source = INIT.read_text(encoding="utf-8")
    assert "install_member_saved_days_home_cleanup" in source
    assert source.rfind("install_member_saved_days_home_cleanup()") > source.rfind(
        "install_member_post_optimization_cleanup()"
    )


def test_daily_log_data_contract_is_not_rewritten():
    source = DAILY_LOG.read_text(encoding="utf-8")
    assert "save_daily_food_journal_day" in source
    assert "get_daily_food_journal_days" in source
