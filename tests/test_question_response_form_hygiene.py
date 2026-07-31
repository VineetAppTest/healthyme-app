import py_compile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
QUESTION_PAGE = ROOT / "pages" / "20_Admin_Question_Manager.py"
RESPONSE_PAGE = ROOT / "pages" / "21_Admin_Response_Editor.py"


class QuestionResponseFormHygieneTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.question_source = QUESTION_PAGE.read_text(encoding="utf-8")
        cls.response_source = RESPONSE_PAGE.read_text(encoding="utf-8")

    def test_changed_pages_compile(self):
        py_compile.compile(str(QUESTION_PAGE), doraise=True)
        py_compile.compile(str(RESPONSE_PAGE), doraise=True)

    def test_question_create_forms_are_context_and_success_version_scoped(self):
        source = self.question_source
        self.assertIn('_version("standard_create", selected_form)', source)
        self.assertIn('_bump_version("standard_create", selected_form)', source)
        self.assertIn('_version("admin_create", system, selected_group_idx)', source)
        self.assertIn('_bump_version("admin_create", system, selected_group_idx)', source)
        self.assertIn('if _save_with_feedback(path, candidate, "New question added."):', source)
        self.assertIn('if _save_with_feedback(path, candidate, "Admin question added."):', source)

    def test_question_edit_forms_reload_canonical_saved_records(self):
        source = self.question_source
        self.assertIn('_version("standard_edit", selected_form, selected_idx)', source)
        self.assertIn('_bump_version("standard_edit", selected_form, selected_idx)', source)
        self.assertIn('"admin_item_edit",', source)
        self.assertIn('if _save_with_feedback(path, candidate, "Question saved."):', source)
        self.assertIn('if _save_with_feedback(path, candidate, "Admin question saved."):', source)
        self.assertIn('render_system_message()', source)
        self.assertIn('set_system_message(success_message, "success")', source)

    def test_question_failures_retain_entered_values(self):
        helper = self.question_source.split("def _save_with_feedback", 1)[1].split("_consume_cleanup()", 1)[0]
        self.assertIn("except Exception as exc:", helper)
        self.assertIn("Your entered values have been retained", helper)
        self.assertIn("return False", helper)
        self.assertNotIn("_bump_version", helper)
        self.assertNotIn("st.rerun", helper)

    def test_response_editor_isolates_member_form_field_state(self):
        source = self.response_source
        self.assertIn('key="hm_response_editor_member_id"', source)
        self.assertIn('key="hm_response_editor_form"', source)
        self.assertIn('_context_token(member_id, selected_form, field["field_code"])', source)
        self.assertIn('value_key = f"hm_response_editor_value_{token}_v{version}"', source)
        self.assertIn('rationale_key = f"hm_response_editor_rationale_{token}_v{version}"', source)

    def test_response_success_reloads_saved_value_and_failure_preserves_work(self):
        source = self.response_source
        save_block = source.split('if st.button(\n        "Save Edited Response with Audit Note"', 1)[1].split("card_end()", 1)[0]
        self.assertIn("elif not rationale.strip():", save_block)
        self.assertIn("except Exception as exc:", save_block)
        self.assertIn("Your entered value and rationale have been retained", save_block)
        self.assertIn("else:\n                _schedule_cleanup(value_key, rationale_key)", save_block)
        self.assertIn("_bump_version(token)", save_block)
        self.assertIn("st.session_state[SUCCESS_KEY] = True", save_block)

    def test_response_write_and_audit_rules_are_not_replaced(self):
        source = self.response_source
        save_position = source.index("save_db_direct(candidate_database)")
        audit_position = source.index("update_member_response_with_audit(")
        self.assertLess(save_position, audit_position)
        self.assertNotIn("switch_page", source)
        self.assertNotIn("st.login", source)
        self.assertNotIn("st.logout", source)

    def test_no_extra_read_or_rerun_is_added_to_submit_helpers(self):
        question_helper = self.question_source.split("def _save_with_feedback", 1)[1].split("_consume_cleanup()", 1)[0]
        response_save = self.response_source.split('if st.button(\n        "Save Edited Response with Audit Note"', 1)[1].split("card_end()", 1)[0]
        self.assertNotIn("load_db", question_helper)
        self.assertNotIn("st.rerun", question_helper)
        self.assertNotIn("load_db", response_save)
        self.assertEqual(response_save.count("st.rerun()"), 1)


if __name__ == "__main__":
    unittest.main()
