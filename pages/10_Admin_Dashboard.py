import streamlit as st
from components.guards import require_admin
from components.ui_common import inject_global_styles, apply_luxe_theme, utility_logout_bar, render_back_to_top

st.set_page_config(page_title="Admin Dashboard", page_icon="💚", layout="wide", initial_sidebar_state="collapsed")
inject_global_styles()
apply_luxe_theme()
require_admin()
utility_logout_bar()
render_back_to_top()

st.markdown("""
<style>
/* v96.9 Admin Dashboard uniform scheduling-style subpoint boxes */
.block-container{
  padding-top:.45rem!important;
  padding-bottom:1rem!important;
  max-width:980px!important;
}
.hm-admin-title{
  margin:.1rem 0 .45rem 0!important;
  color:#064E3B!important;
  font-size:1.02rem!important;
  font-weight:900!important;
}
.hm-dash-grid{
  display:grid;
  grid-template-columns:1fr 1fr;
  gap:.55rem 1.6rem;
  align-items:start;
}
.hm-dash-section{
  margin:0 0 .72rem 0;
  padding:0;
  background:transparent;
  border:0;
  box-shadow:none;
}
.hm-dash-section-title{
  margin:0 0 .18rem 0;
  color:#064E3B;
  font-size:.86rem;
  line-height:1.05;
  font-weight:900;
}
/* Every clickable subpoint uses the same cell/box schema as Scheduling */
.hm-dash-section [data-testid="stButton"]{
  margin:0 0 .18rem 0!important;
}
.hm-dash-section [data-testid="stButton"] > button{
  width:100%!important;
  min-height:28px!important;
  height:28px!important;
  padding:0 .55rem!important;
  border:1px solid #D8C89D!important;
  border-radius:3px!important;
  background:#FAF8F1!important;
  color:#102A43!important;
  box-shadow:none!important;
  font-size:.8rem!important;
  line-height:1!important;
  font-weight:520!important;
  display:flex!important;
  align-items:center!important;
  justify-content:center!important;
}
.hm-dash-section [data-testid="stButton"] > button:hover{
  background:#FFFDF8!important;
  border-color:#C9B47A!important;
  color:#064E3B!important;
}
.hm-dash-section [data-testid="stButton"] p{
  font-size:.8rem!important;
  line-height:1!important;
  margin:0!important;
  font-weight:520!important;
}
.hm-dash-subpoint-placeholder{
  width:100%;
  min-height:28px;
  height:28px;
  border:1px solid #D8C89D;
  border-radius:3px;
  display:flex;
  align-items:center;
  justify-content:center;
  color:#102A43;
  font-size:.8rem;
  font-weight:520;
  background:#FAF8F1;
  margin:0 0 .18rem 0;
  box-sizing:border-box;
}
@media(max-width:760px){
  .hm-dash-grid{
    grid-template-columns:1fr;
    gap:.45rem;
  }
}
</style>
""", unsafe_allow_html=True)

st.markdown("<div class='hm-admin-title'>Main Workflows</div>", unsafe_allow_html=True)

left, right = st.columns(2, gap="large")

def start_section(title):
    st.markdown(f"<div class='hm-dash-section'><div class='hm-dash-section-title'>{title}</div>", unsafe_allow_html=True)

def end_section():
    st.markdown("</div>", unsafe_allow_html=True)

def nav_cell(label, page, key):
    if st.button(label, key=key, use_container_width=True):
        st.switch_page(page)

def placeholder_cell(label):
    st.markdown(f"<div class='hm-dash-subpoint-placeholder'>{label}</div>", unsafe_allow_html=True)

with left:
    start_section("Review & Assessment")
    nav_cell("Review", "pages/26_Admin_Review_Queue.py", "dash_review_v96_9")
    nav_cell("Evaluation Status", "pages/11_Evaluation_Status.py", "dash_eval_status_v96_9")
    nav_cell("Reassessment", "pages/25_Admin_Reassessment_Manager.py", "dash_reassessment_v96_9")
    nav_cell("NSP Compare", "pages/27_Comparative_NSP_Report.py", "dash_nsp_compare_v96_9")
    end_section()

    start_section("Content & Allocation")
    nav_cell("Recipes", "pages/15_Admin_Recipe_Manager.py", "dash_recipes_v96_9")
    nav_cell("Exercises", "pages/16_Admin_Exercise_Manager.py", "dash_exercises_v96_9")
    end_section()

    start_section("Member & Access")
    nav_cell("Create Users", "pages/17_Admin_User_Manager.py", "dash_create_users_v96_9")
    nav_cell("Access Manager", "pages/30_Admin_User_Access_Manager.py", "dash_access_manager_v96_9")
    end_section()

with right:
    start_section("Communication & Scheduling")
    nav_cell("Messages", "pages/31_Admin_Member_Communication.py", "dash_messages_v96_9")
    placeholder_cell("Scheduling")

    end_section()

    start_section("Reports & Logs")
    nav_cell("Daily Logs", "pages/22_Admin_Daily_Log_Report.py", "dash_daily_logs_v96_9")
    nav_cell("Questions", "pages/20_Admin_Question_Manager.py", "dash_questions_v96_9")
    nav_cell("Responses", "pages/21_Admin_Response_Editor.py", "dash_responses_v96_9")
    end_section()

    start_section("System Tools")
    nav_cell("Database", "pages/28_Admin_Database_Status.py", "dash_database_v96_9")
    nav_cell("Demo", "pages/29_Admin_Demo_Mode.py", "dash_demo_v96_9")
    end_section()
