import pathlib
import re
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
PAGES = ROOT / "pages"
COMPONENTS = ROOT / "components"

# Every entry was inspected during Issue #259 and classified as corrected,
# already compliant, an editable-record exception, or a non-production/support surface.
CLASSIFIED_RUNTIME_PATHS = {
    # Member assessment/profile editable records and one-time submission controls.
    "pages/00_Reset_Password.py",
    "pages/03_LAF_Form.py",
    "pages/04_NSP_Page1.py",
    "pages/05_NSP_Page2.py",
    "pages/06_Submit_Status.py",
    "pages/07_My_Profile.py",
    "pages/18_Daily_Log.py",
    "pages/19_Body_Mind_Connection.py",
    "pages/24_NSP_Consent_Submit.py",
    # Admin/practitioner forms corrected or confirmed compliant.
    "pages/13_Admin_Assessment_Form.py",
    "pages/15_Admin_Recipe_Manager.py",
    "pages/16_Admin_Exercise_Manager.py",
    "pages/17_Admin_User_Manager.py",
    "pages/20_Admin_Question_Manager.py",
    "pages/21_Admin_Response_Editor.py",
    "pages/22_Admin_Daily_Log_Report.py",
    "pages/23_Admin_Body_Mind_Control.py",
    "pages/25_Admin_Reassessment_Manager.py",
    "pages/25_Admin_Daily_Log_Settings.py",
    "pages/28_Admin_Database_Status.py",
    "pages/30_Admin_User_Access_Manager.py",
    "pages/31_Admin_Member_Communication.py",
    "pages/32_Admin_Scheduling.py",
    "pages/34_Admin_Supabase_Auth_Provisioning_Workbench.py",
    "pages/35_Admin_Recommendations_Share.py",
    "pages/36_Admin_Nutritionist_Notes_Workbench.py",
    "pages/36_Admin_Unified_Recommendations.py",
    "pages/39_Admin_Supplement_Manager.py",
    "pages/41_Admin_Packages.py",
    "pages/42_Admin_Exercise_Member_Allocation.py",
    # Member schedule/journal and repositories are editable records or navigation surfaces.
    "pages/01_Login.py",
    "pages/02_Member_Home.py",
    "pages/08_Recipe_Repository.py",
    "pages/09_Exercise_Repository.py",
    "pages/33_My_Schedule.py",
    # Diagnostics and mockups are non-production/support surfaces.
    "pages/29_Admin_Demo_Mode.py",
    "pages/37_Admin_Recommendation_Profile_Builder_Mockup.py",
    "pages/39_Admin_Recommendation_Profile_Builder_Mockup_V3.py",
    "pages/40_Admin_Recommendation_Profile_Builder_Mockup_V4.py",
    # Shared form implementations and accepted hygiene layers.
    "components/admin_content_form_cleanup.py",
    "components/admin_scheduling_consolidated.py",
    "components/auth_provisioning_form_hygiene.py",
    "components/member_exercise_journal.py",
    "components/member_exercise_journal_layout_v4.py",
    "components/member_exercise_journal_table.py",
    "components/member_schedule_tabbed_page.py",
    "components/notes_supplement_form_hygiene.py",
    "components/package_hardening_form_hygiene.py",
    "components/package_hardening_ui.py",
    "components/package_value_formula_ui.py",
    "components/pbm_modules.py",
    "components/pbm_setup.py",
    "components/performance_measurement_gate.py",
    "components/profile_builder_form_hygiene.py",
    "components/profile_builder_modular.py",
    "components/profile_publish_control.py",
    "components/profile_publish_control_v2.py",
    "components/recommendations_share_form_hygiene.py",
    "components/schedule_timezone_ui.py",
    "components/sprint1_schedule_hygiene.py",
}

MUTATION_LABEL = re.compile(
    r"(?:st\.|\.)(?:button|form_submit_button)\(\s*[furbFURB]*[\"']"
    r"[^\"']*(?:save|submit|send|create|add|update|publish|assign|replace|renew|"
    r"approve|reject|activate|disable|delete|remove|upload|record|confirm|request|"
    r"finali[sz]e|generate|reset|migrate|sync)[^\"']*[\"']",
    re.IGNORECASE,
)
FORM_CALL = re.compile(r"(?:st\.|\.)(?:form|form_submit_button)\(")


def candidate_paths():
    for base in (PAGES, COMPONENTS):
        for path in sorted(base.rglob("*.py")):
            relative = path.relative_to(ROOT).as_posix()
            source = path.read_text(encoding="utf-8", errors="ignore")
            if FORM_CALL.search(source) or MUTATION_LABEL.search(source):
                yield relative


class FormResetClosureInventoryV2Tests(unittest.TestCase):
    def test_every_submit_like_runtime_is_classified(self):
        candidates = set(candidate_paths())
        unknown = sorted(candidates - CLASSIFIED_RUNTIME_PATHS)
        self.assertEqual(
            unknown,
            [],
            "Unclassified Streamlit mutation/form candidates remain:\n- "
            + "\n- ".join(unknown),
        )

    def test_classified_paths_still_exist(self):
        missing = sorted(
            path for path in CLASSIFIED_RUNTIME_PATHS if not (ROOT / path).exists()
        )
        self.assertEqual(missing, [], "Stale classified paths:\n- " + "\n- ".join(missing))


if __name__ == "__main__":
    unittest.main()
