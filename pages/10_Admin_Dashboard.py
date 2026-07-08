import streamlit as st

from components.guards import require_admin
from components.ui_common import (
    inject_keepalive_guard_v96_11,
    inject_global_styles,
    apply_luxe_theme,
    utility_logout_bar,
    topbar,
)

st.set_page_config(page_title="Admin Dashboard", page_icon="💚", layout="wide", initial_sidebar_state="collapsed")

inject_global_styles()
apply_luxe_theme()
require_admin()
utility_logout_bar()

topbar(
    "Admin Dashboard",
    "Access review workflows, content allocation, reports, communication, scheduling and system tools.",
    "Admin workflow",
)

st.markdown(
    """
<style>
/* v102.4B4 Admin Dashboard premium polish */
section.main > div.block-container,
.main .block-container,
[data-testid="stAppViewBlockContainer"],
.stMainBlockContainer,
.block-container{
  max-width:1140px!important;
  padding-top:.58rem!important;
  padding-bottom:1.2rem!important;
}
.hm-admin-title-row{
  margin:.10rem 0 .75rem 0!important;
  padding:.74rem .92rem!important;
  border:1px solid rgba(216,180,98,.46)!important;
  border-radius:20px!important;
  background:linear-gradient(135deg, rgba(255,253,248,.98), rgba(255,247,230,.78))!important;
  box-shadow:0 12px 28px rgba(15,23,42,.055)!important;
}
.hm-admin-title{
  margin:0!important;
  color:#064E3B!important;
  font-size:1.08rem!important;
  font-weight:950!important;
  letter-spacing:.01em!important;
  line-height:1.16!important;
}
.hm-admin-subtitle{
  margin:.18rem 0 0 0!important;
  color:#5D4A1E!important;
  font-size:.82rem!important;
  font-weight:760!important;
  line-height:1.32!important;
}
/* Streamlit bordered containers used as premium section cards on this page */
div[data-testid="stVerticalBlockBorderWrapper"]{
  border:1.25px solid rgba(216,180,98,.62)!important;
  border-radius:22px!important;
  background:linear-gradient(180deg, rgba(255,253,248,.98) 0%, rgba(255,250,239,.94) 100%)!important;
  box-shadow:0 12px 26px rgba(15,23,42,.06)!important;
  padding:.72rem .78rem .68rem .78rem!important;
  margin:0 0 .94rem 0!important;
}
div[data-testid="stVerticalBlockBorderWrapper"]:hover{
  border-color:rgba(184,147,69,.80)!important;
  box-shadow:0 16px 34px rgba(15,23,42,.075)!important;
}
.hm-dash-section-title{
  margin:0 0 .10rem 0!important;
  color:#064E3B!important;
  font-size:.94rem!important;
  line-height:1.10!important;
  font-weight:950!important;
  letter-spacing:.01em!important;
}
.hm-dash-section-caption{
  margin:0 0 .54rem 0!important;
  color:#72551A!important;
  font-size:.76rem!important;
  line-height:1.25!important;
  font-weight:760!important;
}
.hm-dash-card [data-testid="stButton"]{
  margin:0 0 .46rem 0!important;
}
.hm-dash-card [data-testid="stButton"] > button,
.hm-dash-system-card [data-testid="stButton"] > button{
  width:100%!important;
  min-height:2.72rem!important;
  height:2.72rem!important;
  padding:0 .84rem!important;
  border:1.25px solid rgba(217,194,143,.92)!important;
  border-radius:15px!important;
  background:linear-gradient(135deg,#FFFFFF 0%,#FFF9ED 100%)!important;
  color:#064E3B!important;
  box-shadow:0 4px 12px rgba(15,23,42,.035)!important;
  font-size:.91rem!important;
  line-height:1.06!important;
  font-weight:880!important;
  display:flex!important;
  align-items:center!important;
  justify-content:center!important;
}
.hm-dash-card [data-testid="stButton"] > button:hover,
.hm-dash-system-card [data-testid="stButton"] > button:hover{
  transform:translateY(-1px)!important;
  background:linear-gradient(135deg,#FFF9EA 0%,#FFF3D6 100%)!important;
  border-color:#B89345!important;
  color:#003C36!important;
  box-shadow:0 9px 18px rgba(15,23,42,.075)!important;
}
.hm-dash-card [data-testid="stButton"] > button:active,
.hm-dash-system-card [data-testid="stButton"] > button:active{
  transform:translateY(0)!important;
}
.hm-dash-system-wrap{
  margin-top:.16rem!important;
}
.hm-dashboard-small-gap [data-testid="stVerticalBlock"]{
  gap:.28rem!important;
}
@media(max-width:760px){
  div[data-testid="stVerticalBlockBorderWrapper"]{
    border-radius:18px!important;
    padding:.62rem .58rem!important;
    margin-bottom:.74rem!important;
  }
  .hm-admin-title-row{
    border-radius:18px!important;
  }
}
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
<div class='hm-admin-title-row'>
  <div class='hm-admin-title'>Main Workflows</div>
  <div class='hm-admin-subtitle'>Premium admin control center with grouped workflow sections.</div>
</div>
""",
    unsafe_allow_html=True,
)


def section_header(title: str, caption: str) -> None:
    st.markdown(
        f"<div class='hm-dash-card'><div class='hm-dash-section-title'>{title}</div>"
        f"<div class='hm-dash-section-caption'>{caption}</div></div>",
        unsafe_allow_html=True,
    )


def nav_cell(label: str, page: str, key: str) -> None:
    if st.button(label, key=key, use_container_width=True):
        st.switch_page(page)


left, right = st.columns(2, gap="large")

with left:
    with st.container(border=True):
        st.markdown("<div class='hm-dash-card'>", unsafe_allow_html=True)
        section_header("Review & Assessment", "Track member assessments, reviews and reassessment tasks.")
        nav_cell("Review", "pages/26_Admin_Review_Queue.py", "dash_review_v102_4b4")
        nav_cell("Evaluation Status", "pages/11_Evaluation_Status.py", "dash_eval_status_v102_4b4")
        nav_cell("Reassessment", "pages/25_Admin_Reassessment_Manager.py", "dash_reassessment_v102_4b4")
        nav_cell("NSP Compare", "pages/27_Comparative_NSP_Report.py", "dash_nsp_compare_v102_4b4")
        st.markdown("</div>", unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown("<div class='hm-dash-card'>", unsafe_allow_html=True)
        section_header("Member & Access", "Create users and manage member/admin access controls.")
        nav_cell("Create Users", "pages/17_Admin_User_Manager.py", "dash_create_users_v102_4b4")
        nav_cell("Access Manager", "pages/30_Admin_User_Access_Manager.py", "dash_access_manager_v102_4b4")
        nav_cell("Packages", "pages/41_Admin_Packages.py", "dash_packages_v102_4b14")
        st.markdown("</div>", unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown("<div class='hm-dash-card'>", unsafe_allow_html=True)
        section_header("Communication & Scheduling", "Send messages and manage member scheduling workflows.")
        nav_cell("Messages", "pages/31_Admin_Member_Communication.py", "dash_messages_v102_4b4")
        nav_cell("Scheduling", "pages/32_Admin_Scheduling.py", "dash_scheduling_v102_4b4")
        st.markdown("</div>", unsafe_allow_html=True)

with right:
    with st.container(border=True):
        st.markdown("<div class='hm-dash-card'>", unsafe_allow_html=True)
        section_header("Reports & Logs", "Review logs, questions, responses and member recommendation shares.")
        nav_cell("Daily Logs", "pages/22_Admin_Daily_Log_Report.py", "dash_daily_logs_v102_4b4")
        nav_cell("Questions", "pages/20_Admin_Question_Manager.py", "dash_questions_v102_4b4")
        nav_cell("Responses", "pages/21_Admin_Response_Editor.py", "dash_responses_v102_4b4")
        nav_cell("Recommendations Share", "pages/35_Admin_Recommendations_Share.py", "dash_recommendations_share_v102_4b4")
        nav_cell("Unified Recommendations", "pages/36_Admin_Unified_Recommendations.py", "dash_unified_recommendations_h9a5e")
        st.markdown("</div>", unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown("<div class='hm-dash-card'>", unsafe_allow_html=True)
        section_header("Content & Allocation", "Manage recipes, exercises and supplement regimens.")
        nav_cell("Recipes", "pages/15_Admin_Recipe_Manager.py", "dash_recipes_v102_4b4")
        nav_cell("Exercises", "pages/16_Admin_Exercise_Manager.py", "dash_exercises_v102_4b4")
        nav_cell("Supplements", "pages/39_Admin_Supplement_Manager.py", "dash_supplements_v102_4b4")
        st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div class='hm-dash-system-wrap'>", unsafe_allow_html=True)
with st.container(border=True):
    st.markdown("<div class='hm-dash-system-card'>", unsafe_allow_html=True)
    section_header("System Tools", "Database checks, recalculation utilities and Supabase migration controls.")
    sys_col_1, sys_col_2 = st.columns(2, gap="large")
    with sys_col_1:
        nav_cell("Database", "pages/28_Admin_Database_Status.py", "dash_database_v102_4b4")
    with sys_col_2:
        nav_cell("NSP Recalculate", "pages/34_Admin_NSP_Score_Recalculation.py", "dash_nsp_recalc_v102_4b4")
    sys_col_3, sys_col_4 = st.columns(2, gap="large")
    with sys_col_3:
        nav_cell("Supabase Auth Readiness", "pages/33_Admin_Supabase_Auth_Pilot_Readiness.py", "dash_supabase_auth_readiness_v102_4b15s3h4")
    with sys_col_4:
        nav_cell("Supabase Provisioning", "pages/34_Admin_Supabase_Auth_Provisioning_Workbench.py", "dash_supabase_provisioning_v102_4b15s3h4")
    st.markdown("</div>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

inject_keepalive_guard_v96_11()

# v101.7: Admin Dashboard restructured per client placement request.
# v102.4: Recipe-1/Exercise-1 testing buttons removed; Recommendations Share added as admin source of truth.
# v102.4B4: Premium bordered section cards added to Admin Dashboard.
# v102.4B14B: Communication & Scheduling section swapped with Content & Allocation.
# v102.4B15S3H4: Added dashboard buttons for Supabase Auth tools because Streamlit sidebar/menu remains intentionally hidden.
# H9A.5E: Added Unified Recommendations contract workbench entry point.
