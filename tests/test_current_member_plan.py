from __future__ import annotations

import datetime as dt
import pathlib
import unittest

from components.current_member_plan import build_current_member_plan


ROOT = pathlib.Path(__file__).resolve().parents[1]
MODEL = ROOT / "components" / "current_member_plan.py"
VIEW = ROOT / "components" / "current_member_plan_view.py"
PAGE = ROOT / "pages" / "37_Member_Plan.py"
TODAY_PAGE = ROOT / "pages" / "36_Todays_Journey.py"
CONTRACT = ROOT / "components" / "member_planning_separation_contract.py"


def profile_loader_with_legacy_rows(member_id: str, email: str):
    return (
        True,
        {
            "id": "profile-1",
            "assigned_member_id": member_id,
            "start_date": "2026-08-04",
            "status": "active",
            "nutrition_guidance": "Keep hydration consistent.",
        },
        [
            {"item_type": "meal", "day_number": 1, "item_order": 1, "reference_label": "Breakfast", "portion": "1 bowl"},
            {"item_type": "exercise", "day_number": 1, "item_order": 2, "reference_label": "Legacy Walk", "instruction": "Old Profile Builder row"},
            {"item_type": "supplement", "day_number": 1, "item_order": 3, "reference_label": "Legacy Magnesium", "instruction": "Old Profile Builder row"},
            {"item_type": "nutrition_guidance", "day_number": 1, "item_order": 4, "reference_label": "Guidance", "instruction": "Sleep on time."},
        ],
        "loaded",
    )


def exercise_loader(member_id: str, include_stopped: bool = True):
    return [
        {"id": "ex-current", "member_id": member_id, "status": "active", "source_type": "exercise_repository", "source_id": "exrepo-current", "exercise_name": "Current Walk", "start_date": "2026-08-01", "end_date": "2026-08-10", "instructions": "Walk steadily.", "source_snapshot": {"title": "Current Walk"}},
        {"id": "ex-upcoming", "member_id": member_id, "status": "active", "source_type": "exercise_repository", "source_id": "exrepo-upcoming", "exercise_name": "Upcoming Strength", "start_date": "2026-08-08", "end_date": "", "source_snapshot": {"title": "Upcoming Strength"}},
        {"id": "ex-expired", "member_id": member_id, "status": "active", "source_type": "exercise_repository", "source_id": "exrepo-expired", "exercise_name": "Expired Mobility", "start_date": "2026-07-01", "end_date": "2026-08-03", "source_snapshot": {"title": "Expired Mobility"}},
        {"id": "ex-stopped", "member_id": member_id, "status": "stopped", "source_type": "exercise_repository", "source_id": "exrepo-stopped", "exercise_name": "Stopped Exercise", "start_date": "", "end_date": "", "source_snapshot": {"title": "Stopped Exercise"}},
    ]


def supplement_loader(member_id: str):
    return [
        {"id": "sup-current", "member_id": member_id, "status": "Active", "source_type": "supplement_repository", "source_id": "suprepo-current", "supplement_name": "Magnesium", "dosage": "1 tablet", "frequency": "Daily", "timing": "Night", "start_date": "2026-08-01", "end_date": "", "admin_notes": "Private repository note", "source_snapshot": {"supplement_name": "Magnesium", "admin_notes": "Private snapshot note", "notes": "Another private note"}},
        {"id": "sup-upcoming", "member_id": member_id, "status": "Active", "source_type": "supplement_repository", "source_id": "suprepo-upcoming", "supplement_name": "Omega-3", "start_date": "2026-08-06", "end_date": "", "source_snapshot": {"supplement_name": "Omega-3"}},
        {"id": "sup-expired", "member_id": member_id, "status": "Active", "source_type": "supplement_repository", "source_id": "suprepo-expired", "supplement_name": "Expired Supplement", "start_date": "2026-07-01", "end_date": "2026-08-03", "source_snapshot": {"supplement_name": "Expired Supplement"}},
        {"id": "sup-stopped", "member_id": member_id, "status": "Stopped", "source_type": "supplement_repository", "source_id": "suprepo-stopped", "supplement_name": "Stopped Supplement", "source_snapshot": {"supplement_name": "Stopped Supplement"}},
    ]


class CurrentMemberPlanPhaseETests(unittest.TestCase):
    def setUp(self):
        self.model = build_current_member_plan(
            "member-1",
            "member@example.com",
            today=dt.date(2026, 8, 4),
            profile_loader=profile_loader_with_legacy_rows,
            exercise_loader=exercise_loader,
            supplement_loader=supplement_loader,
        )

    def test_read_model_uses_three_separate_authorities(self):
        self.assertTrue(self.model["read_only"])
        self.assertEqual(self.model["source_authority"], {"meal": "active_meal_profile", "exercise": "member_exercise_allocations", "supplement": "member_supplements"})

    def test_retained_profile_exercise_and_supplement_rows_are_excluded(self):
        self.assertEqual(len(self.model["meals"]), 1)
        self.assertEqual(self.model["ignored_profile_rows"], {"exercise": 1, "supplement": 1})
        labels = [row.get("reference_label") for row in self.model["meals"]]
        self.assertNotIn("Legacy Walk", labels)
        self.assertNotIn("Legacy Magnesium", labels)

    def test_current_upcoming_expired_and_stopped_are_partitioned(self):
        self.assertEqual([row["id"] for row in self.model["exercise"]["current"]], ["ex-current"])
        self.assertEqual([row["id"] for row in self.model["exercise"]["upcoming"]], ["ex-upcoming"])
        self.assertEqual([row["id"] for row in self.model["exercise"]["expired_pending_stop"]], ["ex-expired"])
        self.assertEqual([row["id"] for row in self.model["exercise"]["stopped"]], ["ex-stopped"])
        self.assertEqual([row["id"] for row in self.model["supplement"]["current"]], ["sup-current"])
        self.assertEqual([row["id"] for row in self.model["supplement"]["upcoming"]], ["sup-upcoming"])

    def test_member_read_model_strips_repository_admin_notes(self):
        row = self.model["supplement"]["current"][0]
        self.assertNotIn("admin_notes", row)
        self.assertNotIn("admin_notes", row["source_snapshot"])
        self.assertNotIn("notes", row["source_snapshot"])

    def test_no_meal_profile_does_not_hide_independent_allocations(self):
        model = build_current_member_plan(
            "member-1",
            today=dt.date(2026, 8, 4),
            profile_loader=lambda member_id, email: (True, {}, [], "No active profile."),
            exercise_loader=exercise_loader,
            supplement_loader=supplement_loader,
        )
        self.assertTrue(model["has_content"])
        self.assertEqual(model["meals"], [])
        self.assertEqual(len(model["exercise"]["current"]), 1)
        self.assertEqual(len(model["supplement"]["current"]), 1)

    def test_read_model_has_no_write_authority(self):
        source = MODEL.read_text(encoding="utf-8")
        self.assertNotIn("save_state", source)
        self.assertNotIn("save_exercise_member_allocation", source)
        self.assertNotIn("save_supplement_member_allocation", source)
        self.assertNotIn("stop_exercise_member_allocation", source)
        self.assertNotIn("stop_supplement_member_allocation", source)
        self.assertNotIn("list_member_supplement_allocations(", source)

    def test_member_pages_use_consolidated_view(self):
        page = PAGE.read_text(encoding="utf-8")
        today = TODAY_PAGE.read_text(encoding="utf-8")
        self.assertIn("render_current_member_plan_view", page)
        self.assertIn('"Current Member Plan"', page)
        self.assertIn("render_todays_current_plan_view", today)
        self.assertNotIn("member_recommendation_member_labels", page)
        self.assertNotIn("member_recommendation_member_labels", today)

    def test_view_does_not_render_private_repository_notes(self):
        source = VIEW.read_text(encoding="utf-8")
        self.assertNotIn('get("admin_notes")', source)

    def test_existing_contract_keeps_current_member_plan_read_only(self):
        source = CONTRACT.read_text(encoding="utf-8")
        self.assertIn('"current_member_plan"', source)
        self.assertIn('"write_authority": False', source)
        self.assertIn('"rule": "consolidated read model only; never another persistence authority"', source)


if __name__ == "__main__":
    unittest.main()
