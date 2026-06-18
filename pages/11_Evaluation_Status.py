from components.ui_common import render_page_nav, render_back_to_top
import streamlit as st
import pandas as pd

from components.guards import require_admin
from components.ui_common import (
    inject_global_styles,
    apply_luxe_theme,
    utility_logout_bar,
    topbar,
    stat_grid,
    render_page_nav,
    render_back_to_top,
)
from components.db import list_members

st.set_page_config(page_title="Eval Status", page_icon="💚", layout="wide", initial_sidebar_state="collapsed")

inject_global_styles()
apply_luxe_theme()
require_admin()
utility_logout_bar()
topbar(
    "Evaluation Status of All Members",
    "Track member progress, then continue admin assessment from the selected member action buttons.",
    "Review workflow",
)

st.markdown("""
<style>
/* v101.8 Evaluation Status action flow */
.member-filter-panel{
  border:1px solid #E3C98E;
  background:#FFFDF8;
  border-radius:18px;
  padding:.95rem 1rem;
  margin:.65rem 0 .85rem 0;
  box-shadow:0 8px 20px rgba(15,23,42,.04);
}
.eval-section-title{
  color:#064E3B;
  font-size:1.02rem;
  font-weight:950;
  margin:.85rem 0 .36rem 0;
}
.eval-section-note{
  color:#475569;
  font-size:.88rem;
  font-weight:700;
  margin:0 0 .70rem 0;
}
.member-count-pill{
  display:inline-flex;
  padding:.22rem .56rem;
  border-radius:999px;
  background:#FFF7E6;
  border:1px solid #E3C98E;
  color:#7A5A16;
  font-size:.78rem;
  font-weight:850;
  margin:.25rem 0 .70rem 0;
}
.member-detail-panel{
  border:1px solid #E3C98E;
  background:linear-gradient(180deg,#FFFDF8 0%,#FFF9EC 100%);
  border-radius:20px;
  padding:1rem 1.08rem;
  box-shadow:0 10px 24px rgba(15,23,42,.05);
  margin:.50rem 0 .95rem 0;
}
.eval-status-grid{
  display:grid;
  grid-template-columns:repeat(3,minmax(0,1fr));
  gap:.65rem;
  margin:.55rem 0 .85rem 0;
}
.eval-status-card{
  border:1px solid #E3C98E;
  background:#FFFDF8;
  border-radius:16px;
  padding:.78rem .9rem;
}
.eval-status-label{
  color:#64748B;
  font-size:.74rem;
  text-transform:uppercase;
  font-weight:850;
}
.eval-status-value{
  color:#064E3B;
  font-size:1.02rem;
  font-weight:950;
  margin-top:.12rem;
}
@media(max-width:768px){
  .eval-status-grid{grid-template-columns:1fr;}
}
</style>
""", unsafe_allow_html=True)

def pretty_status(raw):
    return (raw or "not_started").replace("_", " ").title()

def state_text(done):
    return "Done" if done else "Pending"

def next_action(member):
    if member.get("final_report_ready"):
        return "View Final Report"
    if member.get("submitted") or member.get("nsp1_completed") or member.get("nsp2_completed"):
        return "Continue Admin Assessment"
    if member.get("laf_completed"):
        return "Wait for NSP Completion"
    return "Await Member Submission"

rows = list_members()
total = len(rows)
submitted = sum(1 for m in rows if m.get("submitted"))
in_progress = sum(1 for m in rows if m.get("workflow_status") == "in_progress")
final_ready = sum(1 for m in rows if m.get("final_report_ready"))

stat_grid([
    {"label": "Members", "value": total, "note": "Total member records"},
    {"label": "Submitted", "value": submitted, "note": "Awaiting review"},
    {"label": "In Progress", "value": in_progress, "note": "Assessment underway"},
    {"label": "Final Ready", "value": final_ready, "note": "Reports available"},
])

st.markdown("<div class='member-filter-panel'>", unsafe_allow_html=True)
filter_col, member_col = st.columns([1, 2], gap="medium")
with filter_col:
    status_options = ["All", "Not Started", "In Progress", "Submitted", "Admin Completed", "Finalized"]
    status_filter = st.selectbox("Status filter", status_options)
filtered = rows
if status_filter != "All":
    filtered = [m for m in filtered if pretty_status(m.get("workflow_status")) == status_filter]

with member_col:
    member_labels = ["Select member"] + [f"{m.get('name','')} — {m.get('email','')}" for m in filtered]
    selected_label = st.selectbox("Select member to continue admin assessment", member_labels)

st.markdown("</div>", unsafe_allow_html=True)
st.markdown(f"<div class='member-count-pill'>{len(filtered)} member(s) shown</div>", unsafe_allow_html=True)

if not filtered:
    st.info("No members match the selected status filter.")
else:
    preview = pd.DataFrame([
        {
            "Name": m["name"],
            "Email": m["email"],
            "LAF": state_text(m.get("laf_completed")),
            "NSP1": state_text(m.get("nsp1_completed")),
            "NSP2": state_text(m.get("nsp2_completed")),
            "Status": pretty_status(m.get("workflow_status")),
            "Final": "Ready" if m.get("final_report_ready") else "Pending",
            "Next Action": next_action(m),
        }
        for m in filtered
    ])
    st.markdown("<div class='eval-section-title'>Member Overview</div>", unsafe_allow_html=True)
    st.dataframe(preview, use_container_width=True, hide_index=True)

if selected_label != "Select member":
    selected_member = filtered[member_labels.index(selected_label) - 1]
    st.session_state["selected_member_id"] = selected_member.get("id")
    st.session_state["selected_member_email"] = selected_member.get("email")
    st.session_state["selected_member_name"] = selected_member.get("name")

    st.markdown("<div class='eval-section-title'>Select Member to Continue Admin Assessment</div>", unsafe_allow_html=True)
    st.markdown("<div class='eval-section-note'>Use the buttons below to open the required workflow directly. This replaces the old expand/collapse member detail flow.</div>", unsafe_allow_html=True)

    st.markdown("<div class='member-detail-panel'>", unsafe_allow_html=True)
    st.subheader(selected_member.get("name", "Selected member"))
    st.caption(selected_member.get("email", ""))

    st.markdown(
        f"""
        <div class='eval-status-grid'>
          <div class='eval-status-card'><div class='eval-status-label'>LAF</div><div class='eval-status-value'>{state_text(selected_member.get("laf_completed"))}</div></div>
          <div class='eval-status-card'><div class='eval-status-label'>NSP Page 1</div><div class='eval-status-value'>{state_text(selected_member.get("nsp1_completed"))}</div></div>
          <div class='eval-status-card'><div class='eval-status-label'>NSP Page 2</div><div class='eval-status-value'>{state_text(selected_member.get("nsp2_completed"))}</div></div>
          <div class='eval-status-card'><div class='eval-status-label'>Workflow Status</div><div class='eval-status-value'>{pretty_status(selected_member.get("workflow_status"))}</div></div>
          <div class='eval-status-card'><div class='eval-status-label'>Final Report</div><div class='eval-status-value'>{'Ready' if selected_member.get("final_report_ready") else 'Pending'}</div></div>
          <div class='eval-status-card'><div class='eval-status-label'>Next Action</div><div class='eval-status-value'>{next_action(selected_member)}</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    b1, b2, b3, b4 = st.columns(4, gap="medium")
    with b1:
        if st.button("Partial Report", key="eval_v1018_partial", use_container_width=True):
            st.switch_page("pages/12_Partial_Assessment_Report.py")
    with b2:
        if st.button("Admin Page", key="eval_v1018_admin", use_container_width=True):
            st.switch_page("pages/13_Admin_Assessment_Form.py")
    with b3:
        if st.button("Full Report", key="eval_v1018_full", use_container_width=True):
            st.switch_page("pages/14_Final_Assessment_Report.py")
    with b4:
        if st.button("Daily Logs", key="eval_v1018_daily", use_container_width=True):
            st.session_state["selected_daily_log_member_id"] = selected_member.get("id")
            st.switch_page("pages/22_Admin_Daily_Log_Report.py")

    st.markdown("</div>", unsafe_allow_html=True)

render_page_nav("Eval Status", back_page="pages/10_Admin_Dashboard.py", show_evaluation=False, show_dashboard=True, location="bottom")
render_back_to_top()

# v101.8: Evaluation Status dropdown and direct action flow.
