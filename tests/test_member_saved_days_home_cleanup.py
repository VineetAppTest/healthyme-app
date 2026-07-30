from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "components" / "member_saved_days_home_cleanup.py"
HOME_COLUMNS = ROOT / "components" / "member_home_side_by_side_runtime.py"
SAVED_DISPATCH = ROOT / "components" / "member_saved_days_dispatch_runtime.py"
INIT = ROOT / "components" / "__init__.py"
CONFIG = ROOT / ".streamlit" / "config.toml"
MEMBER_HOME = ROOT / "pages" / "02_Member_Home.py"
DAILY_LOG = ROOT / "pages" / "18_Daily_Log.py"


def test_member_correction_components_compile():
    for component in (COMPONENT, HOME_COLUMNS, SAVED_DISPATCH):
        compile(component.read_text(encoding="utf-8"), str(component), "exec")


def test_saved_days_filters_remain_visible_with_seven_day_default():
    source = COMPONENT.read_text(encoding="utf-8")
    assert "date_input_with_visible_saved_filters" in source
    assert "st.session_state.setdefault(key, today - dt.timedelta(days=6))" in source
    assert "st.session_state.setdefault(key, today)" in source
    assert "return current_date_input(label, *args, **kwargs)" in source
    assert "columns_without_saved_filter_layout" not in source


def test_saved_days_show_meal_section_and_comma_separated_items():
    source = COMPONENT.read_text(encoding="utf-8")
    assert "Meal Section" in source
    assert "_STRUCTURED_MEALS" in source
    assert '", ".join(items)' in source
    assert "Breakfast" in source and "Dinner" in source and "Bedtime" in source
    assert "water_litres" not in source
    assert "poop_rounds" not in source
    assert "Member Notes" not in source


def test_saved_day_dispatch_does_not_reload_the_food_form():
    component = COMPONENT.read_text(encoding="utf-8")
    dispatch = SAVED_DISPATCH.read_text(encoding="utf-8")
    assert "_render_filtered_meal_summary" in dispatch
    assert "filtered_days" in dispatch
    assert "return False" in dispatch
    assert 'st.session_state["hm_food_journal_date"]' not in component
    assert 'st.session_state["hm_food_journal_date"]' not in dispatch


def test_member_home_kpis_are_suppressed_only_on_member_home():
    source = COMPONENT.read_text(encoding="utf-8")
    assert "stat_grid_without_member_home" in source
    assert "_is_member_home_frame(caller)" in source
    assert "return current_stat_grid(*args, **kwargs)" in source
    assert "stat_grid(" in MEMBER_HOME.read_text(encoding="utf-8")


def test_messages_and_schedule_use_real_streamlit_columns_and_stack_lookup():
    source = HOME_COLUMNS.read_text(encoding="utf-8")
    assert "current_columns([1, 1], gap=\"large\")" in source
    assert "_member_home_stack_has" in source
    assert "return right.markdown" in source
    assert "return right.button" in source
    assert "return left.expander" in source
    assert "float:right" not in source
    assert "float:left" not in source


def test_streamlit_toolbar_is_minimized_without_auth_changes():
    config = CONFIG.read_text(encoding="utf-8")
    assert 'toolbarMode = "minimal"' in config
    assert "authorization_id" not in config
    assert "logout" not in config.lower()


def test_member_runtimes_are_outermost_in_correct_order():
    source = INIT.read_text(encoding="utf-8")
    assert source.index("install_admin_content_form_cleanup()") < source.index(
        "install_member_saved_days_home_cleanup()"
    )
    assert source.index("install_member_saved_days_home_cleanup()") < source.index(
        "install_member_home_side_by_side_runtime()"
    )
    assert source.index("install_member_home_side_by_side_runtime()") < source.index(
        "install_member_saved_days_dispatch_runtime()"
    )
    assert source.rstrip().endswith("install_member_saved_days_dispatch_runtime()")


def test_daily_log_data_contract_is_not_rewritten():
    source = DAILY_LOG.read_text(encoding="utf-8")
    assert "save_daily_food_journal_day" in source
    assert "get_daily_food_journal_days" in source
