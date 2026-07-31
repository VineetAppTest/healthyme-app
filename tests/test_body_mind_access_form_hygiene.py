import pathlib
import py_compile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
PAGE = ROOT / "pages" / "23_Admin_Body_Mind_Control.py"
NSP_RECALC_PAGE = ROOT / "pages" / "34_Admin_NSP_Score_Recalculation.py"


class BodyMindAccessFormHygieneTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = PAGE.read_text(encoding="utf-8")

    def test_page_compiles(self):
        py_compile.compile(str(PAGE), doraise=True)

    def test_member_selection_uses_stable_member_id(self):
        self.assertIn('SELECTED_MEMBER_KEY = "hm_body_mind_access_member_id"', self.source)
        self.assertIn("member_map = {", self.source)
        self.assertIn("member_ids = list(member_map.keys())", self.source)
        self.assertIn("format_func=lambda value: _member_label(member_map[value])", self.source)
        self.assertIn("key=SELECTED_MEMBER_KEY", self.source)

    def test_disable_confirmation_is_member_and_success_version_scoped(self):
        self.assertIn('DISABLE_VERSION_PREFIX = "hm_body_mind_disable_version_"', self.source)
        self.assertIn("def _disable_version(member_id: str)", self.source)
        self.assertIn("def _advance_disable_version(member_id: str)", self.source)
        self.assertIn(
            'f"hm_body_mind_disable_confirm_{member_id}_{disable_version}"',
            self.source,
        )
        self.assertIn(
            'key=f"hm_body_mind_disable_button_{member_id}_{disable_version}"',
            self.source,
        )

    def test_confirmation_clears_only_after_success(self):
        action = self.source.split("try:\n                clear_body_mind_activation", 1)[1]
        failure, success = action.split("            else:", 1)
        self.assertIn("st.error(", failure)
        self.assertNotIn("_advance_disable_version", failure)
        self.assertIn("_advance_disable_version(member_id)", success)
        self.assertIn("st.rerun()", success)

    def test_existing_visibility_business_actions_remain(self):
        self.assertIn("clear_body_mind_activation(member_id)", self.source)
        self.assertIn(
            "manually_unlock_body_mind_after_finalization(member_id)",
            self.source,
        )
        self.assertIn(
            "sync_member_finalization_state(member_id, body_mind_unlock=None)",
            self.source,
        )
        self.assertIn("has_explicit_body_mind_access(member_id)", self.source)

    def test_hygiene_helpers_add_no_database_or_rerun_work(self):
        helper_block = self.source.split("def _member_label", 1)[1].split(
            "st.set_page_config", 1
        )[0]
        for forbidden in (
            "list_members(",
            "load_db(",
            "get_workflow(",
            "st.rerun(",
            "st.switch_page(",
        ):
            self.assertNotIn(forbidden, helper_block)

    def test_nsp_recalculation_has_no_reusable_transaction_fields(self):
        source = NSP_RECALC_PAGE.read_text(encoding="utf-8")
        self.assertIn("recalculate_all_nsp_system_scores", source)
        self.assertIn("recalculate_member_nsp_system_scores", source)
        self.assertNotIn("clear_on_submit=True", source)
        self.assertNotIn("form_version", source)


if __name__ == "__main__":
    unittest.main()
