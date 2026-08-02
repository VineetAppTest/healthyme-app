from __future__ import annotations

import datetime as dt
import functools
import html
from collections import defaultdict
from zoneinfo import ZoneInfo

import streamlit as st


_MARKER = "_hm_exercise_saved_days_readonly_v2"


def _clean(value: object) -> str:
    return "" if value is None else str(value).strip()


def _parse_date(value: object) -> dt.date | None:
    if isinstance(value, dt.date) and not isinstance(value, dt.datetime):
        return value
    try:
        return dt.date.fromisoformat(_clean(value)[:10])
    except (TypeError, ValueError):
        return None


def _india_today() -> dt.date:
    return dt.datetime.now(ZoneInfo("Asia/Kolkata")).date()


def _display_time(value: object) -> str:
    raw = _clean(value)
    if not raw:
        return "—"
    for fmt in ("%H:%M:%S", "%H:%M", "%I:%M %p"):
        try:
            parsed = dt.datetime.strptime(raw, fmt)
            return parsed.strftime("%I:%M %p").lstrip("0")
        except ValueError:
            continue
    return raw


def _render_saved_exercise_summary(rows: list[dict]) -> None:
    grouped: dict[dt.date, list[dict]] = defaultdict(list)
    for raw_row in rows:
        row = dict(raw_row or {})
        saved_date = _parse_date(row.get("log_date"))
        if saved_date is not None:
            grouped[saved_date].append(row)

    st.markdown(
        """
<style id="hm-saved-exercise-summary-v1">
.hm-saved-exercise-window{display:grid;grid-template-columns:1fr;gap:.55rem;margin:.10rem 0 .20rem 0;}
.hm-saved-exercise-day{border:1px solid #E3C98E;background:linear-gradient(180deg,#FFFDF8,#FFF9EC);border-radius:14px;padding:.68rem .76rem;}
.hm-saved-exercise-date{color:#064E3B;font-size:.90rem;font-weight:950;margin-bottom:.34rem;}
.hm-saved-exercise-head,.hm-saved-exercise-line{display:grid;grid-template-columns:minmax(8rem,1.35fr) minmax(5.8rem,.8fr) minmax(7.5rem,1fr) minmax(6.8rem,.8fr) minmax(5.8rem,.75fr) minmax(8rem,1.35fr);gap:.48rem;align-items:start;}
.hm-saved-exercise-head{color:#72551A;font-size:.73rem;font-weight:900;padding:.18rem .18rem .28rem;border-bottom:1px solid #E8D8B6;}
.hm-saved-exercise-line{color:#334155;font-size:.79rem;line-height:1.35;padding:.38rem .18rem;border-bottom:1px solid #EFE3CA;}
.hm-saved-exercise-line:last-child{border-bottom:0;}
.hm-saved-exercise-status{font-weight:850;color:#064E3B;}
.hm-saved-exercise-empty{color:#64748B;font-size:.79rem;font-weight:720;}
@media(max-width:860px){
  .hm-saved-exercise-head{display:none;}
  .hm-saved-exercise-line{grid-template-columns:1fr 1fr;gap:.20rem .55rem;padding:.55rem .18rem;}
  .hm-saved-exercise-line>div::before{display:block;color:#72551A;font-size:.69rem;font-weight:900;}
  .hm-saved-exercise-line>div:nth-child(1)::before{content:'Activity';}
  .hm-saved-exercise-line>div:nth-child(2)::before{content:'Timing';}
  .hm-saved-exercise-line>div:nth-child(3)::before{content:'Duration / Sets';}
  .hm-saved-exercise-line>div:nth-child(4)::before{content:'Status';}
  .hm-saved-exercise-line>div:nth-child(5)::before{content:'Completion';}
  .hm-saved-exercise-line>div:nth-child(6)::before{content:'Remarks';}
}
</style>
        """,
        unsafe_allow_html=True,
    )

    cards: list[str] = []
    for saved_date in sorted(grouped, reverse=True):
        day_rows = sorted(
            grouped[saved_date],
            key=lambda row: int(row.get("item_order") or 0),
        )
        lines = [
            "<div class='hm-saved-exercise-head'>"
            "<div>Activity</div><div>Timing</div><div>Duration / Sets</div>"
            "<div>Status</div><div>Completion</div><div>Remarks</div></div>"
        ]
        for row in day_rows:
            lines.append(
                "<div class='hm-saved-exercise-line'>"
                f"<div>{html.escape(_clean(row.get('exercise_name')) or '—')}</div>"
                f"<div>{html.escape(_clean(row.get('scheduled_time')) or '—')}</div>"
                f"<div>{html.escape(_clean(row.get('duration_or_reps')) or '—')}</div>"
                f"<div class='hm-saved-exercise-status'>{html.escape(_clean(row.get('status')) or 'Not Started')}</div>"
                f"<div>{html.escape(_display_time(row.get('completion_time')))}</div>"
                f"<div>{html.escape(_clean(row.get('member_notes')) or '—')}</div>"
                "</div>"
            )
        cards.append(
            "<div class='hm-saved-exercise-day'>"
            f"<div class='hm-saved-exercise-date'>{saved_date.strftime('%a, %d %b %Y')}</div>"
            f"{''.join(lines)}</div>"
        )

    st.markdown(
        "<div class='hm-saved-exercise-window'>" + "".join(cards) + "</div>",
        unsafe_allow_html=True,
    )


def install_exercise_saved_days_readonly_runtime() -> None:
    """Replace Exercise saved-date loaders with the accepted read-only summary."""

    from components import member_exercise_journal_table as table

    current = table._render_saved_days
    if getattr(current, _MARKER, False):
        return

    @functools.wraps(current)
    def render_saved_days_readonly(
        member_id: str,
        key_prefix: str,
        date_key: str,
        pending_key: str,
    ) -> None:
        del date_key, pending_key

        today = _india_today()
        from_key = f"{key_prefix}_saved_from"
        to_key = f"{key_prefix}_saved_to"
        init_key = f"{key_prefix}_saved_filter_today_v2"
        if not st.session_state.get(init_key):
            # Start closed on today's date. Historical data appears only after the
            # member deliberately expands the From/To range.
            st.session_state[from_key] = today
            st.session_state[to_key] = today
            st.session_state[init_key] = True
        else:
            st.session_state.setdefault(from_key, today)
            st.session_state.setdefault(to_key, today)

        with st.container(border=True):
            st.markdown("### View Saved Days")
            from_col, to_col = st.columns(2)
            with from_col:
                filter_from = st.date_input("From", key=from_key)
            with to_col:
                filter_to = st.date_input("To", key=to_key)

            if filter_from > filter_to:
                st.warning("From date cannot be after To date.")
                return

            filtered_rows = [
                dict(row or {})
                for row in table.list_saved_exercise_rows(member_id)
                if (saved_date := _parse_date((row or {}).get("log_date")))
                and filter_from <= saved_date <= filter_to
            ]
            saved_dates = {
                saved_date
                for row in filtered_rows
                if (saved_date := _parse_date(row.get("log_date"))) is not None
            }
            if not filtered_rows:
                st.caption("No saved exercise days found in this range.")
                return

            st.caption(
                f"Showing {len(saved_dates)} saved exercise day(s) in the selected range."
            )
            _render_saved_exercise_summary(filtered_rows)

    setattr(render_saved_days_readonly, _MARKER, True)
    render_saved_days_readonly._hm_original = current
    table._render_saved_days = render_saved_days_readonly
