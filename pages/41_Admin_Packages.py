import components.package_hardening_ui as package_hardening_ui
from components.admin_performance_optimization import (
    install_admin_packages_performance,
)
from components.admin_uiux_corrections import render_admin_packages_uiux_styles
from components.package_hardening_form_hygiene import install_package_form_hygiene
from components.package_value_formula_ui import install_package_value_formula
from components.performance_diagnostics import (
    begin_page_measurement,
    finish_and_render_page_diagnostics,
)


begin_page_measurement("Admin Packages")
render_admin_packages_uiux_styles()
install_admin_packages_performance(package_hardening_ui)
install_package_value_formula(package_hardening_ui)
# Install form hygiene last so it wraps the accepted performance and value-formula
# renderers without replacing their business behaviour.
install_package_form_hygiene(package_hardening_ui)
package_hardening_ui.render_package_hardening_admin_page()
finish_and_render_page_diagnostics("Admin Packages")
