from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text()


def write(path: str, content: str) -> None:
    (ROOT / path).write_text(content)


def replace_once(path: str, old: str, new: str) -> None:
    content = read(path)
    if content.count(old) != 1:
        raise RuntimeError(f"Expected exactly one replacement target in {path}")
    write(path, content.replace(old, new, 1))


# ---------------------------------------------------------------------------
# Food Journal: keep five controls in one stable row and move food autosave
# away from synthetic Save Day clicks.
# ---------------------------------------------------------------------------
autosave_path = "components/member_journal_server_autosave.py"
autosave = read(autosave_path)
autosave = autosave.replace(
    "from typing import Any\n",
    "from typing import Any, Callable\n",
    1,
)
autosave = autosave.replace(
    '_MARKER = "_hm_member_journal_server_autosave_v2"',
    '_MARKER = "_hm_member_journal_server_autosave_v3"',
    1,
)
food_baseline_block = '''def _food_baseline_key(date_key: str) -> str:
    member_id = str(st.session_state.get("user_id") or "member")
    return f"_hm_food_autosave_baseline_{member_id}_{date_key}"
'''
food_payload_api = '''def _food_baseline_key(date_key: str) -> str:
    member_id = str(st.session_state.get("user_id") or "member")
    return f"_hm_food_autosave_baseline_{member_id}_{date_key}"


def _food_payload_baseline_key(user_id: object, date_key: object) -> str:
    return (
        "_hm_food_payload_autosave_baseline_"
        f"{str(user_id or 'member').strip()}_{str(date_key or '').strip()}"
    )


def mark_food_payload_saved(
    user_id: object,
    date_key: object,
    payload: dict[str, Any],
) -> None:
    """Record the payload committed by the explicit Save Day action."""

    st.session_state[_food_payload_baseline_key(user_id, date_key)] = _signature(
        dict(payload or {})
    )


def autosave_food_payload(
    user_id: object,
    date_key: object,
    payload: dict[str, Any],
    save_func: Callable[[object, object, dict[str, Any]], Any],
    *,
    meaningful: bool,
) -> tuple[bool, str]:
    """Persist a changed Food Journal payload without feedback or rerunning.

    The old runtime made the visible Save Day button appear clicked when widget
    state changed. That reused the manual handler but also moved browser focus.
    This direct boundary hashes the already-built payload, writes only when it
    changes, and never calls ``st.rerun`` or queues a success message.
    """

    current_payload = dict(payload or {})
    signature = _signature(current_payload)
    baseline_key = _food_payload_baseline_key(user_id, date_key)
    baseline = st.session_state.get(baseline_key)
    if baseline is None:
        st.session_state[baseline_key] = signature
        return False, ""
    if signature == baseline:
        return False, ""
    if not meaningful:
        # Preserve the no-empty-day contract while accepting this as the new UI
        # baseline so partial/cleared fields do not repeatedly attempt a save.
        st.session_state[baseline_key] = signature
        return False, ""
    try:
        save_func(user_id, date_key, current_payload)
    except Exception as exc:
        return False, f"Food Journal autosave failed: {exc}"
    st.session_state[baseline_key] = signature
    st.session_state["_hm_last_journal_autosave"] = "food"
    return True, ""
'''
if autosave.count(food_baseline_block) != 1:
    raise RuntimeError("Food autosave baseline insertion point was not found")
autosave = autosave.replace(food_baseline_block, food_payload_api, 1)
old_food_button = '''        if text == _FOOD_BUTTON:
            date_key = _food_date_key()
            if clicked:
                st.session_state[_food_baseline_key(date_key)] = _signature(
                    _food_state(date_key)
                )
                return True
            return _should_autosave_food()
'''
new_food_button = '''        if text == _FOOD_BUTTON:
            # Food autosave is now called directly with the completed payload from
            # Daily Log. Never synthesize a Save Day click from widget changes.
            return clicked
'''
if autosave.count(old_food_button) != 1:
    raise RuntimeError("Synthetic Food Save Day branch was not found")
autosave = autosave.replace(old_food_button, new_food_button, 1)
write(autosave_path, autosave)


daily_path = "pages/18_Daily_Log.py"
daily = read(daily_path)
import_anchor = "from components.member_timezone import member_local_today\n"
import_replacement = '''from components.member_timezone import member_local_today
from components.member_journal_server_autosave import (
    autosave_food_payload,
    mark_food_payload_saved,
)
'''
if daily.count(import_anchor) != 1:
    raise RuntimeError("Daily Log autosave import point was not found")
daily = daily.replace(import_anchor, import_replacement, 1)
old_grid_css = '''        .hm-meal-entry-grid-anchor{display:none!important;height:0!important;min-height:0!important;margin:0!important;padding:0!important;overflow:hidden!important;}
        div[data-testid="stHorizontalBlock"]:has(.hm-meal-entry-grid-anchor){gap:.38rem!important;align-items:flex-end!important;}
        div[data-testid="stHorizontalBlock"]:has(.hm-meal-entry-grid-anchor) label p{font-size:.74rem!important;font-weight:820!important;white-space:nowrap!important;}
        div[data-testid="stHorizontalBlock"]:has(.hm-meal-entry-grid-anchor) [data-baseweb="select"] > div,
        div[data-testid="stHorizontalBlock"]:has(.hm-meal-entry-grid-anchor) input{min-height:2.42rem!important;padding-left:.36rem!important;padding-right:.28rem!important;}
        .hm-meal-grid-spacer{display:block;height:1px;min-height:1px;}
        @media(max-width:900px){
          div[data-testid="stHorizontalBlock"]:has(.hm-meal-entry-grid-anchor){display:grid!important;grid-template-columns:repeat(3,minmax(0,1fr))!important;}
          div[data-testid="stHorizontalBlock"]:has(.hm-meal-entry-grid-anchor)>div:nth-child(4),
          div[data-testid="stHorizontalBlock"]:has(.hm-meal-entry-grid-anchor)>div:nth-child(5){grid-column:span 3!important;}
        }
'''
new_grid_css = '''        .hm-meal-entry-grid-anchor{display:none!important;height:0!important;min-height:0!important;margin:0!important;padding:0!important;overflow:hidden!important;}
        /* Exact desktop contract: Hour | Minutes | AM/PM | Food Item | Portion.
           Override Streamlit's flex widths at the row boundary so global responsive
           column rules cannot shrink or reorder these five controls. */
        div[data-testid="stHorizontalBlock"]:has(.hm-meal-entry-grid-anchor){
          display:grid!important;
          grid-template-columns:minmax(4.75rem,.72fr) minmax(5.10rem,.78fr) minmax(5.55rem,.92fr) minmax(15rem,2.15fr) minmax(9rem,1.35fr)!important;
          gap:.48rem!important;
          align-items:end!important;
          width:100%!important;
          overflow:visible!important;
        }
        div[data-testid="stHorizontalBlock"]:has(.hm-meal-entry-grid-anchor)>div[data-testid="stColumn"],
        div[data-testid="stHorizontalBlock"]:has(.hm-meal-entry-grid-anchor)>div[data-testid="column"]{
          width:100%!important;min-width:0!important;max-width:none!important;
          flex:none!important;align-self:end!important;overflow:visible!important;
        }
        div[data-testid="stHorizontalBlock"]:has(.hm-meal-entry-grid-anchor) label p{
          font-size:.74rem!important;font-weight:820!important;white-space:nowrap!important;
          overflow:visible!important;text-overflow:clip!important;
        }
        div[data-testid="stHorizontalBlock"]:has(.hm-meal-entry-grid-anchor) [data-testid="stSelectbox"],
        div[data-testid="stHorizontalBlock"]:has(.hm-meal-entry-grid-anchor) [data-testid="stTextInput"]{
          width:100%!important;min-width:0!important;margin-bottom:0!important;
        }
        div[data-testid="stHorizontalBlock"]:has(.hm-meal-entry-grid-anchor) [data-baseweb="select"] > div,
        div[data-testid="stHorizontalBlock"]:has(.hm-meal-entry-grid-anchor) input{
          width:100%!important;min-width:0!important;min-height:2.42rem!important;
          padding-left:.42rem!important;padding-right:.34rem!important;
        }
        .hm-meal-grid-spacer{display:block;height:1px;min-height:1px;}
        @media(max-width:780px){
          div[data-testid="stHorizontalBlock"]:has(.hm-meal-entry-grid-anchor){
            grid-template-columns:repeat(6,minmax(0,1fr))!important;
          }
          div[data-testid="stHorizontalBlock"]:has(.hm-meal-entry-grid-anchor)>div:nth-child(1),
          div[data-testid="stHorizontalBlock"]:has(.hm-meal-entry-grid-anchor)>div:nth-child(2),
          div[data-testid="stHorizontalBlock"]:has(.hm-meal-entry-grid-anchor)>div:nth-child(3){grid-column:span 2!important;}
          div[data-testid="stHorizontalBlock"]:has(.hm-meal-entry-grid-anchor)>div:nth-child(4){grid-column:span 4!important;}
          div[data-testid="stHorizontalBlock"]:has(.hm-meal-entry-grid-anchor)>div:nth-child(5){grid-column:span 2!important;}
        }
'''
if daily.count(old_grid_css) != 1:
    raise RuntimeError("Daily Log meal-grid CSS target was not found")
daily = daily.replace(old_grid_css, new_grid_css, 1)
old_manual_save = '''            save_daily_food_journal_day(user_id, date_key, payload)
            set_system_message(
'''
new_manual_save = '''            save_daily_food_journal_day(user_id, date_key, payload)
            mark_food_payload_saved(user_id, date_key, payload)
            set_system_message(
'''
if daily.count(old_manual_save) != 1:
    raise RuntimeError("Daily Log manual save boundary was not found")
daily = daily.replace(old_manual_save, new_manual_save, 1)
old_after_save = '''            st.rerun()

    with st.container(border=True):
        st.markdown("### Full Day Report")
'''
new_after_save = '''            st.rerun()

    _autosaved, _autosave_error = autosave_food_payload(
        user_id,
        date_key,
        payload,
        save_daily_food_journal_day,
        meaningful=_day_has_meaningful_entry(payload),
    )
    if _autosave_error:
        st.error(_autosave_error)

    with st.container(border=True):
        st.markdown("### Full Day Report")
'''
if daily.count(old_after_save) != 1:
    raise RuntimeError("Daily Log direct autosave insertion point was not found")
daily = daily.replace(old_after_save, new_after_save, 1)
write(daily_path, daily)


# Update the existing autosave regression to require direct payload persistence and
# to prohibit synthetic Save Day clicks.
autosave_test_path = "tests/test_member_journal_server_autosave.py"
autosave_test = read(autosave_test_path)
old_food_test = '''    def test_food_autosaves_only_after_meaningful_change(self):
        self.fake_st.session_state["hm_food_journal_date"] = dt.date(2026, 8, 4)
        food_key = "2026-08-04_breakfast_food_0"
        self.fake_st.session_state[food_key] = "Eggs"

        self.assertFalse(self.fake_st.button("Save Day"))
        self.fake_st.session_state[food_key] = "Oats"
        self.assertTrue(self.fake_st.button("Save Day"))
        self.assertEqual(
            self.fake_st.session_state.get("_hm_last_journal_autosave"),
            "food",
        )

        autosave.flash.set_system_message("Saved food journal.", "success")
        self.fake_st.rerun()

        self.assertEqual(self.messages, [])
        self.assertEqual(self.fake_st.rerun_count, 0)
        self.assertFalse(self.fake_st.button("Save Day"))
'''
new_food_test = '''    def test_food_changes_do_not_synthesize_save_day_clicks(self):
        self.fake_st.session_state["hm_food_journal_date"] = dt.date(2026, 8, 4)
        food_key = "2026-08-04_breakfast_food_0"
        self.fake_st.session_state[food_key] = "Eggs"

        self.assertFalse(self.fake_st.button("Save Day"))
        self.fake_st.session_state[food_key] = "Oats"
        self.assertFalse(self.fake_st.button("Save Day"))
        self.assertEqual(self.fake_st.rerun_count, 0)
        self.assertEqual(self.messages, [])

    def test_food_payload_autosaves_directly_without_rerun_or_flash(self):
        saved = []
        payload = {"date": "2026-08-04", "meals": {}}

        did_save, error = autosave.autosave_food_payload(
            "member-1",
            "2026-08-04",
            payload,
            lambda user_id, date_key, row: saved.append((user_id, date_key, row)),
            meaningful=False,
        )
        self.assertFalse(did_save)
        self.assertEqual(error, "")

        changed = {
            "date": "2026-08-04",
            "meals": {"breakfast": {"food_items": [{"food": "Oats"}]}},
        }
        did_save, error = autosave.autosave_food_payload(
            "member-1",
            "2026-08-04",
            changed,
            lambda user_id, date_key, row: saved.append((user_id, date_key, row)),
            meaningful=True,
        )

        self.assertTrue(did_save)
        self.assertEqual(error, "")
        self.assertEqual(len(saved), 1)
        self.assertEqual(saved[0][2], changed)
        self.assertEqual(self.fake_st.rerun_count, 0)
        self.assertEqual(self.messages, [])
'''
if autosave_test.count(old_food_test) != 1:
    raise RuntimeError("Existing Food autosave regression test was not found")
autosave_test = autosave_test.replace(old_food_test, new_food_test, 1)
write(autosave_test_path, autosave_test)


# ---------------------------------------------------------------------------
# Recipe / Exercise / Supplement repositories: sharp segmented selector,
# vertically centred action buttons, and one full-width disclosure contract.
# ---------------------------------------------------------------------------
repo_path = "components/repository_layout_correction_runtime.py"
repo = read(repo_path)
repo = repo.replace(
    '_MARKER = "_hm_repository_layout_correction_v2"',
    '_MARKER = "_hm_repository_layout_correction_v3"',
    1,
)
repo_css_end = repo.index("</style>\n\"\"\"", repo.index("_REPOSITORY_CSS"))
repo_override = r'''

/* v3: current Streamlit DOM + sharper repository controls. */
div[data-testid="stSegmentedControl"] [role="radiogroup"],
div[data-testid="stSegmentedControl"] [data-baseweb="button-group"]{
  border:1px solid #D8A84E!important;border-radius:9px!important;
  overflow:hidden!important;background:#FFFFFF!important;box-shadow:none!important;
}
div[data-testid="stSegmentedControl"] button,
div[data-testid="stSegmentedControl"] label{
  min-height:2.34rem!important;border-radius:0!important;box-shadow:none!important;
  font-weight:850!important;align-items:center!important;justify-content:center!important;
}
div[data-testid="stSegmentedControl"] button:first-child,
div[data-testid="stSegmentedControl"] label:first-child{border-radius:8px 0 0 8px!important;}
div[data-testid="stSegmentedControl"] button:last-child,
div[data-testid="stSegmentedControl"] label:last-child{border-radius:0 8px 8px 0!important;}

div[data-testid="stHorizontalBlock"]:has(.hm-repo-row)>div[data-testid="column"],
div[data-testid="stHorizontalBlock"]:has(.hm-sup-row)>div[data-testid="column"],
div[data-testid="stHorizontalBlock"]:has(.hm-repo-row)>div[data-testid="stColumn"],
div[data-testid="stHorizontalBlock"]:has(.hm-sup-row)>div[data-testid="stColumn"]{
  display:flex!important;align-items:center!important;align-self:stretch!important;
}
div[data-testid="stHorizontalBlock"]:has(.hm-repo-row)>div[data-testid="column"]>div[data-testid="stVerticalBlock"],
div[data-testid="stHorizontalBlock"]:has(.hm-sup-row)>div[data-testid="column"]>div[data-testid="stVerticalBlock"],
div[data-testid="stHorizontalBlock"]:has(.hm-repo-row)>div[data-testid="stColumn"]>div[data-testid="stVerticalBlock"],
div[data-testid="stHorizontalBlock"]:has(.hm-sup-row)>div[data-testid="stColumn"]>div[data-testid="stVerticalBlock"]{
  width:100%!important;height:100%!important;min-height:2.68rem!important;
  display:flex!important;justify-content:center!important;gap:0!important;
}
div[data-testid="stHorizontalBlock"]:has(.hm-repo-row) div[data-testid="stElementContainer"],
div[data-testid="stHorizontalBlock"]:has(.hm-sup-row) div[data-testid="stElementContainer"]{
  margin:0!important;padding:0!important;}
div[data-testid="stHorizontalBlock"]:has(.hm-repo-row) div[data-testid="stButton"]>button,
div[data-testid="stHorizontalBlock"]:has(.hm-sup-row) div[data-testid="stButton"]>button{
  min-height:2.18rem!important;height:2.18rem!important;border-radius:9px!important;
  display:flex!important;align-items:center!important;justify-content:center!important;
}
div[data-testid="stHorizontalBlock"]:has(.hm-repo-row) .hm-repo-row,
div[data-testid="stHorizontalBlock"]:has(.hm-sup-row) .hm-sup-row{
  min-height:2.68rem!important;border-radius:10px!important;}

div[data-testid="stExpander"] details{
  border:1.2px solid #D8A84E!important;border-radius:10px!important;
  background:#FFFDF8!important;overflow:hidden!important;}
div[data-testid="stExpander"] summary{
  min-height:2.42rem!important;padding:.48rem .62rem!important;gap:.48rem!important;
  display:flex!important;align-items:center!important;border-radius:9px!important;}
div[data-testid="stExpander"] summary:before{
  content:"+"!important;display:inline-flex!important;align-items:center!important;
  justify-content:center!important;width:1.34rem!important;height:1.34rem!important;
  border-radius:6px!important;background:#DDF7F3!important;color:#006D6F!important;
  font-size:.82rem!important;font-weight:950!important;line-height:1!important;
  margin:0!important;flex:0 0 1.34rem!important;}
div[data-testid="stExpander"] details[open] summary:before{content:"−"!important;}
div[data-testid="stExpander"] summary p{
  display:block!important;width:100%!important;max-width:none!important;
  margin:0!important;color:#064E3B!important;font-size:.82rem!important;
  font-weight:900!important;line-height:1.2!important;white-space:normal!important;
  overflow:visible!important;text-overflow:clip!important;text-align:left!important;}
'''
repo = repo[:repo_css_end] + repo_override + repo[repo_css_end:]
write(repo_path, repo)


# ---------------------------------------------------------------------------
# Member Plan Builder: use the same disclosure control everywhere and never
# truncate More details labels.
# ---------------------------------------------------------------------------
profile_css_path = "components/profile_builder_modular.py"
profile_css = read(profile_css_path)
old_expander_css = '''div[data-testid="stExpander"]{border-color:#E3C98E!important;border-radius:12px!important;background:#FFFDF8!important}
div[data-testid="stExpander"] details summary{min-height:2.42rem!important;padding:.34rem .58rem!important;display:flex!important;align-items:center!important}
div[data-testid="stExpander"] details summary p{white-space:nowrap!important;overflow:hidden!important;text-overflow:ellipsis!important;color:#064E3B!important;font-size:.80rem!important;font-weight:900!important;line-height:1.2!important;margin:0!important}
div[data-testid="stExpander"] details summary svg{flex:0 0 auto!important}
'''
new_expander_css = '''div[data-testid="stExpander"]{border:0!important;border-radius:10px!important;background:transparent!important}
div[data-testid="stExpander"] details{border:1.2px solid #D8A84E!important;border-radius:10px!important;background:#FFFDF8!important;overflow:hidden!important}
div[data-testid="stExpander"] details summary{list-style:none!important;min-height:2.42rem!important;padding:.42rem .58rem!important;display:flex!important;align-items:center!important;gap:.48rem!important;border-radius:9px!important}
div[data-testid="stExpander"] details summary::-webkit-details-marker{display:none!important}
div[data-testid="stExpander"] details summary::marker{content:""!important;display:none!important}
div[data-testid="stExpander"] details summary:before{content:"+"!important;display:inline-flex!important;align-items:center!important;justify-content:center!important;width:1.34rem!important;height:1.34rem!important;flex:0 0 1.34rem!important;border-radius:6px!important;background:#DDF7F3!important;color:#006D6F!important;font-size:.82rem!important;font-weight:950!important;line-height:1!important}
div[data-testid="stExpander"] details[open] summary:before{content:"−"!important}
div[data-testid="stExpander"] details summary p{display:block!important;width:100%!important;max-width:none!important;white-space:normal!important;overflow:visible!important;text-overflow:clip!important;color:#064E3B!important;font-size:.80rem!important;font-weight:900!important;line-height:1.2!important;margin:0!important;text-align:left!important}
div[data-testid="stExpander"] details summary svg,div[data-testid="stExpander"] details summary [data-testid="stExpanderToggleIcon"]{display:none!important;width:0!important;min-width:0!important}
'''
if profile_css.count(old_expander_css) != 1:
    raise RuntimeError("Profile Builder expander CSS target was not found")
profile_css = profile_css.replace(old_expander_css, new_expander_css, 1)
write(profile_css_path, profile_css)


# ---------------------------------------------------------------------------
# View Member Plan: replace the custom rowspan Meal HTML table with the same
# native dataframe treatment used by Exercise and Supplement allocations.
# ---------------------------------------------------------------------------
view_path = "components/member_plan_builder_view_compact.py"
view = read(view_path)
view = view.replace("import io\n", "import html\nimport io\n", 1)
view = view.replace(
    "    _meal_cells,\n    _render_profile_table,\n    _render_view_profiles_css,\n",
    "    _meal_cells,\n    _render_view_profiles_css,\n",
    1,
)
allocation_end = '''    return output


def _legacy_rows(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
'''
meal_table_helpers = '''    return output


def _plain_table_cell(value: object) -> str:
    return html.unescape(str(value or "").replace("<br>", "\\n"))


def _meal_plan_rows(
    start_date: str,
    items: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for day in range(1, 8):
        timing, meal, liquid, remarks = _meal_cells(items, day)
        rows.append(
            {
                "Start Date": start_date,
                "Type": "Meal",
                "Day": f"Day {day}",
                "Timing": _plain_table_cell(timing),
                "Meal": _plain_table_cell(meal),
                "Liquid": _plain_table_cell(liquid),
                "Remarks": _plain_table_cell(remarks),
            }
        )
    return rows


def _render_meal_plan_table(
    start_date: str,
    items: List[Dict[str, Any]],
) -> None:
    st.dataframe(
        pd.DataFrame(_meal_plan_rows(start_date, items)),
        use_container_width=True,
        hide_index=True,
    )


def _legacy_rows(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
'''
if view.count(allocation_end) != 1:
    raise RuntimeError("Member Plan meal table helper insertion point was not found")
view = view.replace(allocation_end, meal_table_helpers, 1)
old_meal_render = '''    _render_profile_table(
        start_date=clean(profile.get("start_date")),
        section_type="Meal",
        headers=("Timing", "Meal", "Liquid", "Remarks"),
        day_cells=lambda day: _meal_cells(items, day),
    )
'''
new_meal_render = '''    _render_meal_plan_table(
        clean(profile.get("start_date")),
        items,
    )
'''
if view.count(old_meal_render) != 1:
    raise RuntimeError("Custom Member Plan meal table call was not found")
view = view.replace(old_meal_render, new_meal_render, 1)
write(view_path, view)


# ---------------------------------------------------------------------------
# Permanent cross-surface regression suite and workflow.
# ---------------------------------------------------------------------------
test_content = '''from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class StreamlitUiConsistencyBatchTests(unittest.TestCase):
    def test_food_journal_keeps_exact_five_part_row(self):
        source = (ROOT / "pages/18_Daily_Log.py").read_text()
        start = source.index(".hm-meal-entry-grid-anchor")
        end = source.index(".hm-toggle-body:empty", start)
        css = source[start:end]

        self.assertIn(
            "grid-template-columns:minmax(4.75rem,.72fr) minmax(5.10rem,.78fr) minmax(5.55rem,.92fr) minmax(15rem,2.15fr) minmax(9rem,1.35fr)!important",
            css,
        )
        self.assertIn('>div[data-testid="stColumn"]', css)
        self.assertIn('>div[data-testid="column"]', css)
        self.assertIn("@media(max-width:780px)", css)
        render_start = source.index("def _render_meal_fields")
        render_end = source.index("def _render_meal_toggle", render_start)
        renderer = source[render_start:render_end]
        for label in ('"Hour"', '"Minutes"', '"AM/PM"', 'f"Food Item {idx + 1}"', 'f"Portion {idx + 1}"'):
            self.assertIn(label, renderer)

    def test_food_autosave_uses_direct_payload_boundary(self):
        page = (ROOT / "pages/18_Daily_Log.py").read_text()
        runtime = (ROOT / "components/member_journal_server_autosave.py").read_text()

        self.assertIn("autosave_food_payload(", page)
        self.assertIn("mark_food_payload_saved(user_id, date_key, payload)", page)
        self.assertIn("save_func(user_id, date_key, current_payload)", runtime)
        self.assertIn("Never synthesize a Save Day click", runtime)
        food_branch = runtime[runtime.index('if text == _FOOD_BUTTON:'):runtime.index('if text == _EXERCISE_BUTTON')]
        self.assertIn("return clicked", food_branch)
        self.assertNotIn("_should_autosave_food()", food_branch)
        direct_api = runtime[runtime.index("def autosave_food_payload"):runtime.index("def _exercise_baseline_key")]
        self.assertNotIn("st.rerun", direct_api)
        self.assertNotIn("set_system_message", direct_api)

    def test_repository_controls_are_sharp_aligned_and_untruncated(self):
        source = (ROOT / "components/repository_layout_correction_runtime.py").read_text()

        self.assertIn('div[data-testid="stSegmentedControl"]', source)
        self.assertIn("border-radius:9px!important", source)
        self.assertIn('>div[data-testid="stColumn"]', source)
        self.assertIn('>div[data-testid="column"]', source)
        self.assertIn("justify-content:center!important;gap:0!important", source)
        self.assertIn("details[open] summary:before{content:\"−\"!important;}", source)
        self.assertIn("white-space:normal!important", source)
        self.assertIn("text-overflow:clip!important", source)

    def test_profile_builder_disclosures_share_full_label_contract(self):
        source = (ROOT / "components/profile_builder_modular.py").read_text()
        start = source.index('div[data-testid="stExpander"]{')
        end = source.index("@media(max-width:980px)", start)
        css = source[start:end]

        self.assertIn("summary:before{content:\"+\"!important", css)
        self.assertIn("details[open] summary:before{content:\"−\"!important", css)
        self.assertIn("white-space:normal!important", css)
        self.assertIn("overflow:visible!important", css)
        self.assertNotIn("text-overflow:ellipsis", css)

    def test_member_plan_meals_use_native_dataframe_format(self):
        source = (ROOT / "components/member_plan_builder_view_compact.py").read_text()

        self.assertIn("def _meal_plan_rows", source)
        self.assertIn('"Start Date": start_date', source)
        self.assertIn('"Type": "Meal"', source)
        self.assertIn('"Day": f"Day {day}"', source)
        self.assertIn("pd.DataFrame(_meal_plan_rows(start_date, items))", source)
        self.assertIn("use_container_width=True", source)
        self.assertIn("hide_index=True", source)
        render_start = source.index("def render_view_member_plan_compact")
        self.assertNotIn("_render_profile_table(", source[render_start:])


if __name__ == "__main__":
    unittest.main()
'''
write("tests/test_streamlit_ui_consistency_batch.py", test_content)

workflow_content = '''name: Streamlit UI Consistency Batch Validation

on:
  pull_request:
    paths:
      - "components/member_journal_server_autosave.py"
      - "components/repository_layout_correction_runtime.py"
      - "components/profile_builder_modular.py"
      - "components/member_plan_builder_view_compact.py"
      - "pages/18_Daily_Log.py"
      - "tests/test_member_journal_server_autosave.py"
      - "tests/test_streamlit_ui_consistency_batch.py"
      - ".github/workflows/streamlit-ui-consistency-batch-validation.yml"
  workflow_dispatch:

permissions:
  contents: read

jobs:
  validate:
    runs-on: ubuntu-24.04
    steps:
      - name: Check out repository
        uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install project dependencies
        run: python -m pip install -r requirements.txt
      - name: Compile changed surfaces
        run: |
          python -m py_compile \\
            components/member_journal_server_autosave.py \\
            components/repository_layout_correction_runtime.py \\
            components/profile_builder_modular.py \\
            components/member_plan_builder_view_compact.py \\
            pages/18_Daily_Log.py \\
            tests/test_member_journal_server_autosave.py \\
            tests/test_streamlit_ui_consistency_batch.py
      - name: Run focused UI and behavior contracts
        run: |
          python -m unittest \\
            tests.test_member_journal_server_autosave \\
            tests.test_streamlit_ui_consistency_batch \\
            tests.test_food_journal_meal_grid_saved_days_cleanup \\
            tests.test_repository_layout_correction_runtime \\
            tests.test_repository_exclusive_tabs_runtime \\
            tests.test_issue_260_profile_builder_ui_cleanup \\
            -v
'''
write(".github/workflows/streamlit-ui-consistency-batch-validation.yml", workflow_content)
