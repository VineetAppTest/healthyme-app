from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


def replace_block(text: str, start_marker: str, end_marker: str, new_block: str, label: str) -> str:
    start = text.find(start_marker)
    if start < 0:
        raise RuntimeError(f"{label}: start marker not found")
    end = text.find(end_marker, start)
    if end < 0:
        raise RuntimeError(f"{label}: end marker not found")
    return text[:start] + new_block + text[end:]


def patch_member_home() -> None:
    path = ROOT / "pages/02_Member_Home.py"
    text = path.read_text()

    css_anchor = ".hm-upcoming-schedule-anchor{display:none!important;height:0!important;margin:0!important;padding:0!important;}\n.hm-v990-task-progress"
    css_replacement = """.hm-upcoming-schedule-anchor{display:none!important;height:0!important;margin:0!important;padding:0!important;}
.hm-home-section-head{display:flex;align-items:center;justify-content:space-between;gap:.75rem;margin:.42rem 0 .48rem 0;padding:.44rem .12rem .38rem .12rem;color:#064E3B;font-size:1rem;font-weight:950;}
.hm-home-section-head span{display:inline-flex;align-items:center;padding:.14rem .42rem;border:1px solid #D9C28F;border-radius:999px;background:#FFF7E6;color:#7A5A16;font-size:.68rem;font-weight:850;white-space:nowrap;}
.hm-home-section-divider{height:1px;background:linear-gradient(90deg,transparent 0%,#D8A84E 12%,#D8A84E 88%,transparent 100%);margin:.88rem 0 .72rem 0;}
.hm-home-grid-anchor,.hm-message-grid-anchor{display:none!important;height:0!important;min-height:0!important;margin:0!important;padding:0!important;overflow:hidden!important;}
div[data-testid=\"stVerticalBlockBorderWrapper\"]:has(.hm-home-grid-anchor),div[data-testid=\"stVerticalBlockBorderWrapper\"]:has(.hm-message-grid-anchor){height:100%!important;padding:.58rem .64rem .64rem!important;border:1px solid #E3C98E!important;border-radius:14px!important;background:#FFFDF8!important;box-shadow:0 5px 14px rgba(15,23,42,.035)!important;}
div[data-testid=\"stVerticalBlockBorderWrapper\"]:has(.hm-home-grid-anchor) > div,div[data-testid=\"stVerticalBlockBorderWrapper\"]:has(.hm-message-grid-anchor) > div{padding:0!important;gap:.32rem!important;}
.hm-b13-message-card{border:0!important;background:transparent!important;border-radius:0!important;padding:0!important;margin:0!important;min-height:6.65rem;box-shadow:none!important;}
.hm-b13-message-subject{font-size:.88rem!important;font-weight:900!important;margin-bottom:.10rem!important;}
.hm-b13-message-date{font-size:.70rem!important;margin-bottom:.24rem!important;}
.hm-b13-message-body{font-size:.79rem!important;line-height:1.34!important;margin:0!important;}
.hm-v101-schedule-card{border:0!important;background:transparent!important;border-radius:0!important;padding:0!important;margin:0!important;min-height:5.85rem;box-shadow:none!important;}
.hm-v101-schedule-title{font-size:.88rem!important;margin-bottom:.14rem!important;}
.hm-v101-schedule-line{font-size:.76rem!important;line-height:1.28!important;margin:.06rem 0!important;}
.hm-v101-schedule-pill{font-size:.64rem!important;padding:.12rem .34rem!important;}
.hm-v104b11-ack-note{font-size:.72rem!important;line-height:1.34!important;padding:.38rem .46rem!important;margin-top:.34rem!important;}
div[data-testid=\"stVerticalBlockBorderWrapper\"]:has(.hm-message-grid-anchor) button{min-height:2.08rem!important;height:2.08rem!important;padding:.28rem .46rem!important;font-size:.74rem!important;border-radius:9px!important;}
@media(max-width:900px){.hm-home-section-head{font-size:.94rem;}}
.hm-v990-task-progress"""
    text = replace_once(text, css_anchor, css_replacement, "Member Home grid CSS")

    new_functions = '''def _render_messages(user_id, show_divider=False):
    auto_archive_expired_nutritionist_messages(user_id)
    messages = get_member_messages(user_id, limit=6)
    if not messages:
        return False

    unique_messages = []
    seen_msg_keys = set()
    for msg in messages:
        msg_key = (
            f"{msg.get('member_id','')}|{msg.get('log_date','')}|"
            f"{' '.join(str(msg.get('message','')).strip().split()).lower()}"
        )
        if msg_key in seen_msg_keys:
            continue
        seen_msg_keys.add(msg_key)
        unique_messages.append(msg)
        if len(unique_messages) == 6:
            break

    if not unique_messages:
        return False
    if show_divider:
        st.markdown(
            "<div class='hm-home-section-divider'></div>",
            unsafe_allow_html=True,
        )
    st.markdown(
        f"<div class='hm-home-section-head'><div>Messages from Nutritionist</div><span>{len(unique_messages)} recent</span></div>",
        unsafe_allow_html=True,
    )

    for row_start in range(0, len(unique_messages), 3):
        cols = st.columns(3, gap="small")
        for col, msg in zip(cols, unique_messages[row_start : row_start + 3]):
            with col:
                with st.container(border=True):
                    st.markdown(
                        f"""
                        <span class='hm-message-grid-anchor'></span>
                        <div class='hm-b13-message-card'>
                          <div class='hm-b13-message-subject'>{_esc(msg.get('subject','Message'))}</div>
                          <div class='hm-b13-message-date'>{_esc(format_local_ts(msg.get('ts','')))}</div>
                          <p class='hm-b13-message-body'>{_esc(msg.get('message',''))}</p>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    if st.button(
                        "Read & Archive",
                        key=f"read_msg_{msg.get('id','')}",
                        use_container_width=True,
                    ):
                        ok = mark_member_message_read(user_id, msg.get("id", ""))
                        if ok:
                            set_system_message(
                                "Message archived. You can find it in Daily Food Journal → "
                                "Nutritionist Notes Archive.",
                                "success",
                            )
                        else:
                            set_system_message(
                                "Message could not be archived. Please refresh and try again.",
                                "error",
                            )
                        st.rerun()
    return True


def _render_upcoming_schedules(user_id):
    queue_schedule_acknowledgement_reminders_v104b11(user_id)
    upcoming_schedules = list_upcoming_member_schedules(user_id, limit=6)
    if not upcoming_schedules:
        return False

    st.markdown(
        f"<div class='hm-home-section-head'><div>Upcoming Schedule</div><span>{len(upcoming_schedules)} upcoming</span></div>",
        unsafe_allow_html=True,
    )
    for row_start in range(0, len(upcoming_schedules), 3):
        cols = st.columns(3, gap="small")
        for col, schedule in zip(cols, upcoming_schedules[row_start : row_start + 3]):
            with col:
                with st.container(border=True):
                    time_text = str(schedule.get("start_time", "") or "")
                    if schedule.get("end_time"):
                        time_text += f" - {schedule.get('end_time')}"
                    notice = schedule_acknowledgement_notice_v104b11(schedule)
                    notice_html = (
                        "<div class='hm-v101-schedule-line hm-v104b11-ack-note'>"
                        f"{_esc(notice)}</div>"
                        if notice
                        else ""
                    )
                    st.markdown(
                        f"""
                        <span class='hm-home-grid-anchor'></span>
                        <div class='hm-v101-schedule-card'>
                          <div class='hm-v101-schedule-title'>{_esc(schedule.get('title','Scheduled session'))}<span class='hm-v101-schedule-pill'>{_esc(schedule_display_status_label_v104b11(schedule))}</span></div>
                          <div class='hm-v101-schedule-line'>{_esc(schedule.get('schedule_date',''))} · {_esc(time_text)}</div>
                          <div class='hm-v101-schedule-line'>Mode: {_esc(schedule.get('mode','-'))} · Link/location: {_esc(schedule.get('location_or_link') or '-')}</div>
                          {notice_html}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
    return True


'''
    text = replace_block(
        text,
        "def _render_messages(user_id):\n",
        "def _render_task_button(label, key, page, disabled=False):\n",
        new_functions,
        "Member Home schedule/message functions",
    )

    text = replace_once(
        text,
        "_render_messages(user_id)\n_render_upcoming_schedules(user_id)",
        "_has_upcoming_schedule = _render_upcoming_schedules(user_id)\n_render_messages(user_id, show_divider=_has_upcoming_schedule)",
        "Member Home section order",
    )
    path.write_text(text)


def patch_schedule_wrapper() -> None:
    path = ROOT / "components/member_home_schedule_presentation.py"
    text = path.read_text()
    text = replace_once(text, '_PATCH_MARKER = "_hm_member_home_schedule_presentation_v2"', '_PATCH_MARKER = "_hm_member_home_schedule_presentation_v3"', "schedule marker")
    text = replace_once(text, '_MARKDOWN_PATCH_MARKER = "_hm_member_home_compact_polish_v5"', '_MARKDOWN_PATCH_MARKER = "_hm_member_home_compact_polish_v6"', "markdown marker")
    text = replace_once(text, "/* hm-member-home-compact-polish-v5 */", "/* hm-member-home-compact-polish-v6 */", "CSS marker")
    text = replace_once(text, 'and "hm-member-home-compact-polish-v5" not in body', 'and "hm-member-home-compact-polish-v6" not in body', "CSS install marker")

    text = replace_once(
        text,
        '''.hm-v101-schedule-card{
  width:47%!important;max-width:460px!important;
  margin:.34rem 0 .16rem 0!important;
  padding:.52rem .68rem!important;border-radius:12px!important;
}''',
        '''.hm-v101-schedule-card{
  width:100%!important;max-width:none!important;
  margin:0!important;padding:0!important;border-radius:0!important;
}''',
        "schedule card width",
    )
    text = replace_once(
        text,
        '''.hm-member-schedule-action-anchor + div[data-testid="stHorizontalBlock"]{
  width:47%!important;max-width:460px!important;
  gap:.42rem!important;margin:0 0 .54rem 0!important;
}''',
        '''.hm-member-schedule-action-anchor + div[data-testid="stHorizontalBlock"]{
  width:100%!important;max-width:none!important;
  gap:.34rem!important;margin:.24rem 0 0 0!important;
}''',
        "schedule action width",
    )
    text = replace_once(
        text,
        '''@media(max-width:900px){
  .hm-v101-schedule-card,
  .hm-member-schedule-action-anchor + div[data-testid="stHorizontalBlock"]{
    width:68%!important;max-width:560px!important;
  }
}''',
        '''@media(max-width:900px){
  .hm-v101-schedule-card,
  .hm-member-schedule-action-anchor + div[data-testid="stHorizontalBlock"]{
    width:100%!important;max-width:none!important;
  }
}''',
        "schedule medium width",
    )
    text = replace_once(
        text,
        '''  .hm-v101-schedule-card,
  .hm-member-schedule-action-anchor + div[data-testid="stHorizontalBlock"]{
    width:100%!important;max-width:none!important;
  }
  .hm-v101-schedule-card{padding:.62rem .72rem!important;}''',
        '''  .hm-v101-schedule-card,
  .hm-member-schedule-action-anchor + div[data-testid="stHorizontalBlock"]{
    width:100%!important;max-width:none!important;
  }
  .hm-v101-schedule-card{padding:0!important;}''',
        "schedule mobile padding",
    )
    path.write_text(text)


def patch_daily_log() -> None:
    path = ROOT / "pages/18_Daily_Log.py"
    text = path.read_text()

    helper = '''def _render_fluid_time_selector(prior_value, date_key, idx):
    parsed = _parse_time(prior_value)
    prior_hour = f"{((parsed.hour - 1) % 12) + 1:02d}" if parsed else "HH"
    prior_minute = f"{parsed.minute:02d}" if parsed else "MM"
    prior_period = ("AM" if parsed.hour < 12 else "PM") if parsed else "AM/PM"

    hour_options = ["HH"] + [f"{value:02d}" for value in range(1, 13)]
    minute_options = ["MM"] + [f"{value:02d}" for value in range(60)]
    period_options = ["AM/PM", "AM", "PM"]

    st.markdown(
        f"<div class='hm-fluid-time-label'>Fluid timing {idx + 1}</div>",
        unsafe_allow_html=True,
    )
    hour_col, minute_col, period_col = st.columns([1, 1, 1.2], gap="small")
    with hour_col:
        st.markdown(
            "<span class='hm-fluid-time-grid-anchor'></span>",
            unsafe_allow_html=True,
        )
        selected_hour = st.selectbox(
            "Hour",
            hour_options,
            index=hour_options.index(prior_hour),
            key=f"hm_h9a4c_fluid_hour_{date_key}_{idx}",
        )
    with minute_col:
        selected_minute = st.selectbox(
            "Minute",
            minute_options,
            index=minute_options.index(prior_minute),
            key=f"hm_h9a4c_fluid_minute_{date_key}_{idx}",
        )
    with period_col:
        selected_period = st.selectbox(
            "AM/PM",
            period_options,
            index=period_options.index(prior_period),
            key=f"hm_h9a4c_fluid_period_{date_key}_{idx}",
        )

    if selected_hour == "HH" or selected_minute == "MM" or selected_period == "AM/PM":
        return None
    return datetime.strptime(
        f"{selected_hour}:{selected_minute} {selected_period}",
        "%I:%M %p",
    ).time()


'''
    text = replace_once(
        text,
        'def _time_text(value):\n    return "" if value is None else value.strftime("%I:%M %p")\n\n\n',
        'def _time_text(value):\n    return "" if value is None else value.strftime("%I:%M %p")\n\n\n' + helper,
        "fluid time helper",
    )

    text = replace_once(
        text,
        '        .hm-snacking-subtitle{color:#64748B;font-size:.82rem;font-weight:720;margin:.35rem 0 .15rem 0;}\n',
        '        .hm-snacking-subtitle{color:#64748B;font-size:.82rem;font-weight:720;margin:.35rem 0 .15rem 0;}\n        .hm-fluid-time-label{color:#334155;font-size:.84rem;font-weight:760;margin:0 0 .18rem 0;}\n        .hm-fluid-time-grid-anchor{display:none!important;height:0!important;min-height:0!important;margin:0!important;padding:0!important;overflow:hidden!important;}\n        div[data-testid="stHorizontalBlock"]:has(.hm-fluid-time-grid-anchor){gap:.38rem!important;align-items:flex-end!important;}\n        div[data-testid="stHorizontalBlock"]:has(.hm-fluid-time-grid-anchor) label p{font-size:.74rem!important;font-weight:820!important;white-space:nowrap!important;}\n        div[data-testid="stHorizontalBlock"]:has(.hm-fluid-time-grid-anchor) [data-baseweb="select"] > div{min-height:2.42rem!important;padding-left:.36rem!important;padding-right:.28rem!important;}\n',
        "fluid time CSS",
    )

    text = replace_once(
        text,
        '''                with time_col:
                    fluid_time = st.time_input(
                        f"Fluid timing {idx + 1}",
                        value=_parse_time(prior.get("time")),
                        key=f"hm_h9a4c_fluid_time_{date_key}_{idx}",
                    )''',
        '''                with time_col:
                    fluid_time = _render_fluid_time_selector(
                        prior.get("time"),
                        date_key,
                        idx,
                    )''',
        "fluid time widget",
    )
    path.write_text(text)


def patch_tests_and_workflow() -> None:
    path = ROOT / "tests/test_member_home_schedule_presentation.py"
    text = path.read_text()
    new_test = '''    def test_member_home_uses_compact_three_by_two_schedule_and_message_grids(self):
        source = (ROOT / "pages/02_Member_Home.py").read_text()
        ast.parse(source)
        self.assertIn("list_upcoming_member_schedules(user_id, limit=6)", source)
        self.assertIn("get_member_messages(user_id, limit=6)", source)
        self.assertIn("for row_start in range(0, len(upcoming_schedules), 3):", source)
        self.assertIn("for row_start in range(0, len(unique_messages), 3):", source)
        self.assertGreaterEqual(source.count('st.columns(3, gap="small")'), 2)
        self.assertIn("hm-home-section-divider", source)
        self.assertIn("hm-home-grid-anchor", source)
        self.assertIn("hm-message-grid-anchor", source)
        self.assertLess(
            source.index("_render_upcoming_schedules(user_id)"),
            source.index("_render_messages(user_id, show_divider="),
        )
        schedule_slice = source[
            source.index("def _render_upcoming_schedules") :
            source.index("def _render_task_button")
        ]
        self.assertNotIn("with st.expander(", schedule_slice)
        for forbidden in (
            "update_member_schedule_status(",
            "session_counted =",
            "save_db(",
        ):
            self.assertNotIn(forbidden, source)

    def test_other_fluid_time_uses_balanced_hour_minute_period_controls(self):
        source = (ROOT / "pages/18_Daily_Log.py").read_text()
        ast.parse(source)
        self.assertIn("def _render_fluid_time_selector", source)
        self.assertIn('st.columns([1, 1, 1.2], gap="small")', source)
        self.assertIn('["HH"] + [f"{value:02d}" for value in range(1, 13)]', source)
        self.assertIn('["MM"] + [f"{value:02d}" for value in range(60)]', source)
        self.assertIn('["AM/PM", "AM", "PM"]', source)
        self.assertIn("hm-fluid-time-grid-anchor", source)
        self.assertNotIn("fluid_time = st.time_input(", source)

'''
    text = replace_block(
        text,
        "    def test_member_home_upcoming_schedule_is_collapsible_after_filtering(self):\n",
        "    def test_every_eligible_home_schedule_has_acknowledge_and_reschedule_actions(self):\n",
        new_test,
        "grid tests",
    )
    path.write_text(text)

    workflow = ROOT / ".github/workflows/member-home-schedule-actions.yml"
    wf = workflow.read_text()
    wf = replace_once(
        wf,
        '      - "pages/02_Member_Home.py"\n',
        '      - "pages/02_Member_Home.py"\n      - "pages/18_Daily_Log.py"\n',
        "workflow path",
    )
    wf = replace_once(
        wf,
        '            pages/02_Member_Home.py \\\n            tests/test_member_home_schedule_presentation.py\n',
        '            pages/02_Member_Home.py \\\n            pages/18_Daily_Log.py \\\n            tests/test_member_home_schedule_presentation.py\n',
        "workflow compile files",
    )
    workflow.write_text(wf)


def main() -> None:
    patch_member_home()
    patch_schedule_wrapper()
    patch_daily_log()
    patch_tests_and_workflow()


if __name__ == "__main__":
    main()
