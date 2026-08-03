from __future__ import annotations

import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "package_domain_authority_trace_phase2_2026-08-03.md"
PACKAGE = ROOT / "components" / "package_hardening.py"
BOOTSTRAP = ROOT / "components" / "package_hardening_bootstrap.py"
ADMIN_UI = ROOT / "components" / "package_hardening_ui.py"
ADMIN_PAGE = ROOT / "pages" / "41_Admin_Packages.py"
ADMIN_SCHEDULING = ROOT / "components" / "admin_scheduling_consolidated.py"
MEMBER_PAGE = ROOT / "pages" / "33_My_Schedule.py"
MEMBER_SCHEDULE_UI = ROOT / "components" / "package_hardening_schedule_ui.py"
MEMBER_CONTRACT_SQL = (
    ROOT / "sql" / "package_hardening_123_04_member_contract_and_usage_audit.sql"
)


class PackageDomainAuthorityTracePhase2Tests(unittest.TestCase):
    def test_trace_document_freezes_authority_and_safety_boundary(self) -> None:
        source = DOC.read_text(encoding="utf-8")
        for required in (
            "dedicated Supabase Package structures are the accepted runtime authority",
            "compatibility mirrors only",
            "Package catalogue | 3 | 3 | 0 | 0",
            "Member subscriptions | 3 | 3 | 0 | 0",
            "No Dart Package client implementation was identified",
            "No mirror retirement or data deletion is included",
        ):
            self.assertIn(required, source)

    def test_canonical_adapter_owns_package_tables_and_admin_rpcs(self) -> None:
        source = PACKAGE.read_text(encoding="utf-8")
        for required in (
            '.table("hm_packages")',
            '.table("hm_member_package_subscriptions")',
            '.table("hm_package_usage_events")',
            '.table("hm_package_payments")',
            '.table("hm_package_subscription_events")',
            '"hm_admin_save_package"',
            '"hm_admin_assign_member_package"',
            '"hm_admin_adjust_package_sessions"',
            '"hm_admin_update_package_subscription"',
            '"hm_package_member_summary"',
            '"hm_package_subscription_metrics"',
        ):
            self.assertIn(required, source)

    def test_remaining_dual_write_is_explicit_and_is_not_the_authority(self) -> None:
        source = PACKAGE.read_text(encoding="utf-8")
        self.assertIn("def _sync_legacy_package_state()", source)
        self.assertIn('db["packages"] =', source)
        self.assertIn('db["member_packages"] =', source)
        self.assertIn("db_api.save_db(db)", source)
        self.assertIn("Normalized tables remain authoritative", source)

    def test_legacy_named_db_api_is_redirected_to_canonical_contract(self) -> None:
        source = BOOTSTRAP.read_text(encoding="utf-8")
        for assignment in (
            "db_api.list_packages_v1024b14 = list_packages_v1024b14",
            "db_api.create_package_v1024b14 = create_package_v1024b14",
            "db_api.update_package_v1024b14 = update_package_v1024b14",
            "db_api.get_member_active_package_v1024b14 = get_member_active_package_v1024b14",
            "db_api.list_member_packages_v1024b14 = list_member_packages_v1024b14",
            "db_api.get_member_session_ledger_v1024b13 = get_member_session_ledger_v1024b13",
        ):
            self.assertIn(assignment, source)
        self.assertIn("hardening.list_packages", source)
        self.assertIn("hardening.list_member_subscriptions", source)
        self.assertIn("hardening.get_member_package_summary", source)
        self.assertIn("hardening.member_session_ledger", source)

    def test_streamlit_admin_and_member_pages_use_canonical_package_modules(self) -> None:
        admin_ui = ADMIN_UI.read_text(encoding="utf-8")
        admin_page = ADMIN_PAGE.read_text(encoding="utf-8")
        admin_scheduling = ADMIN_SCHEDULING.read_text(encoding="utf-8")
        member_page = MEMBER_PAGE.read_text(encoding="utf-8")
        member_ui = MEMBER_SCHEDULE_UI.read_text(encoding="utf-8")

        self.assertIn("components.package_hardening_ui", admin_page)
        self.assertIn("render_package_hardening_admin_page", admin_page)
        for required in (
            "list_packages",
            "list_member_subscriptions",
            "save_package",
            "assign_or_replace_member_package",
            "adjust_subscription_sessions",
            "update_subscription",
        ):
            self.assertIn(required, admin_ui)
        self.assertIn("from components.package_hardening import member_session_ledger, schedule_capacity", admin_scheduling)
        self.assertIn("install_package_hardening_schedule_ui", member_page)
        self.assertIn("get_member_package_summary", member_ui)
        self.assertIn("member_session_ledger", member_ui)
        self.assertIn("schedule_capacity", member_ui)

    def test_flutter_boundary_is_the_authenticated_member_rpc(self) -> None:
        sql = MEMBER_CONTRACT_SQL.read_text(encoding="utf-8")
        for required in (
            "create or replace function public.hm_member_schedule_contract()",
            "from public.hm_member_package_subscriptions",
            "public.hm_package_subscription_metrics",
            "from public.healthyme_app_state",
            "grant execute on function public.hm_member_schedule_contract() to authenticated",
            "contract_version",
        ):
            self.assertIn(required, sql)

    def test_no_untraced_runtime_direct_package_mirror_access(self) -> None:
        tokens = (
            'get("packages"',
            "get('packages'",
            '["packages"]',
            "['packages']",
            'setdefault("packages"',
            "setdefault('packages'",
            'get("member_packages"',
            "get('member_packages'",
            '["member_packages"]',
            "['member_packages']",
            'setdefault("member_packages"',
            "setdefault('member_packages'",
        )
        allowed = {
            pathlib.Path("components/db.py"),
            pathlib.Path("components/package_hardening.py"),
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
            "Untraced direct Package mirror access found: " + ", ".join(sorted(hits)),
        )

    def test_no_untraced_dart_package_client_in_this_repository(self) -> None:
        package_tokens = (
            "hm_member_schedule_contract",
            "hm_member_package_subscriptions",
            "hm_packages",
            "member_package",
            "package_history",
        )
        hits: list[str] = []
        for path in ROOT.rglob("*.dart"):
            source = path.read_text(encoding="utf-8", errors="ignore").lower()
            if any(token.lower() in source for token in package_tokens):
                hits.append(str(path.relative_to(ROOT)))
        self.assertEqual(
            hits,
            [],
            "Flutter/Dart Package clients must be added to the authority trace: "
            + ", ".join(sorted(hits)),
        )


if __name__ == "__main__":
    unittest.main()
