import components.package_hardening_ui as package_hardening_ui
from components.package_value_formula_ui import install_package_value_formula
from components.performance_diagnostics import (
    begin_page_measurement,
    finish_and_render_page_diagnostics,
)


begin_page_measurement("Admin Packages")
install_package_value_formula(package_hardening_ui)
package_hardening_ui.render_package_hardening_admin_page()
finish_and_render_page_diagnostics("Admin Packages")
