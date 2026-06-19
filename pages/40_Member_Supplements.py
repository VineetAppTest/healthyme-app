import html

import streamlit as st

from components.guards import require_member
from components.db import list_active_member_supplements
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
    "Your active supplement regimen assigned by your nutritionist.",
    "Member supplements",
)


def _esc(value):
    return html.escape(str(value or ""))


def _chips(text):
    parts = [p.strip() for p in str(text or "").replace("|", ",").split(",") if p.strip()]
    if not parts:
        return "<span class='hm-ms-chip'>As advised</span>"
    return "".join([f"<span class='hm-ms-chip'>{_esc(p)}</span>" for p in parts])


st.markdown("""
<style>
.hero-shell{margin-bottom:.20rem!important;}
div[data-testid="stVerticalBlock"] > div:has(.hero-shell){margin-bottom:.05rem!important;padding-bottom:.05rem!important;}
.hm-ms-page{max-width:960px;margin:-.18rem auto 0 auto;}
.hm-ms-card{border:1px solid #E3C98E;background:linear-gradient(180deg,#FFFDF8 0%,#FFF9EC 100%);border-radius:20px;padding:1rem;box-shadow:0 10px 24px rgba(15,23,42,.05);margin:.25rem 0 .55rem 0;}
.hm-ms-title{color:#064E3B;font-size:1.05rem;font-weight:950;margin-bottom:.25rem;}
.hm-ms-sub{color:#475569;font-size:.86rem;font-weight:700;line-height:1.45;}
.hm-ms-row{border:1px solid #E6D4A8;background:#FFFDF8;border-radius:16px;padding:.85rem;margin:.7rem 0;display:grid;grid-template-columns:42px 1fr;gap:.75rem;}
.hm-ms-icon{width:36px;height:36px;border-radius:999px;background:#FFF0EA;color:#B35C4D;display:flex;align-items:center;justify-content:center;font-weight:950;}
.hm-ms-name{color:#1F2937;font-size:.95rem;font-weight:930;margin-bottom:.15rem;}
.hm-ms-dose{color:#64748B;font-size:.80rem;font-weight:760;margin:.10rem 0;}
.hm-ms-chip{display:inline-flex;background:#F8F5EE;border:1px solid #E6D4A8;border-radius:999px;padding:.12rem .42rem;font-size:.68rem;font-weight:850;color:#475569;margin:.34rem .16rem 0 0;}
.hm-ms-note{border:1px dashed #D9C28F;background:#FFF9EC;border-radius:16px;padding:.85rem;color:#7A5A16;font-size:.82rem;font-weight:790;margin:.85rem 0;}
.hm-ms-empty{border:1px dashed #D9C28F;background:#FFFDF8;border-radius:18px;padding:1.1rem;color:#64748B;font-size:.88rem;font-weight:760;margin:.85rem 0;}
.hm-ms-tabs{display:flex;justify-content:center;gap:.35rem;flex-wrap:wrap;margin:1rem 0 .25rem;}
.hm-ms-tab{border:1px dashed #9AB6FF;border-radius:999px;padding:.32rem .55rem;font-size:.72rem;font-weight:850;color:#475569;background:#FFFDF8;}
.hm-ms-tab.active{background:#006D6F;color:#FFF;border-color:#006D6F;}
@media(max-width:760px){.hm-ms-row{grid-template-columns:36px 1fr}}
</style>
""", unsafe_allow_html=True)

user_id = st.session_state.get("user_id", "")
supplements = list_active_member_supplements(user_id)

st.markdown("<div class='hm-ms-page'>", unsafe_allow_html=True)

st.markdown(f"""
<div class='hm-ms-card'>
  <div class='hm-ms-title'>My Supplement Regimen</div>
  <div class='hm-ms-sub'>Showing only your currently active supplements assigned by your nutritionist. Stopped items are removed from this view automatically.</div>
</div>
""", unsafe_allow_html=True)

if not supplements:
    st.markdown("<div class='hm-ms-empty'>No supplements have been assigned yet. Your nutritionist will update this section when applicable.</div>", unsafe_allow_html=True)
else:
    for item in supplements:
        st.markdown(f"""
        <div class='hm-ms-row'>
          <div class='hm-ms-icon'>◉</div>
          <div>
            <div class='hm-ms-name'>{_esc(item.get('supplement_name'))}</div>
            <div class='hm-ms-dose'>{_esc(item.get('dosage') or 'Dosage not specified')} · {_esc(item.get('frequency') or 'Frequency not specified')}</div>
            <div class='hm-ms-dose'>Start date: {_esc(item.get('start_date') or 'As advised')}</div>
            {f"<div class='hm-ms-dose'>End date: {_esc(item.get('end_date'))}</div>" if item.get('end_date') else ""}
            <div>{_chips(item.get('timing'))}</div>
            <div class='hm-ms-dose'>Instructions: {_esc(item.get('instructions') or 'Follow as advised by your nutritionist.')}</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

render_page_nav("My Supplements", back_page="pages/02_Member_Home.py", dashboard_page="pages/02_Member_Home.py", show_evaluation=False, show_dashboard=True, location="bottom")
render_back_to_top()

# v102.3A: Member Supplements active regimen publishing view. Expired end-date records auto-stop before reaching this active view.
