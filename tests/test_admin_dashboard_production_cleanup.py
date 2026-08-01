from __future__ import annotations

import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DASHBOARD = ROOT / "pages" / "10_Admin_Dashboard.py"


class AdminDashboardProductionCleanupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = DASHBOARD.read_text(encoding="utf-8")

    def test_dashboard_compiles(self):
        ast.parse(self.source, filename=str(DASHBOARD))

    def test_system_tools_are_not_exposed(self):
        forbidden = (
            'section_header("System Tools"',
            'nav_cell("Database"',
            'nav_cell("NSP Recalculate"',
            'nav_cell("Supabase Auth Readiness"',
            'nav_cell("Supabase Provisioning"',
            'nav_cell("Legacy Recommendations Share"',
            'nav_cell("Unified Recommendations Diagnostics"',
            'nav_cell("Active Profile Contract Diagnostics"',
            'nav_cell("Profile Source Alignment"',
            'nav_cell("Performance Diagnostics"',
            "hm-dash-system-wrap",
            "hm-dash-system-card",
        )
        for token in forbidden:
            self.assertNotIn(token, self.source)

    def test_normal_workflows_remain_available(self):
        for label in (
            "Review & Assessment",
            "Member & Access",
            "Content & Allocation",
            "Reports & Logs",
            "Communication & Scheduling",
            "Recommendation Profile Builder",
            "Packages",
            "Messages",
            "Scheduling",
        ):
            self.assertIn(label, self.source)

    def test_technical_build_label_is_exactly_suppressed(self):
        self.assertIn('_HIDDEN_BUILD_LABEL = "Full Admin integration build:"', self.source)
        self.assertIn("_install_build_label_suppression()", self.source)
        self.assertIn("if should_hide(body):", self.source)
        self.assertIn('for attribute in ("caption", "markdown", "write"):', self.source)

    def test_dashboard_copy_no_longer_mentions_system_tools(self):
        self.assertIn(
            '"Access review workflows, content allocation, reports, communication and scheduling."',
            self.source,
        )
        self.assertNotIn("communication, scheduling and system tools", self.source)

    def test_safety_boundaries_remain(self):
        self.assertIn("require_admin()", self.source)
        self.assertIn("inject_keepalive_guard_v96_11()", self.source)
        self.assertIn('finish_and_render_page_diagnostics("Admin Dashboard")', self.source)


if __name__ == "__main__":
    unittest.main()
