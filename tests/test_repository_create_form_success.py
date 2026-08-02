from __future__ import annotations

import importlib
import unittest

import components.repository_create_form_success as runtime


class FakeStreamlit:
    def __init__(self):
        self.session_state = {}
        self.success_messages = []
        self.rerun_count = 0
        self.last_widget_key = None
        self.button_result = False
        self.form_submit_result = False

    def button(self, *args, **kwargs):
        self.last_widget_key = kwargs.get("key")
        return self.button_result

    def form_submit_button(self, *args, **kwargs):
        return self.form_submit_result

    def text_input(self, *args, **kwargs):
        self.last_widget_key = kwargs.get("key")
        return ""

    def text_area(self, *args, **kwargs):
        self.last_widget_key = kwargs.get("key")
        return ""

    def selectbox(self, *args, **kwargs):
        self.last_widget_key = kwargs.get("key")
        return ""

    def multiselect(self, *args, **kwargs):
        self.last_widget_key = kwargs.get("key")
        return []

    def file_uploader(self, *args, **kwargs):
        self.last_widget_key = kwargs.get("key")
        return None

    def success(self, body, *args, **kwargs):
        self.success_messages.append(str(body))
        return body

    def rerun(self, *args, **kwargs):
        self.rerun_count += 1


class RepositoryCreateFormSuccessTests(unittest.TestCase):
    def setUp(self):
        importlib.reload(runtime)
        self.fake = FakeStreamlit()
        runtime.st = self.fake
        runtime.install_repository_create_form_success()

    def test_recipe_confirmed_save_advances_version_and_clears_top_flash(self):
        runtime._page_kind = lambda: "recipe"
        self.fake.session_state["hm_recipe_repository_flash"] = (
            "success",
            "Recipe saved.",
        )
        self.fake.session_state["new_recipe_repository_uploaded_image_meta"] = {
            "image_url": "old"
        }

        self.fake.rerun()

        self.assertEqual(
            self.fake.session_state["_hm_recipe_repository_create_version"], 2
        )
        self.assertNotIn("hm_recipe_repository_flash", self.fake.session_state)
        self.assertNotIn(
            "new_recipe_repository_uploaded_image_meta", self.fake.session_state
        )
        self.assertIn(
            "new recipe",
            self.fake.session_state["_hm_recipe_repository_create_success"],
        )
        self.assertEqual(self.fake.rerun_count, 1)

    def test_failed_recipe_save_retains_version_and_entered_state(self):
        runtime._page_kind = lambda: "recipe"
        self.fake.session_state["hm_recipe_repository_flash"] = (
            "error",
            "Recipe title is required.",
        )
        self.fake.session_state["new_recipe_repository_uploaded_image_meta"] = {
            "image_url": "retain"
        }

        self.fake.rerun()

        self.assertNotIn(
            "_hm_recipe_repository_create_version", self.fake.session_state
        )
        self.assertIn("hm_recipe_repository_flash", self.fake.session_state)
        self.assertIn(
            "new_recipe_repository_uploaded_image_meta", self.fake.session_state
        )

    def test_recipe_create_widgets_receive_success_versioned_keys(self):
        runtime._page_kind = lambda: "recipe"
        runtime._inside_create_form = lambda kind: kind == "recipe"
        self.fake.session_state["_hm_recipe_repository_create_version"] = 4

        self.fake.text_input("Title", key="new_recipe_repository_title")

        self.assertEqual(
            self.fake.last_widget_key,
            "new_recipe_repository_title__v4",
        )

    def test_recipe_success_is_rendered_next_to_save_button(self):
        runtime._page_kind = lambda: "recipe"
        message = "Recipe saved successfully. The form is ready for a new recipe."
        self.fake.session_state["_hm_recipe_repository_create_success"] = message

        self.fake.button("Save Recipe", type="primary")

        self.assertEqual(self.fake.success_messages, [message])
        self.assertNotIn(
            "_hm_recipe_repository_create_success", self.fake.session_state
        )

    def test_exercise_confirmed_save_uses_same_rule(self):
        runtime._page_kind = lambda: "exercise"
        self.fake.session_state["hm_exercise_repository_flash"] = (
            "success",
            "Exercise saved.",
        )

        self.fake.rerun()

        self.assertEqual(
            self.fake.session_state["_hm_exercise_repository_create_version"], 2
        )
        self.assertIn(
            "new exercise",
            self.fake.session_state["_hm_exercise_repository_create_success"],
        )

    def test_supplement_confirmed_save_advances_established_hygiene_version(self):
        runtime._page_kind = lambda: "supplement"
        self.fake.session_state["hm_supplement_repository_flash"] = (
            "success",
            "Supplement added to repository.",
        )

        self.fake.rerun()

        self.assertEqual(
            self.fake.session_state["_hm_supplement_create_version_member"], 2
        )
        self.assertNotIn("hm_supplement_repository_flash", self.fake.session_state)
        self.assertIn(
            "new supplement",
            self.fake.session_state["_hm_supplement_repository_create_success"],
        )

    def test_supplement_success_is_local_and_does_not_retrigger_reset(self):
        runtime._page_kind = lambda: "supplement"
        message = "Saved successfully. The form is ready for a new supplement."
        self.fake.session_state["_hm_supplement_repository_create_success"] = message

        self.fake.form_submit_button("Add to Repository")

        self.assertEqual(self.fake.success_messages, [message])
        self.assertFalse(message.startswith("Supplement added"))

    def test_no_database_auth_or_routing_operations_are_introduced(self):
        source = open(runtime.__file__, encoding="utf-8").read()
        for forbidden in (
            "components.db",
            "load_state(",
            "save_state(",
            "st.switch_page",
            "st.login",
            "st.logout",
        ):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
