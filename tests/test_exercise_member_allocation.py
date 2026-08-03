from __future__ import annotations

import copy
import unittest
from pathlib import Path
from unittest import mock

from components import exercise_member_allocation as allocation


ACTIVE_SOURCE = {
    "id": "12",
    "source_id": "12",
    "title": "Chair Squat",
    "status": "active",
    "category": "Strength",
    "difficulty": "Beginner",
    "duration_or_reps": "3 x 10",
    "instructions": "Keep the knees aligned.",
    "content_version": 4,
}
INACTIVE_SOURCE = {
    **ACTIVE_SOURCE,
    "id": "13",
    "source_id": "13",
    "title": "Legacy Stretch",
    "status": "inactive",
}


class ExerciseMemberAllocationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.db = {
            "member_exercise_allocations": {},
            "exercise_member_allocation_audit": [],
        }

        self.load_patch = mock.patch.object(
            allocation,
            "load_state",
            side_effect=lambda: copy.deepcopy(self.db),
        )

        def save(next_state):
            self.db.clear()
            self.db.update(copy.deepcopy(next_state))

        self.save_patch = mock.patch.object(
            allocation,
            "save_state",
            side_effect=save,
        )
        self.repo_patch = mock.patch.object(
            allocation,
            "list_exercise_repository",
            side_effect=lambda active_only=True: (
                [copy.deepcopy(ACTIVE_SOURCE)]
                if active_only
                else [copy.deepcopy(ACTIVE_SOURCE), copy.deepcopy(INACTIVE_SOURCE)]
            ),
        )
        self.load_patch.start()
        self.save_patch.start()
        self.repo_patch.start()
        self.addCleanup(self.load_patch.stop)
        self.addCleanup(self.save_patch.stop)
        self.addCleanup(self.repo_patch.stop)

    def test_new_allocation_uses_active_canonical_source_and_snapshot(self):
        saved = allocation.save_exercise_member_allocation(
            member_id="member-1",
            source_id="12",
            start_date="2026-08-04",
            end_date="2026-08-10",
            instructions="Do this after breakfast.",
            notes="Low-impact plan.",
            actor_id="admin-1",
        )

        self.assertEqual(saved["source_type"], "exercise_repository")
        self.assertEqual(saved["source_id"], "12")
        self.assertEqual(saved["exercise_id"], "12")
        self.assertEqual(saved["exercise_name"], "Chair Squat")
        self.assertEqual(saved["source_snapshot"]["title"], "Chair Squat")
        self.assertEqual(
            len(self.db["member_exercise_allocations"]["member-1"]), 1
        )
        self.assertEqual(
            self.db["exercise_member_allocation_audit"][-1]["action"],
            "create",
        )

    def test_inactive_source_cannot_be_newly_allocated(self):
        with self.assertRaisesRegex(ValueError, "Only active canonical"):
            allocation.save_exercise_member_allocation(
                member_id="member-1",
                source_id="13",
            )

    def test_existing_allocation_identity_is_preserved_on_update(self):
        self.db["member_exercise_allocations"]["member-1"] = [
            {
                "id": "legacy-allocation-7",
                "member_id": "member-1",
                "exercise_id": "12",
                "exercise_name": "Chair Squat",
                "status": "active",
                "source_snapshot": {"source_id": "12", "title": "Chair Squat"},
            }
        ]

        saved = allocation.save_exercise_member_allocation(
            member_id="member-1",
            source_id="12",
            allocation_id="legacy-allocation-7",
            start_date="2026-08-05",
            end_date="2026-08-12",
            instructions="Updated",
            status="active",
        )

        self.assertEqual(saved["id"], "legacy-allocation-7")
        self.assertEqual(
            len(self.db["member_exercise_allocations"]["member-1"]), 1
        )
        self.assertEqual(
            self.db["member_exercise_allocations"]["member-1"][0]["id"],
            "legacy-allocation-7",
        )

    def test_existing_source_identity_cannot_be_changed(self):
        self.db["member_exercise_allocations"]["member-1"] = [
            {
                "id": "allocation-1",
                "member_id": "member-1",
                "exercise_id": "12",
                "status": "active",
            }
        ]
        with self.assertRaisesRegex(
            ValueError, "source identity cannot be changed"
        ):
            allocation.save_exercise_member_allocation(
                member_id="member-1",
                source_id="13",
                allocation_id="allocation-1",
            )

    def test_stop_retains_row_and_history(self):
        self.db["member_exercise_allocations"]["member-1"] = [
            {
                "id": "allocation-1",
                "member_id": "member-1",
                "exercise_id": "12",
                "status": "active",
                "start_date": "2026-08-04",
            }
        ]

        stopped = allocation.stop_exercise_member_allocation(
            member_id="member-1",
            allocation_id="allocation-1",
            stop_date="2026-08-06",
            stop_reason="Pain reported.",
        )

        self.assertEqual(stopped["id"], "allocation-1")
        self.assertEqual(stopped["status"], "stopped")
        self.assertEqual(stopped["end_date"], "2026-08-06")
        self.assertEqual(
            len(self.db["member_exercise_allocations"]["member-1"]), 1
        )

    def test_historical_inactive_source_remains_readable(self):
        self.db["member_exercise_allocations"]["member-1"] = [
            {
                "id": "historical-13",
                "member_id": "member-1",
                "exercise_id": "13",
                "exercise_name": "Legacy Stretch",
                "status": "stopped",
            }
        ]

        rows = allocation.list_member_exercise_allocations(
            "member-1", include_stopped=True
        )

        self.assertEqual(rows[0]["id"], "historical-13")
        self.assertEqual(rows[0]["source_id"], "13")
        self.assertEqual(rows[0]["status"], "stopped")

    def test_end_date_cannot_precede_start_date(self):
        with self.assertRaisesRegex(ValueError, "End date"):
            allocation.save_exercise_member_allocation(
                member_id="member-1",
                source_id="12",
                start_date="2026-08-10",
                end_date="2026-08-04",
            )

    def test_page_boundary_is_exercise_only(self):
        page = Path("pages/42_Admin_Exercise_Member_Allocation.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("member_exercise_allocations", page)
        self.assertIn("save_exercise_member_allocation", page)
        self.assertNotIn("recommendation_shares", page)
        self.assertNotIn("member_supplements", page)
        self.assertNotIn("save_unified_recommendation_share", page)
        self.assertIn("_clear_add_form(member_id)", page)
        self.assertIn("st.session_state.pop", page)


if __name__ == "__main__":
    unittest.main()
