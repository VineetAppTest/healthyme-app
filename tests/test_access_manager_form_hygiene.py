from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
ACCESS_PAGE = ROOT / "pages" / "30_Admin_User_Access_Manager.py"
CREATE_PAGE = ROOT / "pages" / "17_Admin_User_Manager.py"


class AccessManagerFormHygieneTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.access_source = ACCESS_PAGE.read_text(encoding="utf-8")
        cls.create_source = CREATE_PAGE.read_text(encoding="utf-8")

    def test_access_selector_is_user_id_based_and_stable(self):
        self.assertIn('SELECTED_USER_KEY = "hm_access_selected_user_id"', self.access_source)
        self.assertIn("user_ids = list(user_map.keys())", self.access_source)
        self.assertIn("format_func=lambda user_id: _user_label(user_map[user_id])", self.access_source)
        self.assertIn("key=SELECTED_USER_KEY", self.access_source)

    def test_access_form_is_isolated_by_user_and_success_version(self):
        self.assertIn('FORM_VERSION_PREFIX = "hm_access_form_version_"', self.access_source)
        self.assertIn('with st.form(f"edit_user_form_{uid}_v{version}", clear_on_submit=False):', self.access_source)
        self.assertIn('name_key = f"hm_access_name_{uid}_v{version}"', self.access_source)
        self.assertIn('role_key = f"hm_access_role_{uid}_v{version}"', self.access_source)
        self.assertIn('active_key = f"hm_access_active_{uid}_v{version}"', self.access_source)

    def test_success_reloads_canonical_values_and_failure_preserves_inputs(self):
        submitted_block = self.access_source.split("if submitted:", 1)[1].split(
            "st.divider()", 1
        )[0]
        ok_block, failure_block = submitted_block.split("if ok:", 1)[1].split(
            "else:", 1
        )
        self.assertIn("st.session_state[CLEANUP_KEY]", ok_block)
        self.assertIn("_bump_form_version(uid)", ok_block)
        self.assertNotIn("_bump_form_version(uid)", failure_block)
        self.assertIn('set_system_message(msg, "error")', failure_block)

    def test_create_user_forms_already_clear_only_after_success(self):
        self.assertIn('st.session_state["clear_member_fields_next_run"] = True', self.create_source)
        self.assertIn('st.session_state["clear_admin_fields_next_run"] = True', self.create_source)
        self.assertIn('if not prov.get("ok"):', self.create_source)
        self.assertIn("st.rerun()", self.create_source)

    def test_no_extra_database_read_is_added_by_form_hygiene(self):
        self.assertEqual(self.access_source.count("list_all_users_for_access_manager()"), 1)
        self.assertNotIn("time.sleep", self.access_source)


if __name__ == "__main__":
    unittest.main()
