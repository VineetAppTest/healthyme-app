import streamlit as st

from components.guards import require_admin
from components.profile_source_alignment import render_profile_source_alignment
from components.ui_common import (
    apply_luxe_theme,
    inject_global_styles,
    render_back_to_top,
    render_page_nav,
    utility_logout_bar,
)

APP_BUILD_VERSION = "v100.37"
APP_BUILD_LABEL = "Repository Source Alignment"

st.set_page_config(
    page_title="Profile Source Alignment",
    page_icon="💚",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_global_styles()
apply_luxe_theme()
require_admin()
utility_logout_bar()

st.markdown(
    f"""
    <div class='hero-shell'>
      <div class='hm-pb-brand-row'>
        <span class='hm-pb-brand'>HealthyMe</span>
        <span class='hm-pb-version'>{APP_BUILD_VERSION} · {APP_BUILD_LABEL}</span>
      </div>
      <div class='hero-kicker'>System Tools · Source Alignment</div>
      <div class='hero-title'>Repository-to-Profile Builder Source Alignment</div>
      <div class='hero-subtitle'>Checks whether Recipe, Exercise and Supplement source information is fully available to the Profile Builder before member recommendation consumption is wired.</div>
      <div><span class='meta-pill'>Contract-first diagnostic</span></div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
<style>
.hm-pb-brand-row{display:flex;align-items:baseline;gap:.55rem;flex-wrap:wrap;margin-bottom:.35rem;}
.hm-pb-brand{color:#064E3B;font-size:.82rem;font-weight:950;letter-spacing:.02em;text-transform:uppercase;}
.hm-pb-version{color:#72551A;font-size:.72rem;font-weight:900;background:#F5E7C8;border-radius:999px;padding:.22rem .55rem;}
.hm-title{color:#064E3B;font-size:1.04rem;font-weight:950;margin:.35rem 0 .25rem}.hm-sub{color:#64748B;font-size:.82rem;font-weight:720;margin:0 0 .7rem}.hm-preview{border:1px dashed #D8A84E;background:#FFF9EC;border-radius:16px;padding:.75rem .85rem;margin:.35rem 0;color:#475569;font-size:.83rem;font-weight:740;line-height:1.45}.hm-count-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:.65rem;margin:.55rem 0 1rem}.hm-count-card{background:#fff;border:1px solid #E3C98E;border-radius:15px;padding:.7rem .8rem}.hm-count-card b{display:block;color:#064E3B;font-size:.95rem}.hm-count-card span{color:#64748B;font-size:.78rem;font-weight:780}
@media(max-width:900px){.hm-count-grid{grid-template-columns:1fr}}
</style>
""",
    unsafe_allow_html=True,
)

render_profile_source_alignment()

render_page_nav(
    "Profile Source Alignment",
    back_page="pages/10_Admin_Dashboard.py",
    dashboard_page="pages/10_Admin_Dashboard.py",
    show_evaluation=False,
    show_dashboard=True,
    location="bottom",
)
render_back_to_top()
