import streamlit as st

from components.guards import require_admin
from components.ui_common import (
    inject_global_styles,
    apply_luxe_theme,
    utility_logout_bar,
    topbar,
    render_page_nav,
    render_back_to_top,
)

st.set_page_config(page_title="Manage & Allocate Recipes-1", page_icon="💚", layout="wide", initial_sidebar_state="collapsed")

inject_global_styles()
apply_luxe_theme()
require_admin()
utility_logout_bar()
topbar(
    "Manage & Allocate Recipes-1",
    "Parallel admin meal-library workspace. Existing Recipe Manager remains available as fallback.",
    "Admin meal library",
)

st.markdown("""
<style>
.hm-a1-grid{display:grid;grid-template-columns:1.25fr .85fr;gap:1rem;margin:.8rem 0 1rem 0;}
.hm-a1-card{border:1px solid #E3C98E;background:linear-gradient(180deg,#FFFDF8 0%,#FFF9EC 100%);border-radius:22px;padding:1rem;box-shadow:0 10px 24px rgba(15,23,42,.05);}
.hm-a1-title{color:#064E3B;font-size:1.1rem;font-weight:950;margin:0 0 .35rem 0;}
.hm-a1-sub{color:#475569;font-size:.88rem;font-weight:720;margin:0 0 .65rem 0;line-height:1.45;}
.hm-a1-chip{display:inline-flex;padding:.22rem .58rem;border:1px solid #E3C98E;border-radius:999px;background:#FFF7E6;color:#7A5A16;font-size:.76rem;font-weight:850;margin:.14rem .16rem .2rem 0;}
.hm-a1-placeholder{border:1px dashed #D9C28F;background:#FFF9EC;border-radius:18px;padding:1rem;color:#7A5A16;font-weight:800;margin:.7rem 0;}
@media(max-width:780px){.hm-a1-grid{grid-template-columns:1fr;}}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hm-a1-grid">
  <div class="hm-a1-card">
    <div class="hm-a1-title">Meal Library Workspace</div>
    <div class="hm-a1-sub">Recipes-1 is the new admin-side experimental workspace for meal/recipe presentation and allocation flow.</div>
    <span class="hm-a1-chip">Create</span>
    <span class="hm-a1-chip">Import</span>
    <span class="hm-a1-chip">Allocate</span>
    <span class="hm-a1-chip">Feedback</span>
  </div>
  <div class="hm-a1-card">
    <div class="hm-a1-title">Fallback protected</div>
    <div class="hm-a1-sub">The existing Manage & Allocate Recipes page is still available for production use.</div>
  </div>
</div>
<div class="hm-a1-placeholder">Recipes-1 placeholder workspace. Data binding and create/edit forms will be connected after visual acceptance.</div>
""", unsafe_allow_html=True)

render_page_nav("Manage & Allocate Recipes-1", back_page="pages/10_Admin_Dashboard.py", dashboard_page="pages/10_Admin_Dashboard.py", show_evaluation=False, show_dashboard=True, location="bottom")
render_back_to_top()

# v102.2D: real parallel admin Recipes-1 page.
