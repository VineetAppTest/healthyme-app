import streamlit as st

from components.guards import require_member
from components.member_recommendation_split_display import render_member_recommendation_view
from components.ui_common import inject_global_styles, apply_luxe_theme, utility_logout_bar, topbar, render_page_nav, render_back_to_top

st.set_page_config(page_title="My Weekly Plan", page_icon="💚", layout="wide", initial_sidebar_state="collapsed")
inject_global_styles()
apply_luxe_theme()
require_member()
utility_logout_bar()
topbar("My Weekly Plan", "Your complete seven-day nutritionist recommendation plan.", "Member recommendations")

render_member_recommendation_view(default_view="weekly")

render_page_nav("My Weekly Plan", back_page="pages/36_Todays_Journey.py", dashboard_page="pages/02_Member_Home.py", show_evaluation=False, show_dashboard=True, location="bottom")
render_back_to_top()
