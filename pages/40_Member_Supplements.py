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

st.set_page_config(page_title="My Supplements", page_icon="💚", layout="wide", initial_sidebar_state="collapsed")

inject_global_styles()
apply_luxe_theme()
require_member()
utility_logout_bar()
topbar(
    "My Supplements",
    "Your current supplement regimen and instructions from your nutritionist.",
    "Member supplements",
)

st.markdown("""
<style>
.hm-ms-page{max-width:960px;margin:0 auto;}
.hm-ms-card{border:1px solid #E3C98E;background:linear-gradient(180deg,#FFFDF8 0%,#FFF9EC 100%);border-radius:20px;padding:1rem;box-shadow:0 10px 24px rgba(15,23,42,.05);margin:.75rem 0;}
.hm-ms-title{color:#064E3B;font-size:1.05rem;font-weight:950;margin-bottom:.25rem;}
.hm-ms-sub{color:#475569;font-size:.86rem;font-weight:700;line-height:1.45;}
.hm-ms-row{border:1px solid #E6D4A8;background:#FFFDF8;border-radius:16px;padding:.85rem;margin:.7rem 0;display:grid;grid-template-columns:42px 1fr;gap:.75rem;}
.hm-ms-icon{width:36px;height:36px;border-radius:999px;background:#FFF0EA;color:#B35C4D;display:flex;align-items:center;justify-content:center;font-weight:950;}
.hm-ms-icon.blue{background:#DDF7F3;color:#006D6F;}
.hm-ms-name{color:#1F2937;font-size:.95rem;font-weight:930;margin-bottom:.15rem;}
.hm-ms-dose{color:#64748B;font-size:.80rem;font-weight:760;}
.hm-ms-chip{display:inline-flex;background:#F8F5EE;border:1px solid #E6D4A8;border-radius:999px;padding:.12rem .42rem;font-size:.68rem;font-weight:850;color:#475569;margin:.34rem .16rem 0 0;}
.hm-ms-note{border:1px dashed #D9C28F;background:#FFF9EC;border-radius:16px;padding:.85rem;color:#7A5A16;font-size:.82rem;font-weight:790;margin:.85rem 0;}
.hm-ms-tabs{display:flex;justify-content:center;gap:.35rem;flex-wrap:wrap;margin:1rem 0 .25rem;}
.hm-ms-tab{border:1px dashed #9AB6FF;border-radius:999px;padding:.32rem .55rem;font-size:.72rem;font-weight:850;color:#475569;background:#FFFDF8;}
.hm-ms-tab.active{background:#006D6F;color:#FFF;border-color:#006D6F;}
@media(max-width:760px){.hm-ms-row{grid-template-columns:36px 1fr}}
</style>
""", unsafe_allow_html=True)

st.markdown("<div class='hm-ms-page'>", unsafe_allow_html=True)

st.markdown("""
<div class='hm-ms-card'>
  <div class='hm-ms-title'>Active Regimen</div>
  <div class='hm-ms-sub'>Follow the timing and dosage advised by your nutritionist. If anything feels unclear, reach out before making changes.</div>
</div>
""", unsafe_allow_html=True)

supplements = [
    {"name": "Vitamin D3 + K2", "dose": "5000 IU / 100 mcg · Capsule", "timing": ["Morning", "With Food"], "icon": ""},
    {"name": "Magnesium Glycinate", "dose": "400 mg · Powder", "timing": ["Evening", "Before Bed"], "icon": "blue"},
]

for item in supplements:
    chips = "".join([f"<span class='hm-ms-chip'>{t}</span>" for t in item["timing"]])
    st.markdown(f"""
    <div class='hm-ms-row'>
      <div class='hm-ms-icon {item['icon']}'>◉</div>
      <div>
        <div class='hm-ms-name'>{item['name']}</div>
        <div class='hm-ms-dose'>{item['dose']}</div>
        <div>{chips}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div class='hm-ms-note'>This is a v102.3 view-only shell. Live member-specific supplement publishing will be connected after admin workflow acceptance.</div>", unsafe_allow_html=True)

st.markdown("""
<div class='hm-ms-tabs'>
  <span class='hm-ms-tab'>Member Plan</span>
  <span class='hm-ms-tab'>Meal Diary</span>
  <span class='hm-ms-tab active'>Supplements</span>
  <span class='hm-ms-tab'>Exercises</span>
</div>
""", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

render_page_nav("My Supplements", back_page="pages/02_Member_Home.py", dashboard_page="pages/02_Member_Home.py", show_evaluation=False, show_dashboard=True, location="bottom")
render_back_to_top()

# v102.3: Member Supplements view shell.
