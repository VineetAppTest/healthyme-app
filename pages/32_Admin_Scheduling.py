import datetime
import streamlit as st

from components.guards import require_admin
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
    list_members,
    create_member_schedule,
    list_member_schedules,
    update_member_schedule_status,
    schedule_status_label_v101,
)

st.set_page_config(page_title="Admin Scheduling", page_icon="💚", layout="wide", initial_sidebar_state="collapsed")
require_admin()
utility_logout_bar()
topbar("Scheduling", "Create and manage member appointments, follow-ups and review sessions.", "Admin workflow")

st.markdown("""
<style>
/* v101.0 Scheduling page */
.hm-schedule-card{
  border:1px solid #E3C98E;
  background:linear-gradient(180deg,#FFFDF8 0%,#FFF9EC 100%);
  border-radius:18px;
  padding:.85rem 1rem;
  margin:.46rem 0;
  box-shadow:0 8px 20px rgba(15,23,42,.045);
}
.hm-schedule-title{
  color:#064E3B;
  font-size:.98rem;
  font-weight:950;
  margin-bottom:.20rem;
}
.hm-schedule-line{
  color:#334155;
  font-size:.84rem;
  font-weight:720;
  margin:.08rem 0;
}
.hm-schedule-pill{
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

members = list_members()
if not members:
    st.info("No members available.")
    st.stop()

member_options = {f"{m.get('name','')} — {m.get('email','')}": m.get("id") for m in members}
selected_label = st.selectbox("Select member", list(member_options.keys()))
member_id = member_options[selected_label]

left, right = st.columns([1.05, .95], gap="large")

with left:
    card_start()
    st.subheader("Create schedule")
    schedule_type = st.selectbox(
        "Schedule type",
        [
            "Consultation",
            "Follow-up",
            "Daily Log Review",
            "Recipe Review",
            "Exercise Review",
            "Reassessment Discussion",
            "Other",
        ],
    )
    title = st.text_input("Schedule title", value=schedule_type, placeholder="Example: Follow-up call")
    date_col, start_col, end_col = st.columns([1, 1, 1])
    with date_col:
        schedule_date = st.date_input("Date", value=datetime.date.today())
    with start_col:
        start_time = st.time_input("Start time", value=datetime.time(10, 0))
    with end_col:
        end_time = st.time_input("End time", value=datetime.time(10, 30))

    mode = st.selectbox("Mode", ["Video", "Call", "In-person", "App message", "Other"])
    location_or_link = st.text_input("Meeting link / phone / location", placeholder="Optional")
    notes = st.text_area("Notes for member", placeholder="Optional instructions for the member", height=90)

    if st.button("Create Schedule / Notify Member", type="primary", use_container_width=True):
        created = create_member_schedule(
            member_id=member_id,
            title=title,
            schedule_type=schedule_type,
            schedule_date=schedule_date.isoformat(),
            start_time=start_time.strftime("%I:%M %p"),
            end_time=end_time.strftime("%I:%M %p"),
            mode=mode,
            location_or_link=location_or_link,
            notes=notes,
            actor_id=st.session_state.get("user_id", "admin"),
        )
        st.success(f"Schedule created and member notification queued. Schedule ID: {created.get('id')}")
        st.rerun()
    card_end()

with right:
    card_start()
    st.subheader("Schedule status")
    rows = list_member_schedules(member_id=member_id, include_cancelled=True, limit=20)
    if not rows:
        st.info("No schedules created for this member yet.")
    else:
        for row in rows:
            status = row.get("status", "scheduled")
            time_text = row.get("start_time", "")
            if row.get("end_time"):
                time_text += f" - {row.get('end_time')}"
            st.markdown(
                f"""
                <div class='hm-schedule-card'>
                  <div class='hm-schedule-title'>{row.get('title','Scheduled session')}<span class='hm-schedule-pill'>{schedule_status_label_v101(status)}</span></div>
                  <div class='hm-schedule-line'>{row.get('schedule_date','')} · {time_text}</div>
                  <div class='hm-schedule-line'>Mode: {row.get('mode','-')} · Link/location: {row.get('location_or_link') or '-'}</div>
                  <div class='hm-schedule-line'>Notes: {row.get('notes') or '-'}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Mark Completed", key=f"schedule_done_{row.get('id')}", use_container_width=True, disabled=status == "completed"):
                    update_member_schedule_status(row.get("id"), "completed", actor_id=st.session_state.get("user_id", "admin"))
                    st.success("Schedule marked completed.")
                    st.rerun()
            with c2:
                if st.button("Cancel", key=f"schedule_cancel_{row.get('id')}", use_container_width=True, disabled=status == "cancelled"):
                    update_member_schedule_status(row.get("id"), "cancelled", actor_id=st.session_state.get("user_id", "admin"))
                    st.warning("Schedule cancelled.")
                    st.rerun()
    card_end()

render_page_nav("Scheduling", back_page="pages/10_Admin_Dashboard.py", show_evaluation=False, location="bottom")
render_back_to_top()

# v101.0: Scheduling section completion build.
