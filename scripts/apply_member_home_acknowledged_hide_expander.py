from __future__ import annotations

from pathlib import Path


COMPONENT = Path("components/member_home_schedule_presentation.py")
PAGE = Path("pages/02_Member_Home.py")
TEST = Path("tests/test_member_home_schedule_presentation.py")

component = COMPONENT.read_text()
old_filter = '''        status = _text(row.get("status") or "scheduled").lower()
        if status in _CLOSED_STATUSES:
            continue
'''
new_filter = '''        status = _text(row.get("status") or "scheduled").lower()
        if status in _CLOSED_STATUSES or status == "acknowledged":
            continue
'''
if old_filter not in component:
    raise RuntimeError("Member Home schedule status filter anchor was not found")
component = component.replace(old_filter, new_filter, 1)
COMPONENT.write_text(component)

page = PAGE.read_text()
start_marker = "def _render_upcoming_schedules(user_id):\n"
end_marker = "\n\ndef _render_task_button(label, key, page, disabled=False):\n"
start = page.find(start_marker)
end = page.find(end_marker, start)
if start < 0 or end < 0:
    raise RuntimeError("Member Home upcoming schedule renderer boundaries were not found")
replacement = '''def _render_upcoming_schedules(user_id):
    queue_schedule_acknowledgement_reminders_v104b11(user_id)
    upcoming_schedules = list_upcoming_member_schedules(user_id, limit=6)
    if not upcoming_schedules:
        return False

    with st.expander(
        f"Upcoming Schedule · {len(upcoming_schedules)} upcoming",
        expanded=True,
    ):
        st.markdown(
            "<span class='hm-upcoming-schedule-anchor'></span>",
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
page = page[:start] + replacement + page[end:]
PAGE.write_text(page)

test = TEST.read_text()
first_start = test.find(
    "    def test_latest_future_schedule_is_rendered_first_and_ended_rows_are_hidden(self):\n"
)
first_end = test.find("\n    def test_duplicate_schedule_ids_are_rendered_once", first_start)
if first_start < 0 or first_end < 0:
    raise RuntimeError("Initial upcoming schedule test boundaries were not found")
first_block = test[first_start:first_end].replace(
    '"status": "acknowledged"',
    '"status": "scheduled"',
)
test = test[:first_start] + first_block + test[first_end:]

closed_anchor = '''    def test_closed_schedule_is_not_returned(self):
'''
acknowledged_test = '''    def test_acknowledged_schedule_disappears_from_member_home(self):
        rows = [
            {
                "id": "acknowledged",
                "status": "acknowledged",
                "start_at_utc": "2026-08-08T04:30:00Z",
                "end_at_utc": "2026-08-08T05:00:00Z",
            },
            {
                "id": "scheduled",
                "status": "scheduled",
                "start_at_utc": "2026-08-09T04:30:00Z",
                "end_at_utc": "2026-08-09T05:00:00Z",
            },
        ]

        visible = prepare_member_home_upcoming_schedules(
            rows,
            now_utc=dt.datetime(2026, 8, 4, tzinfo=UTC),
            limit=6,
        )

        self.assertEqual([row["id"] for row in visible], ["scheduled"])

'''
if acknowledged_test not in test:
    if closed_anchor not in test:
        raise RuntimeError("Closed schedule test anchor was not found")
    test = test.replace(closed_anchor, acknowledged_test + closed_anchor, 1)

old_expander_assertion = '''        self.assertNotIn("with st.expander(", schedule_slice)
'''
new_expander_assertions = '''        self.assertIn("with st.expander(", schedule_slice)
        self.assertIn("hm-upcoming-schedule-anchor", schedule_slice)
        self.assertIn("expanded=True", schedule_slice)
'''
if old_expander_assertion not in test:
    raise RuntimeError("Retired no-expander assertion was not found")
test = test.replace(old_expander_assertion, new_expander_assertions, 1)

status_assert_anchor = '''        self.assertIn("seen_schedule_keys", helper)
'''
status_assert_replacement = '''        self.assertIn("seen_schedule_keys", helper)
        self.assertIn('status == "acknowledged"', helper)
'''
if status_assert_replacement not in test:
    if status_assert_anchor not in test:
        raise RuntimeError("Schedule helper assertion anchor was not found")
    test = test.replace(status_assert_anchor, status_assert_replacement, 1)

TEST.write_text(test)
