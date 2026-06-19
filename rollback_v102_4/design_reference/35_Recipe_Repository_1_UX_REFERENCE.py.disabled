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
topbar("Recipes-1", "A refreshed meal library and plan workspace inspired by the shared mockup.", "Member meal library")
st.markdown("""
<style>
.hm-rx-page{max-width:1120px;margin:0 auto;}
.hm-rx-headrow{display:flex;align-items:flex-start;justify-content:space-between;gap:1rem;margin:.35rem 0 .95rem 0;}
.hm-rx-title{color:#0B1F1E;font-size:1.8rem;font-weight:950;line-height:1.05;margin:0;}
.hm-rx-sub{color:#475569;font-size:.88rem;font-weight:650;line-height:1.45;margin:.35rem 0 0 0;max-width:520px;}
.hm-rx-search{border:1px solid #E3C98E;background:#FFFDF8;border-radius:999px;padding:.55rem 1rem;color:#64748B;font-size:.78rem;min-width:230px;text-align:left;}
.hm-rx-layout{display:grid;grid-template-columns:1.18fr .82fr;gap:1.15rem;margin-top:.65rem;}
.hm-rx-chiprow{display:flex;flex-wrap:wrap;gap:.35rem;margin:.55rem 0 .85rem 0;}
.hm-rx-chip{display:inline-flex;align-items:center;padding:.33rem .75rem;border-radius:999px;border:1px solid #E6D4A8;background:#F7F3EA;color:#1F2937;font-size:.72rem;font-weight:850;}
.hm-rx-chip.active{background:#007A7A;color:white;border-color:#007A7A;}
.hm-rx-chip.soft{background:#F6C9BD;color:#7A2E1D;border-color:#F6C9BD;}
.hm-rx-cardgrid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:.78rem;}
.hm-rx-foodcard{border:1px solid #E6D4A8;border-radius:16px;background:#FFFDF8;box-shadow:0 8px 18px rgba(15,23,42,.04);overflow:hidden;min-height:196px;}
.hm-rx-img{height:118px;background:linear-gradient(135deg,#6B5139,#E7D7B7);position:relative;}
.hm-rx-img.salad{background:linear-gradient(135deg,#536D36,#F2B05E);}
.hm-rx-img.move{background:#F8D6CE;display:flex;align-items:center;justify-content:center;color:#A4665A;font-size:2rem;}
.hm-rx-tag{position:absolute;top:.5rem;left:.5rem;border-radius:999px;padding:.18rem .45rem;background:#F5EEDC;color:#7A5A16;font-size:.62rem;font-weight:900;}
.hm-rx-cardbody{padding:.72rem .82rem;}
.hm-rx-cardtitle{font-size:.98rem;color:#263B35;font-weight:950;margin:0 0 .25rem 0;}
.hm-rx-carddesc{font-size:.76rem;color:#64748B;font-weight:650;line-height:1.35;margin:0 0 .45rem 0;}
.hm-rx-kcal{font-size:.68rem;color:#7A5A16;font-weight:850;}
.hm-rx-plus{float:right;width:24px;height:24px;border-radius:999px;background:#007A7A;color:white;display:inline-flex;align-items:center;justify-content:center;font-weight:900;}
.hm-rx-plan{border:1px solid #E6D4A8;border-radius:18px;background:#FFFDF8;box-shadow:0 10px 24px rgba(15,23,42,.05);padding:1rem;}
.hm-rx-plan-head{display:flex;justify-content:space-between;align-items:center;margin-bottom:.8rem;}
.hm-rx-plan-title{font-size:1.25rem;color:#334155;font-weight:950;}
.hm-rx-client{border:1px solid #EFE7D5;border-radius:12px;background:#F8F5EE;padding:.65rem;display:flex;gap:.55rem;align-items:center;margin-bottom:.85rem;}
.hm-rx-avatar{width:32px;height:32px;border-radius:999px;background:#007A7A;color:#FFF;display:flex;align-items:center;justify-content:center;font-weight:950;}
.hm-rx-clienttext{font-size:.72rem;color:#475569;font-weight:800;line-height:1.25;}
.hm-rx-drop{border:1px dashed #D8C28E;border-radius:16px;background:#FFFDF8;min-height:145px;display:flex;align-items:center;justify-content:center;text-align:center;color:#64748B;font-size:.82rem;font-weight:760;padding:1rem;margin-bottom:.9rem;}
.hm-rx-actions{display:flex;gap:.6rem;}
.hm-rx-btn{border:1px solid #0B6B6B;border-radius:999px;padding:.55rem 1.1rem;text-align:center;font-size:.75rem;font-weight:900;flex:1;}
.hm-rx-btn.primary{background:#006D6F;color:white;}
.hm-rx-btn.secondary{background:white;color:#006D6F;}
@media(max-width:850px){.hm-rx-headrow{display:block}.hm-rx-search{margin-top:.75rem}.hm-rx-layout{grid-template-columns:1fr}.hm-rx-cardgrid{grid-template-columns:1fr}}
</style>
<div class="hm-rx-page">
  <div class="hm-rx-headrow">
    <div>
      <h1 class="hm-rx-title">Library & Workspace</h1>
      <div class="hm-rx-sub">Curated nourishing meal plans and gentle recipe ideas for your wellness journey.</div>
    </div>
    <div class="hm-rx-search">⌕ &nbsp; Search database...</div>
  </div>
  <div class="hm-rx-chiprow">
    <span class="hm-rx-chip active">All Items</span><span class="hm-rx-chip">Breakfast</span><span class="hm-rx-chip">Lunch</span><span class="hm-rx-chip">Dinner</span><span class="hm-rx-chip soft">Movement</span>
  </div>
  <div class="hm-rx-layout">
    <div class="hm-rx-cardgrid">
      <div class="hm-rx-foodcard"><div class="hm-rx-img"><span class="hm-rx-tag">Breakfast</span></div><div class="hm-rx-cardbody"><div class="hm-rx-cardtitle">Morning Harmony Bowl</div><div class="hm-rx-carddesc">A gentle start to the day with oats, chia, and seasonal berries.</div><span class="hm-rx-kcal">320 kcal</span><span class="hm-rx-plus">+</span></div></div>
      <div class="hm-rx-foodcard"><div class="hm-rx-img salad"><span class="hm-rx-tag">Lunch</span></div><div class="hm-rx-cardbody"><div class="hm-rx-cardtitle">Rooted Vitality Salad</div><div class="hm-rx-carddesc">Earthy sweet potatoes and crisp greens for sustained energy.</div><span class="hm-rx-kcal">410 kcal</span><span class="hm-rx-plus">+</span></div></div>
      <div class="hm-rx-foodcard"><div class="hm-rx-img move">☯</div><div class="hm-rx-cardbody"><div class="hm-rx-cardtitle">Restorative Stretch</div><div class="hm-rx-carddesc">15 minutes of gentle mobility to support recovery.</div><span class="hm-rx-kcal">Movement</span><span class="hm-rx-plus">+</span></div></div>
    </div>
    <div class="hm-rx-plan">
      <div class="hm-rx-plan-head"><div class="hm-rx-plan-title">Current Plan</div><div>•••</div></div>
      <div class="hm-rx-client"><div class="hm-rx-avatar">M</div><div class="hm-rx-clienttext">Member View<br/>Assigned meal plan preview</div></div>
      <div class="hm-rx-drop">Meals and gentle movement appear here when assigned by the nutritionist.</div>
      <div class="hm-rx-actions"><div class="hm-rx-btn secondary">View Draft</div><div class="hm-rx-btn primary">View Plan</div></div>
    </div>
  </div>
</div>""", unsafe_allow_html=True)
render_page_nav("Recipes-1", back_page="pages/02_Member_Home.py", dashboard_page="pages/02_Member_Home.py", show_evaluation=False, show_dashboard=True, location="bottom")
render_back_to_top()
# v102.2E: mockup-aligned member Recipes-1 page.
