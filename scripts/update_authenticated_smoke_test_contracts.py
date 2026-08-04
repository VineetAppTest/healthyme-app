from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def write(path: str, text: str) -> None:
    (ROOT / path).write_text(text, encoding="utf-8")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one match, found {count}")
    return text.replace(old, new, 1)


# Streamlit UI consistency now validates the authenticated-smoke target layouts.
path = "tests/test_streamlit_ui_consistency_batch.py"
text = read(path)
start = text.index("    def test_food_journal_keeps_exact_five_part_row")
end = text.index("    def test_food_autosave_uses_direct_payload_boundary", start)
new_test = '''    def test_food_journal_uses_two_row_time_and_food_structure(self):
        source = (ROOT / "pages/18_Daily_Log.py").read_text()
        self.assertIn("hm-meal-time-grid-anchor", source)
        self.assertIn("hm-meal-food-grid-anchor", source)
        render_start = source.index("def _render_meal_fields")
        render_end = source.index("def _render_meal_toggle", render_start)
        renderer = source[render_start:render_end]
        self.assertIn("time_cols = st.columns([1, 1, 1.15, 3]", renderer)
        self.assertIn("food_col, portion_col = st.columns([2.2, 1.25]", renderer)
        self.assertIn('"Hour"', renderer)
        self.assertIn('"Minutes"', renderer)
        self.assertIn('"AM/PM"', renderer)
        self.assertIn('f"Food Item {idx + 1}"', renderer)
        self.assertIn('f"Portion {idx + 1}"', renderer)
        self.assertIn("hm_daily_log_add_food_item_", renderer)

'''
text = text[:start] + new_test + text[end:]
start = text.index("    def test_repository_controls_are_sharp_aligned_and_untruncated")
end = text.index("    def test_profile_builder_disclosures_share_full_label_contract", start)
new_test = '''    def test_repository_controls_are_sharp_aligned_and_untruncated(self):
        runtime = (ROOT / "components/repository_layout_correction_runtime.py").read_text()
        for page_path in (
            "pages/15_Admin_Recipe_Manager.py",
            "pages/16_Admin_Exercise_Manager.py",
            "pages/39_Admin_Supplement_Manager.py",
        ):
            page = (ROOT / page_path).read_text()
            self.assertIn('button[role="tab"][aria-selected="true"]', page)
            self.assertIn('vertical_alignment="center"', page)
            self.assertIn('summary [data-testid="stIconMaterial"]', page)
        self.assertIn("details[open] summary:before", runtime)
        self.assertIn("white-space:normal!important", runtime)
        self.assertIn("text-overflow:clip!important", runtime)

'''
text = text[:start] + new_test + text[end:]
start = text.index("    def test_member_plan_meals_use_native_dataframe_format")
end = text.index("\n\n\nif __name__", start)
new_test = '''    def test_member_plan_uses_consistent_weekly_tables(self):
        source = (ROOT / "components/member_plan_builder_view_compact.py").read_text()
        self.assertIn("def _render_weekly_table", source)
        self.assertIn('"Start Date"', source)
        self.assertIn('"Type"', source)
        self.assertIn('"Day"', source)
        self.assertIn('("Timing", "Meal", "Liquid", "Remarks")', source)
        self.assertIn('("Timing", "Activity", "Duration/Sets", "Remarks")', source)
        self.assertIn('("Timing", "Supplement", "Dosage", "Remarks")', source)
        self.assertNotIn("Active-plan integrity verified", source)

'''
text = text[:start] + new_test + text[end:]
write(path, text)

# Food Journal focused contract now validates the requested two-row composition.
path = "tests/test_food_journal_meal_grid_saved_days_cleanup.py"
text = read(path)
start = text.index("    def test_meal_entry_uses_five_part_inline_grid")
end = text.index("    def test_meal_disclosure_text_is_left_aligned", start)
new_test = '''    def test_meal_entry_uses_two_row_time_and_food_grid(self):
        source = (ROOT / "pages/18_Daily_Log.py").read_text()
        start = source.index("def _render_meal_fields")
        end = source.index("def _render_meal_toggle", start)
        block = source[start:end]
        self.assertIn("time_cols = st.columns([1, 1, 1.15, 3]", block)
        self.assertIn("food_col, portion_col = st.columns([2.2, 1.25]", block)
        self.assertIn('"Hour"', block)
        self.assertIn('"Minutes"', block)
        self.assertIn('"AM/PM"', block)
        self.assertIn('f"Food Item {idx + 1}"', block)
        self.assertIn('f"Portion {idx + 1}"', block)
        self.assertIn("hm_daily_hour_v13_", block)
        self.assertIn("hm_daily_minute_v13_", block)
        self.assertIn("hm_daily_ampm_v13_", block)
        self.assertIn("hm_daily_log_add_food_item_", block)
        self.assertIn('st.session_state["_hm_h13r9e_pending_rerun_path"] = "Daily_Log"', block)
        self.assertNotIn("st.time_input(", block)

'''
text = text[:start] + new_test + text[end:]
write(path, text)

# Header runtime contract now enforces the structural-shell implementation.
path = "tests/test_member_home_global_header_runtime.py"
text = read(path)
start = text.index("    def test_member_home_controls_root_header_sequence_and_mobile_row")
end = text.index("    def test_other_pages_keep_their_existing_header_sequence", start)
new_test = '''    def test_member_home_controls_root_header_sequence_and_mobile_row(self):
        calls = []

        def base_topbar(title, *args, **kwargs):
            calls.append(title)

        ui_common.topbar = base_topbar
        runtime.install_member_home_global_header_runtime()
        ui_common.topbar("Member Home", "Member subtitle", "Member experience")
        self.assertEqual(calls, ["Member Home"])
        rendered_css = "\\n".join(self.fake_st.markdown_calls)
        self.assertIn("hm-member-home-global-header-v6", rendered_css)
        self.assertIn("hm-member-identity-pill", rendered_css)
        self.assertIn("hm-top-profile-anchor", rendered_css)
        self.assertIn("hm-top-logout-anchor", rendered_css)
        self.assertIn("@media(max-width:760px)", rendered_css)
        self.assertIn("grid-template-columns:minmax(0,1fr) 2.55rem 4.65rem!important", rendered_css)
        self.assertIn("text-overflow:ellipsis!important", rendered_css)
        self.assertNotIn("padding-top:.12rem!important", rendered_css)
        self.assertNotIn("margin-top:-", rendered_css)

'''
text = text[:start] + new_test + text[end:]
write(path, text)

# Member Home page contract now checks the structural shell, not global zero padding.
path = "tests/test_member_home_schedule_presentation.py"
text = read(path)
start = text.index("    def test_member_home_header_renders_before_slow_workflow_reads")
end = text.index("    def test_installer_and_export_discovery_are_active", start)
new_test = '''    def test_member_home_header_renders_before_slow_workflow_reads(self):
        source = (ROOT / "pages/02_Member_Home.py").read_text()
        self.assertIn("hm-member-home-local-style-v3", source)
        self.assertIn("hm-member-home-root-anchor", source)
        self.assertIn("# Render one structural header shell", source)
        self.assertNotIn("html,body,#root{margin-top:0", source)
        render_start = source.index("# Render one structural header shell")
        workflow_read = source.index("get_workflow(user_id)")
        self.assertLess(render_start, workflow_read)
        self.assertLess(source.index("_render_member_home_css()", render_start), workflow_read)
        self.assertLess(source.index("_render_member_utility_bar()", render_start), workflow_read)
        self.assertLess(source.index('topbar(\n        "Member Home"', render_start), workflow_read)
        self.assertEqual(source.count("_render_member_home_css()"), 1)
        self.assertEqual(source.count("_render_member_utility_bar()"), 1)

'''
text = text[:start] + new_test + text[end:]
write(path, text)

print("Authenticated smoke test contracts updated.")
