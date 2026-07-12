import streamlit as st

from components.guards import require_member
from components.member_recommendation_member_labels import render_my_weekly_plan_view
from components.ui_common import inject_global_styles, apply_luxe_theme, utility_logout_bar, topbar, render_page_nav, render_back_to_top

st.set_page_config(page_title="My Weekly Plan", page_icon="💚", layout="wide", initial_sidebar_state="collapsed")
inject_global_styles()
apply_luxe_theme()
require_member()
utility_logout_bar()
topbar("My Weekly Plan", "Your complete seven-day nutritionist recommendation plan.", "Member plan")

st.markdown(
    """
    <style>
    div[data-testid="stExpander"]{margin:.55rem 0 .82rem 0!important;}
    div[data-testid="stExpander"] details{border:1.35px solid #D8A84E!important;border-radius:14px!important;background:#FFFFFF!important;box-shadow:0 6px 14px rgba(15,23,42,.045)!important;overflow:hidden!important;}
    div[data-testid="stExpander"] details > summary{min-height:2.72rem!important;display:flex!important;align-items:center!important;justify-content:center!important;gap:.45rem!important;background:#FFFFFF!important;padding:.55rem .75rem!important;border-radius:14px!important;text-align:center!important;}
    div[data-testid="stExpander"] details > summary svg{width:13px!important;height:13px!important;min-width:13px!important;flex:0 0 13px!important;color:#064E3B!important;margin:0!important;}
    div[data-testid="stExpander"] details > summary [data-testid="stMarkdownContainer"]{min-width:0!important;max-width:100%!important;}
    div[data-testid="stExpander"] details > summary p{font-weight:880!important;color:#064E3B!important;font-size:.88rem!important;line-height:1.2!important;white-space:normal!important;overflow-wrap:normal!important;word-break:normal!important;margin:0!important;text-align:center!important;}
    div[data-testid="stExpander"] details[open] > summary{background:linear-gradient(135deg,#FFFDF8 0%,#FFF6E5 100%)!important;border-bottom:1px solid #E7D8BE!important;}
    </style>
    """,
    unsafe_allow_html=True,
)

render_my_weekly_plan_view()

render_page_nav("My Weekly Plan", back_page="pages/02_Member_Home.py", dashboard_page="pages/02_Member_Home.py", show_evaluation=False, show_dashboard=True, location="bottom")
render_back_to_top()
