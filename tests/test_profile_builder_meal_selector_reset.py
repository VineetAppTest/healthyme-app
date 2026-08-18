from pathlib import Path


def test_meal_profile_selector_reset_is_deferred_before_widget_render():
    source = Path("components/profile_builder_modular.py").read_text(encoding="utf-8")

    assert 'from streamlit.errors import StreamlitAPIException' in source
    assert '_MEAL_PROFILE_SELECTOR = "mpb_meal_repository_profile"' in source
    assert '_MEAL_PROFILE_SELECTOR_RESET_PENDING' in source
    assert 'except StreamlitAPIException as exc:' in source
    assert '"cannot be modified after the widget with key"' in source

    render_start = source.index("def render_modular_profile_builder()")
    ensure_state = source.index("    ensure_state()", render_start)
    apply_reset = source.index(
        "    _apply_pending_meal_profile_selector_reset()", render_start
    )
    render_css = source.index("    _render_css()", render_start)

    assert ensure_state < apply_reset < render_css


def test_meal_profile_selector_guard_only_wraps_meals_section():
    source = Path("components/profile_builder_modular.py").read_text(encoding="utf-8")

    assert "_render_meals_with_selector_reset_guard(can_publish)" in source
    assert "render_member_plan_exercise()" in source
    assert "render_member_plan_supplement()" in source
    assert "render_view_member_plan_compact()" in source
