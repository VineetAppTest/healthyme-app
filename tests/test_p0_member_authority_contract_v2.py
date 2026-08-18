from __future__ import annotations

import datetime as dt
import pathlib
import unittest
from unittest.mock import patch

from components.exercise_member_allocation import (
    exercise_allocation_effective_state,
    list_member_exercise_allocations_for_date,
)
from components.member_exercise_journal_table import (
    base_exercise_journal_rows,
    build_exercise_log_payload,
)


ROOT = pathlib.Path(__file__).resolve().parents[1]
ALLOCATION = ROOT / "components" / "exercise_member_allocation.py"
JOURNAL = ROOT / "components" / "member_exercise_journal.py"
JOURNAL_TABLE = ROOT / "components" / "member_exercise_journal_table.py"
JOURNAL_LAYOUT = ROOT / "components" / "member_exercise_journal_layout_v4.py"
CURRENT_PLAN = ROOT / "components" / "current_member_plan.py"
MIGRATION = ROOT / "sql" / "p0_member_exercise_log_allocation_identity_v2.sql"
CONTRACT = ROOT / "docs" / "P0_MEMBER_AUTHORITY_CONTRACT_V2.md"


class P0MemberAuthorityContractV2Tests(unittest.TestCase):
    def test_effective_exercise_allocation_date_states_are_side_effect_free(self):
        current = {
            "status": "active",
            "start_date": "2026-08-01",
            "end_date": "2026-08-31",
        }
        upcoming = {"status": "active", "start_date": "2026-08-20"}
        expired = {"status": "active", "end_date": "2026-08-10"}
        stopped = {"status": "stopped"}
        target = dt.date(2026, 8, 18)
        self.assertEqual(exercise_allocation_effective_state(current, target), "current")
        self.assertEqual(exercise_allocation_effective_state(upcoming, target), "upcoming")
        self.assertEqual(exercise_allocation_effective_state(expired, target), "expired")
        self.assertEqual(exercise_allocation_effective_state(stopped, target), "stopped")
        source = ALLOCATION.read_text(encoding="utf-8")
        helper = source[
            source.index("def list_member_exercise_allocations_for_date"):
            source.index("def _validate_dates")
        ]
        self.assertNotIn("save_state", helper)
        self.assertNotIn("stop_exercise_member_allocation", helper)

    def test_date_reader_returns_only_current_independent_allocations(self):
        rows = [
            {"id": "a", "status": "active", "start_date": "2026-08-01", "end_date": "2026-08-31", "exercise_name": "Walk"},
            {"id": "b", "status": "active", "start_date": "2026-08-20", "exercise_name": "Later"},
            {"id": "c", "status": "active", "end_date": "2026-08-10", "exercise_name": "Old"},
            {"id": "d", "status": "stopped", "exercise_name": "Stopped"},
        ]
        with patch(
            "components.exercise_member_allocation.list_member_exercise_allocations",
            return_value=rows,
        ):
            current = list_member_exercise_allocations_for_date(
                "member-1", dt.date(2026, 8, 18)
            )
        self.assertEqual([row["id"] for row in current], ["a"])
        self.assertEqual(current[0]["effective_state"], "current")

    def test_exercise_journal_no_longer_reads_recommendation_profile_exercises(self):
        journal = JOURNAL.read_text(encoding="utf-8")
        table = JOURNAL_TABLE.read_text(encoding="utf-8")
        self.assertIn("list_member_exercise_allocations_for_date", journal)
        self.assertIn('"authority": "member_exercise_allocations"', journal)
        for forbidden in (
            "load_active_recommendation_profile",
            "build_member_recommendation_contract",
            "today_day_number",
        ):
            self.assertNotIn(forbidden, journal)
            self.assertNotIn(forbidden, table)
        self.assertIn("load_member_exercise_contract", table)

    def test_current_plan_and_journal_share_exercise_authority(self):
        current_plan = CURRENT_PLAN.read_text(encoding="utf-8")
        journal = JOURNAL.read_text(encoding="utf-8")
        self.assertIn('"exercise": "member_exercise_allocations"', current_plan)
        self.assertIn("list_member_exercise_allocations_for_date", journal)

    def test_allocation_linked_payload_keeps_allocation_identity_when_actual_changes(self):
        payload = build_exercise_log_payload(
            member_id="member-1",
            log_date="2026-08-18",
            item_order=1,
            selected_activity="Cycling",
            selected_timing="Evening",
            selected_duration="20 min",
            remarks="Actual activity changed",
            status="Completed",
            completion_time="7:30 PM",
            selected_definition={
                "source_id": "repo-cycle",
                "difficulty": "Moderate",
                "equipment": "Cycle",
            },
            allocation_id="exercise_alloc_walk",
        )
        self.assertEqual(payload["allocation_id"], "exercise_alloc_walk")
        self.assertEqual(payload["source_id"], "repo-cycle")
        self.assertEqual(payload["exercise_name"], "Cycling")
        self.assertNotIn("profile_id", payload)
        self.assertNotIn("day_number", payload)

    def test_manual_actual_row_has_stable_non_profile_identity(self):
        payload = build_exercise_log_payload(
            member_id="member-1",
            log_date="2026-08-18",
            item_order=3,
            selected_activity="Yoga",
            selected_timing="Morning",
            selected_duration="15 min",
            remarks="Extra activity",
            status="Completed",
            completion_time="07:15",
            selected_definition={"source_id": "repo-yoga"},
            journal_entry_key="manual:3",
        )
        self.assertEqual(payload["journal_entry_key"], "manual:3")
        self.assertEqual(payload["source_id"], "repo-yoga")
        self.assertNotIn("allocation_id", payload)
        self.assertNotIn("profile_id", payload)

    def test_legacy_log_identity_remains_supported(self):
        payload = build_exercise_log_payload(
            member_id="member-1",
            log_date="2026-07-29",
            item_order=1,
            selected_activity="Legacy Walk",
            selected_timing="Night",
            selected_duration="30 min",
            remarks="Historical row",
            status="Completed",
            completion_time="22:00",
            selected_definition={},
            profile={"id": "profile-1", "profile_name": "Starter"},
            day_number=2,
        )
        self.assertEqual(payload["profile_id"], "profile-1")
        self.assertEqual(payload["day_number"], 2)
        self.assertNotIn("allocation_id", payload)

    def test_legacy_history_is_not_matched_to_new_allocation_by_name_or_order(self):
        rows = base_exercise_journal_rows(
            [
                {
                    "allocation_id": "alloc-new",
                    "source_id": "repo-walk",
                    "name": "Walk",
                    "item_order": 1,
                }
            ],
            [
                {
                    "id": "legacy-log",
                    "profile_id": "legacy-profile",
                    "profile_name": "Old Plan",
                    "day_number": 1,
                    "item_order": 1,
                    "exercise_name": "Walk",
                }
            ],
        )
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["allocation_id"], "alloc-new")
        self.assertEqual(rows[0]["prior"], {})
        self.assertEqual(rows[1]["legacy_profile"]["id"], "legacy-profile")

    def test_save_contract_has_distinct_new_and_legacy_conflicts(self):
        source = JOURNAL.read_text(encoding="utf-8")
        self.assertIn('conflict = "member_id,log_date,allocation_id"', source)
        self.assertIn('conflict = "member_id,log_date,journal_entry_key"', source)
        self.assertIn(
            'conflict = "member_id,log_date,profile_id,day_number,item_order"',
            source,
        )

    def test_migration_is_additive_and_preserves_legacy_rows(self):
        sql = MIGRATION.read_text(encoding="utf-8")
        self.assertIn("add column if not exists allocation_id text", sql)
        self.assertIn("add column if not exists source_id text", sql)
        self.assertIn("add column if not exists journal_entry_key text", sql)
        self.assertIn("alter column profile_id drop not null", sql)
        self.assertIn("alter column day_number drop not null", sql)
        self.assertIn("unique (member_id, log_date, allocation_id)", sql)
        self.assertIn("unique (member_id, log_date, journal_entry_key)", sql)
        self.assertNotIn("drop table", sql.lower())
        self.assertNotIn("delete from", sql.lower())
        self.assertNotIn("update public.hm_member_exercise_logs", sql.lower())

    def test_accepted_journal_edit_and_saved_day_behaviour_remains(self):
        layout = JOURNAL_LAYOUT.read_text(encoding="utf-8")
        for label in (
            "Timing",
            "Activity",
            "Duration / Sets",
            "Remarks",
            "Status",
            "Completion time (optional)",
            "+ Add Exercise",
            "Remove Exercise",
        ):
            self.assertIn(label, layout)
        table = JOURNAL_TABLE.read_text(encoding="utf-8")
        self.assertIn("### View Saved Days", table)
        self.assertIn("list_saved_exercise_rows", table)

    def test_contract_documents_manual_row_exception_without_new_authority(self):
        source = CONTRACT.read_text(encoding="utf-8")
        self.assertIn("Exercise: `member_exercise_allocations` only", source)
        self.assertIn("Current Member Plan: read-only consolidation only", source)
        self.assertIn("Historical rows are not deleted", source)


if __name__ == "__main__":
    unittest.main()
