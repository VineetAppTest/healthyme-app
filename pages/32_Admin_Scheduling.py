from components.ui_common import render_page_nav, render_back_to_top
import datetime
import streamlit as st

from components.guards import require_admin
from components.ui_common import (
    inject_global_styles,
    apply_luxe_theme,
    utility_logout_bar,
    render_back_to_top,
    topbar,
    render_page_nav,
)
from components.db import (
    list_members,
    create_member_schedule,
    list_member_schedules,
    update_member_schedule_status,
    schedule_status_label_v101,
    list_reschedule_requests,
    decide_reschedule_request,
    reschedule_policy_text_v1012,
)

st.set_page_config(page_title="Admin Scheduling", page_icon="💚", layout="wide", initial_sidebar_state="collapsed")

inject_global_styles()
apply_luxe_theme()
require_admin()
utility_logout_bar()
topbar("Scheduling", "Create, manage and approve member appointments, follow-ups and reschedule requests.", "Admin workflow")

st.markdown("""
<style>
/* v101.2 Admin Scheduling + Reschedule Review UI */
section.main > div.block-container,
.main .block-container,
[data-testid="stAppViewBlockContainer"],
.stMainBlockContainer,
.block-container{
  max-width:1180px!important;
  padding-top:.72rem!important;
}
.hm-v1011-context-shell{
  border:1px solid #E3C98E;
  background:#FFFDF8;
  border-radius:18px;
  padding:.82rem 1rem;
  margin:.25rem 0 .80rem 0;
  box-shadow:0 8px 20px rgba(15,23,42,.04);
}
.hm-v1011-context-title{
  color:#064E3B;
  font-size:.84rem;
  font-weight:950;
  margin-bottom:.32rem;
  letter-spacing:.01em;
}
.hm-v1011-section-card{
  border:1px solid #E3C98E;
  background:linear-gradient(180deg,#FFFDF8 0%,#FFF9EC 100%);
  border-radius:20px;
  padding:1rem 1.08rem;
  box-shadow:0 10px 24px rgba(15,23,42,.05);
  margin:.40rem 0 .90rem 0;
}
.hm-v1011-section-title{
  color:#003C36;
  font-size:1.12rem;
  font-weight:980;
  margin:0 0 .25rem 0;
}
.hm-v1011-section-sub{
  color:#475569;
  font-size:.86rem;
  font-weight:700;
  margin:0 0 .90rem 0;
}
.hm-v1011-schedule-card,
.hm-v1012-request-card{
  border:1px solid #E3C98E;
  background:#FFFDF8;
  border-radius:16px;
  padding:.82rem .92rem;
  margin:.55rem 0;
  box-shadow:0 8px 18px rgba(15,23,42,.04);
}
.hm-v1011-schedule-title{
  color:#064E3B;
  font-size:.96rem;
  font-weight:950;
  margin-bottom:.18rem;
}
.hm-v1011-schedule-line{
  color:#334155;
  font-size:.83rem;
  font-weight:720;
  margin:.08rem 0;
}
.hm-v1011-pill{
  display:inline-flex;
  padding:.16rem .46rem;
  border-radius:999px;
  border:1px solid #D9C28F;
  background:#FFF7E6;
  color:#7A5A16;
  font-size:.70rem;
  font-weight:850;
  margin-left:.25rem;
}
.hm-v1012-request-warning{
  border:1px solid #E3C98E;
  background:#FFF7E6;
  border-radius:14px;
  padding:.66rem .78rem;
  color:#7A5A16;
  font-size:.82rem;
  font-weight:780;
  margin:.45rem 0;
}
div[data-testid="stButton"] > button{
  min-height:2.72rem!important;
  border-radius:14px!important;
  border:1.25px solid #D9C28F!important;
  background:#FFFDF8!important;
  color:#064E3B!important;
  font-weight:850!important;
  box-shadow:none!important;
}
div[data-testid="stButton"] > button:hover{
  border-color:#B89345!important;
  background:#FFF7E6!important;
}
div[data-testid="stTextInput"] input,
div[data-testid="stTextArea"] textarea,
div[data-testid="stSelectbox"] [data-baseweb="select"] > div,
div[data-testid="stDateInput"] input,
div[data-testid="stTimeInput"] input{
  border-radius:12px!important;
}
</style>
""", unsafe_allow_html=True)

members = list_members()
if not members:
    st.info("No members available.")
    st.stop()

st.markdown("<div class='hm-v1011-context-shell'>", unsafe_allow_html=True)
st.markdown("<div class='hm-v1011-context-title'>Page Context Selector</div>", unsafe_allow_html=True)
member_options = {f"{m.get('name','')} — {m.get('email','')}": m.get("id") for m in members}
selected_label = st.selectbox("Select member", list(member_options.keys()), label_visibility="collapsed")
member_id = member_options[selected_label]
st.markdown("</div>", unsafe_allow_html=True)

left, right = st.columns([1.04, .96], gap="large")

with left:
    st.markdown("<div class='hm-v1011-section-card'>", unsafe_allow_html=True)
    st.markdown("<div class='hm-v1011-section-title'>Create schedule</div>", unsafe_allow_html=True)
    st.markdown("<div class='hm-v1011-section-sub'>Set an appointment, review session or follow-up and notify the member.</div>", unsafe_allow_html=True)

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

    date_col, start_col, end_col = st.columns([1, 1, 1], gap="medium")
    with date_col:
        schedule_date = st.date_input("Date", value=datetime.date.today())
    with start_col:
        start_time = st.time_input("Start time", value=datetime.time(10, 0))
    with end_col:
        end_time = st.time_input("End time", value=datetime.time(10, 30))

    mode_col, link_col = st.columns([.9, 1.4], gap="medium")
    with mode_col:
        mode = st.selectbox("Mode", ["Video", "Call", "In-person", "App message", "Other"])
    with link_col:
        location_or_link = st.text_input("Meeting link / phone / location", placeholder="Optional")

    notes = st.text_area("Notes for member", placeholder="Optional instructions for the member", height=100)

    if st.button("Create Schedule / Notify Member", use_container_width=True):
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

    st.markdown("</div>", unsafe_allow_html=True)

with right:
    st.markdown("<div class='hm-v1011-section-card'>", unsafe_allow_html=True)
    st.markdown("<div class='hm-v1011-section-title'>Schedule status</div>", unsafe_allow_html=True)
    st.markdown("<div class='hm-v1011-section-sub'>Track upcoming, acknowledged, completed, cancelled and rescheduled sessions.</div>", unsafe_allow_html=True)

    rows = list_member_schedules(member_id=member_id, include_cancelled=True, limit=20)
    if not rows:
        st.info("No schedules created for this member yet.")
    else:
        for row in rows:
            status = row.get("status", "scheduled")
            time_text = row.get("start_time", "")
            if row.get("end_time"):
                time_text += f" - {row.get('end_time')}"
            counted_note = " · Prior session counted" if row.get("session_counted") else ""
            st.markdown(
                f"""
                <div class='hm-v1011-schedule-card'>
                  <div class='hm-v1011-schedule-title'>{row.get('title','Scheduled session')}<span class='hm-v1011-pill'>{schedule_status_label_v101(status)}</span></div>
                  <div class='hm-v1011-schedule-line'>{row.get('schedule_date','')} · {time_text}{counted_note}</div>
                  <div class='hm-v1011-schedule-line'>Mode: {row.get('mode','-')} · Link/location: {row.get('location_or_link') or '-'}</div>
                  <div class='hm-v1011-schedule-line'>Notes: {row.get('notes') or '-'}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            c1, c2 = st.columns(2, gap="medium")
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

    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div class='hm-v1011-section-card'>", unsafe_allow_html=True)
st.markdown("<div class='hm-v1011-section-title'>Reschedule requests</div>", unsafe_allow_html=True)
st.markdown("<div class='hm-v1011-section-sub'>Approve or reject member-requested schedule changes. The 24-hour rule is shown for each request.</div>", unsafe_allow_html=True)

requests_v1012 = list_reschedule_requests(member_id=member_id, status=None, limit=30)
if not requests_v1012:
    st.info("No reschedule requests for this member.")
else:
    for req_v1012 in requests_v1012:
        status_v1012 = req_v1012.get("status", "pending")
        st.markdown(
            f"""
            <div class='hm-v1012-request-card'>
              <div class='hm-v1011-schedule-title'>{req_v1012.get('current_title','Scheduled session')}<span class='hm-v1011-pill'>{status_v1012.title()}</span></div>
              <div class='hm-v1011-schedule-line'>Current: {req_v1012.get('current_date','')} · {req_v1012.get('current_start_time','')}</div>
              <div class='hm-v1011-schedule-line'>Requested: {req_v1012.get('requested_date','')} · {req_v1012.get('requested_start_time','')} - {req_v1012.get('requested_end_time','')}</div>
              <div class='hm-v1011-schedule-line'>Reason: {req_v1012.get('reason') or '-'}</div>
            </div>
            <div class='hm-v1012-request-warning'>{reschedule_policy_text_v1012(bool(req_v1012.get('within_24_hours')))}</div>
            """,
            unsafe_allow_html=True,
        )
        admin_note_v1012 = st.text_input(
            "Admin note",
            key=f"reschedule_admin_note_{req_v1012.get('id')}",
            placeholder="Optional note to member",
            disabled=status_v1012 != "pending",
        )
        approve_col_v1012, reject_col_v1012 = st.columns(2, gap="medium")
        with approve_col_v1012:
            if st.button(
                "Approve Reschedule",
                key=f"approve_reschedule_{req_v1012.get('id')}",
                use_container_width=True,
                disabled=status_v1012 != "pending",
            ):
                decide_reschedule_request(
                    req_v1012.get("id"),
                    "approved",
                    admin_note=admin_note_v1012,
                    actor_id=st.session_state.get("user_id", "admin"),
                )
                st.success("Reschedule approved and member notified.")
                st.rerun()
        with reject_col_v1012:
            if st.button(
                "Reject Request",
                key=f"reject_reschedule_{req_v1012.get('id')}",
                use_container_width=True,
                disabled=status_v1012 != "pending",
            ):
                decide_reschedule_request(
                    req_v1012.get("id"),
                    "rejected",
                    admin_note=admin_note_v1012,
                    actor_id=st.session_state.get("user_id", "admin"),
                )
                st.warning("Reschedule request rejected and member notified.")
                st.rerun()

st.markdown("</div>", unsafe_allow_html=True)


# v101.2: Scheduling page includes admin reschedule review.

# v102.0: canonical global footer navigation

# v102.1: single canonical footer navigation only
render_page_nav("Scheduling", back_page="pages/10_Admin_Dashboard.py", dashboard_page="pages/10_Admin_Dashboard.py", show_evaluation=False, show_dashboard=True, location="bottom")
render_back_to_top()
