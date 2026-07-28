from __future__ import annotations

import pathlib
import unittest

from components.package_hardening import (
    COMMERCIAL_SNAPSHOT_NOTE,
    INCLUSIONS_RULE,
    _date_text,
    _integer,
    _number,
)


ROOT = pathlib.Path(__file__).resolve().parents[1]


class PackageHardeningContractTests(unittest.TestCase):
    def test_inclusions_are_explicitly_informational(self):
        self.assertIn("informational only", INCLUSIONS_RULE.lower())
        self.assertIn("do not grant", INCLUSIONS_RULE.lower())
        self.assertIn("future subscriptions only", COMMERCIAL_SNAPSHOT_NOTE.lower())

    def test_normalization_helpers_are_safe(self):
        self.assertEqual(_integer("4"), 4)
        self.assertEqual(_integer("invalid", 3), 3)
        self.assertEqual(_number("12.50"), 12.5)
        self.assertEqual(_date_text("2026-07-29T10:30:00Z"), "2026-07-29")
        self.assertIsNone(_date_text(""))

    def test_schema_enforces_one_current_package_and_snapshot_rule(self):
        sql = (ROOT / "sql/package_hardening_123_01_schema_and_backfill.sql").read_text()
        self.assertIn("hm_member_package_one_current_idx", sql)
        self.assertIn("inclusions_informational_only boolean not null default true", sql)
        self.assertIn("hm_member_package_subscriptions", sql)
        self.assertIn("hm_package_usage_events", sql)
        self.assertIn("hm_package_payments", sql)

    def test_consumption_and_reservation_rules_are_canonical(self):
        sql = (ROOT / "sql/package_hardening_123_02_metrics_and_cost_contract.sql").read_text()
        compact = "".join(sql.split())
        self.assertIn("lower(coalesce(value->>'status',''))='completed'", compact)
        self.assertIn("session_counted", sql)
        self.assertIn("lower(coalesce(value->>'status',''))in('scheduled','acknowledged')", compact)
        self.assertIn("sessions_available_to_schedule", sql)
        self.assertIn("hm_package_schedule_subscription_id", sql)
        self.assertIn("never substitutes the latest active package", sql.lower())

    def test_replacement_and_override_require_reasons(self):
        sql = (ROOT / "sql/package_hardening_123_03_admin_write_contracts.sql").read_text()
        self.assertIn("A replacement or renewal reason is required", sql)
        self.assertIn("Select how unused sessions should be handled", sql)
        self.assertIn("A schedule-limit override reason is required", sql)
        self.assertIn("retain_until_exhausted", sql)
        self.assertIn("carry_forward", sql)

    def test_member_contract_exposes_financial_and_usage_fields(self):
        sql = (ROOT / "sql/package_hardening_123_04_member_contract_and_usage_audit.sql").read_text()
        for field in (
            "total_value",
            "payment_status",
            "amount_paid",
            "outstanding_amount",
            "sessions_reserved",
            "sessions_available_to_schedule",
            "package_history",
        ):
            self.assertIn(field, sql)
        self.assertIn("inclusions_informational_only", sql)

    def test_admin_ui_removes_people_control_and_labels_inclusions(self):
        admin_ui = (ROOT / "components/package_hardening_ui.py").read_text()
        schedule_ui = (ROOT / "components/package_hardening_schedule_ui.py").read_text()
        self.assertNotIn("Number of people", admin_ui)
        self.assertNotIn("People", schedule_ui)
        self.assertIn("Informational inclusions", admin_ui)
        self.assertIn("Mandatory package-limit override reason", schedule_ui)


if __name__ == "__main__":
    unittest.main()
