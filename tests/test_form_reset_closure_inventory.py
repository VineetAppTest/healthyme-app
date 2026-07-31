import pathlib
import re
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
PAGES = ROOT / "pages"
COMPONENTS = ROOT / "components"

# Files already corrected, confirmed compliant, read-only, or deliberately retained
# as editable-record exceptions during Issue #259.
AUDITED_RUNTIME_PATHS = {
    "pages/03_LAF_Form.py",
    "pages/04_NSP_Page1.py",
    "pages/05_NSP_Page2.py",
    "pages/06_Submit_Status.py",
    "pages/07_My_Profile.py",
    "pages/13_Admin_Assessment_Form.py",
    "pages/17_Admin_User_Manager.py",
    "pages/18_Daily_Log.py",
    "pages/19_Body_Mind_Connection.py",
    "pages/20_Admin_Question_Manager.py",
    "pages/21_Admin_Response_Editor.py",
    "pages/22_Admin_Daily_Log_Report.py",
    "pages/23_Admin_Body_Mind_Control.py",
    "pages/24_NSP_Consent_Submit.py",
    "pages/25_Admin_Reassessment_Manager.py",
    "pages/30_Admin_User_Access_Manager.py",
    "pages/31_Admin_Member_Communication.py",
    "pages/32_Admin_Scheduling.py",
    "pages/33_My_Schedule.py",
    "pages/41_Admin_Packages.py",
    "components/profile_builder_modular.py",
    "components/profile_builder_form_hygiene.py",
    "components/package_hardening_form_hygiene.py",
    "components/sprint1_schedule_hygiene.py",
}

MUTATION_LABEL = re.compile(
    r"(?:st\.|\.)(?:button|form_submit_button)\(\s*[furbFURB]*[\"']"
    r"[^\"']*(?:save|submit|send|create|add|update|publish|assign|replace|renew|"
    r"approve|reject|activate|disable|delete|remove|upload|record|confirm|request|"
    r"finali[sz]e|generate)[^\"']*[\"']",
    re.IGNORECASE,
)
FORM_CALL = re.compile(r"(?:st\.|\.)(?:form|form_submit_button)\(")


def _candidate_paths():
    for base in (PAGES, COMPONENTS):
        for path in sorted(base.rglob("*.py")):
            relative = path.relative_to(ROOT).as_posix()
            source = path.read_text(encoding="utf-8", errors="ignore")
            if FORM_CALL.search(source) or MUTATION_LABEL.search(source):
                yield relative


class FormResetClosureInventoryTests(unittest.TestCase):
    def test_every_submit_like_runtime_is_classified(self):
        candidates = set(_candidate_paths())
        unknown = sorted(candidates - AUDITED_RUNTIME_PATHS)
        self.assertEqual(
            unknown,
            [],
            "Unclassified Streamlit mutation/form candidates remain:\n- "
            + "\n- ".join(unknown),
        )

    def test_audited_paths_still_exist(self):
        missing = sorted(
            path for path in AUDITED_RUNTIME_PATHS if not (ROOT / path).exists()
        )
        self.assertEqual(missing, [], "Stale audit paths:\n- " + "\n- ".join(missing))


if __name__ == "__main__":
    unittest.main()
