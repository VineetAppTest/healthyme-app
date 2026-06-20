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
    schedule_display_status_label_v104b11,
    list_admin_open_schedules_v104b12,
    list_reschedule_requests,
    decide_reschedule_request,
    reschedule_policy_text_v1012,
    get_member_session_ledger_v1024b13,
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
.hm-b13-flash-ok{border:1px solid #B7DEC5;background:#EEF9F1;color:#14532D;border-radius:14px;padding:.72rem .86rem;margin:.45rem 0 .80rem 0;font-weight:650;}
.hm-b13-flash-error{border:1px solid #F0B4A5;background:#FFF2EE;color:#9A3412;border-radius:14px;padding:.72rem .86rem;margin:.45rem 0 .80rem 0;font-weight:650;}
.hm-b13-ledger-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:.7rem;margin:.45rem 0 1rem 0;}
.hm-b13-ledger-kpi{border:1px solid #E3C98E;background:#FFFDF8;border-radius:16px;padding:.75rem .85rem;}
.hm-b13-ledger-kpi b{display:block;color:#064E3B;font-size:1.25rem;margin-top:.12rem;}
.hm-b13-ledger-table{border:1px solid #E3C98E;border-radius:16px;overflow:hidden;background:#FFFDF8;margin:.35rem 0;}
.hm-b13-ledger-row{display:grid;grid-template-columns:1.3fr .9fr .85fr .75fr .75fr;gap:.5rem;padding:.62rem .72rem;border-top:1px solid #F0E3C5;align-items:center;font-size:.82rem;}
.hm-b13-ledger-head{background:#FFF7E6;border-top:0;font-weight:760;color:#064E3B;}
.hm-b13-consumed{color:#166534;font-weight:700;}
.hm-b13-notconsumed{color:#64748B;font-weight:600;}
div[data-testid="stButton"] > button{
  min-height:2.72rem!important;
  border-radius:14px!important;
  border:1.25px solid #D9C28F!important;
  background:#FFFDF8!important;
  color:#064E3B!important;
  font-weight:500!important;
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

# v102.4B13: durable admin action feedback after rerun.
_flash = st.session_state.pop('hm_b13_schedule_flash', None)
if _flash:
    _klass = 'hm-b13-flash-ok' if _flash.get('kind') == 'success' else 'hm-b13-flash-error'
    st.markdown(f"<div class='{_klass}'>{_flash.get('message','')}</div>", unsafe_allow_html=True)

open_schedule_count_v104b12 = len(list_admin_open_schedules_v104b12(member_id=member_id, limit=0))
pending_reschedule_count_v104b12 = len(list_reschedule_requests(member_id=member_id, status="pending", limit=0))

tab_create, tab_status, tab_reschedule, tab_ledger = st.tabs([
    "Create Schedule",
    f"Schedule Status ({open_schedule_count_v104b12})" if open_schedule_count_v104b12 else "Schedule Status",
    f"Reschedule Status ({pending_reschedule_count_v104b12})" if pending_reschedule_count_v104b12 else "Reschedule Status",
    "Session Ledger",
])

with tab_create:
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

    cost_col, _cost_spacer = st.columns([0.55, 1.45], gap="medium")
    with cost_col:
        session_cost = st.number_input("Session cost", min_value=0.0, value=0.0, step=100.0, format="%.2f")

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
            session_cost=session_cost,
        )
        if created and isinstance(created, dict) and created.get("error"):
            st.session_state["hm_b13_schedule_flash"] = {"kind": "error", "message": created.get("error")}
        else:
            st.session_state["hm_b13_schedule_flash"] = {"kind": "success", "message": "Schedule created successfully and shared with the member."}
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

with tab_status:
    st.markdown("<div class='hm-v1011-section-card'>", unsafe_allow_html=True)
    st.markdown("<div class='hm-v1011-section-title'>Schedule status</div>", unsafe_allow_html=True)
    st.markdown("<div class='hm-v1011-section-sub'>Track upcoming, acknowledged, completed, cancelled and rescheduled sessions. Closed rows are shown for admin history only.</div>", unsafe_allow_html=True)

    rows = list_member_schedules(member_id=member_id, include_cancelled=True, limit=30)
    if not rows:
        st.info("No schedules created for this member yet.")
    else:
        for row in rows:
            status = str(row.get("status", "scheduled") or "scheduled").lower().strip()
            time_text = row.get("start_time", "")
            if row.get("end_time"):
                time_text += f" - {row.get('end_time')}"
            counted_note = " · Prior session counted" if row.get("session_counted") else ""
            st.markdown(
                f"""
                <div class='hm-v1011-schedule-card'>
                  <div class='hm-v1011-schedule-title'>{row.get('title','Scheduled session')}<span class='hm-v1011-pill'>{schedule_display_status_label_v104b11(row)}</span></div>
                  <div class='hm-v1011-schedule-line'>{row.get('schedule_date','')} · {time_text}{counted_note}</div>
                  <div class='hm-v1011-schedule-line'>Mode: {row.get('mode','-')} · Link/location: {row.get('location_or_link') or '-'}</div>
                  <div class='hm-v1011-schedule-line'>Notes: {row.get('notes') or '-'}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if status in {"scheduled", "acknowledged"}:
                c1, c2 = st.columns(2, gap="medium")
                with c1:
                    if st.button("Mark Completed", key=f"schedule_done_{row.get('id')}", use_container_width=True):
                        update_member_schedule_status(row.get("id"), "completed", actor_id=st.session_state.get("user_id", "admin"))
                        st.success("Schedule marked completed.")
                        st.rerun()
                with c2:
                    if st.button("Cancel", key=f"schedule_cancel_{row.get('id')}", use_container_width=True):
                        update_member_schedule_status(row.get("id"), "cancelled", actor_id=st.session_state.get("user_id", "admin"))
                        st.warning("Schedule cancelled.")
                        st.rerun()
            else:
                st.caption("Closed schedule — no action available.")

    st.markdown("</div>", unsafe_allow_html=True)

with tab_reschedule:
    st.markdown("<div class='hm-v1011-section-card'>", unsafe_allow_html=True)
    st.markdown("<div class='hm-v1011-section-title'>Reschedule status</div>", unsafe_allow_html=True)
    st.markdown("<div class='hm-v1011-section-sub'>Approve or reject member-requested schedule changes. Pending requests are counted in the tab title.</div>", unsafe_allow_html=True)

    requests_v1012 = list_reschedule_requests(member_id=member_id, status=None, limit=30)
    if not requests_v1012:
        st.info("No reschedule requests for this member.")
    else:
        for req_v1012 in requests_v1012:
            status_v1012 = req_v1012.get("status", "pending")
            requested_date_text_v104b12 = str(req_v1012.get("requested_date", "") or "")[:10]
            requested_in_past_v104b12 = False
            try:
                requested_in_past_v104b12 = bool(requested_date_text_v104b12 and datetime.date.fromisoformat(requested_date_text_v104b12) < datetime.date.today())
            except Exception:
                requested_in_past_v104b12 = False
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
            if requested_in_past_v104b12 and status_v1012 == "pending":
                st.error("This requested date is already in the past. Ask the member to submit a fresh future date or reject this request.")
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
                    disabled=status_v1012 != "pending" or requested_in_past_v104b12,
                ):
                    result_v104b12 = decide_reschedule_request(
                        req_v1012.get("id"),
                        "approved",
                        admin_note=admin_note_v1012,
                        actor_id=st.session_state.get("user_id", "admin"),
                    )
                    if result_v104b12 and result_v104b12.get("error"):
                        st.error(result_v104b12.get("error"))
                    else:
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


with tab_ledger:
    st.markdown("<div class='hm-v1011-section-card'>", unsafe_allow_html=True)
    st.markdown("<div class='hm-v1011-section-title'>Session ledger</div>", unsafe_allow_html=True)
    st.markdown("<div class='hm-v1011-section-sub'>Scheduler-controlled session usage and cost view for the selected member.</div>", unsafe_allow_html=True)
    ledger_v1024b13 = get_member_session_ledger_v1024b13(member_id)
    rows_v1024b13 = ledger_v1024b13.get("rows", [])
    total_sessions_v1024b13 = len(rows_v1024b13)
    consumed_v1024b13 = ledger_v1024b13.get("consumed_count", 0)
    consumed_cost_v1024b13 = ledger_v1024b13.get("consumed_cost", 0)
    st.markdown(
        f"""
        <div class='hm-b13-ledger-grid'>
          <div class='hm-b13-ledger-kpi'>Total scheduled<b>{total_sessions_v1024b13}</b></div>
          <div class='hm-b13-ledger-kpi'>Sessions consumed<b>{consumed_v1024b13}</b></div>
          <div class='hm-b13-ledger-kpi'>Consumed cost<b>₹{consumed_cost_v1024b13:,.2f}</b></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if not rows_v1024b13:
        st.info("No sessions have been scheduled for this member yet.")
    else:
        st.markdown("<div class='hm-b13-ledger-table'>", unsafe_allow_html=True)
        st.markdown("<div class='hm-b13-ledger-row hm-b13-ledger-head'><div>Session</div><div>Date</div><div>Time</div><div>Cost</div><div>Usage</div></div>", unsafe_allow_html=True)
        for r in rows_v1024b13:
            usage_class = "hm-b13-consumed" if r.get("consumed") else "hm-b13-notconsumed"
            usage_text = "Consumed" if r.get("consumed") else "Open / not consumed"
            st.markdown(
                f"<div class='hm-b13-ledger-row'><div>{r.get('title','Session')}<br><small>{r.get('status','')}</small></div><div>{r.get('date','')}</div><div>{r.get('time','')}</div><div>₹{r.get('cost',0):,.2f}</div><div class='{usage_class}'>{usage_text}</div></div>",
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


# v101.2: Scheduling page includes admin reschedule review.

# v102.0: canonical global footer navigation

# v102.1: single canonical footer navigation only
render_page_nav("Scheduling", back_page="pages/10_Admin_Dashboard.py", dashboard_page="pages/10_Admin_Dashboard.py", show_evaluation=False, show_dashboard=True, location="bottom")
render_back_to_top()
