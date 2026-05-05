
import streamlit as st
from components.guards import require_admin
from components.ui_common import inject_global_styles, apply_luxe_theme, topbar, stat_grid, card_start, card_end, utility_logout_bar
from components.db import get_admin_dashboard_snapshot
from components.flash import render_system_message
from components.storage_backend import get_storage_status

st.set_page_config(page_title="Admin Dashboard", page_icon="💚", layout="wide", initial_sidebar_state="collapsed")
inject_global_styles(); apply_luxe_theme(); require_admin(); utility_logout_bar()

snapshot = get_admin_dashboard_snapshot()
members = snapshot["members"]
member_count = snapshot["member_count"]
admin_count = snapshot["admin_count"]
initial_pending = snapshot["initial_pending"]
reassess_pending = snapshot["reassess_pending"]
finalized_count = snapshot["finalized_count"]
db_status = get_storage_status(force_check=False)

topbar("Admin Dashboard", "Structured command center for review, access, content, and system controls.", "Admin experience")
render_system_message()

if db_status.get("mode") != "SUPABASE":
    st.warning("Database is currently running in LOCAL FALLBACK mode. For live Streamlit use, configure Supabase and verify via Database Status.")

stat_grid([
    {"label": "Members", "value": member_count, "note": "Member accounts only"},
    {"label": "Initial Reviews", "value": len(initial_pending), "note": "Pending initial assessment"},
    {"label": "Reassessments", "value": len(reassess_pending), "note": "Pending follow-up review"},
    {"label": "Finalized", "value": finalized_count, "note": "Reports ready"},
])


card_start()
st.subheader("Today's Priority")
p1, p2, p3 = st.columns(3, gap="large")
with p1:
    st.metric("Initial Reviews", len(initial_pending), help="Members who submitted first assessment and need admin review.")
    if st.button("Open Review Queue", type="primary", key="priority_review", use_container_width=True):
        st.switch_page("pages/26_Admin_Review_Queue.py")
with p2:
    st.metric("Reassessments", len(reassess_pending), help="Follow-up NSP submissions waiting for review.")
    if st.button("Open Reassessment Manager", key="priority_reassess", use_container_width=True):
        st.switch_page("pages/25_Admin_Reassessment_Manager.py")
with p3:
    st.metric("Finalized", finalized_count, help="Members with final reports ready.")
    if st.button("Open Evaluation Status", key="priority_eval", use_container_width=True):
        st.switch_page("pages/11_Evaluation_Status.py")
card_end()

st.markdown("""
<style>
.hm-section-title {
    font-size: 1.05rem;
    font-weight: 900;
    color: #064E3B;
    margin-bottom: .25rem;
}
.hm-section-subtitle {
    color: #64748B;
    font-size: .86rem;
    margin-bottom: .75rem;
}
.hm-action-card {
    border: 1px solid #EADFCB;
    border-radius: 20px;
    padding: 1rem;
    background: linear-gradient(180deg, #FFFFFF 0%, #FFFCF6 100%);
    box-shadow: 0 14px 35px rgba(15,23,42,.06);
    min-height: 100%;
}
.hm-action-chip {
    font-size: .75rem;
    color: #047857;
    background: #ECFDF5;
    padding: .2rem .55rem;
    border-radius: 999px;
    font-weight: 800;
}
</style>
""", unsafe_allow_html=True)

def action_button(label, page, key, primary=False, help_text=None):
    if st.button(label, key=key, type="primary" if primary else "secondary", use_container_width=True, help=help_text):
        st.switch_page(page)

def action_group(title, subtitle, chip, actions):
    with st.container(border=True):
        st.markdown(f"<div class='hm-section-title'>{title} <span class='hm-action-chip'>{chip}</span></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='hm-section-subtitle'>{subtitle}</div>", unsafe_allow_html=True)
        for action in actions:
            action_button(
                action["label"],
                action["page"],
                action["key"],
                action.get("primary", False),
                action.get("help"),
            )

card_start()
st.subheader("Quick Actions")

row1_col1, row1_col2 = st.columns(2, gap="large")
with row1_col1:
    action_group(
        "Review & Assessment",
        "Daily operating area for member assessments, queues, reassessment requests, and reports.",
        "Main workflow",
        [
            {"label": "Review Queue", "page": "pages/26_Admin_Review_Queue.py", "key": "qa_review_queue", "primary": True, "help": "Start here for submitted assessments awaiting review."},
            {"label": "Evaluation Status", "page": "pages/11_Evaluation_Status.py", "key": "qa_eval_status"},
            {"label": "Reassessment Manager", "page": "pages/25_Admin_Reassessment_Manager.py", "key": "qa_reassessment"},
            {"label": "Comparative NSP Report", "page": "pages/27_Comparative_NSP_Report.py", "key": "qa_comparative"},
        ],
    )

with row1_col2:
    action_group(
        "User & Access Management",
        "Create users, manage roles, deactivate/reactivate access, and control Body-Mind visibility.",
        "Access control",
        [
            {"label": "Create Members / Admins", "page": "pages/17_Admin_User_Manager.py", "key": "qa_create_users", "primary": True},
            {"label": "User Access Manager", "page": "pages/30_Admin_User_Access_Manager.py", "key": "qa_access_manager"},
            {"label": "Body-Mind Access", "page": "pages/23_Admin_Body_Mind_Control.py", "key": "qa_bodymind_access"},
        ],
    )

row2_col1, row2_col2 = st.columns(2, gap="large")
with row2_col1:
    action_group(
        "Questionnaire & Response Controls",
        "Tools for managing questions, corrections, audit rationale, and member daily logs.",
        "Admin controls",
        [
            {"label": "Question Manager", "page": "pages/20_Admin_Question_Manager.py", "key": "qa_questions", "primary": True},
            {"label": "Edit Responses", "page": "pages/21_Admin_Response_Editor.py", "key": "qa_responses"},
            {"label": "Daily Log Report", "page": "pages/22_Admin_Daily_Log_Report.py", "key": "qa_daily_log"},
        ],
    )

with row2_col2:
    action_group(
        "Content / Resource Management",
        "Manage content repositories used after expert review and personalized guidance.",
        "Resources",
        [
            {"label": "Manage Recipes", "page": "pages/15_Admin_Recipe_Manager.py", "key": "qa_recipes", "primary": True},
            {"label": "Manage Exercises", "page": "pages/16_Admin_Exercise_Manager.py", "key": "qa_exercises"},
        ],
    )

row3_col1, row3_col2 = st.columns(2, gap="large")
with row3_col1:
    action_group(
        "System & Database Tools",
        "Database status, Supabase verification, backups, and demo walkthrough controls.",
        "System",
        [
            {"label": "Database Status", "page": "pages/28_Admin_Database_Status.py", "key": "qa_db_status", "primary": True},
            {"label": "Demo Mode", "page": "pages/29_Admin_Demo_Mode.py", "key": "qa_demo"},
        ],
    )

with row3_col2:
    with st.container(border=True):
        st.markdown("<div class='hm-section-title'>Recommended Flow <span class='hm-action-chip'>Guide</span></div>", unsafe_allow_html=True)
        st.markdown("""
        <div class='hm-section-subtitle'>
        For daily work: start with <b>Review Queue</b>. For user issues: use <b>User Access Manager</b>.
        For scoring/report configuration: use <b>Question Manager</b> and <b>Edit Responses</b>.
        </div>
        """, unsafe_allow_html=True)
        st.info("Use Review Queue for daily work, User Access Manager for login/access issues, and Database Status only when checking Supabase.")
card_end()
