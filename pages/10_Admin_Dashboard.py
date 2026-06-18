from components.ui_common import render_page_nav, render_back_to_top
import streamlit as st

from components.guards import require_admin
from components.ui_common import (
    inject_keepalive_guard_v96_11,
    inject_global_styles,
    apply_luxe_theme,
    utility_logout_bar,
    render_back_to_top,
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

st.markdown("""
<style>
/* v101.7 Admin Dashboard placement polish */
section.main > div.block-container,
.main .block-container,
[data-testid="stAppViewBlockContainer"],
.stMainBlockContainer,
.block-container{
  max-width:1120px!important;
  padding-top:.72rem!important;
  padding-bottom:1.2rem!important;
}
.hm-admin-title{
  margin:.18rem 0 .58rem 0!important;
  color:#064E3B!important;
  font-size:1.05rem!important;
  font-weight:950!important;
  letter-spacing:.01em!important;
}
.hm-dash-section{
  margin:0 0 1.02rem 0!important;
  padding:0!important;
  background:transparent!important;
  border:0!important;
  box-shadow:none!important;
}
.hm-dash-section-title{
  margin:0 0 .36rem 0!important;
  color:#064E3B!important;
  font-size:.90rem!important;
  line-height:1.08!important;
  font-weight:950!important;
  letter-spacing:.01em!important;
}
.hm-dash-section [data-testid="stButton"]{
  margin:0 0 .52rem 0!important;
}
.hm-dash-section [data-testid="stButton"] > button{
  width:100%!important;
  min-height:2.72rem!important;
  height:2.72rem!important;
  padding:0 .80rem!important;
  border:1.25px solid #D9C28F!important;
  border-radius:14px!important;
  background:#FFFDF8!important;
  color:#064E3B!important;
  box-shadow:none!important;
  font-size:.92rem!important;
  line-height:1.05!important;
  font-weight:850!important;
  display:flex!important;
  align-items:center!important;
  justify-content:center!important;
}
.hm-dash-section [data-testid="stButton"] > button:hover{
  background:#FFF7E6!important;
  border-color:#B89345!important;
  color:#003C36!important;
  box-shadow:0 6px 16px rgba(15,23,42,.06)!important;
}
.hm-dash-subpoint-placeholder{
  width:100%;
  min-height:2.72rem;
  height:2.72rem;
  border:1.25px dashed #D9C28F;
  border-radius:14px;
  display:flex;
  align-items:center;
  justify-content:center;
  color:#7A5A16;
  font-size:.90rem;
  font-weight:820;
  background:#FFF9EC;
  margin:0 0 .52rem 0;
  box-sizing:border-box;
}
.hm-dash-system-tools{
  margin-top:.22rem!important;
  padding-top:.20rem!important;
  border-top:1px solid rgba(227,201,142,.46);
}
@media(max-width:760px){
  .hm-dash-system-tools{
    border-top:0;
  }
}
</style>
""", unsafe_allow_html=True)

st.markdown("<div class='hm-admin-title'>Main Workflows</div>", unsafe_allow_html=True)

def start_section(title):
    st.markdown(f"<div class='hm-dash-section'><div class='hm-dash-section-title'>{title}</div>", unsafe_allow_html=True)

def end_section():
    st.markdown("</div>", unsafe_allow_html=True)

def nav_cell(label, page, key):
    if st.button(label, key=key, use_container_width=True):
        st.switch_page(page)

def placeholder_cell(label):
    st.markdown(f"<div class='hm-dash-subpoint-placeholder'>{label}</div>", unsafe_allow_html=True)

left, right = st.columns(2, gap="large")

with left:
    start_section("Review & Assessment")
    nav_cell("Review", "pages/26_Admin_Review_Queue.py", "dash_review_v101_7")
    nav_cell("Evaluation Status", "pages/11_Evaluation_Status.py", "dash_eval_status_v101_7")
    nav_cell("Reassessment", "pages/25_Admin_Reassessment_Manager.py", "dash_reassessment_v101_7")
    nav_cell("NSP Compare", "pages/27_Comparative_NSP_Report.py", "dash_nsp_compare_v101_7")
    end_section()

    start_section("Member & Access")
    nav_cell("Create Users", "pages/17_Admin_User_Manager.py", "dash_create_users_v101_7")
    nav_cell("Access Manager", "pages/30_Admin_User_Access_Manager.py", "dash_access_manager_v101_7")
    end_section()

    start_section("Content & Allocation")
    nav_cell("Recipes", "pages/15_Admin_Recipe_Manager.py", "dash_recipes_v101_7")
    nav_cell("Exercises", "pages/16_Admin_Exercise_Manager.py", "dash_exercises_v101_7")
    end_section()

with right:
    start_section("Reports & Logs")
    nav_cell("Daily Logs", "pages/22_Admin_Daily_Log_Report.py", "dash_daily_logs_v101_7")
    nav_cell("Questions", "pages/20_Admin_Question_Manager.py", "dash_questions_v101_7")
    nav_cell("Responses", "pages/21_Admin_Response_Editor.py", "dash_responses_v101_7")
    placeholder_cell("Recommendations to Members")
    end_section()

    start_section("Communication & Scheduling")
    nav_cell("Messages", "pages/31_Admin_Member_Communication.py", "dash_messages_v101_7")
    nav_cell("Scheduling", "pages/32_Admin_Scheduling.py", "dash_scheduling_v101_7")
    end_section()

st.markdown("<div class='hm-dash-system-tools'>", unsafe_allow_html=True)
start_section("System Tools")
sys_col_1, sys_col_2 = st.columns(2, gap="large")
with sys_col_1:
    nav_cell("Database", "pages/28_Admin_Database_Status.py", "dash_database_v101_7")
with sys_col_2:
    nav_cell("NSP Recalculate", "pages/34_Admin_NSP_Score_Recalculation.py", "dash_nsp_recalc_v101_7")
# v101.7: Demo hidden from Admin Dashboard by client request.
end_section()
st.markdown("</div>", unsafe_allow_html=True)

inject_keepalive_guard_v96_11()

# v101.7: Admin Dashboard restructured per client placement request.