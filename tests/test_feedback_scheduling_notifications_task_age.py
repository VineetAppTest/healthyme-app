from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCHEDULE = ROOT / "components" / "admin_schedule_feedback_aug04.py"
ADMIN_DASHBOARD = ROOT / "pages" / "10_Admin_Dashboard.py"
ADMIN_DASHBOARD_REMINDER = ROOT / "components" / "admin_dashboard_schedule_reminder.py"
SCHEDULE_POLISH = ROOT / "components" / "admin_schedule_disclosure_polish.py"
SCHEDULE_PAGE = ROOT / "pages" / "32_Admin_Scheduling.py"
EXERCISE = ROOT / "components" / "member_plan_builder_exercise.py"
NOTIFICATIONS = ROOT / "components" / "member_allocation_notifications.py"
TASK_AGE = ROOT / "components" / "member_task_pending_age.py"
APP_HEADER = ROOT / "components" / "streamlit_app_header_regression_guard.py"
BOOTSTRAP = ROOT / "components" / "__init__.py"


class FeedbackSchedulingNotificationsTaskAgeTests(unittest.TestCase):
    def test_changed_python_files_compile(self):
        for path in (
            SCHEDULE,
            ADMIN_DASHBOARD,
            ADMIN_DASHBOARD_REMINDER,
            SCHEDULE_POLISH,
            SCHEDULE_PAGE,
            EXERCISE,
            NOTIFICATIONS,
            TASK_AGE,
            APP_HEADER,
            BOOTSTRAP,
        ):
            compile(path.read_text(encoding="utf-8"), str(path), "exec")

    def test_admin_dashboard_shows_read_only_48_hour_schedule_intimation(self):
        source = ADMIN_DASHBOARD_REMINDER.read_text(encoding="utf-8")
        dashboard = ADMIN_DASHBOARD.read_text(encoding="utf-8")
        self.assertIn("def upcoming_admin_schedule_rows", source)
        self.assertIn("hours: int = 48", source)
        self.assertIn("window_end = now_value + dt.timedelta(hours=hours)", source)
        self.assertIn("Upcoming Schedule for Admin", source)
        self.assertIn("Next 48 hrs", source)
        self.assertIn("Practitioner Time", source)
        self.assertIn("Open Scheduling", source)
        self.assertIn("load_state()", source)
        self.assertNotIn("save_state", source)
        self.assertNotIn("update_member_schedule_status", source)
        self.assertIn("render_admin_upcoming_schedule_reminder", dashboard)

    def test_schedule_is_full_width_and_sharply_structured(self):
        source = SCHEDULE.read_text(encoding="utf-8")
        page = SCHEDULE_PAGE.read_text(encoding="utf-8")

        self.assertNotIn("st.columns([3, 1]", source)
        self.assertIn("type_col, title_col = st.columns([0.85, 1.35]", source)
        self.assertIn("date_col, start_col, end_col = st.columns(3", source)

        schedule_panel = source.index("selected_day_rows = _admin_schedule_for_date(")
        mode_row = source.index("mode_col, location_col = st.columns")
        self.assertLess(schedule_panel, mode_row)
        self.assertIn("_render_day_schedule(selected_day_rows, schedule_date)", source)

        for label in (
            "Schedule date",
            "Name of Member",
            "Schedule Time",
            "Subject",
        ):
            self.assertIn(label, source)
        self.assertIn("_admin_schedule_for_date(", source)
        self.assertIn("schedule_time_context", source)
        self.assertIn("install_admin_schedule_feedback(admin_scheduling)", page)
        self.assertNotIn(
            "Only this workspace section is rendered. A successful creation opens a fresh transaction form",
            source,
        )

    def test_schedule_uses_app_standard_direct_disclosure_and_safe_table(self):
        source = SCHEDULE_POLISH.read_text(encoding="utf-8")
        page = SCHEDULE_PAGE.read_text(encoding="utf-8")
        self.assertIn('marker = "−" if is_open else "+"', source)
        self.assertIn("Admin schedule · {len(rows)} {meeting_word}", source)
        self.assertIn("st.button(", source)
        self.assertNotIn("st.expander(", source)
        self.assertIn("hm-sched-polish-table-card", source)
        self.assertIn("overflow-x:auto!important", source)
        self.assertIn("table-layout:fixed!important", source)
        self.assertIn("white-space:nowrap!important", source)
        self.assertIn("install_admin_schedule_disclosure_polish", page)
        self.assertIn("No meeting is scheduled on the selected date", source)

    def test_schedule_success_queues_cleanup_before_new_transaction(self):
        source = SCHEDULE.read_text(encoding="utf-8")
        self.assertIn("_consume_pending_reset(scheduling_module)", source)
        self.assertIn("_clear_transaction_prefix", source)
        cleanup = source.index(
            "st.session_state[scheduling_module._CREATE_CLEANUP_KEY] = version"
        )
        next_version = source.index(
            "st.session_state[scheduling_module._CREATE_VERSION_KEY] = version + 1"
        )
        rerun = source.index("st.rerun()", next_version)
        self.assertLess(cleanup, next_version)
        self.assertLess(next_version, rerun)
        self.assertIn("A fresh form is ready for the next schedule", source)

    def test_schedule_read_model_is_read_only_against_identity_authority(self):
        source = SCHEDULE.read_text(encoding="utf-8")
        polish = SCHEDULE_POLISH.read_text(encoding="utf-8")
        self.assertIn("from components.storage_backend import load_state", source)
        for text in (source, polish):
            self.assertNotIn("get_user_by_id", text)
            self.assertNotIn('get("users"', text)
            self.assertNotIn("save_state", text)

    def test_exercise_feedback_disclosure_and_equal_compact_notes(self):
        source = EXERCISE.read_text(encoding="utf-8")
        self.assertIn("mpb-exercise-more-details-anchor", source)
        self.assertIn('content:"+"', source)
        self.assertIn('content:"−"', source)
        self.assertIn("note_cols = st.columns(2", source)
        self.assertGreaterEqual(source.count('height=60'), 4)
        self.assertNotIn('note_cols[1].text_input(', source)
        self.assertIn("Reps/Duration:", source)
        self.assertIn("delivery_summary", source)
        self.assertIn("available in View Member Plan", source)
        self.assertIn('st.success(f"✓ {flash}")', source)

    def test_allocations_write_visible_member_messages_with_benefits(self):
        source = NOTIFICATIONS.read_text(encoding="utf-8")
        bootstrap = BOOTSTRAP.read_text(encoding="utf-8")
        self.assertIn('state.setdefault("messages", []).append(message_row)', source)
        self.assertIn('state.setdefault("notifications", []).append(notification)', source)
        self.assertIn('"Benefits": benefits', source)
        self.assertIn('"benefits": benefits', source)
        self.assertIn("exercise_api.save_exercise_member_allocation", source)
        self.assertIn("supplement_api.save_supplement_member_allocation", source)
        self.assertIn("supplement_api.stop_supplement_member_allocation", source)
        self.assertIn("queue_member_event_email", source)
        self.assertIn("queue_meal_plan_allocation", source)
        self.assertIn("member-allocation-email-v2", source)
        self.assertIn("meal-plan-allocation-email-v2", source)
        self.assertIn("install_member_allocation_notifications()", bootstrap)

    def test_notification_delivery_does_not_invoke_identity_write_paths(self):
        source = NOTIFICATIONS.read_text(encoding="utf-8")
        self.assertNotIn("get_user_by_id", source)
        self.assertNotIn('get("users"', source)
        self.assertNotIn('setdefault("users"', source)
        self.assertIn('saved.get("member_email")', source)

    def test_pending_age_is_one_adjacent_badge_not_duplicate_action_text(self):
        source = TASK_AGE.read_text(encoding="utf-8")
        bootstrap = BOOTSTRAP.read_text(encoding="utf-8")

        self.assertIn("today - due_date", source)
        self.assertIn("Task is pending for {delta} {unit}", source)
        self.assertIn("hm-task-alert-row", source)
        rendered_badge = "<span class='hm-task-alert-pill'>ACTION REQUIRED</span>"
        self.assertEqual(source.count(rendered_badge), 1)
        self.assertIn("_RUNTIME_STYLE", source)
        self.assertIn("hm-member-task-pending-age-runtime-v2", source)
        self.assertIn(".hm-v990-task-progress::before", source)
        self.assertIn("display:none!important", source)
        self.assertIn("content:none!important", source)
        self.assertIn("white-space:nowrap!important", source)
        self.assertIn("install_member_task_pending_age()", bootstrap)

        runtime_style = source.index("_RUNTIME_STYLE")
        alert_row = source.index("<div class='hm-task-alert-row'>")
        self.assertLess(runtime_style, alert_row)

    def test_new_streamlit_app_header_is_hidden_globally(self):
        source = APP_HEADER.read_text(encoding="utf-8")
        bootstrap = BOOTSTRAP.read_text(encoding="utf-8")
        self.assertIn('[data-testid="stAppHeader"]', source)
        self.assertIn('[data-testid="stAppHeaderActions"]', source)
        self.assertIn('button[aria-label="Share this app"]', source)
        self.assertIn("install_streamlit_app_header_regression_guard()", bootstrap)


if __name__ == "__main__":
    unittest.main()
