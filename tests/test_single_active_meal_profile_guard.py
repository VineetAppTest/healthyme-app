from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
MIGRATION = (
    ROOT
    / "supabase"
    / "migrations"
    / "20260804052000_enforce_single_active_meal_profile.sql"
)
PUBLISH_CONTROL = ROOT / "components" / "profile_publish_control.py"


class SingleActiveMealProfileGuardTests(unittest.TestCase):
    def test_database_enforces_one_active_profile_per_member(self) -> None:
        source = MIGRATION.read_text(encoding="utf-8").lower()
        self.assertIn("create unique index", source)
        self.assertIn(
            "hm_recommendation_profiles_one_active_per_member_idx",
            source,
        )
        self.assertIn("on public.hm_recommendation_profiles (assigned_member_id)", source)
        self.assertIn("where status = 'active'", source)
        self.assertIn("nullif(btrim(assigned_member_id), '') is not null", source)

    def test_migration_refuses_to_hide_existing_duplicates(self) -> None:
        source = MIGRATION.read_text(encoding="utf-8").lower()
        self.assertIn("group by assigned_member_id", source)
        self.assertIn("having count(*) > 1", source)
        self.assertIn("raise exception", source)

    def test_publish_path_replaces_old_active_before_new_activation(self) -> None:
        source = PUBLISH_CONTROL.read_text(encoding="utf-8")
        replacement = source.index(
            'update({"status": "replaced", "updated_at": ts})'
        )
        activation = source.index(
            'update(update_payload).eq("id", profile_id).execute()'
        )
        self.assertLess(replacement, activation)
        self.assertIn('.eq("assigned_member_id", assigned_member_id)', source)
        self.assertIn('.eq("status", "active")', source)


if __name__ == "__main__":
    unittest.main()
