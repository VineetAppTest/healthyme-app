from __future__ import annotations

import pathlib
import unittest

from components.package_value_formula_ui import calculated_package_total


ROOT = pathlib.Path(__file__).resolve().parents[1]


class UiCorrectionsSs1Ss3Tests(unittest.TestCase):
    def test_total_package_value_is_exact_multiplication(self):
        self.assertEqual(calculated_package_total(10, 100), 1000.0)
        self.assertEqual(calculated_package_total(2, 175), 350.0)
        self.assertEqual(calculated_package_total(0, 100), 0.0)

    def test_database_enforces_master_formula_without_rewriting_snapshots(self):
        sql = (ROOT / "sql/package_hardening_123_08_total_formula.sql").read_text()
        self.assertIn("new.total_value := new.session_count * new.cost_per_session", sql)
        self.assertIn("hm_packages_total_formula_check", sql)
        self.assertIn("Existing member subscription snapshots are intentionally not changed", sql)

    def test_package_page_installs_read_only_formula_renderer(self):
        page = (ROOT / "pages/41_Admin_Packages.py").read_text()
        renderer = (ROOT / "components/package_value_formula_ui.py").read_text()
        self.assertIn("install_package_value_formula", page)
        self.assertIn("disabled=True", renderer)
        self.assertIn("Calculated automatically: allowance × cost per session", renderer)

    def test_messages_page_explains_where_secrets_come_from(self):
        page = (ROOT / "pages/31_Admin_Member_Communication.py").read_text()
        for text in (
            "Where to obtain and configure the production secrets",
            "Resend dashboard",
            "API Keys",
            "verify the HealthyMe sending domain",
            "Settings → Secrets",
            "RESEND_API_KEY",
            "RESEND_FROM_EMAIL",
            "never commit it to GitHub",
        ):
            self.assertIn(text, page)

    def test_default_scheduling_state_renders_back_navigation_before_stop(self):
        page = (ROOT / "pages/32_Admin_Scheduling.py").read_text()
        renderer = (
            ROOT / "components/admin_scheduling_consolidated.py"
        ).read_text()
        self.assertIn("render_admin_scheduling_consolidated_page", page)
        nav_position = renderer.index('_render_return_navigation("top")')
        context_position = renderer.index("context = _render_context_selector()")
        stop_position = renderer.index("st.stop()", context_position)
        self.assertLess(nav_position, context_position)
        self.assertLess(nav_position, stop_position)
        self.assertIn('st.switch_page("pages/10_Admin_Dashboard.py")', renderer)


if __name__ == "__main__":
    unittest.main()
