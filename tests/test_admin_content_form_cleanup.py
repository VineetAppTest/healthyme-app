from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "components" / "admin_content_form_cleanup.py"
INIT = ROOT / "components" / "__init__.py"
RECIPE = ROOT / "pages" / "15_Admin_Recipe_Manager.py"
EXERCISE = ROOT / "pages" / "16_Admin_Exercise_Manager.py"
SUPPLEMENT = ROOT / "pages" / "39_Admin_Supplement_Manager.py"
INVENTORY = ROOT / "docs" / "form_success_reset_inventory.md"


def test_component_compiles_and_precedes_final_member_wrappers():
    compile(COMPONENT.read_text(encoding="utf-8"), str(COMPONENT), "exec")
    source = INIT.read_text(encoding="utf-8")
    assert "install_admin_content_form_cleanup" in source
    assert source.index("install_admin_content_form_cleanup()") < source.index(
        "install_member_saved_days_home_cleanup()"
    )
    assert source.index("install_member_saved_days_home_cleanup()") < source.index(
        "install_member_home_side_by_side_runtime()"
    )
    assert source.index("install_member_home_side_by_side_runtime()") < source.index(
        "install_member_saved_days_dispatch_runtime()"
    )
    assert source.rstrip().endswith("install_member_saved_days_dispatch_runtime()")


def test_recipe_and_exercise_show_only_four_stable_sections():
    source = COMPONENT.read_text(encoding="utf-8")
    assert '"visible": ("Current Repository", "Add Recipe", "Import CSV", "Edit / Delete")' in source
    assert '"visible": ("Current Repository", "Add Exercise", "Import CSV", "Edit / Delete")' in source
    assert "Member Feedback" in source
    assert "Allocate to Member" in source
    assert "zip(columns, visible)" in source


def test_inactive_sections_do_not_render_widgets_or_context_containers():
    source = COMPONENT.read_text(encoding="utf-8")
    assert "_INACTIVE_DEPTH" in source
    assert "if _inactive():" in source
    assert "return [contextlib.nullcontext() for _ in range(count)]" in source
    assert "return contextlib.nullcontext()" in source
    assert "st.container(border=True)" not in source
    assert "hm-admin-content-section-inactive" not in source


def test_legacy_feedback_and_allocation_are_retained_but_never_active():
    recipe = RECIPE.read_text(encoding="utf-8")
    exercise = EXERCISE.read_text(encoding="utf-8")
    assert '"Member Feedback", "Allocate to Member"' in recipe
    assert '"Member Feedback", "Allocate to Member"' in exercise
    source = COMPONENT.read_text(encoding="utf-8")
    assert "active=(label == selected and label in visible)" in source


def test_recipe_edit_is_in_place_not_append():
    source = RECIPE.read_text(encoding="utf-8")
    edit = source.split("with tabs[3]:", 1)[1].split("with tabs[4]:", 1)[0]
    assert 'df.at[idx, c] = edited.get(c, "")' in edit
    assert "df.loc[len(df)]" not in edit


def test_exercise_edit_is_in_place_not_append():
    source = EXERCISE.read_text(encoding="utf-8")
    edit = source.split("with tabs[3]:", 1)[1].split("with tabs[4]:", 1)[0]
    assert 'df.at[idx, c] = edited.get(c, "")' in edit
    assert "df.loc[len(df)]" not in edit


def test_footer_navigation_remains_in_both_admin_pages():
    for page in (RECIPE, EXERCISE):
        source = page.read_text(encoding="utf-8")
        assert "render_page_nav(" in source
        assert "render_back_to_top()" in source


def test_success_reset_is_staged_before_next_widget_render():
    source = COMPONENT.read_text(encoding="utf-8")
    assert "_PENDING_RESET_PREFIXES" in source
    assert "_stage_reset(prefixes)" in source
    assert "_apply_staged_reset()" in source
    assert "for key in list(st.session_state.keys())" in source


def test_content_success_messages_persist_across_rerun():
    source = COMPONENT.read_text(encoding="utf-8")
    for message in (
        "Recipe saved.",
        "Recipe updated.",
        "Exercise saved.",
        "Exercise updated.",
        "Supplement added",
        "Supplement updated",
        "Supplement stopped",
    ):
        assert message in source
    assert "_PENDING_MESSAGE" in source
    assert "_pop_success" in source


def test_supplement_write_contract_remains_update_not_append():
    source = SUPPLEMENT.read_text(encoding="utf-8")
    assert 'update_member_supplement(row["id"]' in source
    assert 'with st.form("hm_v1023a_add_supplement_form", clear_on_submit=True)' in source


def test_form_inventory_covers_admin_practitioner_and_member_workflows():
    inventory = INVENTORY.read_text(encoding="utf-8")
    assert "## Admin / practitioner forms" in inventory
    assert "## Member forms" in inventory
    for workflow in (
        "Recipe manager",
        "Exercise manager",
        "Supplement manager",
        "Recommendation Profile Builder",
        "Scheduling",
        "Food Journal",
        "Exercise Journal",
        "My Schedule",
    ):
        assert workflow in inventory


def test_no_auth_or_database_contract_changes_in_cleanup_component():
    source = COMPONENT.read_text(encoding="utf-8")
    for forbidden in (
        "require_admin",
        "require_member",
        "logout_current_user",
        "save_resource_assignments",
        "update_member_supplement(",
        "add_member_supplement(",
        "st.switch_page",
    ):
        assert forbidden not in source
