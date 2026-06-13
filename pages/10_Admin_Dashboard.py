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
/* v96.8 Admin Dashboard compact workflow layout */
.block-container{
  padding-top:.45rem!important;
  padding-bottom:1rem!important;
  max-width:1080px!important;
}
.hm-admin-title{
  margin:.1rem 0 .5rem 0!important;
  color:#064E3B!important;
  font-size:1.05rem!important;
  font-weight:900!important;
}
.hm-dash-grid{
  display:grid;
  grid-template-columns:1fr 1fr;
  gap:.75rem 1rem;
  align-items:start;
}
.hm-dash-card{
  background:rgba(255,255,255,.62);
  border:1px solid #D8C89D;
  border-radius:4px;
  padding:.42rem .55rem .52rem .55rem;
  margin:0 0 .55rem 0;
  box-shadow:none;
}
.hm-dash-section-title{
  margin:0 0 .28rem 0;
  color:#064E3B;
  font-size:.82rem;
  line-height:1.05;
  font-weight:900;
}
.hm-dash-card [data-testid="stButton"]{
  margin:0 0 .28rem 0!important;
}
.hm-dash-card [data-testid="stButton"] > button{
  min-height:31px!important;
  height:31px!important;
  padding:0 .55rem!important;
  border-radius:9px!important;
  font-size:.76rem!important;
  line-height:1!important;
  font-weight:720!important;
  box-shadow:none!important;
}
.hm-dash-card [data-testid="stButton"] p{
  font-size:.76rem!important;
  line-height:1!important;
  margin:0!important;
}
.hm-dash-placeholder{
  min-height:31px;
  border:1px solid #D8C89D;
  border-radius:9px;
  display:flex;
  align-items:center;
  justify-content:center;
  color:#64705F;
  font-size:.76rem;
  background:#FAF8F1;
  margin-bottom:.28rem;
}
@media(max-width:760px){
  .hm-dash-grid{
    grid-template-columns:1fr;
  }
}
</style>
""", unsafe_allow_html=True)

st.markdown("<div class='hm-admin-title'>Main Workflows</div>", unsafe_allow_html=True)

left, right = st.columns(2, gap="large")

def workflow_card(title):
    st.markdown(f"<div class='hm-dash-card'><div class='hm-dash-section-title'>{title}</div>", unsafe_allow_html=True)

def end_card():
    st.markdown("</div>", unsafe_allow_html=True)

def nav_button(label, page, key):
    if st.button(label, key=key, use_container_width=True):
        st.switch_page(page)

with left:
    workflow_card("Review & Assessment")
    nav_button("Review", "pages/26_Admin_Review_Queue.py", "dash_review_v96_8")
    nav_button("Evaluation Status", "pages/11_Evaluation_Status.py", "dash_eval_status_v96_8")
    nav_button("Reassessment", "pages/25_Admin_Reassessment_Manager.py", "dash_reassessment_v96_8")
    nav_button("NSP Compare", "pages/27_Comparative_NSP_Report.py", "dash_nsp_compare_v96_8")
    end_card()

    workflow_card("Content & Allocation")
    nav_button("Recipes", "pages/15_Admin_Recipe_Manager.py", "dash_recipes_v96_8")
    nav_button("Exercises", "pages/16_Admin_Exercise_Manager.py", "dash_exercises_v96_8")
    end_card()

    workflow_card("Member & Access")
    nav_button("Create Users", "pages/17_Admin_User_Manager.py", "dash_create_users_v96_8")
    nav_button("Access Manager", "pages/30_Admin_User_Access_Manager.py", "dash_access_manager_v96_8")
    end_card()

with right:
    workflow_card("Communication & Scheduling")
    nav_button("Messages", "pages/31_Admin_Member_Communication.py", "dash_messages_v96_8")
    st.markdown("<div class='hm-dash-placeholder'>Scheduling</div>", unsafe_allow_html=True)

    end_card()

    workflow_card("Reports & Logs")
    nav_button("Daily Logs", "pages/22_Admin_Daily_Log_Report.py", "dash_daily_logs_v96_8")
    nav_button("Questions", "pages/20_Admin_Question_Manager.py", "dash_questions_v96_8")
    nav_button("Responses", "pages/21_Admin_Response_Editor.py", "dash_responses_v96_8")
    end_card()

    workflow_card("System Tools")
    nav_button("Database", "pages/28_Admin_Database_Status.py", "dash_database_v96_8")
    nav_button("Demo", "pages/29_Admin_Demo_Mode.py", "dash_demo_v96_8")
    end_card()
