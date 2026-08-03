from __future__ import annotations

import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
COMPONENTS_INIT = ROOT / "components" / "__init__.py"
RECIPE_REPOSITORY = ROOT / "components" / "recipe_repository.py"
EXERCISE_REPOSITORY = ROOT / "components" / "exercise_repository.py"
SUPPLEMENT_REPOSITORY = ROOT / "components" / "supplement_repository.py"
ADMIN_RECIPE = ROOT / "pages" / "15_Admin_Recipe_Manager.py"
MEMBER_RECIPE = ROOT / "pages" / "08_Recipe_Repository.py"
MEMBER_EXERCISE = ROOT / "pages" / "09_Exercise_Repository.py"
RECOMMENDATION_CONTRACT = ROOT / "components" / "recommendation_contract.py"
ADMIN_EXERCISE = ROOT / "pages" / "16_Admin_Exercise_Manager.py"
ADMIN_SUPPLEMENT = ROOT / "pages" / "39_Admin_Supplement_Manager.py"
RECIPES_CSV = ROOT / "data" / "recipes.csv"
EXERCISES_CSV = ROOT / "data" / "exercises.csv"


class ContentRepositoryLegacyRetirementTests(unittest.TestCase):
    def test_member_pages_read_canonical_modules_without_runtime_shims(self) -> None:
        recipe = MEMBER_RECIPE.read_text(encoding="utf-8")
        exercise = MEMBER_EXERCISE.read_text(encoding="utf-8")
        bootstrap = COMPONENTS_INIT.read_text(encoding="utf-8")
        contract = RECOMMENDATION_CONTRACT.read_text(encoding="utf-8")

        self.assertIn("list_recipe_repository", recipe)
        self.assertIn("list_exercise_repository", exercise)
        self.assertNotIn("pd.read_csv", recipe)
        self.assertNotIn("pd.read_csv", exercise)
        self.assertNotIn("install_recipe_repository_runtime", bootstrap)
        self.assertNotIn("install_exercise_repository_runtime", bootstrap)
        self.assertIn("list_recipe_repository(active_only=active_only)", contract)
        self.assertIn("list_exercise_repository(active_only=active_only)", contract)

    def test_legacy_sync_api_is_removed_from_live_code(self) -> None:
        source = RECOMMENDATION_CONTRACT.read_text(encoding="utf-8")
        self.assertNotIn("def sync_repository_to_state(", source)
        self.assertNotIn("def sync_all_repositories_to_state(", source)
        self.assertNotIn("sync_all_repositories_to_state()", source)

        for folder in (ROOT / "components", ROOT / "pages"):
            for path in folder.rglob("*.py"):
                live_source = path.read_text(encoding="utf-8")
                self.assertNotIn("sync_repository_to_state(", live_source, str(path))
                self.assertNotIn("sync_all_repositories_to_state(", live_source, str(path))

    def test_repository_diagnostics_use_canonical_sources(self) -> None:
        source = RECOMMENDATION_CONTRACT.read_text(encoding="utf-8")
        self.assertIn("recipe_repo = list_recipe_repository(active_only=False)", source)
        self.assertIn("exercise_repo = list_exercise_repository(active_only=False)", source)
        self.assertNotIn('recipe_repo = list(db.get("recipes", [])', source)
        self.assertNotIn('exercise_repo = list(db.get("exercises", [])', source)
        self.assertNotIn("repository mirror is empty", source)

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
