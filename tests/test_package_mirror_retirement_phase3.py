from __future__ import annotations

import ast
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "package_mirror_retirement_phase3_2026-08-03.md"
PACKAGE = ROOT / "components" / "package_hardening.py"
BOOTSTRAP = ROOT / "components" / "package_hardening_bootstrap.py"
ADMIN_UI = ROOT / "components" / "package_hardening_ui.py"
ADMIN_SCHEDULING = ROOT / "components" / "admin_scheduling_consolidated.py"
MEMBER_PAGE = ROOT / "pages" / "33_My_Schedule.py"
MEMBER_SCHEDULE_UI = ROOT / "components" / "package_hardening_schedule_ui.py"
MEMBER_CONTRACT_SQL = (
    ROOT / "sql" / "package_hardening_123_04_member_contract_and_usage_audit.sql"
)


class PackageMirrorRetirementPhase3Tests(unittest.TestCase):
    def test_document_freezes_retirement_and_rollback_boundary(self) -> None:
        source = DOC.read_text(encoding="utf-8")
        for required in (
            "no longer refresh",
            "retained unchanged as rollback evidence",
            "After a future canonical Package mutation, divergence",
            "No database migration or SQL change",
            "Physical cleanup remains a later, separately approved data migration",
        ):
            self.assertIn(required, source)

    def test_package_adapter_has_no_mirror_function_or_assignment(self) -> None:
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

    def test_each_canonical_write_function_avoids_app_state_package_writes(self) -> None:
        source = PACKAGE.read_text(encoding="utf-8")
        tree = ast.parse(source)
        functions = {
            node.name: ast.get_source_segment(source, node) or ""
            for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        expected_rpcs = {
            "save_package": "hm_admin_save_package",
            "assign_or_replace_member_package": "hm_admin_assign_member_package",
            "adjust_subscription_sessions": "hm_admin_adjust_package_sessions",
            "update_subscription": "hm_admin_update_package_subscription",
        }
        for function_name, rpc_name in expected_rpcs.items():
            body = functions[function_name]
            self.assertIn(rpc_name, body)
            self.assertNotIn("load_db", body)
            self.assertNotIn("save_db", body)
            self.assertNotIn('"packages"', body)
            self.assertNotIn('"member_packages"', body)

    def test_member_communications_remain_separate_from_package_authority(self) -> None:
        source = PACKAGE.read_text(encoding="utf-8")
        self.assertIn("def _notify_package_assignment", source)
        self.assertIn("def _notify_subscription_update", source)
        self.assertIn("queue_member_event_email", source)
        self.assertIn("append_message=True", source)
        self.assertIn("append_notification=True", source)

    def test_legacy_named_api_still_redirects_to_canonical_readers(self) -> None:
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

    def test_admin_and_member_surfaces_remain_on_canonical_contract(self) -> None:
        admin_ui = ADMIN_UI.read_text(encoding="utf-8")
        admin_scheduling = ADMIN_SCHEDULING.read_text(encoding="utf-8")
        member_page = MEMBER_PAGE.read_text(encoding="utf-8")
        member_ui = MEMBER_SCHEDULE_UI.read_text(encoding="utf-8")

        for required in (
            "list_packages",
            "list_member_subscriptions",
            "save_package",
            "assign_or_replace_member_package",
            "adjust_subscription_sessions",
            "update_subscription",
        ):
            self.assertIn(required, admin_ui)
        self.assertIn("member_session_ledger", admin_scheduling)
        self.assertIn("schedule_capacity", admin_scheduling)
        self.assertIn("install_package_hardening_schedule_ui", member_page)
        self.assertIn("get_member_package_summary", member_ui)
        self.assertIn("member_session_ledger", member_ui)

    def test_authenticated_member_rpc_boundary_is_unchanged(self) -> None:
        source = MEMBER_CONTRACT_SQL.read_text(encoding="utf-8")
        for required in (
            "create or replace function public.hm_member_schedule_contract()",
            "from public.hm_member_package_subscriptions",
            "public.hm_package_subscription_metrics",
            "grant execute on function public.hm_member_schedule_contract() to authenticated",
        ):
            self.assertIn(required, source)

    def test_no_new_runtime_package_mirror_reader(self) -> None:
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
            "Unexpected Package mirror reader found: " + ", ".join(sorted(hits)),
        )

    def test_future_dart_package_clients_require_trace_update(self) -> None:
        tokens = (
            "hm_member_schedule_contract",
            "hm_member_package_subscriptions",
            "hm_packages",
            "member_package",
            "package_history",
        )
        hits: list[str] = []
        for path in ROOT.rglob("*.dart"):
            source = path.read_text(encoding="utf-8", errors="ignore").lower()
            if any(token.lower() in source for token in tokens):
                hits.append(str(path.relative_to(ROOT)))
        self.assertEqual(
            hits,
            [],
            "Flutter/Dart Package clients require authority-trace coverage: "
            + ", ".join(sorted(hits)),
        )


if __name__ == "__main__":
    unittest.main()
