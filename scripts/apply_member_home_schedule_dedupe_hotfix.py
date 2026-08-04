from pathlib import Path


COMPONENT = Path("components/member_home_schedule_presentation.py")
TEST = Path("tests/test_member_home_schedule_presentation.py")

component = COMPONENT.read_text()

old_constants = '''_ACTION_ROWS_KEY = "_hm_member_home_schedule_action_rows"
_ACTION_INDEX_KEY = "_hm_member_home_schedule_action_index"
'''
new_constants = '''_ACTION_ROWS_KEY = "_hm_member_home_schedule_action_rows"
_ACTION_INDEX_KEY = "_hm_member_home_schedule_action_index"
_ACTION_RENDERED_IDS_KEY = "_hm_member_home_schedule_action_rendered_ids"
'''
if old_constants not in component:
    raise RuntimeError("Schedule action constant anchor was not found")
component = component.replace(old_constants, new_constants, 1)

old_return = '''    visible.sort(
        key=lambda row: (
            _schedule_start_utc(row) or minimum,
            _text(row.get("created_at")),
        ),
        reverse=True,
    )
    return visible[:limit] if limit else visible
'''
new_return = '''    visible.sort(
        key=lambda row: (
            _schedule_start_utc(row) or minimum,
            _text(row.get("created_at")),
        ),
        reverse=True,
    )

    # One schedule is one Member Home card. Some legacy/read projections may
    # surface the same stored schedule more than once; keep the newest sorted
    # occurrence and never register duplicate action widgets for the same ID.
    deduplicated: list[dict[str, Any]] = []
    seen_schedule_keys: set[tuple[str, ...]] = set()
    for row in visible:
        schedule_id = _text(row.get("id"))
        schedule_key = (
            ("id", schedule_id)
            if schedule_id
            else (
                "legacy",
                _text(row.get("member_id")),
                _text(row.get("schedule_date")),
                _text(row.get("start_time")),
                _text(row.get("title")),
            )
        )
        if schedule_key in seen_schedule_keys:
            continue
        seen_schedule_keys.add(schedule_key)
        deduplicated.append(row)

    return deduplicated[:limit] if limit else deduplicated
'''
if old_return not in component:
    raise RuntimeError("Schedule ordering return anchor was not found")
component = component.replace(old_return, new_return, 1)

old_action_start = '''    schedule_id = _text(row.get("id"))
    if not schedule_id:
        return
    status = _text(row.get("status") or "scheduled").lower()
'''
new_action_start = '''    schedule_id = _text(row.get("id"))
    if not schedule_id:
        return

    rendered_ids = set(st.session_state.get(_ACTION_RENDERED_IDS_KEY) or ())
    if schedule_id in rendered_ids:
        return
    rendered_ids.add(schedule_id)
    st.session_state[_ACTION_RENDERED_IDS_KEY] = rendered_ids

    status = _text(row.get("status") or "scheduled").lower()
'''
if old_action_start not in component:
    raise RuntimeError("Schedule action render anchor was not found")
component = component.replace(old_action_start, new_action_start, 1)

old_reset = '''        st.session_state[_ACTION_ROWS_KEY] = [dict(row or {}) for row in visible]
        st.session_state[_ACTION_INDEX_KEY] = 0
        return visible
'''
new_reset = '''        st.session_state[_ACTION_ROWS_KEY] = [dict(row or {}) for row in visible]
        st.session_state[_ACTION_INDEX_KEY] = 0
        st.session_state[_ACTION_RENDERED_IDS_KEY] = set()
        return visible
'''
if old_reset not in component:
    raise RuntimeError("Schedule action state reset anchor was not found")
component = component.replace(old_reset, new_reset, 1)

COMPONENT.write_text(component)


test = TEST.read_text()
closed_test_anchor = '''    def test_closed_schedule_is_not_returned(self):
'''
dedupe_test = '''    def test_duplicate_schedule_ids_are_rendered_once(self):
        rows = [
            {
                "id": "same-schedule",
                "status": "scheduled",
                "start_at_utc": "2026-08-08T04:30:00Z",
                "end_at_utc": "2026-08-08T05:00:00Z",
                "created_at": "2026-08-04T10:00:00Z",
            },
            {
                "id": "same-schedule",
                "status": "scheduled",
                "start_at_utc": "2026-08-08T04:30:00Z",
                "end_at_utc": "2026-08-08T05:00:00Z",
                "created_at": "2026-08-04T09:00:00Z",
            },
            {
                "id": "different-schedule",
                "status": "scheduled",
                "start_at_utc": "2026-08-07T04:30:00Z",
                "end_at_utc": "2026-08-07T05:00:00Z",
            },
        ]

        visible = prepare_member_home_upcoming_schedules(
            rows,
            now_utc=dt.datetime(2026, 8, 4, tzinfo=UTC),
            limit=6,
        )

        self.assertEqual(
            [row["id"] for row in visible],
            ["same-schedule", "different-schedule"],
        )
        self.assertEqual(
            visible[0]["created_at"],
            "2026-08-04T10:00:00Z",
        )

'''
if dedupe_test not in test:
    if closed_test_anchor not in test:
        raise RuntimeError("Closed schedule test anchor was not found")
    test = test.replace(closed_test_anchor, dedupe_test + closed_test_anchor, 1)

source_assert_anchor = '''        self.assertIn("hm-member-schedule-action-anchor", helper)
'''
source_assert_replacement = '''        self.assertIn("hm-member-schedule-action-anchor", helper)
        self.assertIn("_ACTION_RENDERED_IDS_KEY", helper)
        self.assertIn("seen_schedule_keys", helper)
'''
if source_assert_replacement not in test:
    if source_assert_anchor not in test:
        raise RuntimeError("Schedule action source assertion anchor was not found")
    test = test.replace(source_assert_anchor, source_assert_replacement, 1)

TEST.write_text(test)
