import streamlit as st

from components.guards import require_member
from components.member_recommendation_display import render_member_recommendation_view
from components.ui_common import inject_global_styles, apply_luxe_theme, utility_logout_bar, topbar, render_page_nav, render_back_to_top

st.set_page_config(page_title="Member Plan", page_icon="💚", layout="wide", initial_sidebar_state="collapsed")
inject_global_styles()
apply_luxe_theme()
require_member()
utility_logout_bar()
topbar("Member Plan", "Your full seven-day nutritionist plan.", "Member plan")

render_member_recommendation_view(default_view="recommendation")

render_page_nav("Member Plan", back_page="pages/02_Member_Home.py", dashboard_page="pages/02_Member_Home.py", show_evaluation=False, show_dashboard=True, location="bottom")
render_back_to_top()
