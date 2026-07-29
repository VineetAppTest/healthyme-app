from __future__ import annotations

import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]


class AdminSchedulingConsolidatedTests(unittest.TestCase):
    def setUp(self):
        self.page = (ROOT / "pages/32_Admin_Scheduling.py").read_text()
        self.source = (
            ROOT / "components/admin_scheduling_consolidated.py"
        ).read_text()

    def test_page_uses_one_direct_renderer_without_runtime_installers(self):
        self.assertIn("render_admin_scheduling_consolidated_page", self.page)
        self.assertNotIn("schedule_timezone_ui", self.page)
        self.assertNotIn("install_admin_scheduling_timezone_selector", self.page)
        self.assertNotIn("install_default_scheduling_navigation", self.page)
        self.assertNotIn("install_package_hardening_schedule_ui", self.page)
        self.assertNotIn("install_sprint1_schedule_hygiene", self.page)

    def test_page_does_not_use_eager_streamlit_tabs(self):
        self.assertNotIn("st.tabs(", self.source)
        self.assertIn("_workspace_navigation(member_id)", self.source)
        self.assertIn('if section == "create"', self.source)
        self.assertIn('elif section == "status"', self.source)
        self.assertIn('elif section == "reschedule"', self.source)
        self.assertIn("_render_session_ledger", self.source)

    def test_navigation_is_direct_and_precedes_timezone_gate(self):
        render = self.source.index('def render_admin_scheduling_consolidated_page()')
        top_nav = self.source.index('_render_return_navigation("top")', render)
        context = self.source.index("context = _render_context_selector()", render)
        stop = self.source.index("st.stop()", context)
        self.assertLess(top_nav, context)
        self.assertLess(top_nav, stop)
        self.assertIn('st.switch_page("pages/10_Admin_Dashboard.py")', self.source)

    def test_create_form_uses_versioned_widget_identity(self):
        self.assertIn("_CREATE_VERSION_KEY", self.source)
        self.assertIn('prefix = f"hm_admin_sched_create_v{version}_"', self.source)
        self.assertIn("st.session_state[_CREATE_CLEANUP_KEY] = version", self.source)
        self.assertIn("st.session_state[_CREATE_VERSION_KEY] = version + 1", self.source)
        self.assertIn("_consume_old_create_state()", self.source)

    def test_success_message_is_prominent_and_exact(self):
        self.assertIn(
            "Schedule created in UTC and shared with both local times.",
            self.source,
        )
        self.assertIn("hm-sched-success", self.source)
        self.assertIn("border:2px solid #0F766E", self.source)

    def test_only_valid_timezone_choice_is_persisted(self):
        self.assertIn("_safe_timezone_options(timezone_options)", self.source)
        self.assertIn("_match_location_timezones(all_timezones)", self.source)
        self.assertIn("persist_practitioner_timezone", self.source)
        self.assertNotIn("st.selectbox =", self.source)
        self.assertNotIn("st.radio =", self.source)
        self.assertNotIn("st.button =", self.source)
        self.assertNotIn("st.markdown =", self.source)

    def test_sections_use_real_streamlit_containers(self):
        self.assertIn("with st.container(border=True):", self.source)
        self.assertNotIn("<div class='hm-schedule-section'>", self.source)

    def test_package_capacity_and_override_are_preserved(self):
        self.assertIn("schedule_capacity(member_id, schedule_date)", self.source)
        self.assertIn("Mandatory package-limit override reason", self.source)
        self.assertIn("hm_package_schedule_limit_override", self.source)
        self.assertIn("current_user_is_admin()", self.source)

    def test_latest_first_status_and_reschedule_ordering_remain(self):
        self.assertIn("def _sorted_schedule_rows", self.source)
        self.assertIn("start_at_utc", self.source)
        self.assertIn("reverse=True", self.source)
        self.assertIn("def _sorted_reschedule_requests", self.source)


if __name__ == "__main__":
    unittest.main()
