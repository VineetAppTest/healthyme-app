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

topbar("Admin Dashboard", "Premium command center for review, reassessment, reporting, and content management.", "Admin experience")
render_system_message()

# Database Status Warning
if db_status.get("mode") != "SUPABASE":
    st.warning("Database is currently running in LOCAL FALLBACK mode. For live Streamlit use, configure Supabase and verify via Database Status.")

stat_grid([
    {"label": "Members", "value": member_count, "note": "Member accounts only"},
    {"label": "Initial Reviews", "value": len(initial_pending), "note": "Pending initial assessment"},
    {"label": "Reassessments", "value": len(reassess_pending), "note": "Pending follow-up review"},
    {"label": "Finalized", "value": finalized_count, "note": "Reports ready"},
])

card_start()
st.subheader("Quick Actions")
a,b,c,d = st.columns(4)
with a:
    if st.button("Review Queue", type="primary", use_container_width=True):
        st.switch_page("pages/26_Admin_Review_Queue.py")
with b:
    if st.button("Evaluation Status", use_container_width=True):
        st.switch_page("pages/11_Evaluation_Status.py")
with c:
    if st.button("Reassessment Manager", use_container_width=True):
        st.switch_page("pages/25_Admin_Reassessment_Manager.py")
with d:
    if st.button("Create Users", use_container_width=True):
        st.switch_page("pages/17_Admin_User_Manager.py")

e,f,g,h = st.columns(4)
with e:
    if st.button("Question Manager", use_container_width=True):
        st.switch_page("pages/20_Admin_Question_Manager.py")
with f:
    if st.button("Edit Responses", use_container_width=True):
        st.switch_page("pages/21_Admin_Response_Editor.py")
with g:
    if st.button("Daily Log Report", use_container_width=True):
        st.switch_page("pages/22_Admin_Daily_Log_Report.py")
with h:
    if st.button("Body-Mind Access", use_container_width=True):
        st.switch_page("pages/23_Admin_Body_Mind_Control.py")

i,j = st.columns(2)
with i:
    if st.button("Manage Recipes", use_container_width=True):
        st.switch_page("pages/15_Admin_Recipe_Manager.py")
with j:
    if st.button("Manage Exercises", use_container_width=True):
        st.switch_page("pages/16_Admin_Exercise_Manager.py")

k,l = st.columns(2)
with k:
    if st.button("Comparative NSP Report", use_container_width=True):
        st.switch_page("pages/27_Comparative_NSP_Report.py")
with l:
    if st.button("Database Status", use_container_width=True):
        st.switch_page("pages/28_Admin_Database_Status.py")

m,n = st.columns(2)
with m:
    if st.button("Demo Mode", use_container_width=True):
        st.switch_page("pages/29_Admin_Demo_Mode.py")
card_end()

# Access manager shortcut
if st.button("User Access Manager", use_container_width=True):
    st.switch_page("pages/30_Admin_User_Access_Manager.py")
