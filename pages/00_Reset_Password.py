from components.ui_common import render_page_nav, render_back_to_top

import streamlit as st
from components.ui_common import inject_global_styles, apply_luxe_theme, render_build_text_v12, render_back_to_top
from components.db import change_password
st.set_page_config(page_title="Reset Password", page_icon="🌿", layout="wide", initial_sidebar_state="collapsed")
inject_global_styles(); apply_luxe_theme()
st.markdown("## Reset Password")
p1=st.text_input("New password", type="password")
p2=st.text_input("Confirm password", type="password")
if st.button("Reset Password", type="primary"):
    if not p1 or p1 != p2: st.error("Passwords do not match.")
    else:
        change_password(st.session_state["user_id"], p1)
        st.session_state["must_reset_password"]=False
        if st.session_state["user_role"]=="admin": st.switch_page("pages/10_Admin_Dashboard.py")
        else: st.switch_page("pages/02_Member_Home.py")

# v102.0: canonical global footer navigation
render_page_nav("Reset Password", back_page="pages/02_Member_Home.py", dashboard_page="pages/02_Member_Home.py", show_evaluation=False, show_dashboard=True, location="bottom")
render_back_to_top()
