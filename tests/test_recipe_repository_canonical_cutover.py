from __future__ import annotations

import pathlib
import unittest
from unittest import mock

import components.recipe_repository as repository


ROOT = pathlib.Path(__file__).resolve().parents[1]
RECIPE = ROOT / "components" / "recipe_repository.py"
ADMIN_PAGE = ROOT / "pages" / "15_Admin_Recipe_Manager.py"
MEMBER_PAGE = ROOT / "pages" / "08_Recipe_Repository.py"


def canonical_row(
    source_id: str = "1",
    *,
    title: str = "Balanced Bowl",
    status: str = "active",
    version: int = 1,
) -> dict:
    return {
        "id": "internal-uuid",
        "repository_type": "recipe",
        "source_id": source_id,
        "display_name": title,
        "status": status,
        "payload": {
            "title": title,
            "description": "Balanced meal",
            "meal_type": "Lunch",
            "diet_type": "Vegetarian",
            "goal_tags": "general",
            "condition_tags": "general",
            "prep_time": "20",
            "calories": "450",
            "protein": "20g",
            "fat": "12g",
            "carbohydrates": "55g",
            "additional_nutrition": "Fibre: 8g",
            "servings": "1",
            "portion_size": "1 bowl",
            "image_url": "",
            "image_bucket": "",
            "image_path": "",
            "image_access_type": "public",
            "ingredients": "Vegetables; grains",
            "steps": "Cook and serve",
            "nutrition": "Balanced",
        },
        "content_version": version,
        "source_system": "recipe_csv",
        "legacy_reference": f"data/recipes.csv:row:{source_id}",
        "created_at": "2026-08-03T04:00:00+00:00",
        "created_by": "system:content_repository_backfill",
        "updated_at": "2026-08-03T04:00:00+00:00",
        "updated_by": "system:content_repository_backfill",
    }


class RecipeRepositoryCanonicalCutoverTests(unittest.TestCase):
    def test_repository_has_no_csv_or_app_state_authority(self) -> None:
        source = RECIPE.read_text(encoding="utf-8")
        self.assertNotIn("recipes.csv", source)
        self.assertNotIn("pandas", source)
        self.assertNotIn("load_state", source)
        self.assertNotIn("save_state", source)
        self.assertIn("list_repository_items", source)
        self.assertIn("create_numeric_repository_item", source)
        self.assertIn("save_repository_item", source)
        self.assertIn("set_repository_item_status", source)

    def test_list_flattens_canonical_envelope_to_legacy_shape(self) -> None:
        with mock.patch.object(
            repository,
            "list_repository_items",
            return_value=[canonical_row()],
        ) as list_items:
            rows = repository.list_recipe_repository(active_only=False)

        list_items.assert_called_once_with("recipe", active_only=False)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["id"], "1")
        self.assertEqual(rows[0]["source_id"], "1")
        self.assertEqual(rows[0]["resource_type"], "recipes")
        self.assertEqual(rows[0]["title"], "Balanced Bowl")
        self.assertEqual(rows[0]["portion_size"], "1 bowl")
        self.assertEqual(rows[0]["content_version"], 1)
        self.assertEqual(rows[0]["legacy_reference"], "data/recipes.csv:row:1")

    def test_add_uses_atomic_numeric_rpc(self) -> None:
        created = canonical_row("2", title="New Recipe")
        with mock.patch.object(
            repository,
            "create_numeric_repository_item",
            return_value=created,
        ) as create_item, mock.patch.object(
            repository,
            "_clear_streamlit_data_cache",
        ):
            result = repository.add_recipe_repository_item(
                {
                    "title": "New Recipe",
                    "meal_type": "Dinner",
                    "status": "active",
                },
                actor_id="admin_vineet",
            )

        args, kwargs = create_item.call_args
        self.assertEqual(args[0], "recipe")
        self.assertEqual(args[1], "New Recipe")
        self.assertEqual(args[2]["title"], "New Recipe")
        self.assertEqual(kwargs["actor_id"], "admin_vineet")
        self.assertEqual(kwargs["source_system"], "recipe_repository")
        self.assertEqual(result["id"], "2")

    def test_update_preserves_source_id_and_legacy_reference(self) -> None:
        before = canonical_row()
        after = canonical_row(title="Updated Bowl", version=2)
        with mock.patch.object(
            repository,
            "get_repository_item",
            return_value=before,
        ), mock.patch.object(
            repository,
            "save_repository_item",
            return_value=after,
        ) as save_item, mock.patch.object(
            repository,
            "_clear_streamlit_data_cache",
        ):
            result = repository.update_recipe_repository_item(
                "1",
                {"title": "Updated Bowl", "portion_size": "2 bowls"},
                actor_id="admin_vineet",
            )

        args, kwargs = save_item.call_args
        self.assertEqual(args[0:3], ("recipe", "1", "Updated Bowl"))
        self.assertEqual(args[3]["portion_size"], "2 bowls")
        self.assertEqual(kwargs["legacy_reference"], "data/recipes.csv:row:1")
        self.assertEqual(result["id"], "1")
        self.assertEqual(result["content_version"], 2)

    def test_delete_is_inactive_status_transition(self) -> None:
        inactive = canonical_row(status="inactive", version=2)
        with mock.patch.object(
            repository,
            "set_repository_item_status",
            return_value=inactive,
        ) as set_status, mock.patch.object(
            repository,
            "_clear_streamlit_data_cache",
        ):
            result = repository.delete_recipe_repository_item(
                "1", actor_id="admin_vineet"
            )

        set_status.assert_called_once_with(
            "recipe",
            "1",
            active=False,
            actor_id="admin_vineet",
        )
        self.assertEqual(result["status"], "inactive")

    def test_member_page_reads_canonical_repository_directly(self) -> None:
        source = MEMBER_PAGE.read_text(encoding="utf-8")
        self.assertIn("list_recipe_repository", source)
        self.assertIn("def load_recipes():", source)
        self.assertIn("frame.index = identities", source)
        self.assertNotIn("pd.read_csv", source)
        self.assertNotIn("DATA_PATH", source)

    def test_admin_page_has_no_csv_write_path(self) -> None:
        source = ADMIN_PAGE.read_text(encoding="utf-8")
        for forbidden in (
            "pandas",
            "pathlib",
            "recipes.csv",
            ".to_csv(",
            "df.loc[",
            "df.at[",
        ):
            self.assertNotIn(forbidden, source)
        self.assertIn("add_recipe_repository_item(", source)
        self.assertIn("update_recipe_repository_item(", source)
        self.assertIn("set_recipe_repository_status(", source)

    def test_member_page_preserves_assignment_identity_contract(self) -> None:
        source = MEMBER_PAGE.read_text(encoding="utf-8")
        self.assertIn("df.index.astype(str).isin(assigned_ids)", source)
        self.assertIn("int(selected_id) in df.index", source)
        self.assertNotIn("recipe_repository_runtime", source)


if __name__ == "__main__":
    unittest.main()
