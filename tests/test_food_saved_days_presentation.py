from __future__ import annotations

from datetime import date
from pathlib import Path
import unittest

from components.food_saved_days_presentation import (
    SAVED_DAYS_DEFAULT_REVISION,
    SAVED_FROM_KEY,
    SAVED_REVISION_KEY,
    SAVED_TO_KEY,
    initialise_food_saved_days_range,
    saved_day_card_html,
    saved_day_card_rows,
    saved_day_meal_rows,
    saved_day_sort_key,
)


ROOT = Path(__file__).resolve().parents[1]


class FoodSavedDaysPresentationTests(unittest.TestCase):
    def test_stale_range_resets_to_today_once(self):
        today = date(2026, 8, 4)
        state = {
            SAVED_FROM_KEY: date(2026, 7, 29),
            SAVED_TO_KEY: date(2026, 8, 4),
        }

        initialise_food_saved_days_range(state, today)

        self.assertEqual(state[SAVED_FROM_KEY], today)
        self.assertEqual(state[SAVED_TO_KEY], today)
        self.assertEqual(state[SAVED_REVISION_KEY], SAVED_DAYS_DEFAULT_REVISION)

    def test_same_page_filter_changes_are_preserved_after_initialisation(self):
        today = date(2026, 8, 4)
        state = {}
        initialise_food_saved_days_range(state, today)
        state[SAVED_FROM_KEY] = date(2026, 8, 1)

        initialise_food_saved_days_range(state, today)

        self.assertEqual(state[SAVED_FROM_KEY], date(2026, 8, 1))
        self.assertEqual(state[SAVED_TO_KEY], today)

    def test_card_includes_meals_water_and_other_liquids(self):
        day = {
            "date": "2026-08-04",
            "meals": {
                "breakfast": {
                    "food_items": [
                        {"food": "Chilla"},
                    ]
                },
                "lunch": {
                    "food_items": [
                        {"food": "Dal"},
                        {"food": "Roti"},
                    ]
                },
            },
            "water_litres": "2 Litres",
            "other_fluids": [
                {
                    "type": "Herbal Tea",
                    "quantity": "200 ml",
                    "time": "04:30 PM",
                }
            ],
        }

        rows = {row["meal"]: row for row in saved_day_meal_rows(day)}
        summaries = dict(saved_day_card_rows(day))
        html = saved_day_card_html(day)

        self.assertEqual(rows["Breakfast"]["food"], "Chilla")
        self.assertEqual(rows["Breakfast"]["quantity"], "No entry")
        self.assertEqual(rows["Lunch"]["food"], "Dal; Roti")
        self.assertEqual(rows["Dinner"]["food"], "No entry")
        self.assertEqual(summaries["Water"], "2 Litres")
        self.assertIn("Herbal Tea", summaries["Other Liquids"])
        self.assertIn("Tue, 04 Aug 2026", html)
        self.assertIn("Meal · Time", html)
        self.assertIn("Quantity", html)
        self.assertIn("Other Liquids", html)

    def test_card_keeps_hydration_labels_when_no_entry_exists(self):
        rows = dict(saved_day_card_rows({"date": "2026-08-04", "meals": {}}))

        self.assertEqual(rows["Water"], "No entry")
        self.assertEqual(rows["Other Liquids"], "No entry")

    def test_saved_days_sort_newest_first_contract(self):
        earlier = {"date": "2026-07-29"}
        later = {"date": "2026-08-04"}

        ordered = sorted([earlier, later], key=saved_day_sort_key, reverse=True)

        self.assertEqual(ordered, [later, earlier])

    def test_daily_log_uses_three_column_card_grid_and_member_local_today(self):
        source = (ROOT / "pages/18_Daily_Log.py").read_text()

        self.assertIn("member_local_today(user_id)", source)
        self.assertIn("initialise_food_saved_days_range", source)
        self.assertIn('st.columns(3, gap="small")', source)
        self.assertIn("saved_day_card_html", source)
        self.assertNotIn('"Open saved day"', source)
        self.assertNotIn("hm_h9a4c_load_", source)
        self.assertNotIn("Viewing saved entries for", source)


if __name__ == "__main__":
    unittest.main()
