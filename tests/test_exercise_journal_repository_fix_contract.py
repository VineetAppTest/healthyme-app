import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]


def source(path):
    return (ROOT / path).read_text(encoding="utf-8")


class ExerciseJournalRepositoryFixContractTests(unittest.TestCase):
    def test_admin_manager_no_longer_writes_local_exercise_csv(self):
        page = source("pages/16_Admin_Exercise_Manager.py")
        self.assertNotIn('data" / "exercises.csv', page)
        self.assertNotIn("to_csv(", page)
        self.assertNotIn("PATH =", page)
        self.assertIn("add_exercise_repository_item", page)
        self.assertIn("update_exercise_repository_item", page)
        self.assertIn("delete_exercise_repository_item", page)
        self.assertIn("import_exercise_repository_items", page)

    def test_admin_success_messages_remain_compatible_with_flash_runtime(self):
        page = source("pages/16_Admin_Exercise_Manager.py")
        cleanup = source("components/admin_content_form_cleanup.py")
        for message in (
            "Exercise saved.",
            "Exercise updated.",
            "Exercise deleted.",
        ):
            self.assertIn(message, page)
            self.assertIn(message, cleanup)
        self.assertIn("CSV imported.", page)
        self.assertIn('text.startswith("CSV imported.")', cleanup)

    def test_repository_preserves_numeric_ids_and_verifies_fresh_state(self):
        repository = source("components/exercise_repository.py")
        self.assertIn("_next_numeric_id", repository)
        self.assertIn("legacy_ids_preserved", repository)
        self.assertIn("load_state(force_refresh=True)", repository)
        self.assertIn("Exercise Repository persistence verification failed", repository)
        self.assertIn('status.get("mode") != "SUPABASE"', repository)

    def test_member_daily_log_uses_persistent_exclusive_selector(self):
        runtime = source("components/member_daily_log_section_runtime.py")
        self.assertIn('("Food Journal", "Exercise Journal")', runtime)
        self.assertIn('hm_daily_log_active_journal', runtime)
        self.assertIn("_INACTIVE_DEPTH", runtime)
        self.assertIn("selected == label", runtime)
        self.assertIn("if _inactive():", runtime)

    def test_runtime_install_order_preserves_admin_cleanup_authority(self):
        bootstrap = source("components/__init__.py")
        daily_install = bootstrap.index("install_member_daily_log_section_runtime()")
        admin_install = bootstrap.index("install_admin_content_form_cleanup()")
        self.assertLess(daily_install, admin_install)

    def test_member_repository_and_profile_builder_read_persistent_exercises(self):
        runtime = source("components/exercise_repository_runtime.py")
        self.assertIn('_LEGACY_SUFFIX = "/data/exercises.csv"', runtime)
        self.assertIn("list_exercise_repository", runtime)
        self.assertIn("persistent_list_repository_items", runtime)
        self.assertIn("recommendation_contract.list_repository_items", runtime)
        self.assertIn("st.cache_data = exercise_repository_cache_policy", runtime)

    def test_no_new_database_table_or_sql_migration_is_required(self):
        repository = source("components/exercise_repository.py")
        self.assertIn('"exercises"', repository)
        self.assertIn("load_state", repository)
        self.assertIn("save_state", repository)
        self.assertNotIn("create table", repository.lower())
        self.assertNotIn("alter table", repository.lower())


if __name__ == "__main__":
    unittest.main()
