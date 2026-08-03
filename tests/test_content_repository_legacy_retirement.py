from __future__ import annotations

import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
COMPONENTS_INIT = ROOT / "components" / "__init__.py"
EXERCISE_RUNTIME = ROOT / "components" / "exercise_repository_runtime.py"
RECIPE_RUNTIME = ROOT / "components" / "recipe_repository_runtime.py"
RECIPE_REPOSITORY = ROOT / "components" / "recipe_repository.py"
EXERCISE_REPOSITORY = ROOT / "components" / "exercise_repository.py"
SUPPLEMENT_REPOSITORY = ROOT / "components" / "supplement_repository.py"
ADMIN_RECIPE = ROOT / "pages" / "15_Admin_Recipe_Manager.py"
ADMIN_EXERCISE = ROOT / "pages" / "16_Admin_Exercise_Manager.py"
ADMIN_SUPPLEMENT = ROOT / "pages" / "39_Admin_Supplement_Manager.py"
RECIPES_CSV = ROOT / "data" / "recipes.csv"
EXERCISES_CSV = ROOT / "data" / "exercises.csv"


class ContentRepositoryLegacyRetirementTests(unittest.TestCase):
    def test_recipe_and_exercise_compatibility_syncs_are_read_only(self) -> None:
        recipe_runtime = RECIPE_RUNTIME.read_text(encoding="utf-8")
        exercise_runtime = EXERCISE_RUNTIME.read_text(encoding="utf-8")

        for source, repository_call in (
            (recipe_runtime, "list_recipe_repository(active_only=False)"),
            (exercise_runtime, "list_exercise_repository(active_only=False)"),
        ):
            self.assertIn("original_sync_repository_to_state", source)
            self.assertIn("canonical_sync_repository_to_state", source)
            self.assertIn(repository_call, source)
            self.assertIn("read-only snapshot", source)
            self.assertNotIn("save_state", source)

    def test_runtime_install_order_composes_both_read_only_guards(self) -> None:
        source = COMPONENTS_INIT.read_text(encoding="utf-8")
        exercise_install = source.index("install_exercise_repository_runtime()")
        recipe_install = source.index("install_recipe_repository_runtime()")
        self.assertLess(exercise_install, recipe_install)

    def test_live_repository_modules_have_no_legacy_state_authority(self) -> None:
        for path in (
            RECIPE_REPOSITORY,
            EXERCISE_REPOSITORY,
            SUPPLEMENT_REPOSITORY,
        ):
            source = path.read_text(encoding="utf-8")
            self.assertNotIn("load_state", source)
            self.assertNotIn("save_state", source)
            self.assertNotIn("healthyme_app_state", source)
            self.assertIn("list_repository_items", source)

    def test_admin_pages_have_no_csv_or_app_state_write_path(self) -> None:
        recipe = ADMIN_RECIPE.read_text(encoding="utf-8")
        exercise = ADMIN_EXERCISE.read_text(encoding="utf-8")
        supplement = ADMIN_SUPPLEMENT.read_text(encoding="utf-8")

        self.assertNotIn("pd.read_csv", recipe)
        self.assertNotIn("to_csv", recipe)
        self.assertNotIn("data/recipes.csv", recipe)
        for source in (recipe, exercise, supplement):
            self.assertNotIn("load_state", source)
            self.assertNotIn("save_state", source)

    def test_legacy_csv_files_are_retained_only_as_rollback_evidence(self) -> None:
        self.assertTrue(RECIPES_CSV.exists())
        self.assertTrue(EXERCISES_CSV.exists())
        self.assertGreater(RECIPES_CSV.stat().st_size, 0)
        self.assertGreater(EXERCISES_CSV.stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
