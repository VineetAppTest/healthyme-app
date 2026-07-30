from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
HYGIENE = ROOT / "components" / "package_hardening_form_hygiene.py"
PAGE = ROOT / "pages" / "41_Admin_Packages.py"


class PackageFormHygieneContractTest(unittest.TestCase):
    def test_changed_python_files_compile(self):
        for path in (HYGIENE, PAGE):
            compile(path.read_text(encoding="utf-8"), str(path), "exec")

    def test_three_transaction_forms_receive_versioned_identities(self):
        source = HYGIENE.read_text(encoding="utf-8")
        for form_prefix in (
            "hm_pkg_library_form_",
            "hm_pkg_assign_form_",
            "hm_pkg_action_form_",
        ):
            self.assertIn(form_prefix, source)
        for version_key in (
            "hm_pkg_hygiene_library_version",
            "hm_pkg_hygiene_assign_version",
            "hm_pkg_hygiene_action_version",
        ):
            self.assertIn(version_key, source)
        self.assertIn("_versioned_package_forms", source)
        self.assertIn("finally:\n        st.form = original_form", source)

    def test_cleanup_is_success_only(self):
        source = HYGIENE.read_text(encoding="utf-8")
        self.assertIn("if _write_succeeded(result):", source)
        self.assertIn('bool(result.get("assigned"))', source)
        self.assertNotIn("except Exception", source)
        self.assertNotIn("finally:", source.split("def install_package_form_hygiene", 1)[1])

    def test_member_package_and_subscription_context_is_not_cleared(self):
        source = HYGIENE.read_text(encoding="utf-8")
        for context_key in (
            "hm_pkg_assign_member",
            "hm_pkg_assign_package",
            "hm_pkg_current_selected",
            "hm_pkg_current_action",
            "hm_package_hardening_section",
        ):
            self.assertNotIn(f'pop("{context_key}"', source)
            self.assertNotIn(f"pop('{context_key}'", source)
        self.assertIn("hm_pkg_library_inclusion_", source)

    def test_hygiene_wraps_existing_package_renderers_without_writes(self):
        source = HYGIENE.read_text(encoding="utf-8")
        for renderer in (
            "_render_package_library",
            "_render_assign_replace",
            "_render_subscription_management",
        ):
            self.assertIn(renderer, source)
        for forbidden in (
            ".table(",
            ".rpc(",
            ".insert(",
            ".update(",
            ".delete(",
            ".upsert(",
            "authorization_id",
            "require_admin",
            "require_member",
        ):
            self.assertNotIn(forbidden, source)

    def test_installer_runs_after_existing_package_wrappers(self):
        source = PAGE.read_text(encoding="utf-8")
        performance = source.index("install_admin_packages_performance")
        formula = source.index("install_package_value_formula(package_hardening_ui)")
        hygiene = source.index("install_package_form_hygiene(package_hardening_ui)")
        render = source.index("package_hardening_ui.render_package_hardening_admin_page()")
        self.assertLess(performance, formula)
        self.assertLess(formula, hygiene)
        self.assertLess(hygiene, render)


if __name__ == "__main__":
    unittest.main()
