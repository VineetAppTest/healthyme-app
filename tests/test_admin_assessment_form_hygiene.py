import pathlib
import py_compile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
PAGE = ROOT / "pages" / "13_Admin_Assessment_Form.py"


class AdminAssessmentFormHygieneTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = PAGE.read_text(encoding="utf-8")

    def test_page_compiles(self):
        py_compile.compile(str(PAGE), doraise=True)

    def test_widget_keys_are_member_and_instance_scoped(self):
        self.assertIn("def _assessment_widget_key(field_key: str)", self.source)
        self.assertIn('selected_instance_id or "legacy"', self.source)
        self.assertIn('f"admin_assessment::{mid}::{instance_scope}::{field_key}"', self.source)
        self.assertIn("key=widget_key", self.source)
        self.assertIn('key=_assessment_widget_key("body_mind_activation")', self.source)

    def test_saved_assessment_is_not_cleared_after_success(self):
        self.assertNotIn("session_state.pop(widget_key", self.source)
        self.assertNotIn("clear_on_submit=True", self.source)
        self.assertNotIn("_bump_form_version", self.source)
        self.assertIn("existing = get_admin_assessment(mid, selected_instance_id)", self.source)

    def test_existing_business_write_paths_remain(self):
        self.assertGreaterEqual(
            self.source.count("save_admin_assessment(mid, all_data, selected_instance_id)"),
            2,
        )
        self.assertIn("result = finalize_admin_assessment(", self.source)
        self.assertIn("request_body_mind_activation(mid)", self.source)
        self.assertIn("sync_member_finalization_state(mid, body_mind_unlock=None)", self.source)

    def test_no_extra_read_or_rerun_is_added_for_context_isolation(self):
        helper = self.source.split("def _assessment_widget_key", 1)[1].split("try:", 1)[0]
        for forbidden in ("load_db(", "get_workflow(", "st.rerun(", "st.switch_page("):
            self.assertNotIn(forbidden, helper)

    def test_read_only_review_and_report_pages_need_no_reset_runtime(self):
        for relative in (
            "pages/26_Admin_Review_Queue.py",
            "pages/12_Partial_Assessment_Report.py",
            "pages/14_Final_Assessment_Report.py",
        ):
            source = (ROOT / relative).read_text(encoding="utf-8")
            self.assertNotIn("form_version", source)
            self.assertNotIn("clear_on_submit=True", source)


if __name__ == "__main__":
    unittest.main()
