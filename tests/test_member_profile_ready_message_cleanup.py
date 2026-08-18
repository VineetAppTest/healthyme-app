import unittest

from components.member_message_display_cleanup import member_home_visible_messages


class MemberProfileReadyMessageCleanupTests(unittest.TestCase):
    def test_profile_activation_message_is_hidden_but_meal_allocation_remains(self) -> None:
        rows = [
            {
                "source": "recommendation_profile",
                "subject": "Your HealthyMe recommendation profile is ready",
                "message": "Your plan has been activated.",
            },
            {
                "source": "meal_plan_allocation",
                "subject": "Meal added",
                "message": "Your Meal allocation has been updated.",
            },
        ]

        visible = member_home_visible_messages(rows)

        self.assertEqual(len(visible), 1)
        self.assertEqual(visible[0]["subject"], "Meal added")

    def test_schedule_duplicates_remain_hidden_and_normal_messages_remain(self) -> None:
        rows = [
            {"source": "schedule", "subject": "Session scheduled", "message": "Review"},
            {
                "source": "nutritionist_note",
                "subject": "Message from Nutritionist",
                "message": "Keep hydration steady.",
            },
        ]

        visible = member_home_visible_messages(rows)

        self.assertEqual(len(visible), 1)
        self.assertEqual(visible[0]["source"], "nutritionist_note")


if __name__ == "__main__":
    unittest.main()
