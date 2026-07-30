from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
HYGIENE = ROOT / "components" / "profile_builder_form_hygiene.py"
BUILDER = ROOT / "components" / "profile_builder_modular.py"


class ProfileBuilderFormHygieneContractTest(unittest.TestCase):
    def test_changed_python_files_compile(self):
        for path in (HYGIENE, BUILDER):
            compile(path.read_text(encoding="utf-8"), str(path), "exec")

    def test_hygiene_is_installed_before_renderer_bindings(self):
        source = BUILDER.read_text(encoding="utf-8")
        install_at = source.index("install_profile_builder_form_hygiene()")
        module_import_at = source.index("from components.pbm_modules import")
        setup_import_at = source.index("from components.pbm_setup import")
        publish_import_at = source.index("from components.profile_publish_control_v2 import")
        self.assertLess(install_at, module_import_at)
        self.assertLess(install_at, setup_import_at)
        self.assertLess(install_at, publish_import_at)

    def test_successful_setup_and_module_saves_reload_canonical_profile(self):
        source = HYGIENE.read_text(encoding="utf-8")
        self.assertIn("if ok:", source)
        self.assertIn("_SETUP_SAVE_PENDING", source)
        self.assertIn("_MODULE_SAVE_PENDING", source)
        self.assertGreaterEqual(source.count("pbm_core.load_selected("), 3)
        self.assertIn("_schedule_widget_cleanup()", source)
        self.assertIn("st.rerun()", source)

    def test_failed_validation_or_save_does_not_schedule_cleanup(self):
        source = HYGIENE.read_text(encoding="utf-8")
        self.assertIn("if ok:\n            st.session_state[_SETUP_SAVE_PENDING]", source)
        self.assertIn("if ok:\n            st.session_state[_MODULE_SAVE_PENDING]", source)
        self.assertIn("if success:\n            st.session_state[_PUBLISH_SUCCESS_PENDING]", source)
        self.assertNotIn("finally:\n            st.session_state[_SETUP_SAVE_PENDING]", source)
        self.assertNotIn("finally:\n            st.session_state[_MODULE_SAVE_PENDING]", source)

    def test_loaded_context_is_preserved_while_stale_widget_copies_clear(self):
        source = HYGIENE.read_text(encoding="utf-8")
        for retained_key in (
            "pbm_loaded_profile_id",
            "pbm_module_scope_",
            "pbm_module_profile_",
            "pbm_day_",
            "pbm_section",
        ):
            self.assertNotIn(f'clear_widget_state(("{retained_key}"', source)
        self.assertIn('"pbm_row_"', source)
        self.assertIn('"pbm_profile_name_"', source)
        self.assertIn("clear_prefixed_widget_state(_PROFILE_WIDGET_PREFIXES)", source)

    def test_clone_and_publish_transaction_controls_clear_only_after_success(self):
        source = HYGIENE.read_text(encoding="utf-8")
        self.assertIn("_CLONE_SUCCESS_PENDING", source)
        self.assertIn("_clear_clone_selector()", source)
        self.assertIn('clear_widget_state(("publish_draft_choice", "hm_publish_review_rows_open"))', source)
        self.assertIn("_PUBLISH_SUCCESS_PENDING", source)

    def test_runtime_does_not_change_profile_business_rules(self):
        source = HYGIENE.read_text(encoding="utf-8")
        for forbidden in (
            ".insert(",
            ".update(",
            ".delete(",
            ".upsert(",
            "authorization_id",
            "assigned_member_id =",
            "status = \"active\"",
            "status = \"draft\"",
        ):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
