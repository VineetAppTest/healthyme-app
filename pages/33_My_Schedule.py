import streamlit as st

from components.guards import require_member
from components.ui_common import (
    inject_global_styles,
    apply_luxe_theme,
    utility_logout_bar,
    render_back_to_top,
    topbar,
    render_page_nav,
)
from components.db import (
    list_member_schedules,
    acknowledge_member_schedule,
    schedule_status_label_v101,
)

st.set_page_config(page_title="My Schedule", page_icon="💚", layout="wide", initial_sidebar_state="collapsed")

# v101.1: Standard HealthyMe page stack.
inject_global_styles()
apply_luxe_theme()
require_member()
user_id = st.session_state.get("user_id")
utility_logout_bar()
topbar("My Schedule", "View upcoming nutritionist sessions and follow-ups.", "Member content")

st.markdown("""
<style>
/* v101.1 Member Schedule structured UI */
section.main > div.block-container,
.main .block-container,
[data-testid="stAppViewBlockContainer"],
.stMainBlockContainer,
.block-container{
  max-width:1080px!important;
  padding-top:.72rem!important;
}
.hm-member-schedule-shell{
  border:1px solid #E3C98E;
  background:linear-gradient(180deg,#FFFDF8 0%,#FFF9EC 100%);
  border-radius:20px;
  padding:1rem 1.08rem;
  box-shadow:0 10px 24px rgba(15,23,42,.05);
  margin:.40rem 0 .90rem 0;
}
.hm-member-schedule-heading{
  color:#003C36;
  font-size:1.12rem;
  font-weight:980;
  margin:0 0 .25rem 0;
}
.hm-member-schedule-sub{
  color:#475569;
  font-size:.86rem;
  font-weight:700;
  margin:0 0 .90rem 0;
}
.hm-member-schedule-card{
  border:1px solid #E3C98E;
  background:#FFFDF8;
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
div[data-testid="stButton"] > button{
  min-height:2.72rem!important;
  border-radius:14px!important;
  border:1.25px solid #D9C28F!important;
  background:#FFFDF8!important;
  color:#064E3B!important;
  font-weight:850!important;
}
div[data-testid="stButton"] > button:hover{
  border-color:#B89345!important;
  background:#FFF7E6!important;
}
</style>
""", unsafe_allow_html=True)

st.markdown("<div class='hm-member-schedule-shell'>", unsafe_allow_html=True)
st.markdown("<div class='hm-member-schedule-heading'>Upcoming and recent schedules</div>", unsafe_allow_html=True)
st.markdown("<div class='hm-member-schedule-sub'>Acknowledge upcoming sessions and review completed or cancelled schedules.</div>", unsafe_allow_html=True)

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

st.markdown("</div>", unsafe_allow_html=True)

render_page_nav("My Schedule", back_page="pages/02_Member_Home.py", show_dashboard=False, show_evaluation=False, location="bottom")
render_back_to_top()

# v101.1: Member Schedule structured using HealthyMe global layout.
