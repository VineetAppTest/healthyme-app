from __future__ import annotations

import datetime as dt
import pathlib
import unittest

from components.member_exercise_journal_table import (
    build_exercise_log_payload,
    saved_exercise_dates,
)


ROOT = pathlib.Path(__file__).resolve().parents[1]


class MemberScheduleTabsExerciseJournalTests(unittest.TestCase):
    def test_my_schedule_uses_exact_three_sections_and_preserves_actions(self):
        source = (ROOT / "components/member_schedule_tabbed_page.py").read_text()
        self.assertIn(
            '_SECTIONS = ("Package Subscribed", "Upcoming Schedule", "Session Usage")',
            source,
        )
        self.assertNotIn("st.tabs(", source)
        self.assertIn("on_click=_activate_section", source)
        self.assertIn('if selected == "Package Subscribed"', source)
        self.assertIn('elif selected == "Upcoming Schedule"', source)
        self.assertIn("schedule_ui._render_package", source)
        self.assertIn("schedule_ui._render_member_ledger", source)
        self.assertIn("Acknowledge schedule", source)
        self.assertIn("Request Reschedule", source)
        self.assertIn("Submit Reschedule Request", source)

    def test_my_schedule_navigation_renders_before_slow_reads(self):
        source = (ROOT / "components/member_schedule_tabbed_page.py").read_text()
        self.assertEqual(source.count("schedule_ui.render_page_nav("), 1)
        page_renderer = source.index("def render_tabbed_member_schedule_page")
        navigation = source.index("schedule_ui.render_page_nav(", page_renderer)
        timezone_read = source.index("schedule_ui.member_timezone_name(", page_renderer)
        self.assertLess(navigation, timezone_read)
        self.assertIn('location="top"', source)

    def test_my_schedule_renders_only_selected_section_and_avoids_eager_rpcs(self):
        source = (ROOT / "components/member_schedule_tabbed_page.py").read_text()
        selector = source.index("selected = _render_section_selector()")
        package_branch = source.index('if selected == "Package Subscribed"', selector)
        upcoming_branch = source.index('elif selected == "Upcoming Schedule"', selector)
        usage_branch = source.index("else:", upcoming_branch)
        package_read = source.index("schedule_ui._render_package", package_branch)
        upcoming_read = source.index("_render_upcoming_section", upcoming_branch)
        ledger_read = source.index("schedule_ui._render_member_ledger", usage_branch)
        self.assertLess(package_branch, package_read)
        self.assertLess(upcoming_branch, upcoming_read)
        self.assertLess(usage_branch, ledger_read)
        self.assertNotIn("package_tab, upcoming_tab, usage_tab", source)

    def test_my_schedule_and_daily_log_use_member_home_spacing(self):
        schedule = (ROOT / "components/member_schedule_tabbed_page.py").read_text()
        daily = (
            ROOT / "components/member_exercise_journal_table_bootstrap.py"
        ).read_text()
        for source in (schedule, daily):
            self.assertIn("padding-top:0!important", source)
            self.assertIn("stHeader", source)
            self.assertIn(".hero-shell", source)
        self.assertIn("hm-member-schedule-nav-anchor", schedule)
        self.assertIn("hm-member-schedule-selector-anchor", schedule)
        self.assertIn("margin:.04rem 0 .06rem 0", schedule)
        self.assertIn("hm-daily-log-journal-selector-v5", daily)

    def test_my_schedule_page_uses_selected_renderer_and_keeps_measurement(self):
        source = (ROOT / "pages/33_My_Schedule.py").read_text()
        self.assertIn("render_tabbed_member_schedule_page", source)
        self.assertIn('begin_page_measurement("Member My Schedule")', source)
        self.assertIn('finish_and_render_page_diagnostics("Member My Schedule")', source)

    def test_member_selected_values_are_saved_to_daily_log_payload(self):
        payload = build_exercise_log_payload(
            member_id="member-1",
            log_date="2026-07-29",
            profile={"id": "profile-1", "profile_name": "Starter"},
            day_number=2,
            item_order=1,
            selected_activity="Walk & Stretches",
            selected_timing="Night",
            selected_duration="30 min & 2 sets of 10",
            remarks="Completed comfortably",
            status="Completed",
            completion_time=dt.time(22, 0),
            selected_definition={
                "difficulty": "Easy",
                "equipment": "None",
                "benefits": "Mobility",
                "instruction": "Walk, then stretch",
                "image_reference": "",
            },
        )
        self.assertEqual(payload["exercise_name"], "Walk & Stretches")
        self.assertEqual(payload["scheduled_time"], "Night")
        self.assertEqual(payload["duration_or_reps"], "30 min & 2 sets of 10")
        self.assertEqual(payload["member_notes"], "Completed comfortably")
        self.assertEqual(payload["completion_time"], "22:00")
        self.assertEqual(payload["status"], "Completed")

    def test_exercise_journal_has_editable_requested_columns(self):
        source = (ROOT / "components/member_exercise_journal_layout_v4.py").read_text()
        for label in ("Timing", "Activity", "Duration / Sets", "Remarks"):
            self.assertIn(label, source)
        self.assertIn("st.selectbox", source)
        self.assertIn("st.text_input", source)
        self.assertIn("Save Exercise Entry", source)
        self.assertIn("Status", source)
        self.assertIn("Completion time (optional)", source)

    def test_zero_assignment_day_still_renders_editable_structure(self):
        source = (ROOT / "components/member_exercise_journal_layout_v4.py").read_text()
        self.assertIn("base_count = max(1, len(assigned), len(existing_rows))", source)
        self.assertIn("for index in range(1, row_count + 1)", source)
        self.assertIn("+ Add Exercise", source)
        self.assertNotIn("No exercise is assigned for this date", source)
        self.assertNotIn("Progress for", source)

    def test_activity_options_use_active_exercise_repository(self):
        source = (ROOT / "components/member_exercise_journal_table.py").read_text()
        self.assertIn('list_repository_items("exercises", active_only=True)', source)
        self.assertIn("exercise_snapshot", source)
        self.assertIn("repository_activity_catalog()", source)

    def test_exercise_journal_uses_normal_palette_and_compact_time(self):
        base_source = (ROOT / "components/member_exercise_journal_table.py").read_text()
        layout_source = (ROOT / "components/member_exercise_journal_layout_v4.py").read_text()
        self.assertIn("hm-exercise-journal-table-v3", base_source)
        self.assertIn("#064E3B", base_source)
        self.assertNotIn("#FFF7E6", base_source)
        self.assertNotIn("hm-exercise-table-head", layout_source)
        self.assertNotIn('st.time_input("Completion time"', layout_source)
        self.assertIn("Example: 10:30 PM", layout_source)

    def test_exercise_actions_follow_all_exercise_rows(self):
        source = (ROOT / "components/member_exercise_journal_layout_v4.py").read_text()
        row_loop = source.index("for index in range(1, row_count + 1)")
        add_action = source.index('"+ Add Exercise"')
        saved_days = source.index("base._render_saved_days")
        self.assertLess(row_loop, add_action)
        self.assertLess(add_action, saved_days)
        self.assertIn('"Remove Exercise"', source)

    def test_daily_log_hides_duplicate_heading_and_aligns_date_spacing(self):
        bootstrap = (
            ROOT / "components/member_exercise_journal_table_bootstrap.py"
        ).read_text()
        self.assertIn('kwargs["heading"] = ""', bootstrap)
        self.assertIn('kwargs["show_build_note"] = False', bootstrap)
        self.assertIn("hm-daily-log-selector-anchor", bootstrap)
        self.assertIn("margin:.02rem 0 .06rem 0", bootstrap)
        self.assertIn("style#hm-exercise-journal-table-v3", bootstrap)
        self.assertIn("style#hm-exercise-journal-layout-v4", bootstrap)

    def test_food_saved_day_is_staged_before_date_widget_instantiation(self):
        bootstrap = (
            ROOT / "components/member_exercise_journal_table_bootstrap.py"
        ).read_text()
        self.assertIn('_FOOD_PENDING_DATE_KEY = "hm_food_journal_pending_date"', bootstrap)
        self.assertIn("button_with_safe_saved_day_callback", bootstrap)
        self.assertIn("date_input_with_pending_saved_day", bootstrap)
        self.assertIn("st.session_state[_FOOD_PENDING_DATE_KEY] = saved_date", bootstrap)
        self.assertIn("return False", bootstrap)
        pending_apply = bootstrap.index("st.session_state[_FOOD_DATE_KEY] = parsed")
        widget_create = bootstrap.index("return current_date_input(label, *args, **kwargs)")
        self.assertLess(pending_apply, widget_create)

    def test_other_fluid_time_uses_one_compact_editable_field(self):
        bootstrap = (
            ROOT / "components/member_exercise_journal_table_bootstrap.py"
        ).read_text()
        self.assertIn('_FLUID_TIME_PREFIX = "hm_h9a4c_fluid_time_"', bootstrap)
        self.assertIn("time_input_with_compact_fluid_field", bootstrap)
        self.assertIn("current_text_input(label, **text_kwargs)", bootstrap)
        self.assertIn('"placeholder": "Example: 10:30 PM"', bootstrap)
        self.assertIn("%I:%M %p", bootstrap)

    def test_exercise_journal_has_saved_days_matching_food_pattern(self):
        source = (ROOT / "components/member_exercise_journal_table.py").read_text()
        self.assertIn("### View Saved Days", source)
        self.assertIn('st.date_input("From"', source)
        self.assertIn('st.date_input("To"', source)
        self.assertIn("pending_key", source)
        dates = saved_exercise_dates(
            [
                {"log_date": "2026-07-27"},
                {"log_date": "2026-07-29"},
                {"log_date": "2026-07-27"},
            ]
        )
        self.assertEqual(
            dates,
            [dt.date(2026, 7, 29), dt.date(2026, 7, 27)],
        )

    def test_member_package_inclusion_rule_is_hidden_only_on_member_page(self):
        helper = (
            ROOT / "components/member_schedule_member_copy_cleanup.py"
        ).read_text()
        page = (ROOT / "pages/33_My_Schedule.py").read_text()
        self.assertIn(".hm-package-summary .hm-package-line:has(> i)", helper)
        self.assertIn("if member_view", helper)
        self.assertIn("install_member_schedule_package_copy_cleanup", page)
        self.assertLess(
            page.index("install_package_hardening_schedule_ui"),
            page.index("install_member_schedule_package_copy_cleanup(schedule_timezone_ui)"),
        )
        self.assertLess(
            page.index("install_member_schedule_package_copy_cleanup(schedule_timezone_ui)"),
            page.index("render_tabbed_member_schedule_page(schedule_timezone_ui)"),
        )

    def test_exercise_journal_does_not_write_to_profile_or_repository(self):
        source = (ROOT / "components/member_exercise_journal_layout_v4.py").read_text()
        for forbidden in (
            "hm_recommendation_profiles",
            "hm_recommendation_profile_items",
            "save_recommendation",
            "update_recommendation",
            "save_exercise_repository",
        ):
            self.assertNotIn(forbidden, source)
        self.assertIn("base.save_member_exercise_log", source)

    def test_shared_renderer_bootstrap_keeps_both_entry_points_aligned(self):
        bootstrap = (
            ROOT / "components/member_exercise_journal_table_bootstrap.py"
        ).read_text()
        components_init = (ROOT / "components/__init__.py").read_text()
        self.assertIn("render_member_exercise_journal_layout_v4", bootstrap)
        self.assertIn(
            "journal.render_member_exercise_journal = contextual_exercise_renderer",
            bootstrap,
        )
        self.assertIn("install_member_exercise_journal_table()", components_init)

    def test_daily_log_selector_is_stable_and_renders_one_journal(self):
        bootstrap = (
            ROOT / "components/member_exercise_journal_table_bootstrap.py"
        ).read_text()
        page = (ROOT / "pages/18_Daily_Log.py").read_text()
        self.assertIn('_DAILY_LOG_LABELS = ("Food Journal", "Exercise Journal")', bootstrap)
        self.assertIn('st.button(\n                "Food Journal"', bootstrap)
        self.assertIn('st.button(\n                "Exercise Journal"', bootstrap)
        self.assertIn('type=(\n                    "primary"', bootstrap)
        self.assertIn("on_click=_activate_daily_log_journal", bootstrap)
        self.assertNotIn("st.segmented_control", bootstrap)
        self.assertIn("contextlib.nullcontext()", bootstrap)
        self.assertIn("render_food_only_when_selected", bootstrap)
        self.assertIn("render_exercise_only_when_selected", bootstrap)
        self.assertIn("pages/18_Daily_Log.py", bootstrap)
        self.assertIn('st.tabs(["Food Journal", "Exercise Journal"])', page)
        for forbidden in (
            "save_daily_food_journal_day",
            "save_member_exercise_log",
            "require_member",
            "switch_page",
        ):
            self.assertNotIn(forbidden, bootstrap)

    def test_member_corrections_do_not_change_auth_routing_or_business_writes(self):
        bootstrap = (
            ROOT / "components/member_exercise_journal_table_bootstrap.py"
        ).read_text()
        schedule = (ROOT / "components/member_schedule_tabbed_page.py").read_text()
        for source in (bootstrap, schedule):
            for forbidden in (
                "logout_current_user",
                "require_admin",
                "save_db(",
                "assign_or_replace_member_package(",
                "update_member_schedule_status(",
            ):
                self.assertNotIn(forbidden, source)

    def test_member_diagnostics_are_single_and_cover_member_home(self):
        source = (ROOT / "components/performance_measurement_gate.py").read_text()
        self.assertIn("back_to_top_with_visible_start", source)
        self.assertIn("keepalive_with_member_home_start", source)
        self.assertIn('page_name == "Member Home"', source)
        self.assertIn("diagnostics.finish_page_measurement(resolved_page)", source)
        self.assertIn("Member pages use the direct panel below", source)
        for forbidden in (
            "st.switch_page",
            "logout_current_user",
            "require_admin",
            "require_member",
        ):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
