import streamlit as st
import pandas as pd
from components.guards import require_admin
from components.ui_common import inject_global_styles, apply_luxe_theme, topbar, utility_logout_bar, stat_grid, render_page_nav, render_build_text_v15, render_back_to_top
from components.db import list_members

st.set_page_config(page_title="Eval Status", page_icon="💚", layout="wide", initial_sidebar_state="collapsed")
inject_global_styles(); apply_luxe_theme(); require_admin(); utility_logout_bar(); render_back_to_top()

st.markdown("""
<style>
/* --- v95.6 Evaluation Status fixed action grid --- */

/* Member toggle rows */
.hm-v95-6-member-list-anchor ~ div div[data-testid="stButton"] > button{
  background:#FFFFFF!important;
  color:#064E3B!important;
  border:1.4px solid #CDBB8F!important;
  border-radius:14px!important;
  min-height:44px!important;
  height:44px!important;
  padding:0 1rem!important;
  display:flex!important;
  align-items:center!important;
  justify-content:center!important;
  font-weight:850!important;
  box-shadow:0 4px 12px rgba(25,36,31,.055)!important;
  line-height:1.1!important;
}
.hm-v95-6-member-list-anchor ~ div div[data-testid="stButton"] > button *{
  color:#064E3B!important;
  line-height:1.1!important;
}

/* The opened-member action row is now forced into a fixed 4-column grid. */
.hm-v95-6-action-grid-anchor + div [data-testid="stHorizontalBlock"]{
  display:grid!important;
  grid-template-columns:repeat(4, minmax(0, 1fr))!important;
  gap:1rem!important;
  align-items:stretch!important;
  width:100%!important;
  margin:.2rem 0 .45rem 0!important;
}
.hm-v95-6-action-grid-anchor + div [data-testid="stHorizontalBlock"] > div[data-testid="column"]{
  width:100%!important;
  min-width:0!important;
  max-width:none!important;
  flex:unset!important;
  display:block!important;
}
.hm-v95-6-action-grid-anchor + div [data-testid="stHorizontalBlock"] > div[data-testid="column"] > div,
.hm-v95-6-action-grid-anchor + div div[data-testid="stButton"]{
  width:100%!important;
}
.hm-v95-6-action-grid-anchor + div div[data-testid="stButton"] > button{
  width:100%!important;
  min-width:100%!important;
  max-width:100%!important;
  min-height:48px!important;
  height:48px!important;
  max-height:48px!important;
  padding:0 1rem!important;
  border-radius:14px!important;
  display:flex!important;
  align-items:center!important;
  justify-content:center!important;
  white-space:nowrap!important;
  line-height:1.1!important;
  font-weight:850!important;
  box-sizing:border-box!important;
  background:linear-gradient(135deg,#064E3B 0%,#0F766E 100%)!important;
  color:#FFFFFF!important;
  border:1px solid #064E3B!important;
  box-shadow:0 8px 18px rgba(6,78,59,.13)!important;
}
.hm-v95-6-action-grid-anchor + div div[data-testid="stButton"] > button *{
  color:#FFFFFF!important;
  line-height:1.1!important;
}

.hm-v95-6-instruction{
  color:#102A43;
  font-size:.96rem;
  margin:.15rem 0 .65rem 0;
}

@media(max-width:768px){
  .hm-v95-6-action-grid-anchor + div [data-testid="stHorizontalBlock"]{
    grid-template-columns:1fr 1fr!important;
    gap:.65rem!important;
  }
}
</style>
""", unsafe_allow_html=True)



render_build_text_v15()

rows = list_members()

render_page_nav("Eval Status", back_page="pages/10_Admin_Dashboard.py", show_evaluation=False, location="top")

topbar(
    "Evaluation Status of All Members",
    "Track member progress, then open a member row below to continue admin assessment.",
    "Review workflow"
)

def pretty_status(raw):
    return (raw or "not_started").replace("_", " ").title()

def state_text(done):
    return "Done" if done else "Pending"

def card_class(done):
    return "eval-ok" if done else "eval-warn"

def next_action(member):
    if member.get("final_report_ready"):
        return "View Final Report"
    if member.get("submitted") or member.get("nsp1_completed") or member.get("nsp2_completed"):
        return "Continue Admin Assessment"
    if member.get("laf_completed"):
        return "Wait for NSP Completion"
    return "Await Member Submission"

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

st.markdown(
    """
    <div class='member-filter-panel'>
      <b>Find members faster</b><br>
      <span style='color:var(--hm-muted);font-size:.9rem;'>Search by name/email and filter by workflow status.</span>
    </div>
    """,
    unsafe_allow_html=True,
)

f1, f2 = st.columns([2, 1])
with f1:
    search = st.text_input(
        "Search members",
        placeholder="Type member name or email",
        label_visibility="collapsed"
    )
with f2:
    status_options = ["All", "Not Started", "In Progress", "Submitted", "Admin Completed", "Finalized"]
    status_filter = st.selectbox("Status filter", status_options, label_visibility="collapsed")

filtered = rows

if search.strip():
    q = search.strip().lower()
    filtered = [
        m for m in filtered
        if q in m.get("name", "").lower() or q in m.get("email", "").lower()
    ]

if status_filter != "All":
    filtered = [
        m for m in filtered
        if pretty_status(m.get("workflow_status")) == status_filter
    ]

st.markdown(f"<div class='member-count-pill'>{len(filtered)} member(s) shown</div>", unsafe_allow_html=True)

if "open_member_id" not in st.session_state:
    st.session_state["open_member_id"] = None

if not filtered:
    st.info("No members match the selected search/filter.")
else:
    st.markdown("<div class='eval-section-title'>Member Overview</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='eval-section-note'>This table is for quick status tracking only. Admin actions are available in the member rows below.</div>",
        unsafe_allow_html=True
    )

    preview = pd.DataFrame([
        {
            "Name": m["name"],
            "Email": m["email"],
            "LAF": state_text(m["laf_completed"]),
            "NSP1": state_text(m["nsp1_completed"]),
            "NSP2": state_text(m["nsp2_completed"]),
            "Status": pretty_status(m["workflow_status"]),
            "Final": "Ready" if m["final_report_ready"] else "Pending",
            "Next Action": next_action(m),
        }
        for m in filtered
    ])
    st.dataframe(preview, use_container_width=True, hide_index=True)

    st.markdown(
        """
        <div class='eval-helper-box'>
          <b>How to fill the 5 admin assessment pages:</b><br>
          Open a member below and click <b>Fill Admin Page</b>. The admin assessment form contains the admin sections/questions and allows saving draft or generating the final report.
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("<div class='eval-section-title'>Select Member to Continue Admin Assessment</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='eval-section-note'>Click a member name to open details. Click the same member again to close it.</div>",
        unsafe_allow_html=True
    )

    for member in filtered:
        is_open = st.session_state.get("open_member_id") == member["id"]
        toggle_label = f"{'[−]' if is_open else '[+]'}  {member['name']}"

        if st.button(toggle_label, key=f"toggle_{member['id']}", use_container_width=True):
            if is_open:
                st.session_state["open_member_id"] = None
            else:
                st.session_state["open_member_id"] = member["id"]
            st.rerun()

        if is_open:
            st.markdown("<div class='member-detail-panel'>", unsafe_allow_html=True)
            st.markdown(
                f"""
                <div class='member-row-header'>
                  <div>
                    <div class='member-row-name'>{member['name']}</div>
                    <div class='member-row-email'>{member['email']}</div>
                  </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            laf_cls = card_class(member["laf_completed"])
            nsp1_cls = card_class(member["nsp1_completed"])
            nsp2_cls = card_class(member["nsp2_completed"])
            final_cls = "eval-gold" if member["final_report_ready"] else "eval-warn"
            status = pretty_status(member["workflow_status"])

            st.markdown(
                f"""
                <div class='eval-status-grid'>
                  <div class='eval-status-card {laf_cls}'>
                    <div class='eval-status-label'>LAF</div>
                    <div class='eval-status-value'>{state_text(member["laf_completed"])}</div>
                  </div>
                  <div class='eval-status-card {nsp1_cls}'>
                    <div class='eval-status-label'>NSP Page 1</div>
                    <div class='eval-status-value'>{state_text(member["nsp1_completed"])}</div>
                  </div>
                  <div class='eval-status-card {nsp2_cls}'>
                    <div class='eval-status-label'>NSP Page 2</div>
                    <div class='eval-status-value'>{state_text(member["nsp2_completed"])}</div>
                  </div>
                  <div class='eval-status-card eval-info'>
                    <div class='eval-status-label'>Workflow Status</div>
                    <div class='eval-status-value'>{status}</div>
                  </div>
                  <div class='eval-status-card {final_cls}'>
                    <div class='eval-status-label'>Final Report</div>
                    <div class='eval-status-value'>{'Ready' if member["final_report_ready"] else 'Pending'}</div>
                  </div>
                  <div class='eval-status-card eval-info'>
                    <div class='eval-status-label'>Next Action</div>
                    <div class='eval-status-value'>{next_action(member)}</div>
                  </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            st.markdown(
                "<div class='eval-section-note hm-v95-6-instruction'>Use the buttons below to continue work for this selected member.</div>",
                unsafe_allow_html=True
            )

            st.markdown("<div class='hm-v95-6-action-grid-anchor'></div>", unsafe_allow_html=True)
            b1, b2, b3, b4 = st.columns(4)
            with b1:
                if st.button("Partial Report", key=f"pr_{member['id']}", type="primary", use_container_width=True):
                    st.session_state["selected_member_id"] = member["id"]
                    st.switch_page("pages/12_Partial_Assessment_Report.py")
            with b2:
                if st.button("Admin Page", key=f"ap_{member['id']}", type="primary", use_container_width=True):
                    st.session_state["selected_member_id"] = member["id"]
                    st.switch_page("pages/13_Admin_Assessment_Form.py")
            with b3:
                # v95.1: Keep Full Report button clickable and visually consistent.
                # If the report is not ready, the Final Report page will show the proper pending message.
                if st.button("Full Report", help="Open final assessment report", key=f"fr_{member['id']}", type="primary", use_container_width=True):
                    st.session_state["selected_member_id"] = member["id"]
                    st.switch_page("pages/14_Final_Assessment_Report.py")

            with b4:
                if st.button("Daily Logs", key=f"dl_{member['id']}", type="primary", use_container_width=True):
                    st.session_state["selected_member_id"] = member["id"]
                    st.session_state["selected_daily_log_member_id"] = member["id"]
                    st.switch_page("pages/22_Admin_Daily_Log_Report.py")

render_page_nav("Eval Status", back_page="pages/10_Admin_Dashboard.py", show_evaluation=False, location="bottom")