from __future__ import annotations

import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "package_post_deployment_observation_phase4_2026-08-03.md"
PACKAGE = ROOT / "components" / "package_hardening.py"
BOOTSTRAP = ROOT / "components" / "package_hardening_bootstrap.py"
ADMIN_PAGE = ROOT / "pages" / "41_Admin_Packages.py"
ADMIN_UI = ROOT / "components" / "package_hardening_ui.py"
ADMIN_SCHEDULING = ROOT / "components" / "admin_scheduling_consolidated.py"
MEMBER_PAGE = ROOT / "pages" / "33_My_Schedule.py"
MEMBER_UI = ROOT / "components" / "package_hardening_schedule_ui.py"
MEMBER_CONTRACT = (
    ROOT / "sql" / "package_hardening_123_04_member_contract_and_usage_audit.sql"
)


class PackagePostDeploymentObservationPhase4Tests(unittest.TestCase):
    def test_document_records_production_observation_without_claiming_visual_smoke(self) -> None:
        source = DOC.read_text(encoding="utf-8")
        for required in (
            "Canonical Package masters | 3",
            "Retained Package rows | 3",
            "Package identities match | Yes",
            "Canonical subscriptions | 3",
            "Retained subscription rows | 3",
            "Subscription identities match | Yes",
            "contract version `package-hardening-123-v1`",
            "not claimed as executed",
            "Physical deletion of the retained arrays is not included",
            "Batch 2 — Users and Workflow",
        ):
            self.assertIn(required, source)

    def test_package_adapter_cannot_refresh_legacy_package_arrays(self) -> None:
        source = PACKAGE.read_text(encoding="utf-8")
        forbidden = (
            "_sync_legacy_package_state",
            'db["packages"] =',
            "db['packages'] =",
            'db["member_packages"] =',
            "db['member_packages'] =",
        )
        for token in forbidden:
            self.assertNotIn(token, source)

    def test_all_package_write_functions_remain_canonical(self) -> None:
        source = PACKAGE.read_text(encoding="utf-8")
        functions = {
            "save_package": "hm_admin_save_package",
            "assign_or_replace_member_package": "hm_admin_assign_member_package",
            "adjust_subscription_sessions": "hm_admin_adjust_package_sessions",
            "update_subscription": "hm_admin_update_package_subscription",
        }
        for name, rpc in functions.items():
            marker = f"def {name}("
            start = source.index(marker)
            next_def = source.find("\ndef ", start + len(marker))
            block = source[start : next_def if next_def >= 0 else len(source)]
            self.assertIn(rpc, block)
            self.assertNotIn("load_db", block)
            self.assertNotIn("save_db", block)
            self.assertNotIn('"packages"', block)
            self.assertNotIn('"member_packages"', block)

    def test_legacy_named_package_api_still_redirects_to_canonical_contract(self) -> None:
        source = BOOTSTRAP.read_text(encoding="utf-8")
        for required in (
            "hardening.list_packages",
            "hardening.list_member_subscriptions",
            "hardening.get_member_package_summary",
            "hardening.member_session_ledger",
            "db_api.list_packages_v1024b14 = list_packages_v1024b14",
            "db_api.get_member_active_package_v1024b14 = get_member_active_package_v1024b14",
            "db_api.list_member_packages_v1024b14 = list_member_packages_v1024b14",
        ):
            self.assertIn(required, source)

    def test_admin_packages_surface_remains_canonical(self) -> None:
        page = ADMIN_PAGE.read_text(encoding="utf-8")
        ui = ADMIN_UI.read_text(encoding="utf-8")
        self.assertIn("components.package_hardening_ui", page)
        self.assertIn("render_package_hardening_admin_page", page)
        for required in (
            "list_packages",
            "list_member_subscriptions",
            "get_member_package_summary",
            "save_package",
            "assign_or_replace_member_package",
            "adjust_subscription_sessions",
            "update_subscription",
        ):
            self.assertIn(required, ui)

    def test_admin_scheduling_and_member_schedule_remain_canonical(self) -> None:
        admin = ADMIN_SCHEDULING.read_text(encoding="utf-8")
        member_page = MEMBER_PAGE.read_text(encoding="utf-8")
        member_ui = MEMBER_UI.read_text(encoding="utf-8")
        self.assertIn("member_session_ledger", admin)
        self.assertIn("schedule_capacity", admin)
        self.assertIn("install_package_hardening_schedule_ui", member_page)
        self.assertIn("get_member_package_summary", member_ui)
        self.assertIn("member_session_ledger", member_ui)

    def test_authenticated_member_contract_still_exposes_complete_package_payload(self) -> None:
        source = MEMBER_CONTRACT.read_text(encoding="utf-8")
        for required in (
            "create or replace function public.hm_member_schedule_contract()",
            "from public.hm_member_package_subscriptions",
            "public.hm_package_subscription_metrics",
            "'upcoming_sessions'",
            "'session_ledger'",
            "'package_history'",
            "'package-hardening-123-v1'",
            "grant execute on function public.hm_member_schedule_contract() to authenticated",
        ):
            self.assertIn(required, source)

    def test_no_new_runtime_direct_package_mirror_reader(self) -> None:
        tokens = (
            'get("packages"',
            "get('packages'",
            '["packages"]',
            "['packages']",
            'get("member_packages"',
            "get('member_packages'",
            '["member_packages"]',
            "['member_packages']",
        )
        allowed = {
            pathlib.Path("components/db.py"),
            pathlib.Path("components/performance_diagnostics.py"),
        }
        hits: list[str] = []
        for folder in (ROOT / "components", ROOT / "pages", ROOT / "native_bridge"):
            if not folder.exists():
                continue
            for path in folder.rglob("*.py"):
                source = path.read_text(encoding="utf-8")
                if any(token in source for token in tokens):
                    relative = path.relative_to(ROOT)
                    if relative not in allowed:
                        hits.append(str(relative))
        self.assertEqual(
            hits,
            [],
            "Direct Package mirror reader found: " + ", ".join(sorted(hits)),
        )


if __name__ == "__main__":
    unittest.main()
