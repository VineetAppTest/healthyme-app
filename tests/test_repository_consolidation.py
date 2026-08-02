from __future__ import annotations

import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
RECIPE = ROOT / "pages" / "15_Admin_Recipe_Manager.py"
EXERCISE = ROOT / "pages" / "16_Admin_Exercise_Manager.py"
SUPPLEMENT = ROOT / "pages" / "39_Admin_Supplement_Manager.py"


class RepositoryConsolidationContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.recipe = RECIPE.read_text(encoding="utf-8")
        cls.exercise = EXERCISE.read_text(encoding="utf-8")
        cls.supplement = SUPPLEMENT.read_text(encoding="utf-8")

    def test_each_page_exposes_only_repository_and_add_sections(self):
        self.assertIn('st.tabs(["Current Repository", "Add Recipe"])', self.recipe)
        self.assertIn('st.tabs(["Current Repository", "Add Exercise"])', self.exercise)
        self.assertIn('st.tabs(["Current Repository", "Add Supplement"])', self.supplement)

    def test_import_feedback_and_direct_allocation_are_not_executable(self):
        for source in (self.recipe, self.exercise, self.supplement):
            self.assertNotIn("list_resource_feedback(", source)
            self.assertNotIn("save_resource_assignments(", source)
            self.assertNotIn("get_resource_assignments(", source)
            self.assertNotIn("Select member", source)
        self.assertNotIn("Import Recipe CSV", self.recipe)
        self.assertNotIn("Import Exercise CSV", self.exercise)
        self.assertNotIn("Member Recipe Feedback", self.recipe)
        self.assertNotIn("Member Exercise Feedback", self.exercise)

    def test_edit_and_delete_are_inline_repository_actions(self):
        for source in (self.recipe, self.exercise, self.supplement):
            self.assertIn('"Edit"', source)
            self.assertIn('"Delete"', source)
            self.assertIn('"Confirm Delete"', source)
            self.assertIn("Inactive Repository Items", source)
            self.assertIn('"Reactivate"', source)

    def test_safe_delete_preserves_history(self):
        self.assertIn('df.at[index, "status"] = "inactive"', self.recipe)
        self.assertNotIn("df.drop(", self.recipe)
        self.assertNotIn("reset_index(", self.recipe)
        self.assertIn("set_exercise_repository_status(", self.exercise)
        self.assertNotIn("delete_exercise_repository_item(", self.exercise)
        self.assertIn("set_supplement_repository_status(", self.supplement)
        for source in (self.recipe, self.exercise, self.supplement):
            self.assertIn("Historical references were retained.", source)

    def test_recipe_legacy_indices_are_not_reassigned(self):
        self.assertIn("physical deletion or index reset", self.recipe)
        self.assertNotIn("ignore_index=True", self.recipe)

    def test_repository_pages_no_longer_claim_to_allocate_members(self):
        self.assertNotIn("Manage & Allocate Recipes", self.recipe)
        self.assertNotIn("Manage & Allocate Exercises", self.exercise)
        for source in (self.recipe, self.exercise, self.supplement):
            self.assertIn("Member allocation is managed separately.", source)


if __name__ == "__main__":
    unittest.main()
