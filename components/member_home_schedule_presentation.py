from __future__ import annotations

import datetime as dt
from functools import wraps
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


_DEFAULT_MEMBER_TIMEZONE = "Asia/Kolkata"
_PATCH_MARKER = "_hm_member_home_schedule_presentation_v3"
_MARKDOWN_PATCH_MARKER = "_hm_member_home_compact_polish_v7"
_MEMBER_HOME_STYLE_MARKER = 'id="hm-member-home-local-style-v3"'
_CLOSED_STATUSES = {"cancelled", "completed", "rescheduled"}
_ACTION_ROWS_KEY = "_hm_member_home_schedule_action_rows"
_ACTION_INDEX_KEY = "_hm_member_home_schedule_action_index"
_ACTION_RENDERED_IDS_KEY = "_hm_member_home_schedule_action_rendered_ids"
_MEMBER_HOME_COMPACT_CSS = """
/* hm-member-home-compact-polish-v7 */
div[data-testid="stExpander"]:has(.hm-upcoming-schedule-anchor),
div[data-testid="stExpander"]:has(.hm-upcoming-schedule-anchor) > div,
div[data-testid="stExpander"]:has(.hm-upcoming-schedule-anchor) details,
div[data-testid="stExpander"]:has(.hm-upcoming-schedule-anchor) [data-testid="stExpanderDetails"]{
  border:0!important;border-top:0!important;border-bottom:0!important;outline:0!important;
  background:transparent!important;box-shadow:none!important;
  margin:.20rem 0 .42rem 0!important;padding:0!important;
}
div[data-testid="stExpander"]:has(.hm-upcoming-schedule-anchor) details::before,
div[data-testid="stExpander"]:has(.hm-upcoming-schedule-anchor) details::after,
div[data-testid="stExpander"]:has(.hm-upcoming-schedule-anchor) summary::after,
div[data-testid="stExpander"]:has(.hm-upcoming-schedule-anchor) summary + div::before,
div[data-testid="stExpander"]:has(.hm-upcoming-schedule-anchor) summary + div::after{
  display:none!important;content:none!important;border:0!important;
}
div[data-testid="stExpander"]:has(.hm-upcoming-schedule-anchor) summary + div{
  border:0!important;border-top:0!important;border-bottom:0!important;
  box-shadow:none!important;margin-top:0!important;padding-top:.24rem!important;
}
div[data-testid="stExpander"]:has(.hm-upcoming-schedule-anchor) hr{
  display:none!important;border:0!important;height:0!important;margin:0!important;
}
div[data-testid="stExpander"]:has(.hm-upcoming-schedule-anchor) summary{
  width:fit-content!important;max-width:100%!important;min-width:0!important;
  min-height:2.12rem!important;padding:.30rem .72rem!important;
  border:1px solid #E3C98E!important;border-bottom:1px solid #E3C98E!important;
  border-radius:999px!important;background:#FFFDF8!important;
  box-shadow:0 3px 8px rgba(6,78,59,.05)!important;
  display:flex!important;align-items:center!important;gap:.44rem!important;
  overflow:visible!important;
}
div[data-testid="stExpander"]:has(.hm-upcoming-schedule-anchor) summary,
div[data-testid="stExpander"]:has(.hm-upcoming-schedule-anchor) summary *{
  white-space:nowrap!important;overflow-wrap:normal!important;
  word-break:keep-all!important;line-height:1.10!important;
}
div[data-testid="stExpander"]:has(.hm-upcoming-schedule-anchor) summary p{
  margin:0!important;font-size:.78rem!important;font-weight:900!important;flex:1 1 auto!important;max-width:none!important;overflow:visible!important;text-overflow:clip!important;
}
div[data-testid="stExpander"]:has(.hm-upcoming-schedule-anchor) summary [data-testid="stExpanderToggleIcon"],
div[data-testid="stExpander"]:has(.hm-upcoming-schedule-anchor) summary [data-testid="stIconMaterial"],
div[data-testid="stExpander"]:has(.hm-upcoming-schedule-anchor) summary [class*="material-symbol"],
div[data-testid="stExpander"]:has(.hm-upcoming-schedule-anchor) summary svg{
  display:none!important;width:0!important;height:0!important;min-width:0!important;
  margin:0!important;padding:0!important;overflow:hidden!important;font-size:0!important;
}
div[data-testid="stExpander"]:has(.hm-upcoming-schedule-anchor) summary::before{
  content:"›";display:inline-flex;align-items:center;justify-content:center;
  width:.78rem;height:.78rem;min-width:.78rem;color:#064E3B;
  font-size:1rem;font-weight:900;line-height:1;transform:rotate(0deg);
  transition:transform .16s ease;
}
div[data-testid="stExpander"]:has(.hm-upcoming-schedule-anchor) details[open] summary::before{
  transform:rotate(90deg);
}
.hm-v101-schedule-card{
  width:100%!important;max-width:none!important;min-height:0!important;
  margin:0!important;padding:0!important;border-radius:0!important;
}
.hm-upcoming-schedule-anchor,.hm-member-schedule-action-anchor{
  display:none!important;height:0!important;min-height:0!important;
  margin:0!important;padding:0!important;overflow:hidden!important;
}
.hm-member-schedule-action-anchor + div[data-testid="stHorizontalBlock"]{
  width:100%!important;max-width:none!important;
  gap:.34rem!important;margin:.24rem 0 0 0!important;
}
.hm-member-schedule-action-anchor + div[data-testid="stHorizontalBlock"] button{
  min-height:2.34rem!important;height:auto!important;
  padding:.34rem .48rem!important;border-radius:10px!important;
  font-size:.72rem!important;font-weight:900!important;
  white-space:normal!important;overflow:visible!important;text-overflow:clip!important;
}
.hm-member-schedule-action-anchor + div[data-testid="stHorizontalBlock"] button p{
  white-space:normal!important;overflow:visible!important;text-overflow:clip!important;
  font-size:.72rem!important;line-height:1.14!important;
}
@media(max-width:900px){
  .hm-v101-schedule-card,
  .hm-member-schedule-action-anchor + div[data-testid="stHorizontalBlock"]{
    width:100%!important;max-width:none!important;
  }
}
@media(max-width:640px){
  div[data-testid="stExpander"]:has(.hm-upcoming-schedule-anchor) summary{
    width:fit-content!important;max-width:calc(100vw - 2rem)!important;
  }
  .hm-v101-schedule-card,
  .hm-member-schedule-action-anchor + div[data-testid="stHorizontalBlock"]{
    width:100%!important;max-width:none!important;
  }
  .hm-v101-schedule-card{padding:0!important;}
}
"""


def _text(value: object) -> str:
    return str(value or "").strip()


def _parse_utc(value: object) -> dt.datetime | None:
    text = _text(value)
    if not text:
        return None
    try:
        parsed = dt.datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed.astimezone(dt.timezone.utc)


def _parse_date(value: object) -> dt.date | None:
    text = _text(value)
    if not text:
        return None
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y"):
        try:
            return dt.datetime.strptime(text[:10], fmt).date()
        except ValueError:
            pass
    return None


def _parse_time(value: object) -> dt.time | None:
    text = _text(value).upper()
    if not text:
        return None
    for fmt in ("%I:%M %p", "%H:%M", "%I %p", "%H"):
        try:
            return dt.datetime.strptime(text, fmt).time()
        except ValueError:
            pass
    return None


def _zone(value: object) -> ZoneInfo:
    candidate = _text(value) or _DEFAULT_MEMBER_TIMEZONE
    try:
        return ZoneInfo(candidate)
    except (ZoneInfoNotFoundError, ValueError):
        return ZoneInfo(_DEFAULT_MEMBER_TIMEZONE)


def _local_schedule_utc(row: dict[str, Any], *, use_end: bool) -> dt.datetime | None:
    schedule_date = _parse_date(row.get("schedule_date"))
    selected_time = _parse_time(row.get("end_time" if use_end else "start_time"))
    if not schedule_date or not selected_time:
        return None
    timezone_name = (
        row.get("member_timezone_name")
        or row.get("source_timezone_name")
        or _DEFAULT_MEMBER_TIMEZONE
    )
    local_value = dt.datetime.combine(schedule_date, selected_time).replace(
        tzinfo=_zone(timezone_name)
    )
    return local_value.astimezone(dt.timezone.utc)


def _schedule_start_utc(row: dict[str, Any]) -> dt.datetime | None:
    return _parse_utc(row.get("start_at_utc")) or _local_schedule_utc(
        row, use_end=False
    )


def _schedule_end_utc(row: dict[str, Any]) -> dt.datetime | None:
    end_value = _parse_utc(row.get("end_at_utc")) or _local_schedule_utc(
        row, use_end=True
    )
    if end_value is not None:
        return end_value
    start_value = _schedule_start_utc(row)
    return start_value + dt.timedelta(minutes=30) if start_value else None


def prepare_member_home_upcoming_schedules(
    rows: list[dict[str, Any]],
    *,
    now_utc: dt.datetime | None = None,
    limit: int = 5,
) -> list[dict[str, Any]]:
    """Hide ended Member Home cards and show the latest future slot first.

    This is presentation-only. It never changes schedule status, session_counted,
    package usage, notifications or stored schedule data.
    """

    now_value = now_utc or dt.datetime.now(dt.timezone.utc)
    if now_value.tzinfo is None:
        now_value = now_value.replace(tzinfo=dt.timezone.utc)
    now_value = now_value.astimezone(dt.timezone.utc)

    visible: list[dict[str, Any]] = []
    for raw in rows or []:
        row = dict(raw or {})
        status = _text(row.get("status") or "scheduled").lower()
        if status in _CLOSED_STATUSES or status == "acknowledged":
            continue
        end_value = _schedule_end_utc(row)
        if end_value is not None and end_value <= now_value:
            continue
        visible.append(row)

    minimum = dt.datetime.min.replace(tzinfo=dt.timezone.utc)
    visible.sort(
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


def _next_schedule_action_row() -> dict[str, Any] | None:
    """Return the schedule matching the next Member Home card render."""

    import streamlit as st

    rows = st.session_state.get(_ACTION_ROWS_KEY) or []
    index = int(st.session_state.get(_ACTION_INDEX_KEY, 0) or 0)
    if index >= len(rows):
        return None
    st.session_state[_ACTION_INDEX_KEY] = index + 1
    return dict(rows[index] or {})


def _accept_member_home_schedule(
    schedule_id: str,
    member_id: object,
    error_key: str,
) -> None:
    """Accept before the normal Streamlit button rerun; do not trigger a second rerun."""

    import streamlit as st
    from components import db as db_api

    updated = db_api.acknowledge_member_schedule(schedule_id, member_id)
    if not updated:
        st.session_state[error_key] = (
            "This schedule could not be accepted. Please refresh and retry."
        )


def _render_member_home_schedule_actions(row: dict[str, Any]) -> None:
    """Render consistent acceptance and reschedule actions under a card."""

    import streamlit as st

    schedule_id = _text(row.get("id"))
    if not schedule_id:
        return

    rendered_ids = set(st.session_state.get(_ACTION_RENDERED_IDS_KEY) or ())
    if schedule_id in rendered_ids:
        return
    rendered_ids.add(schedule_id)
    st.session_state[_ACTION_RENDERED_IDS_KEY] = rendered_ids

    status = _text(row.get("status") or "scheduled").lower()
    if status not in {"scheduled", "acknowledged"}:
        return
    pending_reschedule = (
        _text(row.get("reschedule_request_status")).lower() == "pending"
    )
    error_key = f"_hm_home_accept_error_{schedule_id}"
    error_message = st.session_state.pop(error_key, "")
    if error_message:
        st.error(error_message)

    st.markdown(
        "<span class='hm-member-schedule-action-anchor'></span>",
        unsafe_allow_html=True,
    )
    accept_col, reschedule_col = st.columns(2, gap="small")
    with accept_col:
        if status == "scheduled":
            st.button(
                "Accept",
                key=f"hm_home_accept_schedule_{schedule_id}",
                use_container_width=True,
                on_click=_accept_member_home_schedule,
                args=(schedule_id, row.get("member_id"), error_key),
            )
        else:
            st.button(
                "Accepted",
                key=f"hm_home_accepted_schedule_{schedule_id}",
                use_container_width=True,
                disabled=True,
            )
    with reschedule_col:
        reschedule_label = "Reschedule pending" if pending_reschedule else "Reschedule"
        if st.button(
            reschedule_label,
            key=f"hm_home_reschedule_schedule_{schedule_id}",
            use_container_width=True,
            disabled=pending_reschedule,
        ):
            st.session_state["hm_member_schedule_active_section"] = "Upcoming Schedule"
            st.session_state[f"hm_tz_show_reschedule_{schedule_id}"] = True
            st.switch_page("pages/33_My_Schedule.py")


def _install_member_home_compact_polish() -> None:
    """Append Member Home-only CSS and schedule actions to card rendering."""

    import streamlit as st

    current_markdown = st.markdown
    if getattr(current_markdown, _MARKDOWN_PATCH_MARKER, False):
        return

    @wraps(current_markdown)
    def polished_markdown(body, *args, **kwargs):
        if (
            isinstance(body, str)
            and _MEMBER_HOME_STYLE_MARKER in body
            and "hm-member-home-compact-polish-v7" not in body
        ):
            body = body.replace(
                "</style>",
                f"{_MEMBER_HOME_COMPACT_CSS}</style>",
                1,
            )
        result = current_markdown(body, *args, **kwargs)
        if isinstance(body, str) and "hm-v101-schedule-card" in body:
            row = _next_schedule_action_row()
            if row:
                _render_member_home_schedule_actions(row)
        return result

    setattr(polished_markdown, _MARKDOWN_PATCH_MARKER, True)
    polished_markdown._hm_original_markdown = current_markdown
    st.markdown = polished_markdown


def install_member_home_schedule_presentation() -> None:
    """Install Member Home schedule filtering, actions and compact presentation."""

    import streamlit as st
    from components import db as db_api

    _install_member_home_compact_polish()

    current = db_api.list_upcoming_member_schedules
    if getattr(current, _PATCH_MARKER, False):
        return

    @wraps(current)
    def latest_visible_member_home_schedules(member_id: object, limit: int = 3):
        rows = current(member_id, limit=0)
        visible = prepare_member_home_upcoming_schedules(rows, limit=limit)
        st.session_state[_ACTION_ROWS_KEY] = [dict(row or {}) for row in visible]
        st.session_state[_ACTION_INDEX_KEY] = 0
        st.session_state[_ACTION_RENDERED_IDS_KEY] = set()
        return visible

    setattr(latest_visible_member_home_schedules, _PATCH_MARKER, True)
    latest_visible_member_home_schedules._hm_original = current
    db_api.list_upcoming_member_schedules = latest_visible_member_home_schedules
