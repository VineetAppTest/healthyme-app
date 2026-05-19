
import streamlit as st
from components.guards import require_admin
from components.ui_common import inject_global_styles, apply_luxe_theme, topbar, stat_grid, utility_logout_bar, render_build_text_v14
from components.db import get_admin_dashboard_snapshot
from components.flash import render_system_message
from components.storage_backend import get_storage_status

st.set_page_config(page_title="Admin Dashboard", page_icon="💚", layout="wide", initial_sidebar_state="collapsed")
inject_global_styles(); apply_luxe_theme(); require_admin(); utility_logout_bar()

@st.cache_data(show_spinner=False, ttl=90)
def cached_dashboard_snapshot():
    return get_admin_dashboard_snapshot()

@st.cache_data(show_spinner=False, ttl=180)
def cached_storage_status():
    return get_storage_status(force_check=False)

snapshot = cached_dashboard_snapshot()
member_count = snapshot["member_count"]
initial_pending = snapshot["initial_pending"]
reassess_pending = snapshot["reassess_pending"]
finalized_count = snapshot["finalized_count"]
db_status = cached_storage_status()

render_build_text_v14()
topbar("Admin Dashboard", "Daily review, assessment, allocation, and communication command center.", "Admin")
render_system_message()

if db_status.get("mode") != "SUPABASE":
    st.warning("Database is running in local fallback mode. Verify Supabase before production use.")

stat_grid([
    {"label": "Members", "value": member_count, "note": "Member accounts"},
    {"label": "Initial Reviews", "value": len(initial_pending), "note": "Pending review"},
    {"label": "Reassessments", "value": len(reassess_pending), "note": "Follow-up review"},
    {"label": "Finalized", "value": finalized_count, "note": "Reports ready"},
])

st.subheader("Today's Priority")

def priority_card(kicker, number, button, page, key, micro, help_text):
    with st.container(border=True):
        st.markdown("<div class='hm-v14-priority-card'>", unsafe_allow_html=True)
        st.markdown(
            f"""
            <div class='hm-v14-kicker'>{kicker}</div>
            <div class='hm-v14-number'>{number}</div>
            """,
            unsafe_allow_html=True,
        )
        if st.button(button, key=key, use_container_width=True, help=help_text):
            st.switch_page(page)
        st.markdown(f"<div class='hm-v14-micro'>{micro}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

p1, p2, p3 = st.columns(3, gap="medium")
with p1:
    priority_card(
        "Initial Reviews",
        len(initial_pending),
        "Review Queue",
        "pages/26_Admin_Review_Queue.py",
        "v14_priority_review",
        "Pending admin review",
        "Open submitted assessments waiting for admin review.",
    )
with p2:
    priority_card(
        "Final Reports",
        finalized_count,
        "Evaluation Status",
        "pages/11_Evaluation_Status.py",
        "v14_priority_eval",
        "Reports and member status",
        "Open all-member evaluation status and final report access.",
    )
with p3:
    priority_card(
        "Reassessments",
        len(reassess_pending),
        "Reassessments",
        "pages/25_Admin_Reassessment_Manager.py",
        "v14_priority_reassess",
        "Follow-up review",
        "Open reassessment manager for follow-up NSP submissions.",
    )

st.subheader("Main Workflows")

def workflow_card(title, actions):
    with st.container(border=True):
        st.markdown("<div class='hm-v14-workflow-card'>", unsafe_allow_html=True)
        st.markdown(f"<div class='hm-v14-workflow-title'>{title}</div>", unsafe_allow_html=True)
        for label, page, key, help_text in actions:
            if st.button(label, key=key, use_container_width=True, help=help_text):
                st.switch_page(page)
        st.markdown("</div>", unsafe_allow_html=True)

w1, w2 = st.columns(2, gap="medium")
with w1:
    workflow_card("Review & Assessment", [
        ("Review Queue", "pages/26_Admin_Review_Queue.py", "v14_review_queue", "Review newly submitted assessments."),
        ("Evaluation Status", "pages/11_Evaluation_Status.py", "v14_eval_status", "See all member statuses and open reports."),
        ("Reassessments", "pages/25_Admin_Reassessment_Manager.py", "v14_reassess", "Manage follow-up submissions."),
        ("NSP Compare", "pages/27_Comparative_NSP_Report.py", "v14_compare", "Compare NSP progress."),
    ])

with w2:
    workflow_card("Member & Access", [
        ("Create Users", "pages/17_Admin_User_Manager.py", "v14_users", "Create members and admins."),
        ("Access Manager", "pages/30_Admin_User_Access_Manager.py", "v14_access", "Deactivate/reactivate users."),
        ("Body-Mind Access", "pages/23_Admin_Body_Mind_Control.py", "v14_bodymind", "Control content visibility."),
    ])

w3, w4 = st.columns(2, gap="medium")
with w3:
    workflow_card("Content & Allocation", [
        ("Recipes", "pages/15_Admin_Recipe_Manager.py", "v14_recipes", "Allocate or manage recipes."),
        ("Exercises", "pages/16_Admin_Exercise_Manager.py", "v14_exercises", "Allocate or manage exercises."),
    ])

with w4:
    workflow_card("Reports & Logs", [
        ("Daily Logs", "pages/22_Admin_Daily_Log_Report.py", "v14_daily", "Download logs and send reminders."),
        ("Questions", "pages/20_Admin_Question_Manager.py", "v14_questions", "Manage assessment questions."),
        ("Responses", "pages/21_Admin_Response_Editor.py", "v14_responses", "Correct member responses with audit notes."),
    ])

w5, w6 = st.columns(2, gap="medium")
with w5:
    workflow_card("Communication", [
        ("Messages", "pages/31_Admin_Member_Communication.py", "v14_messages", "Send in-app messages and queue email notification."),
    ])

with w6:
    workflow_card("System Tools", [
        ("Database", "pages/28_Admin_Database_Status.py", "v14_database", "Check Supabase/local fallback status."),
        ("Demo", "pages/29_Admin_Demo_Mode.py", "v14_demo", "Manage demo walkthrough controls."),
    ])

st.subheader("Recommended Flow")
with st.container(border=True):
    st.markdown("<div class='hm-v14-flow-card'>", unsafe_allow_html=True)
    st.markdown("<div class='hm-v14-flow-title'>Suggested operating sequence</div>", unsafe_allow_html=True)
    st.markdown(
        """
        <div class='hm-v14-flow-list'>
          <div class='hm-v14-flow-step'><b>1. New submission</b><br>Review Queue → Evaluation Status → Final Report</div>
          <div class='hm-v14-flow-step'><b>2. Follow-up</b><br>Reassessments → NSP Compare</div>
          <div class='hm-v14-flow-step'><b>3. Access issue</b><br>Access Manager</div>
          <div class='hm-v14-flow-step'><b>4. Allocation</b><br>Recipes / Exercises</div>
          <div class='hm-v14-flow-step'><b>5. Troubleshooting</b><br>Database</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)


# v43 Daily Log Settings quick access
card_start()
st.subheader("Daily Log Configuration")
st.caption("Manage meal sections used in the member Daily Food Journal.")
if st.button("Daily Log Settings", use_container_width=True):
    st.switch_page("pages/25_Admin_Daily_Log_Settings.py")
card_end()
