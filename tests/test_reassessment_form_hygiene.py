from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "pages" / "25_Admin_Reassessment_Manager.py"


class ReassessmentFormHygieneTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = PAGE.read_text(encoding="utf-8")

    def test_member_selector_uses_stable_member_id(self):
        self.assertIn(
            'SELECTED_MEMBER_KEY = "hm_task_request_member_id"',
            self.source,
        )
        self.assertIn("member_map = {", self.source)
        self.assertIn("format_func=lambda value: _member_label(member_map[value])", self.source)
        self.assertIn("key=SELECTED_MEMBER_KEY", self.source)

    def test_request_fields_are_member_and_success_version_scoped(self):
        self.assertIn(
            'FORM_VERSION_PREFIX = "hm_task_request_form_version_"',
            self.source,
        )
        self.assertIn('nsp1_key = f"hm_task_nsp1_{member_id}_v{version}"', self.source)
        self.assertIn('nsp2_key = f"hm_task_nsp2_{member_id}_v{version}"', self.source)
        self.assertIn(
            'body_mind_key = f"hm_task_body_mind_{member_id}_v{version}"',
            self.source,
        )
        self.assertIn('due_key = f"hm_task_due_{member_id}_v{version}"', self.source)
        self.assertIn('note_key = f"hm_task_note_{member_id}_v{version}"', self.source)

    def test_success_retires_request_fields_only_after_created_true(self):
        created_block = self.source.split("if created:", 1)[1].split("else:", 1)[0]
        self.assertIn("st.session_state[CLEANUP_KEY]", created_block)
        self.assertIn("_bump_form_version(member_id)", created_block)

        duplicate_block = self.source.split("if created:", 1)[1].split("else:", 1)[1]
        duplicate_block = duplicate_block.split("st.rerun()", 1)[0]
        self.assertNotIn("_bump_form_version(member_id)", duplicate_block)
        self.assertIn("entered values have been retained", duplicate_block)

    def test_backend_failure_retains_request_values(self):
        self.assertIn("except Exception as exc:", self.source)
        exception_block = self.source.split("except Exception as exc:", 1)[1]
        exception_block = exception_block.split("task_names =", 1)[0]
        self.assertNotIn("_bump_form_version(member_id)", exception_block)
        self.assertIn("entered values have been retained", exception_block)

    def test_no_extra_read_or_delay_is_added(self):
        self.assertEqual(self.source.count("get_assessment_instances(member_id)"), 1)
        self.assertNotIn("time.sleep", self.source)
        self.assertNotIn("st.cache_data.clear", self.source)

    def test_body_mind_controls_remain_present(self):
        self.assertIn("clear_body_mind_activation(member_id)", self.source)
        self.assertIn("manually_unlock_body_mind_after_finalization(member_id)", self.source)


if __name__ == "__main__":
    unittest.main()
