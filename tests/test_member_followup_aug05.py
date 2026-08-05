from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_member_utility_row_aligns_identity_profile_and_logout_globally():
    source = (ROOT / "components" / "native_member_auth.py").read_text(
        encoding="utf-8"
    )
    assert "hm-native-member-utility-v2" in source
    assert "identity_col, profile_col, logout_col = st.columns(" in source
    assert 'key="h13r0_native_member_profile"' in source
    assert 'st.switch_page("pages/07_My_Profile.py")' in source
    assert "vertical_alignment=\"center\"" in source
    assert "grid-template-columns:minmax(0,1fr) 2.55rem 4.65rem" in source
    assert 'stElementContainer\"]:has(style#hm-native-member-utility-v2)' in source
    assert 'div[data-testid="column"]' in source


def test_member_home_archive_label_is_compact_without_changing_archive_action():
    source = (ROOT / "pages" / "02_Member_Home.py").read_text(encoding="utf-8")
    assert '"Archive",\n                            key=f"read_msg_' in source
    assert '"Read & Archive"' not in source
    assert "mark_member_message_read" in source


def test_todays_plan_ends_with_two_balanced_member_actions_only():
    view = (ROOT / "components" / "current_member_plan_view.py").read_text(
        encoding="utf-8"
    )
    page = (ROOT / "pages" / "36_Todays_Journey.py").read_text(encoding="utf-8")
    assert 'activity_col, dashboard_col = st.columns(2, gap="medium")' in view
    assert '"Today\'s Activity"' in view
    assert '"Dashboard"' in view
    assert 'st.switch_page("pages/18_Daily_Log.py")' in view
    assert 'st.switch_page("pages/02_Member_Home.py")' in view
    assert "render_page_nav" not in page


def test_daily_log_keeps_member_notes_field_but_hides_duplicate_label():
    source = (ROOT / "pages" / "18_Daily_Log.py").read_text(encoding="utf-8")
    member_notes = source[source.index('st.markdown("### Member Notes")') :]
    field = member_notes[: member_notes.index("clean_meals_payload")]
    assert 'label_visibility="collapsed"' in field
    assert '"notes": clean_notes' in source


def test_weekly_plan_uses_single_line_plus_minus_day_disclosures():
    source = (ROOT / "components" / "current_member_plan_view.py").read_text(
        encoding="utf-8"
    )
    assert 'marker = "−" if is_open else "+"' in source
    assert "target_date.strftime('%a, %d %b')" in source
    assert "white-space:nowrap!important" in source
    assert "on_click=_toggle_day_disclosure" in source
    assert "with st.expander(label, expanded=is_today):" not in source


def test_internal_member_build_footer_remains_removed():
    source = (
        ROOT / "native_bridge" / "native_bridge_full_member_app.py"
    ).read_text(encoding="utf-8")
    route_start = source.index("def _render_member_route")
    route_end = source.index("def _make_member_page", route_start)
    assert "Full Member integration build:" not in source[route_start:route_end]
