from pathlib import Path
import py_compile
import unittest


ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "components" / "auth_provisioning_form_hygiene.py"
INIT = ROOT / "components" / "__init__.py"
PAGE = ROOT / "pages" / "34_Admin_Supabase_Auth_Provisioning_Workbench.py"
LIFECYCLE = ROOT / "components" / "supabase_auth_lifecycle_h10.py"
PROVISIONING = ROOT / "components" / "supabase_provisioning_h6.py"


class AuthProvisioningFormHygieneTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = COMPONENT.read_text(encoding="utf-8")
        cls.init_source = INIT.read_text(encoding="utf-8")
        cls.page_source = PAGE.read_text(encoding="utf-8")

    def test_changed_runtime_and_unchanged_auth_sources_compile(self):
        for path in (COMPONENT, INIT, PAGE, LIFECYCLE, PROVISIONING):
            py_compile.compile(str(path), doraise=True)

    def test_installer_runs_after_existing_admin_hygiene_layers(self):
        self.assertIn("install_auth_provisioning_form_hygiene", self.init_source)
        self.assertLess(
            self.init_source.index("install_notes_supplement_form_hygiene()"),
            self.init_source.index("install_auth_provisioning_form_hygiene()"),
        )
        self.assertLess(
            self.init_source.index("install_auth_provisioning_form_hygiene()"),
            self.init_source.index("install_member_saved_days_home_cleanup()"),
        )

    def test_only_the_three_existing_workbench_forms_are_versioned(self):
        for form_key in (
            "hm_h10_password_reset_form",
            "hm_h6_single_supabase_provisioning_form",
            "hm_h6_batch_supabase_provisioning_form",
        ):
            self.assertIn(form_key, self.source)
            self.assertIn(f'with st.form("{form_key}")', self.page_source)
        self.assertIn('f"{form_key}_{_version(scope)}"', self.source)
        self.assertIn('pages/34_Admin_Supabase_Auth_Provisioning_Workbench.py', self.source)

    def test_dry_runs_never_advance_form_identity(self):
        self.assertIn("if dry_run:", self.source)
        self.assertIn("return False", self.source)
        reset_block = self.source.split("def reset_with_success_hygiene", 1)[1].split(
            "def single_with_success_hygiene", 1
        )[0]
        self.assertIn('not dry_run', reset_block)
        single_block = self.source.split("def single_with_success_hygiene", 1)[1].split(
            "def batch_with_success_hygiene", 1
        )[0]
        self.assertIn("_single_completed(result, dry_run=dry_run)", single_block)
        batch_block = self.source.split("def batch_with_success_hygiene", 1)[1].split(
            "for wrapped in", 1
        )[0]
        self.assertIn("_batch_completed(result, dry_run=dry_run)", batch_block)

    def test_password_reset_clears_only_after_confirmed_send(self):
        reset_block = self.source.split("def reset_with_success_hygiene", 1)[1].split(
            "def single_with_success_hygiene", 1
        )[0]
        self.assertIn('== "sent"', reset_block)
        self.assertIn('_stage_completed(', reset_block)
        self.assertIn('return result', reset_block)

    def test_single_live_action_requires_complete_success(self):
        helper = self.source.split("def _single_completed", 1)[1].split(
            "def _batch_completed", 1
        )[0]
        self.assertIn('status == "ok"', helper)
        self.assertIn('reset_status != "failed"', helper)
        self.assertIn('dry_run', helper)

    def test_batch_live_action_is_conservative(self):
        helper = self.source.split("def _batch_completed", 1)[1].split(
            "def _stage_completed", 1
        )[0]
        self.assertIn('"ok" not in statuses', helper)
        self.assertIn('{"failed", "partial", "review", "stopped"}', helper)
        self.assertIn('password_reset_status', helper)
        self.assertIn('== "failed"', helper)

    def test_failed_partial_and_review_results_retain_widget_identity(self):
        self.assertEqual(self.source.count("_advance(scope)"), 1)
        self.assertEqual(self.source.count("st.rerun()"), 1)
        self.assertIn("_stage_completed", self.source)
        self.assertIn("_render_pending(scope)", self.source)
        self.assertIn("st.dataframe(rows", self.source)

    def test_explicit_dry_run_checkboxes_follow_form_version(self):
        for key in ("h10_reset_dry_run", "h6_batch_dry_run"):
            self.assertIn(key, self.source)
            self.assertIn(key, self.page_source)
        self.assertIn('kwargs["key"] = f"{key}_{_version(scope)}"', self.source)

    def test_original_auth_results_are_returned_without_payload_mutation(self):
        for function_name in (
            "reset_with_success_hygiene",
            "single_with_success_hygiene",
            "batch_with_success_hygiene",
        ):
            block = self.source.split(f"def {function_name}", 1)[1]
            self.assertIn("return result", block)
        self.assertNotIn('result["status"] =', self.source)
        self.assertNotIn('result.update(', self.source)

    def test_no_login_routing_database_or_auth_write_is_added(self):
        for forbidden in (
            "st.login",
            "st.logout",
            "st.switch_page",
            "require_admin",
            "require_member",
            "create_auth_user(",
            "link_hm_user_to_auth(",
            "send_password_reset_email(",
            "write_audit(",
            "load_hm_users(",
            "list_auth_users(",
            ".table(",
        ):
            self.assertNotIn(forbidden, self.source)


if __name__ == "__main__":
    unittest.main()
