from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCHEDULE = ROOT / "components" / "admin_schedule_feedback_aug04.py"
SCHEDULE_PAGE = ROOT / "pages" / "32_Admin_Scheduling.py"
NOTIFICATIONS = ROOT / "components" / "member_allocation_notifications.py"
TASK_AGE = ROOT / "components" / "member_task_pending_age.py"
APP_HEADER = ROOT / "components" / "streamlit_app_header_regression_guard.py"
BOOTSTRAP = ROOT / "components" / "__init__.py"


class FeedbackSchedulingNotificationsTaskAgeTests(unittest.TestCase):
    def test_changed_python_files_compile(self):
        for path in (
            SCHEDULE,
            SCHEDULE_PAGE,
            NOTIFICATIONS,
            TASK_AGE,
            APP_HEADER,
            BOOTSTRAP,
        ):
            compile(path.read_text(encoding="utf-8"), str(path), "exec")

    def test_schedule_uses_75_25_layout_and_selected_date_table(self):
        source = SCHEDULE.read_text(encoding="utf-8")
        page = SCHEDULE_PAGE.read_text(encoding="utf-8")
        self.assertIn("st.columns([3, 1]", source)
        for label in (
            "Schedule date",
            "Name of Member",
            "Schedule Time",
            "Subject",
        ):
            self.assertIn(label, source)
        self.assertIn("_admin_schedule_for_date(schedule_date, practitioner_id)", source)
        self.assertIn("schedule_time_context", source)
        self.assertIn("install_admin_schedule_feedback(admin_scheduling)", page)
        self.assertNotIn(
            "Only this workspace section is rendered. A successful creation opens a fresh transaction form",
            source,
        )

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

    def test_schedule_side_panel_is_read_only_against_identity_authority(self):
        source = SCHEDULE.read_text(encoding="utf-8")
        self.assertIn("from components.storage_backend import load_state", source)
        self.assertNotIn("get_user_by_id", source)
        self.assertNotIn('get("users"', source)
        self.assertNotIn("save_state", source)

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
        self.assertIn("install_member_allocation_notifications()", bootstrap)

    def test_notification_delivery_does_not_invoke_identity_write_paths(self):
        source = NOTIFICATIONS.read_text(encoding="utf-8")
        self.assertNotIn("get_user_by_id", source)
        self.assertNotIn('get("users"', source)
        self.assertNotIn('setdefault("users"', source)
        self.assertIn('saved.get("member_email")', source)

    def test_pending_age_is_real_adjacent_content_not_css_only(self):
        source = TASK_AGE.read_text(encoding="utf-8")
        bootstrap = BOOTSTRAP.read_text(encoding="utf-8")
        self.assertIn("today - due_date", source)
        self.assertIn("Task is pending for {delta} {unit}", source)
        self.assertIn("hm-task-alert-row", source)
        self.assertIn("ACTION REQUIRED", source)
        self.assertIn("hm-v990-task-progress::before", source)
        self.assertIn("content:none", source)
        self.assertIn("install_member_task_pending_age()", bootstrap)

    def test_new_streamlit_app_header_is_hidden_globally(self):
        source = APP_HEADER.read_text(encoding="utf-8")
        bootstrap = BOOTSTRAP.read_text(encoding="utf-8")
        self.assertIn('[data-testid="stAppHeader"]', source)
        self.assertIn('[data-testid="stAppHeaderActions"]', source)
        self.assertIn('button[aria-label="Share this app"]', source)
        self.assertIn("install_streamlit_app_header_regression_guard()", bootstrap)


if __name__ == "__main__":
    unittest.main()
