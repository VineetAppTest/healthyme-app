from pathlib import Path
import py_compile
import unittest


ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "components" / "notes_supplement_form_hygiene.py"
INIT = ROOT / "components" / "__init__.py"
NOTES = ROOT / "pages" / "36_Admin_Nutritionist_Notes_Workbench.py"
SUPPLEMENT = ROOT / "pages" / "39_Admin_Supplement_Manager.py"


class NotesSupplementFormHygieneTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = COMPONENT.read_text(encoding="utf-8")
        cls.init_source = INIT.read_text(encoding="utf-8")
        cls.notes_source = NOTES.read_text(encoding="utf-8")
        cls.supplement_source = SUPPLEMENT.read_text(encoding="utf-8")

    def test_component_and_unchanged_pages_compile(self):
        for path in (COMPONENT, NOTES, SUPPLEMENT):
            py_compile.compile(str(path), doraise=True)

    def test_installer_runs_after_existing_admin_content_cleanup(self):
        self.assertIn("install_notes_supplement_form_hygiene", self.init_source)
        self.assertLess(
            self.init_source.index("install_admin_content_form_cleanup()"),
            self.init_source.index("install_notes_supplement_form_hygiene()"),
        )
        self.assertLess(
            self.init_source.index("install_notes_supplement_form_hygiene()"),
            self.init_source.index("install_member_saved_days_home_cleanup()"),
        )

    def test_page_detection_walks_to_the_actual_page_frame(self):
        self.assertIn("def _page_context()", self.source)
        self.assertIn("while frame is not None:", self.source)
        self.assertIn("return \"notes\", frame", self.source)
        self.assertIn("return \"supplement\", frame", self.source)

    def test_notes_form_is_member_scoped_and_failure_safe(self):
        self.assertIn('"h9a4_structured_note_form"', self.source)
        self.assertIn('kwargs["clear_on_submit"] = False', self.source)
        self.assertIn('_NOTES_MEMBER_KEY = "hm_h9a4_note_member"', self.source)
        self.assertIn('kwargs.setdefault("key", _NOTES_MEMBER_KEY)', self.source)
        self.assertIn('f"h9a4_structured_note_form_{scope}_{version}"', self.source)
        self.assertIn('with st.form("h9a4_structured_note_form", clear_on_submit=False)', self.notes_source)

    def test_first_notes_render_uses_real_member_scope(self):
        self.assertIn("def _initialise_notes_member(page_frame", self.source)
        self.assertIn('page_frame.f_locals.get("member_options")', self.source)
        self.assertIn("_initialise_notes_member(page_frame)", self.source)
        self.assertIn("st.session_state[_NOTES_MEMBER_KEY] = first_label", self.source)

    def test_notes_reset_occurs_only_after_confirmed_publish(self):
        success_block = self.source.split('if kind == "notes" and text.startswith("Published note "):', 1)[1].split(
            'if kind == "supplement"', 1
        )[0]
        self.assertIn("_advance(kind, scope)", success_block)
        self.assertIn("current_rerun()", success_block)
        self.assertNotIn("_advance(kind, scope)", self.source.split("def form_with_success_version", 1)[1].split("def selectbox_with_stable_context", 1)[0])

    def test_supplement_add_overrides_unsafe_clear_on_submit(self):
        self.assertIn('str(form_key) == "hm_v1023a_add_supplement_form"', self.source)
        self.assertIn('f"hm_v1023a_add_supplement_form_{scope}_{version}"', self.source)
        self.assertIn('kwargs["clear_on_submit"] = False', self.source)
        self.assertIn('with st.form("hm_v1023a_add_supplement_form", clear_on_submit=True)', self.supplement_source)

    def test_explicit_supplement_add_keys_are_success_versioned(self):
        for token in (
            "hm_v1023a_add_frequency_{scope}_{version}",
            "hm_v1023a_add_end_enabled_{scope}_{version}",
            "hm_v1023a_add_end_date_{scope}_{version}",
        ):
            self.assertIn(token, self.source)

    def test_supplement_version_advances_only_after_confirmed_add(self):
        success_block = self.source.split('if kind == "supplement" and text.startswith("Supplement added"):', 1)[1].split(
            "return current_success", 1
        )[0]
        self.assertIn("_advance(kind, scope)", success_block)

    def test_no_database_auth_or_routing_functions_are_replaced(self):
        for forbidden in (
            "components.db",
            "create_structured_nutritionist_note",
            "add_member_supplement",
            "update_member_supplement",
            "stop_member_supplement",
            "require_admin",
            "require_member",
            "st.switch_page",
            "st.login",
            "st.logout",
        ):
            self.assertNotIn(forbidden, self.source)

    def test_no_database_read_or_normal_page_rerun_is_added(self):
        for forbidden in (
            "load_db(",
            "list_members(",
            "get_latest",
            "get_profile",
        ):
            self.assertNotIn(forbidden, self.source)
        self.assertEqual(self.source.count("current_rerun()"), 1)


if __name__ == "__main__":
    unittest.main()
