import pathlib
import py_compile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
CONSENT_PAGE = ROOT / "pages" / "24_NSP_Consent_Submit.py"
STATUS_PAGE = ROOT / "pages" / "06_Submit_Status.py"


class MemberAssessmentSubmitFormHygieneTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.consent_source = CONSENT_PAGE.read_text(encoding="utf-8")
        cls.status_source = STATUS_PAGE.read_text(encoding="utf-8")

    def test_changed_pages_compile(self):
        py_compile.compile(str(CONSENT_PAGE), doraise=True)
        py_compile.compile(str(STATUS_PAGE), doraise=True)

    def test_consent_controls_are_member_and_instance_scoped(self):
        self.assertIn("def _instance_scope(instance: dict)", self.consent_source)
        self.assertIn("instance_scope = _instance_scope(instance)", self.consent_source)
        self.assertIn("consent_version = _consent_version(instance_scope)", self.consent_source)
        for token in (
            "hm_member_consent_accept_{user_id}_{instance_scope}_{consent_version}",
            "hm_member_consent_name_{user_id}_{instance_scope}_{consent_version}",
            "hm_member_consent_date_{user_id}_{instance_scope}_{consent_version}",
            "hm_member_consent_submit_{user_id}_{instance_scope}_{consent_version}",
        ):
            self.assertIn(token, self.consent_source)

    def test_consent_clears_only_after_confirmed_first_submission(self):
        success_block = self.consent_source.split("if first_submission:", 1)[1].split(
            "else:", 1
        )[0]
        self.assertIn("_advance_consent_version(instance_scope)", success_block)
        self.assertIn("submit_current_assessment_instance_once(", self.consent_source)
        self.assertIn("recalculate_member_nsp_system_scores(", self.consent_source)
        self.assertIn("except Exception:", self.consent_source)
        self.assertIn("Your consent, name and ", self.consent_source)
        self.assertIn("date remain available so you can try again.", self.consent_source)

    def test_submit_status_confirmation_is_instance_scoped(self):
        self.assertIn("instance_scope = _instance_scope(current)", self.status_source)
        self.assertIn("submit_version = _submit_version(instance_scope)", self.status_source)
        self.assertIn(
            "hm_member_submit_confirm_{user_id}_{instance_scope}_{submit_version}",
            self.status_source,
        )
        self.assertIn(
            "hm_member_submit_button_{user_id}_{instance_scope}_{submit_version}",
            self.status_source,
        )

    def test_submit_status_clears_only_after_confirmed_success(self):
        success_block = self.status_source.split("if first_submission:", 1)[1].split(
            "else:", 1
        )[0]
        self.assertIn("_advance_submit_version(instance_scope)", success_block)
        self.assertIn("except Exception:", self.status_source)
        self.assertIn("The confirmation remains ", self.status_source)
        self.assertIn("selected so you can try again.", self.status_source)
        self.assertIn("submit_current_assessment_instance_once(", self.status_source)

    def test_editable_member_records_are_not_blank_reset(self):
        editable_pages = (
            "pages/03_LAF_Form.py",
            "pages/04_NSP_Page1.py",
            "pages/05_NSP_Page2.py",
            "pages/07_My_Profile.py",
            "pages/19_Body_Mind_Connection.py",
        )
        for relative in editable_pages:
            source = (ROOT / relative).read_text(encoding="utf-8")
            self.assertNotIn("clear_on_submit=True", source)
            self.assertNotIn("clear_widget_state(", source)
            self.assertNotIn("clear_prefixed_widget_state(", source)

    def test_no_additional_read_is_used_for_reset_state(self):
        consent_helper = self.consent_source.split("CONSENT_VERSION_PREFIX", 1)[1].split(
            "def task_title_v96_2", 1
        )[0]
        status_helper = self.status_source.split("SUBMIT_VERSION_PREFIX", 1)[1].split(
            "def task_title_v96_2", 1
        )[0]
        for helper in (consent_helper, status_helper):
            for forbidden in (
                "get_current_assessment_instance(",
                "get_assessment_instances(",
                "get_workflow(",
                "load_db(",
                "st.rerun(",
            ):
                self.assertNotIn(forbidden, helper)


if __name__ == "__main__":
    unittest.main()
