from __future__ import annotations

import datetime as dt
from pathlib import Path
import unittest

from components.current_member_plan_view import (
    _exercise_week_rows,
    _supplement_week_rows,
    build_day_timeline,
)


ROOT = Path(__file__).resolve().parents[1]
VIEW = ROOT / "components" / "current_member_plan_view.py"


class MemberPlanExperienceRedesignTests(unittest.TestCase):
    def setUp(self):
        self.model = {
            "meals": [
                {
                    "item_type": "meal",
                    "day_number": 2,
                    "item_order": 1,
                    "slot_name": "Breakfast",
                    "reference_label": "Moong Chilla",
                    "portion": "2",
                    "source_snapshot": {"prep_time": "15 min"},
                },
                {
                    "item_type": "meal",
                    "day_number": 2,
                    "item_order": 2,
                    "slot_name": "Dinner",
                    "reference_label": "Paneer Salad",
                    "portion": "1 bowl",
                },
                {
                    "item_type": "meal",
                    "day_number": 2,
                    "item_order": 1,
                    "slot_name": "Wake-up / Early Morning",
                    "reference_label": "Fennel Water",
                    "portion": "1 glass",
                },
            ],
            "supplement": {
                "current": [
                    {
                        "id": "sup-1",
                        "supplement_name": "Magnesium",
                        "dosage": "400",
                        "frequency": "Once",
                        "timing": "Morning, Before Bed, None",
                        "start_date": "2026-08-01",
                        "end_date": "",
                    }
                ],
                "upcoming": [],
            },
            "exercise": {
                "current": [
                    {
                        "id": "ex-1",
                        "exercise_name": "Brisk Walking",
                        "start_date": "2026-08-01",
                        "end_date": "2026-08-10",
                        "source_snapshot": {"duration_or_reps": "20 min"},
                    }
                ],
                "upcoming": [],
            },
        }

    def test_day_timeline_combines_all_three_domains(self):
        grouped = build_day_timeline(
            self.model,
            day_number=2,
            target_date=dt.date(2026, 8, 6),
        )
        rows = [row for values in grouped.values() for row in values]
        self.assertEqual(
            {row["domain"] for row in rows},
            {"meal", "supplement", "exercise"},
        )
        self.assertIn("Morning", grouped)
        self.assertIn("Evening", grouped)
        self.assertIn("Night", grouped)
        self.assertIn("Anytime", grouped)
        self.assertEqual(grouped["Anytime"][0]["timing"], "Anytime / as advised")
        self.assertEqual(grouped["Morning"][0]["title"], "Moong Chilla - 2")
        self.assertNotIn(
            "Fennel Water - 1 glass",
            [row["title"] for values in grouped.values() for row in values],
        )

    def test_none_timing_is_not_rendered_when_real_timings_exist(self):
        grouped = build_day_timeline(
            self.model,
            day_number=2,
            target_date=dt.date(2026, 8, 6),
        )
        supplement_timings = [
            row["timing"]
            for values in grouped.values()
            for row in values
            if row["domain"] == "supplement"
        ]
        self.assertEqual(supplement_timings, ["Morning", "Before Bed"])

    def test_weekly_view_uses_meal_grid_and_flat_exercise_supplement_tables(self):
        source = VIEW.read_text(encoding="utf-8")
        self.assertIn("def _render_meal_week_grid", source)
        self.assertIn("hm-member-weekly-meal-grid-v1", source)
        self.assertIn("def _render_weekly_allocation_table", source)
        self.assertIn("hm-week-allocation-table", source)
        self.assertIn('"Breakfast",', source)
        self.assertIn('"Mid-morning Snack",', source)
        self.assertNotIn('"Wake-up / Early Morning",', source)
        self.assertIn('" + ".join(values)', source)
        self.assertIn("without day-wise open/close rows", source)
        self.assertNotIn("hm_member_plan_day_open", source)
        self.assertNotIn("hm_member_plan_day_toggle", source)
        self.assertNotIn("_toggle_day_disclosure", source)
        self.assertIn("white-space:nowrap", source)
        self.assertIn("Your weekly meals are shown first.", source)
        self.assertIn("_supplement_week_rows(model, dates)", source)
        self.assertIn("_exercise_week_rows(model, dates)", source)
        self.assertNotIn("st.tabs(", source)
        self.assertNotIn("st.columns(3", source)
        self.assertNotIn("source_id", source)
        self.assertNotIn("admin_notes", source)
        self.assertIn(".hm-guidance-box", source)
        self.assertIn(".hm-chip-row", source)

    def test_weekly_allocation_rows_are_flat_this_week_tables(self):
        dates = [
            (day, dt.date(2026, 8, 5) + dt.timedelta(days=day - 1))
            for day in range(1, 8)
        ]
        supplements = _supplement_week_rows(self.model, dates)
        exercises = _exercise_week_rows(self.model, dates)
        self.assertEqual(supplements[0]["Supplement"], "Magnesium")
        self.assertEqual(supplements[0]["Dose/Frequency"], "400 · Once")
        self.assertEqual(supplements[0]["Dates"], "2026-08-01 to Open")
        self.assertEqual(exercises[0]["Exercise"], "Brisk Walking")
        self.assertEqual(exercises[0]["Reps/Duration"], "20 min")
        self.assertNotIn("Day", exercises[0])


if __name__ == "__main__":
    unittest.main()