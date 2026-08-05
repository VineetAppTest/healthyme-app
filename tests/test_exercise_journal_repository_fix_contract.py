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
        self.assertIn("set_exercise_repository_status", page)
        self.assertNotIn("delete_exercise_repository_item", page)
        self.assertNotIn("import_exercise_repository_items", page)

    def test_admin_success_messages_remain_compatible_with_final_repair_runtime(self):
        page = source("pages/16_Admin_Exercise_Manager.py")
        repair = source("components/admin_exercise_repair_runtime.py")
        for message in (
            "Exercise saved.",
            "Exercise updated.",
        ):
            self.assertIn(message, page)
            self.assertIn(message, repair)
        self.assertIn("Historical references were retained.", page)
        self.assertIn("Exercise reactivated.", page)
        self.assertIn("_flash", page)
        self.assertIn("_show_flash", page)
        self.assertIn("_render_pending_success", repair)

    def test_repository_preserves_numeric_ids_and_verifies_fresh_supabase_state(self):
        repository = source("components/exercise_repository.py")
        store = source("components/content_repository_store.py")
        migration = source(
            "supabase/migrations/20260803104500_create_numeric_content_repository_item_rpc.sql"
        )
        self.assertIn("_next_numeric_id", repository)
        self.assertIn("create_numeric_repository_item", repository)
        self.assertIn("list_repository_items", repository)
        self.assertIn("save_repository_item", repository)
        self.assertIn("set_repository_item_status", repository)
        self.assertNotIn("load_state", repository)
        self.assertNotIn("save_state", repository)
        self.assertIn("_verified_item", store)
        self.assertIn("get_repository_item(repository_type, source_id)", store)
        self.assertIn("pg_advisory_xact_lock", migration)

    def test_member_daily_log_uses_exclusive_server_rendering(self):
        runtime = source("components/member_daily_log_native_tab_persistence.py")
        self.assertIn(
            '("Food Journal", "Exercise Journal", "Supplement Journal")',
            runtime,
        )
        self.assertIn("_daily_log_frame", runtime)
        self.assertIn("_install_renderer_gates", runtime)
        self.assertIn("_render_food_journal", runtime)
        self.assertIn("_render_exercise_journal", runtime)
        self.assertIn("_render_supplement_journal", runtime)
        self.assertIn("contextlib.nullcontext()", runtime)
        self.assertNotIn("sessionStorage", runtime)
        self.assertNotIn("MutationObserver", runtime)
        self.assertNotIn("_bound_native_tabs", runtime)

    def test_runtime_install_order_preserves_admin_and_daily_log_authority(self):
        bootstrap = source("components/__init__.py")
        self.assertNotIn("install_member_daily_log_section_runtime()", bootstrap)
        admin_cleanup = bootstrap.index("install_admin_content_form_cleanup()")
        admin_repair = bootstrap.index("install_admin_exercise_repair_runtime()")
        daily_exclusive = bootstrap.index(
            "install_member_daily_log_native_tab_persistence()"
        )
        self.assertLess(admin_cleanup, admin_repair)
        self.assertLess(admin_repair, daily_exclusive)

    def test_member_repository_and_profile_builder_read_persistent_exercises(self):
        page = source("pages/09_Exercise_Repository.py")
        contract = source("components/recommendation_contract.py")
        bootstrap = source("components/__init__.py")
        self.assertIn("list_exercise_repository", page)
        self.assertIn("def load_exercises():", page)
        self.assertIn("frame.index = identities", page)
        self.assertNotIn("pd.read_csv", page)
        self.assertNotIn("DATA_PATH", page)
        self.assertIn("list_exercise_repository(active_only=active_only)", contract)
        self.assertNotIn("install_exercise_repository_runtime", bootstrap)

    def test_exercise_uses_standard_content_repository_without_new_table(self):
        repository = source("components/exercise_repository.py")
        store = source("components/content_repository_store.py")
        migration = source(
            "supabase/migrations/20260803104500_create_numeric_content_repository_item_rpc.sql"
        )
        self.assertIn('list_repository_items("exercise"', repository)
        self.assertIn('save_repository_item(\n        "exercise"', repository)
        self.assertIn('set_repository_item_status(\n        "exercise"', repository)
        self.assertIn('CONTENT_TABLE = "hm_content_repository_items"', store)
        self.assertNotIn("create table", migration.lower())
        self.assertNotIn("alter table", migration.lower())


if __name__ == "__main__":
    unittest.main()
