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

st.set_page_config(page_title="Exercises-1", page_icon="💚", layout="wide", initial_sidebar_state="collapsed")

inject_global_styles()
apply_luxe_theme()
require_member()
utility_logout_bar()
topbar(
    "Exercises-1",
    "New movement-library experience for assigned movement, stretching and exercise guidance. Existing Exercises page remains available as fallback.",
    "Member movement library",
)

st.markdown("""
<style>
.hm-e1-hero-grid{display:grid;grid-template-columns:1.2fr .9fr;gap:1rem;margin:.8rem 0 1rem 0;}
.hm-e1-card{border:1px solid #E3C98E;background:linear-gradient(180deg,#FFFDF8 0%,#FFF9EC 100%);border-radius:22px;padding:1rem;box-shadow:0 10px 24px rgba(15,23,42,.05);}
.hm-e1-dark{background:#006D6F;color:#F8FAFC;border-color:#006D6F;}
.hm-e1-title{color:#064E3B;font-size:1.1rem;font-weight:950;margin:0 0 .35rem 0;}
.hm-e1-dark .hm-e1-title{color:#F8FAFC;}
.hm-e1-sub{color:#475569;font-size:.88rem;font-weight:720;margin:0 0 .65rem 0;line-height:1.45;}
.hm-e1-dark .hm-e1-sub{color:#DDF7F3;}
.hm-e1-chip{display:inline-flex;padding:.22rem .58rem;border:1px solid #E3C98E;border-radius:999px;background:#FFF7E6;color:#7A5A16;font-size:.76rem;font-weight:850;margin:.14rem .16rem .2rem 0;}
.hm-e1-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:.85rem;margin:.8rem 0;}
.hm-e1-item{border:1px solid #E3C98E;background:#FFFDF8;border-radius:18px;padding:.85rem .95rem;}
.hm-e1-item h4{margin:.1rem 0 .35rem 0;color:#064E3B;}
.hm-e1-item p{margin:.1rem 0;color:#475569;font-size:.86rem;font-weight:700;}
.hm-e1-placeholder{border:1px dashed #D9C28F;background:#FFF9EC;border-radius:18px;padding:1rem;text-align:center;color:#7A5A16;font-weight:800;margin:.7rem 0;}
@media(max-width:780px){.hm-e1-hero-grid,.hm-e1-grid{grid-template-columns:1fr;}}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hm-e1-hero-grid">
  <div class="hm-e1-card">
    <div class="hm-e1-title">Exercise Library</div>
    <div class="hm-e1-sub">This is the parallel Exercises-1 member page. It is intentionally separate from the existing Exercises page so the new UX can be tested safely.</div>
    <span class="hm-e1-chip">Assigned movement</span>
    <span class="hm-e1-chip">Duration</span>
    <span class="hm-e1-chip">Intensity</span>
    <span class="hm-e1-chip">Feedback-ready</span>
  </div>
  <div class="hm-e1-card hm-e1-dark">
    <div class="hm-e1-title">Movement Overview</div>
    <div class="hm-e1-sub">A cleaner view of stretching, yoga, mobility and exercise recommendations.</div>
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hm-e1-grid">
  <div class="hm-e1-item"><h4>Mindful Yoga</h4><p>Assigned yoga recommendation placeholder.</p></div>
  <div class="hm-e1-item"><h4>Stretching</h4><p>Mobility and flexibility placeholder.</p></div>
  <div class="hm-e1-item"><h4>Light Movement</h4><p>Daily movement guidance placeholder.</p></div>
</div>
""", unsafe_allow_html=True)

st.markdown("<div class='hm-e1-placeholder'>Exercises-1 currently uses a safe placeholder/listing-first UX. Allocation/data binding can be connected after visual acceptance.</div>", unsafe_allow_html=True)

render_page_nav("Exercises-1", back_page="pages/02_Member_Home.py", dashboard_page="pages/02_Member_Home.py", show_evaluation=False, show_dashboard=True, location="bottom")
render_back_to_top()

# v102.2D: real parallel member Exercises-1 page.
