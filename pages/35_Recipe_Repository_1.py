import streamlit as st

from components.guards import require_member
from components.ui_common import (
    inject_global_styles,
    apply_luxe_theme,
    utility_logout_bar,
    topbar,
    render_page_nav,
    render_back_to_top,
)
st.set_page_config(page_title="Recipes-1", page_icon="💚", layout="wide", initial_sidebar_state="collapsed")

inject_global_styles()
apply_luxe_theme()
require_member()
utility_logout_bar()
topbar(
    "Recipes-1",
    "New meal-library experience for assigned meals and recipe guidance. Existing Recipes page remains available as fallback.",
    "Member meal library",
)

st.markdown("""
<style>
.hm-r1-hero-grid{display:grid;grid-template-columns:1.25fr .85fr;gap:1rem;margin:.8rem 0 1rem 0;}
.hm-r1-card{border:1px solid #E3C98E;background:linear-gradient(180deg,#FFFDF8 0%,#FFF9EC 100%);border-radius:22px;padding:1rem;box-shadow:0 10px 24px rgba(15,23,42,.05);}
.hm-r1-title{color:#064E3B;font-size:1.1rem;font-weight:950;margin:0 0 .35rem 0;}
.hm-r1-sub{color:#475569;font-size:.88rem;font-weight:720;margin:0 0 .65rem 0;line-height:1.45;}
.hm-r1-chip{display:inline-flex;padding:.22rem .58rem;border:1px solid #E3C98E;border-radius:999px;background:#FFF7E6;color:#7A5A16;font-size:.76rem;font-weight:850;margin:.14rem .16rem .2rem 0;}
.hm-r1-section-title{color:#064E3B;font-size:1.02rem;font-weight:950;margin:1rem 0 .5rem 0;}
.hm-r1-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:.85rem;margin:.6rem 0;}
.hm-r1-meal{border:1px solid #E3C98E;background:#FFFDF8;border-radius:18px;padding:.85rem .95rem;}
.hm-r1-meal h4{margin:.1rem 0 .35rem 0;color:#064E3B;}
.hm-r1-meal p{margin:.1rem 0;color:#475569;font-size:.86rem;font-weight:700;}
.hm-r1-placeholder{border:1px dashed #D9C28F;background:#FFF9EC;border-radius:18px;padding:1rem;text-align:center;color:#7A5A16;font-weight:800;margin:.7rem 0;}
@media(max-width:780px){.hm-r1-hero-grid,.hm-r1-grid{grid-template-columns:1fr;}}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hm-r1-hero-grid">
  <div class="hm-r1-card">
    <div class="hm-r1-title">Meal Library & Workspace</div>
    <div class="hm-r1-sub">This is the parallel Recipes-1 member page. It is intentionally separate from the existing Recipes page so the new UX can be tested safely.</div>
    <span class="hm-r1-chip">Assigned meals</span>
    <span class="hm-r1-chip">Meal timing</span>
    <span class="hm-r1-chip">Recipe guidance</span>
    <span class="hm-r1-chip">Feedback-ready</span>
  </div>
  <div class="hm-r1-card">
    <div class="hm-r1-title">Fallback protected</div>
    <div class="hm-r1-sub">The old Recipes page is still available. Once Recipes-1 is accepted, the old page can be retired or redirected.</div>
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown("<div class='hm-r1-section-title'>Today’s Meal Guidance</div>", unsafe_allow_html=True)
st.markdown("""
<div class="hm-r1-grid">
  <div class="hm-r1-meal"><h4>Breakfast</h4><p>Assigned recipe card will appear here.</p></div>
  <div class="hm-r1-meal"><h4>Lunch</h4><p>Meal-plan card and nutritionist notes will appear here.</p></div>
  <div class="hm-r1-meal"><h4>Dinner</h4><p>Recipe details, portions, and instructions will appear here.</p></div>
  <div class="hm-r1-meal"><h4>Snacks</h4><p>Optional snack recommendation placeholder.</p></div>
</div>
""", unsafe_allow_html=True)

st.markdown("<div class='hm-r1-placeholder'>Recipes-1 currently uses a safe placeholder/listing-first UX. Allocation/data binding can be connected after visual acceptance.</div>", unsafe_allow_html=True)

render_page_nav("Recipes-1", back_page="pages/02_Member_Home.py", dashboard_page="pages/02_Member_Home.py", show_evaluation=False, show_dashboard=True, location="bottom")
render_back_to_top()

# v102.2D: real parallel member Recipes-1 page.
