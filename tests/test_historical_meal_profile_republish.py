from __future__ import annotations

import inspect
import unittest

from components import member_plan_builder_meals_compact as meals


class HistoricalMealProfileRepublishTests(unittest.TestCase):
    def test_retained_historical_profiles_are_publishable_but_not_editable(self) -> None:
        replaced = {
            "id": "profile-replaced",
            "status": "replaced",
            "assigned_member_id": "member-old",
        }
        archived = {
            "id": "profile-archived",
            "status": "archived",
            "assigned_member_id": "member-old",
        }

        for row in (replaced, archived):
            self.assertTrue(meals._profile_is_publishable_source(row))
            self.assertFalse(meals._profile_is_editable(row))

    def test_active_or_allocated_profile_can_seed_a_fresh_copy_without_becoming_editable(self) -> None:
        active = {
            "id": "profile-active",
            "status": "active",
            "assigned_member_id": "member-current",
        }

        self.assertTrue(meals._profile_is_publishable_source(active))
        self.assertFalse(meals._profile_is_editable(active))
        self.assertFalse(meals._profile_is_publishable_source({}))

    def test_publish_control_is_decoupled_from_editability(self) -> None:
        source = inspect.getsource(meals._render_publish_controls)

        self.assertIn("profile_publishable = _profile_is_publishable_source", source)
        self.assertIn("or not profile_publishable", source)
        self.assertNotIn("or not profile_editable", source)
        self.assertIn("source remains read-only and unchanged", source)
        self.assertIn("Meal Profile only when you need to modify", source)

    def test_publish_still_creates_a_new_copy_and_retains_source_identity(self) -> None:
        source = inspect.getsource(meals._publish_repository_plan)

        self.assertIn('member_plan = copy.deepcopy(profile)', source)
        self.assertIn('"id": ""', source)
        self.assertIn('"status": "draft"', source)
        self.assertIn('"clone_source_profile_id": source_id', source)
        self.assertIn('"assigned_member_id": member_id', source)
        self.assertIn('activate_profile(member_plan, "ACTIVATE")', source)


if __name__ == "__main__":
    unittest.main()
