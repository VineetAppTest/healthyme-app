from __future__ import annotations

from pathlib import Path


ROOT = Path('.')


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one match, found {count}")
    return text.replace(old, new, 1)


# Retire the legacy side-by-side relocation while preserving task-state helpers.
path = ROOT / 'components/member_home_side_by_side_runtime.py'
text = path.read_text()
text = replace_once(
    text,
    '_MARKER = "_hm_member_home_side_by_side_runtime_v5"',
    '_MARKER = "_hm_member_home_side_by_side_runtime_v6"',
    'side-by-side marker',
)
start = text.index('def install_member_home_side_by_side_runtime() -> None:\n')
new_installer = '''def install_member_home_side_by_side_runtime() -> None:
    """Keep task-state presentation helpers without relocating page sections.

    Upcoming Schedule and Messages are now owned directly by Member Home. The
    retired runtime used to move them into a dynamically created two-column row,
    which also introduced negative margins and made the global header regress
    whenever one of those sections appeared or disappeared.
    """

    current_markdown = st.markdown
    current_button = st.button
    if getattr(current_markdown, _MARKER, False):
        return

    @functools.wraps(current_markdown)
    def markdown_with_task_state(body, *args, **kwargs):
        if (
            _member_home_stack_has("_render_task_progress")
            and isinstance(body, str)
            and "hm-v990-task-progress" in body
        ):
            state_class = _task_due_state_class()
            body = body.replace(
                "hm-v990-task-progress",
                f"hm-v990-task-progress {state_class}",
                1,
            )
        return current_markdown(body, *args, **kwargs)

    @functools.wraps(current_button)
    def button_with_completed_task_labels(label, *args, **kwargs):
        completed_label = _completed_task_button_label(label)
        if completed_label is not None:
            label = completed_label
            kwargs = dict(kwargs)
            kwargs["disabled"] = True
        return current_button(label, *args, **kwargs)

    setattr(markdown_with_task_state, _MARKER, True)
    setattr(button_with_completed_task_labels, _MARKER, True)
    st.markdown = markdown_with_task_state
    st.button = button_with_completed_task_labels
'''
text = text[:start] + new_installer
path.write_text(text)


# Member Home: stable header, page-owned schedule grid, readable task card and message cleanup.
path = ROOT / 'pages/02_Member_Home.py'
text = path.read_text()
text = replace_once(
    text,
    '''def _esc(value):
    return html.escape(str(value or ""))
''',
    '''def _esc(value):
    return html.escape(str(value or ""))


def _member_message_text(value):
    """Remove only the redundant allocation sentence from Member Home."""

    return str(value or "").replace("Nutritionist has allocated a Task.", "").strip()
''',
    'member message helper',
)
text = replace_once(
    text,
    "div[data-testid=\"stAppViewContainer\"] .block-container:has(.hm-member-home-root-anchor){padding-top:.55rem!important;padding-block-start:.55rem!important;margin-top:0!important;}",
    "div[data-testid=\"stAppViewContainer\"] .block-container:has(.hm-member-home-root-anchor){padding-top:.18rem!important;padding-block-start:.18rem!important;margin-top:0!important;}",
    'member home top spacing',
)
text = replace_once(
    text,
    "div[data-testid=\"stVerticalBlock\"]:has(.hm-member-home-root-anchor) .hero-shell{margin-top:0!important;}",
    """div[data-testid=\"stVerticalBlock\"]:has(.hm-member-home-root-anchor) .hero-shell{margin-top:0!important;}
div[data-testid=\"stHorizontalBlock\"]:has(.hm-member-home-balanced-card){align-items:stretch!important;}
div[data-testid=\"stHorizontalBlock\"]:has(.hm-member-home-balanced-card)>div[data-testid=\"column\"]{display:flex!important;align-self:stretch!important;}
div[data-testid=\"stHorizontalBlock\"]:has(.hm-member-home-balanced-card)>div[data-testid=\"column\"]>div[data-testid=\"stVerticalBlock\"]{width:100%!important;height:100%!important;}
div[data-testid=\"stVerticalBlockBorderWrapper\"]:has(.hm-member-home-balanced-card){height:100%!important;min-height:100%!important;}""",
    'balanced member columns',
)
text = replace_once(
    text,
    ".hm-v990-task-progress{border:1px solid #E5D2A9;background:#FFFDF8;border-radius:14px;padding:.62rem .72rem;margin:.52rem 0 .62rem 0;}",
    ".hm-v990-task-progress{border:1px solid #E5D2A9;background:#FFFDF8;border-radius:14px;padding:.82rem .86rem .88rem;margin:.58rem 0 .72rem 0;min-height:15.75rem;box-sizing:border-box;}",
    'task card breathing space',
)
text = replace_once(
    text,
    "f\"<div class='hm-home-section-head'><div>Messages from Nutritionist</div><span>{len(unique_messages)} recent</span></div>\"",
    "f\"<div class='hm-home-section-head'><div>Messages from Nutritionist</div><span>{len(unique_messages)} recent</span></div>\"",
    'messages heading anchor',
)
text = replace_once(
    text,
    "<p class='hm-b13-message-body'>{_esc(msg.get('message',''))}</p>",
    "<p class='hm-b13-message-body'>{_esc(_member_message_text(msg.get('message','')))}</p>",
    'member message cleanup render',
)
text = replace_once(
    text,
    '''    with st.expander(
        f"Upcoming Schedule · {len(upcoming_schedules)} upcoming",
        expanded=True,
    ):
''',
    '''    with st.expander(
        f"Upcoming Schedule ({len(upcoming_schedules)})",
        expanded=True,
    ):
''',
    'upcoming schedule title',
)
text = replace_once(
    text,
    '''        for row_start in range(0, len(upcoming_schedules), 3):
            cols = st.columns(3, gap="small")
            for col, schedule in zip(cols, upcoming_schedules[row_start : row_start + 3]):
''',
    '''        for row_start in range(0, len(upcoming_schedules), 2):
            cols = st.columns(2, gap="medium")
            for col, schedule in zip(cols, upcoming_schedules[row_start : row_start + 2]):
''',
    'upcoming schedule two-card grid',
)
if 'SHOW_MEMBER_REFERENCE_LIBRARY = False' not in text:
    raise RuntimeError('Reference Library must remain hidden on Member Home')
if "Due date: <b>&nbsp;{due_date}</b>" not in text:
    raise RuntimeError('Due date must remain inside Task Progress')
path.write_text(text)


# Schedule presentation: remove residual mobile offset and keep full action labels.
path = ROOT / 'components/member_home_schedule_presentation.py'
text = path.read_text()
text = text.replace('_MARKDOWN_PATCH_MARKER = "_hm_member_home_compact_polish_v6"', '_MARKDOWN_PATCH_MARKER = "_hm_member_home_compact_polish_v7"')
text = text.replace('hm-member-home-compact-polish-v6', 'hm-member-home-compact-polish-v7')
text = replace_once(
    text,
    '''  min-height:2.18rem!important;height:2.18rem!important;
  padding:.30rem .55rem!important;border-radius:10px!important;
  font-size:.66rem!important;font-weight:900!important;
''',
    '''  min-height:2.34rem!important;height:auto!important;
  padding:.34rem .48rem!important;border-radius:10px!important;
  font-size:.72rem!important;font-weight:900!important;
  white-space:normal!important;overflow:visible!important;text-overflow:clip!important;
''',
    'schedule action readability',
)
text = replace_once(
    text,
    '''@media(max-width:640px){
  div[data-testid="stHorizontalBlock"]:has(.hm-member-identity-pill){
    top:-1.75rem!important;margin-bottom:-1.30rem!important;
  }
''',
    '''@media(max-width:640px){
''',
    'remove mobile header offset',
)
text = replace_once(
    text,
    '''@media(max-width:900px){
  .hm-v101-schedule-card,
''',
    '''.hm-member-schedule-action-anchor + div[data-testid="stHorizontalBlock"] button p{
  white-space:normal!important;overflow:visible!important;text-overflow:clip!important;
  font-size:.72rem!important;line-height:1.14!important;
}
@media(max-width:900px){
  .hm-v101-schedule-card,
''',
    'schedule action text rule',
)
path.write_text(text)


# Route preservation must cover native time controls as well as food-row controls.
path = ROOT / 'components/daily_log_widget_route_preservation.py'
text = path.read_text()
text = text.replace('_INSTALL_MARKER = "_hm_daily_log_widget_route_preservation_v1"', '_INSTALL_MARKER = "_hm_daily_log_widget_route_preservation_v2"')
text = replace_once(
    text,
    '''_DAILY_LOG_KEY_PREFIXES = (
    "hm_daily_log_",
    "hm_h9a4c_",
    "hm_food_journal_",
)
''',
    '''_DAILY_LOG_KEY_PREFIXES = (
    "hm_daily_log_",
    "hm_daily_",
    "hm_h9a4c_",
    "hm_food_journal_",
)
''',
    'Daily Log route prefixes',
)
path.write_text(text)


# Food Journal: keep two rows, prefix every editable field, remove load-mode note and button.
path = ROOT / 'pages/18_Daily_Log.py'
text = path.read_text()
text = text.replace(
    'key=f"{date_key}_{key}_food_{idx}"',
    'key=f"hm_daily_log_{date_key}_{key}_food_{idx}"',
)
text = text.replace(
    'key=f"{date_key}_{key}_portion_{idx}"',
    'key=f"hm_daily_log_{date_key}_{key}_portion_{idx}"',
)
text = text.replace(
    'key=f"{date_key}_{key}_mood"',
    'key=f"hm_daily_log_{date_key}_{key}_mood"',
)
text = text.replace(
    'key=f"{date_key}_{key}_energy"',
    'key=f"hm_daily_log_{date_key}_{key}_energy"',
)
text = replace_once(
    text,
    '    is_saved_date = bool(existing and _day_has_meaningful_entry(existing))\n\n',
    '',
    'remove saved-date mode flag',
)
text = replace_once(
    text,
    '''        if is_saved_date:
            st.markdown(
                f"<div class='hm-h9a4c-note'>Viewing saved entries for {log_date.strftime('%d %b')}. Open a section only if you want to edit it.</div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                "<div class='hm-h9a4c-note'>Open only the meal you want to update.</div>",
                unsafe_allow_html=True,
            )

''',
    '',
    'remove saved-entry guidance message',
)
text = replace_once(
    text,
    '                label_date = _parse_date(date_text)\n',
    '',
    'remove saved-day load date',
)
button_block = '''                        if st.button(
                            "Open saved day",
                            key=(
                                f"hm_h9a4c_load_{date_text}_"
                                f"{row_start}_{column_index}"
                            ),
                            use_container_width=True,
                        ):
                            if label_date:
                                st.session_state["hm_food_journal_date"] = label_date
                                st.rerun()
'''
text = replace_once(text, button_block, '', 'remove Open saved day button')
path.write_text(text)


# Update the existing saved-days contract and add focused follow-up tests.
path = ROOT / 'tests/test_food_journal_meal_grid_saved_days_cleanup.py'
text = path.read_text()
text = replace_once(
    text,
    '        self.assertIn(\'"Open saved day"\', page)\n',
    '        self.assertNotIn(\'"Open saved day"\', page)\n        self.assertNotIn("Viewing saved entries for", page)\n',
    'saved-days test expectation',
)
path.write_text(text)

path = ROOT / 'tests/test_authenticated_member_followup_corrections.py'
path.write_text('''from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class AuthenticatedMemberFollowupCorrectionTests(unittest.TestCase):
    def test_member_home_owns_schedule_and_message_layout(self):
        source = (ROOT / "components/member_home_side_by_side_runtime.py").read_text()
        installer = source[source.index("def install_member_home_side_by_side_runtime"):]
        self.assertIn("without relocating page sections", installer)
        self.assertNotIn("ensure_pair()", installer)
        self.assertNotIn("left.expander", installer)
        self.assertNotIn("message_expander", installer)
        self.assertNotIn("margin:-", installer)

    def test_header_has_no_negative_offset_and_schedule_is_two_across(self):
        page = (ROOT / "pages/02_Member_Home.py").read_text()
        presentation = (ROOT / "components/member_home_schedule_presentation.py").read_text()
        self.assertIn('padding-top:.18rem!important', page)
        self.assertIn('f"Upcoming Schedule ({len(upcoming_schedules)})"', page)
        self.assertIn('range(0, len(upcoming_schedules), 2)', page)
        self.assertIn('st.columns(2, gap="medium")', page)
        self.assertNotIn('top:-1.75rem', presentation)
        self.assertIn('font-size:.72rem!important', presentation)

    def test_task_card_and_balanced_columns_have_breathing_space(self):
        page = (ROOT / "pages/02_Member_Home.py").read_text()
        self.assertIn('min-height:15.75rem', page)
        self.assertIn(':has(.hm-member-home-balanced-card){align-items:stretch', page)
        self.assertIn('Due date: <b>&nbsp;{due_date}</b>', page)
        self.assertIn('SHOW_MEMBER_REFERENCE_LIBRARY = False', page)

    def test_task_allocation_sentence_is_removed_only_from_member_message_body(self):
        page = (ROOT / "pages/02_Member_Home.py").read_text()
        self.assertIn('replace("Nutritionist has allocated a Task.", "")', page)
        self.assertIn("_member_message_text(msg.get('message',''))", page)

    def test_food_journal_route_and_saved_day_contract(self):
        page = (ROOT / "pages/18_Daily_Log.py").read_text()
        route = (ROOT / "components/daily_log_widget_route_preservation.py").read_text()
        self.assertIn('"hm_daily_",', route)
        self.assertIn('key=f"hm_daily_log_{date_key}_{key}_food_{idx}"', page)
        self.assertIn('key=f"hm_daily_log_{date_key}_{key}_portion_{idx}"', page)
        self.assertIn('key=f"hm_daily_log_{date_key}_{key}_mood"', page)
        self.assertIn('key=f"hm_daily_log_{date_key}_{key}_energy"', page)
        self.assertNotIn('Viewing saved entries for', page)
        self.assertNotIn('"Open saved day"', page)
        self.assertNotIn('hm_h9a4c_load_', page)


if __name__ == "__main__":
    unittest.main()
''')
