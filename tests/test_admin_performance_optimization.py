from __future__ import annotations

import pathlib
import unittest

from components.admin_performance_optimization import LazySubscriptionMetrics


ROOT = pathlib.Path(__file__).resolve().parents[1]


class AdminPerformanceOptimizationTests(unittest.TestCase):
    def test_lazy_subscription_metrics_load_once(self):
        calls = []

        def loader(subscription_id):
            calls.append(subscription_id)
            return {"sessions_remaining": 4}

        metrics = LazySubscriptionMetrics(loader, "subscription-1")
        self.assertEqual(dict(metrics), {"sessions_remaining": 4})
        self.assertEqual(metrics["sessions_remaining"], 4)
        self.assertEqual(calls, ["subscription-1"])

    def test_profile_builder_installs_cache_before_modular_import(self):
        source = (ROOT / "pages/38_Admin_Recommendation_Profile_Builder.py").read_text()
        self.assertLess(
            source.index("install_profile_builder_performance()"),
            source.index("from components.profile_builder_modular import"),
        )
        optimizer = (ROOT / "components/admin_performance_optimization.py").read_text()
        self.assertIn("PROFILE_CACHE_TTL_SECONDS = 60", optimizer)
        self.assertIn("patch_profile_builder_source_detail_layout", optimizer)

    def test_packages_use_lazy_metrics_only_on_consumption(self):
        source = (ROOT / "pages/41_Admin_Packages.py").read_text()
        optimizer = (ROOT / "components/admin_performance_optimization.py").read_text()
        self.assertIn("install_admin_packages_performance", source)
        self.assertIn("LazySubscriptionMetrics", optimizer)
        self.assertIn('"hm_member_package_subscriptions"', optimizer)
        self.assertNotIn("for row in rows:\n        row[\"metrics\"] = package_contract.get_subscription_metrics", optimizer)

    def test_scheduling_cache_is_request_scoped(self):
        source = (ROOT / "pages/32_Admin_Scheduling.py").read_text()
        optimizer = (ROOT / "components/admin_performance_optimization.py").read_text()
        self.assertIn("with admin_scheduling_render_scope(admin_scheduling):", source)
        self.assertIn("ContextVar", optimizer)
        self.assertIn("_SCHEDULING_REQUEST_CACHE.reset(token)", optimizer)
        self.assertIn('"timezone.member"', optimizer)
        self.assertIn('"timezone.practitioner"', optimizer)

    def test_scope_excludes_auth_routing_and_member_pages(self):
        optimizer = (ROOT / "components/admin_performance_optimization.py").read_text()
        for forbidden in (
            "require_member",
            "authorization_id",
            "native_logout",
            "switch_page",
            "Member_Home",
        ):
            self.assertNotIn(forbidden, optimizer)

    def test_build_identifies_admin_performance_release(self):
        build = (ROOT / "components/current_build.py").read_text()
        self.assertIn('APP_BUILD_VERSION = "v102.5P1"', build)
        self.assertIn('APP_BUILD_LABEL = "Admin Performance Optimisation"', build)


if __name__ == "__main__":
    unittest.main()
