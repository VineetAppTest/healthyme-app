from __future__ import annotations

import datetime as dt
import pathlib
import unittest
from unittest import mock

from components import member_supplement_journal as journal


ROOT = pathlib.Path(__file__).resolve().parents[1]
MIGRATION = (
    ROOT
    / "supabase/migrations/20260805114000_create_member_supplement_logs.sql"
)


class _Response:
    data = []


class _FakeQuery:
    def __init__(self):
        self.upsert_payload = None
        self.on_conflict = ""

    def table(self, _name):
        return self

    def upsert(self, payload, *, on_conflict):
        self.upsert_payload = dict(payload)
        self.on_conflict = on_conflict
        return self

    def execute(self):
        return _Response()


class MemberSupplementJournalTests(unittest.TestCase):
    def test_allocations_expand_once_per_timing_and_follow_date_boundaries(self):
        allocations = [
            {
                "id": "allocation-1",
                "source_id": "supplement-1",
                "supplement_name": "Vitamin D",
                "dosage": "1 tablet",
                "timing": "Morning, Evening, Morning",
                "status": "Active",
                "start_date": "2026-08-01",
                "end_date": "2026-08-31",
            },
            {
                "id": "future-allocation",
                "supplement_name": "Future supplement",
                "timing": "Night",
                "status": "Active",
                "start_date": "2026-09-01",
            },
        ]
        with mock.patch.object(
            journal,
            "list_member_supplement_allocations",
            return_value=allocations,
        ):
            rows = journal.supplement_entries_for_date(
                "member-1",
                dt.date(2026, 8, 5),
            )

        self.assertEqual([row["timing"] for row in rows], ["Morning", "Evening"])
        self.assertEqual({row["allocation_id"] for row in rows}, {"allocation-1"})
        self.assertEqual(rows[0]["dosage"], "1 tablet")

    def test_stopped_allocation_remains_available_only_through_stop_date(self):
        allocation = {
            "id": "allocation-1",
            "supplement_name": "Vitamin D",
            "timing": "Morning",
            "status": "Stopped",
            "start_date": "2026-08-01",
            "stop_date": "2026-08-05",
        }
        with mock.patch.object(
            journal,
            "list_member_supplement_allocations",
            return_value=[allocation],
        ):
            on_stop_date = journal.supplement_entries_for_date(
                "member-1", dt.date(2026, 8, 5)
            )
            after_stop_date = journal.supplement_entries_for_date(
                "member-1", dt.date(2026, 8, 6)
            )
        self.assertEqual(len(on_stop_date), 1)
        self.assertEqual(after_stop_date, [])

    def test_save_uses_idempotent_member_date_allocation_timing_upsert(self):
        query = _FakeQuery()
        with mock.patch.object(journal, "_client", return_value=query):
            journal.save_member_supplement_log(
                {
                    "member_id": "member-1",
                    "log_date": "2026-08-05",
                    "allocation_id": "allocation-1",
                    "source_id": "supplement-1",
                    "supplement_name": "Vitamin D",
                    "dosage": "1 tablet",
                    "timing": "Morning",
                    "status": "Taken",
                }
            )
        self.assertEqual(
            query.on_conflict,
            "member_id,log_date,allocation_id,timing",
        )
        self.assertEqual(query.upsert_payload["status"], "Taken")
        self.assertIn("updated_at", query.upsert_payload)

    def test_invalid_status_is_rejected_before_any_write(self):
        with self.assertRaisesRegex(ValueError, "Taken or Not Taken"):
            journal.save_member_supplement_log(
                {
                    "member_id": "member-1",
                    "log_date": "2026-08-05",
                    "allocation_id": "allocation-1",
                    "supplement_name": "Vitamin D",
                    "timing": "Morning",
                    "status": "Skipped",
                }
            )

    def test_migration_is_private_member_scoped_and_deduplicated(self):
        sql = MIGRATION.read_text(encoding="utf-8")
        for contract in (
            "enable row level security",
            "member.auth_user_id = (select auth.uid())",
            "status in ('Taken', 'Not Taken')",
            "unique (member_id, log_date, allocation_id, timing)",
            "hm_member_supplement_logs_member_date_idx",
            "revoke all on table public.hm_member_supplement_logs from anon",
            "to authenticated, service_role",
        ):
            self.assertIn(contract, sql)
        self.assertNotIn("grant delete", sql)

    def test_daily_log_exposes_exclusive_supplement_journal(self):
        page = (ROOT / "pages/18_Daily_Log.py").read_text(encoding="utf-8")
        runtime = (
            ROOT / "components/member_daily_log_native_tab_persistence.py"
        ).read_text(encoding="utf-8")
        journal_source = (
            ROOT / "components/member_supplement_journal.py"
        ).read_text(encoding="utf-8")
        for contract in (
            "Supplement Journal Date",
            "Supplement Section",
            "Save Supplement Entry",
            "View Saved Days",
        ):
            self.assertIn(contract, journal_source)
        self.assertIn("_render_supplement_journal", page)
        self.assertIn(
            '["Food Journal", "Exercise Journal", "Supplement Journal"]',
            page,
        )
        self.assertIn("_render_supplement_journal", runtime)
        self.assertIn("st.columns(3, gap=\"small\")", runtime)


if __name__ == "__main__":
    unittest.main()
