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

st.set_page_config(page_title="Exercises-1", page_icon="💚", layout="wide", initial_sidebar_state="collapsed")
inject_global_styles()
apply_luxe_theme()
require_admin()
utility_logout_bar()
topbar("Exercises-1", "A refreshed exercise library inspired by the shared movement mockup.", "Admin movement library")
st.markdown("""
<style>
.hm-ex-page{max-width:1120px;margin:0 auto;}
.hm-ex-head{display:flex;align-items:flex-start;justify-content:space-between;gap:1rem;margin:.3rem 0 .8rem 0;}
.hm-ex-title{font-size:1.85rem;font-weight:950;color:#064E3B;margin:0;line-height:1.05;}
.hm-ex-sub{font-size:.9rem;color:#475569;font-weight:650;line-height:1.45;max-width:560px;margin:.35rem 0 0;}
.hm-ex-actions{display:flex;gap:.55rem;}
.hm-ex-btn{border:1px solid #006D6F;border-radius:999px;padding:.55rem 1rem;font-size:.76rem;font-weight:900;}
.hm-ex-btn.primary{background:#006D6F;color:white;}
.hm-ex-btn.secondary{background:#FFFDF8;color:#006D6F;}
.hm-ex-search{border:1px solid #E3C98E;border-radius:999px;background:#FFFDF8;color:#64748B;font-size:.82rem;font-weight:650;padding:.7rem 1rem;margin:.9rem 0 .65rem 0;}
.hm-ex-chiprow{display:flex;flex-wrap:wrap;gap:.35rem;margin-bottom:1rem;}
.hm-ex-chip{border-radius:999px;background:#F1EFE8;color:#334155;padding:.28rem .62rem;font-size:.72rem;font-weight:850;}
.hm-ex-chip.active{background:#007A7A;color:white;}
.hm-ex-layout{display:grid;grid-template-columns:1.25fr .75fr;gap:1rem;margin:.85rem 0 1rem;}
.hm-ex-feature{border:1px solid #E3C98E;border-radius:18px;background:#FFFDF8;padding:1rem;display:grid;grid-template-columns:210px 1fr;gap:1rem;box-shadow:0 8px 18px rgba(15,23,42,.04);}
.hm-ex-img{border-radius:12px;background:linear-gradient(135deg,#E8D8BE,#6B7A4D);min-height:150px;}
.hm-ex-badge{display:inline-block;border-radius:999px;background:#FFB9A8;color:#8A3A27;padding:.22rem .58rem;font-size:.68rem;font-weight:900;margin-bottom:.5rem;}
.hm-ex-name{font-size:1.35rem;color:#064E3B;font-weight:950;margin:0 0 .45rem;}
.hm-ex-desc{font-size:.82rem;color:#475569;font-weight:650;line-height:1.42;}
.hm-ex-meta{font-size:.72rem;color:#64748B;font-weight:850;margin-top:.75rem;}
.hm-ex-overview{border-radius:18px;background:#006D6F;color:#F8FAFC;padding:1.1rem;box-shadow:0 10px 24px rgba(15,23,42,.05);}
.hm-ex-over-title{font-size:1.05rem;font-weight:950;margin-bottom:.3rem;}
.hm-ex-over-sub{font-size:.78rem;font-weight:700;color:#DDF7F3;margin-bottom:1rem;}
.hm-ex-stat{display:flex;justify-content:space-between;border-top:1px solid rgba(255,255,255,.18);padding:.62rem 0;font-size:.75rem;font-weight:850;}
.hm-ex-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:.85rem;margin:.85rem 0 1rem;}
.hm-ex-card{border:1px solid #E3C98E;border-radius:18px;background:#FFFDF8;min-height:170px;padding:.75rem;box-shadow:0 8px 18px rgba(15,23,42,.04);}
.hm-ex-thumb{border-radius:12px;background:linear-gradient(135deg,#D5B56D,#17202A);height:110px;margin-bottom:.65rem;}
.hm-ex-card-title{color:#064E3B;font-size:.95rem;font-weight:950;}
.hm-ex-card-sub{color:#64748B;font-size:.75rem;font-weight:700;margin-top:.25rem;}
@media(max-width:850px){.hm-ex-head{display:block}.hm-ex-actions{margin-top:.75rem}.hm-ex-layout,.hm-ex-feature{grid-template-columns:1fr}.hm-ex-grid{grid-template-columns:1fr}}
</style>
<div class="hm-ex-page">
  <div class="hm-ex-head">
    <div><h1 class="hm-ex-title">Exercise Library</h1><div class="hm-ex-sub">Curated gentle movement and mindful exercises to support holistic patient wellness.</div></div>
    <div class="hm-ex-actions"><div class="hm-ex-btn secondary">☰ Filter</div><div class="hm-ex-btn primary">+ New Exercise</div></div>
  </div>
  <div class="hm-ex-search">⌕ &nbsp; Search for gentle movements, stretches, or yoga poses...</div>
  <div class="hm-ex-chiprow"><span class="hm-ex-chip">All</span><span class="hm-ex-chip active">Mindful Yoga</span><span class="hm-ex-chip">Stretching</span><span class="hm-ex-chip">Pilates</span><span class="hm-ex-chip">Mobility</span></div>
  <div class="hm-ex-layout">
    <div class="hm-ex-feature"><div class="hm-ex-img"></div><div><span class="hm-ex-badge">Featured</span><div class="hm-ex-name">Morning Sun Salutation</div><div class="hm-ex-desc">A sequence of gentle postures designed to awaken the body, improve circulation and set a calm tone.</div><div class="hm-ex-meta">◷ 15 mins &nbsp;&nbsp; ♙ Beginner</div></div></div>
    <div class="hm-ex-overview"><div class="hm-ex-over-title">Library Overview</div><div class="hm-ex-over-sub">Your curated collection of wellness movements.</div><div class="hm-ex-stat"><span>Total Exercises</span><span>142</span></div><div class="hm-ex-stat"><span>Categories</span><span>8</span></div><div class="hm-ex-btn secondary" style="text-align:center;margin-top:.8rem;background:white;">Manage Categories</div></div>
  </div>
  <div class="hm-ex-grid"><div class="hm-ex-card"><div class="hm-ex-thumb"></div><div class="hm-ex-card-title">Restorative Flow</div><div class="hm-ex-card-sub">Gentle yoga sequence</div></div><div class="hm-ex-card"><div class="hm-ex-thumb"></div><div class="hm-ex-card-title">Breath Mobility</div><div class="hm-ex-card-sub">Low-impact movement</div></div><div class="hm-ex-card"><div class="hm-ex-thumb"></div><div class="hm-ex-card-title">Guided Stretch</div><div class="hm-ex-card-sub">Evening release</div></div></div>
</div>""", unsafe_allow_html=True)
render_page_nav("Exercises-1", back_page="pages/10_Admin_Dashboard.py", dashboard_page="pages/10_Admin_Dashboard.py", show_evaluation=False, show_dashboard=True, location="bottom")
render_back_to_top()
# v102.2E: mockup-aligned admin Exercises-1 page.
