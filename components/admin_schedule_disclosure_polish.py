from __future__ import annotations

import datetime as dt
import functools
from typing import Any

import streamlit as st


_MARKER = "_hm_admin_schedule_disclosure_polish_v1"


def install_admin_schedule_disclosure_polish(feedback_module: Any) -> None:
    """Replace the native schedule expander with the app-standard +/- disclosure."""
    if getattr(feedback_module, _MARKER, False):
        return

    base_table = feedback_module._render_schedule_table

    @functools.wraps(feedback_module._render_day_schedule)
    def render_day_schedule(rows: list[dict[str, str]], selected_date: dt.date) -> None:
        date_label = selected_date.strftime("%d %b %Y")
        if not rows:
            st.markdown(
                "<div class='hm-sched-polish-empty'>"
                f"No meeting is scheduled on the selected date · {date_label}"
                "</div>",
                unsafe_allow_html=True,
            )
            return

        meeting_word = "meeting" if len(rows) == 1 else "meetings"
        state_key = f"hm_admin_schedule_open_{selected_date.isoformat()}"
        st.session_state.setdefault(state_key, False)
        is_open = bool(st.session_state.get(state_key))
        marker = "−" if is_open else "+"
        label = f"{marker} Admin schedule · {len(rows)} {meeting_word} · {date_label}"
        if st.button(
            label,
            key=f"hm_admin_schedule_toggle_{selected_date.isoformat()}",
            use_container_width=True,
        ):
            st.session_state[state_key] = not is_open
            st.rerun()
        if is_open:
            st.markdown(
                "<div class='hm-sched-polish-table-card'>",
                unsafe_allow_html=True,
            )
            base_table(rows)
            st.markdown("</div>", unsafe_allow_html=True)

    feedback_module._render_day_schedule = render_day_schedule
    setattr(feedback_module, _MARKER, True)

    st.markdown(
        """
<style id="hm-admin-schedule-disclosure-polish-v1">
.hm-sched-polish-empty{
  border:1px solid #E3C98E;
  border-radius:12px;
  background:#FFFDF8;
  color:#64748B;
  font-size:.80rem;
  font-weight:750;
  padding:.58rem .72rem;
  margin:.28rem 0 .62rem;
}
div[data-testid="stButton"]:has(button[kind="secondary"] p:first-child){min-width:0!important;}
button[data-testid="baseButton-secondary"]:has(p:first-child){overflow:hidden!important;}
button[data-testid="baseButton-secondary"] p{
  white-space:nowrap!important;
  overflow:hidden!important;
  text-overflow:ellipsis!important;
}
.hm-sched-polish-table-card{
  width:100%;
  min-width:0;
  overflow:hidden;
  border:1px solid #E3C98E;
  border-radius:12px;
  background:#FFFFFF;
  padding:.42rem;
  margin:-.12rem 0 .62rem;
}
.hm-sched-polish-table-card .hm-sched-day-table-wrap{
  width:100%!important;
  max-width:100%!important;
  min-width:0!important;
  overflow-x:auto!important;
  border-radius:9px!important;
}
.hm-sched-polish-table-card .hm-sched-day-table{
  table-layout:fixed!important;
  width:100%!important;
  min-width:680px!important;
}
.hm-sched-polish-table-card .hm-sched-day-table th,
.hm-sched-polish-table-card .hm-sched-day-table td{
  overflow-wrap:normal!important;
  word-break:normal!important;
  white-space:normal!important;
}
@media(max-width:760px){
  .hm-sched-polish-table-card{padding:.30rem;}
}
</style>
""",
        unsafe_allow_html=True,
    )
