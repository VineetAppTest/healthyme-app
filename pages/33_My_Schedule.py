import streamlit as st

from components.guards import require_member
from components.ui_common import (
    inject_global_styles,
    apply_luxe_theme,
    utility_logout_bar,
    render_back_to_top,
    topbar,
    card_start,
    card_end,
    render_page_nav,
)
from components.db import (
    list_member_schedules,
    acknowledge_member_schedule,
    schedule_status_label_v101,
)

st.set_page_config(page_title="My Schedule", page_icon="💚", layout="wide", initial_sidebar_state="collapsed")
require_member()
user_id = st.session_state.get("user_id")

utility_logout_bar()
topbar("My Schedule", "View upcoming nutritionist sessions and follow-ups.", "Member content")

st.markdown("""
<style>
/* v101.0 Member Schedule */
.hm-member-schedule-card{
  border:1px solid #E3C98E;
  background:linear-gradient(180deg,#FFFDF8 0%,#FFF9EC 100%);
  border-radius:18px;
  padding:.90rem 1.05rem;
  margin:.50rem 0;
  box-shadow:0 8px 20px rgba(15,23,42,.045);
}
.hm-member-schedule-title{
  color:#064E3B;
  font-size:1rem;
  font-weight:950;
  margin-bottom:.20rem;
}
.hm-member-schedule-line{
  color:#334155;
  font-size:.86rem;
  font-weight:720;
  margin:.10rem 0;
}
.hm-member-schedule-pill{
  display:inline-flex;
  padding:.18rem .48rem;
  border-radius:999px;
  border:1px solid #D9C28F;
  background:#FFF7E6;
  color:#7A5A16;
  font-size:.72rem;
  font-weight:850;
  margin-left:.25rem;
}
</style>
""", unsafe_allow_html=True)

card_start()
st.subheader("Upcoming and recent schedules")
rows = list_member_schedules(member_id=user_id, include_cancelled=True, limit=30)
if not rows:
    st.info("No schedule has been created for you yet.")
else:
    for row in rows:
        status = row.get("status", "scheduled")
        time_text = row.get("start_time", "")
        if row.get("end_time"):
            time_text += f" - {row.get('end_time')}"
        st.markdown(
            f"""
            <div class='hm-member-schedule-card'>
              <div class='hm-member-schedule-title'>{row.get('title','Scheduled session')}<span class='hm-member-schedule-pill'>{schedule_status_label_v101(status)}</span></div>
              <div class='hm-member-schedule-line'>{row.get('schedule_date','')} · {time_text}</div>
              <div class='hm-member-schedule-line'>Mode: {row.get('mode','-')} · Link/location: {row.get('location_or_link') or '-'}</div>
              <div class='hm-member-schedule-line'>Notes: {row.get('notes') or '-'}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if status == "scheduled":
            if st.button("Acknowledge schedule", key=f"ack_schedule_{row.get('id')}", use_container_width=True):
                acknowledge_member_schedule(row.get("id"), user_id)
                st.success("Schedule acknowledged.")
                st.rerun()
card_end()

render_page_nav("My Schedule", back_page="pages/02_Member_Home.py", show_dashboard=False, show_evaluation=False, location="bottom")
render_back_to_top()

# v101.0: Member schedule view.
