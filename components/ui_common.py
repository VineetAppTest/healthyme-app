
import streamlit as st
from components.auth_session import logout_current_user

LUXE_CSS = """
<style>
#MainMenu {visibility:hidden !important;}
header[data-testid="stHeader"] {visibility:hidden !important; height:0 !important;}
[data-testid="stToolbar"] {display:none !important;}
[data-testid="stSidebar"], [data-testid="collapsedControl"], section[data-testid="stSidebar"] {display:none !important;}
:root{--hm-emerald:#064E3B;--hm-emerald-2:#0F766E;--hm-gold:#D8A84E;--hm-gold-deep:#8A5F10;--hm-gold-soft:#F5E7C8;--hm-ivory:#FFF8EE;--hm-text:#17211F;--hm-heading:#063F32;--hm-muted:#4B5A57;--hm-border:#E9DFCC;--hm-shadow:0 14px 34px rgba(25,36,31,.08);}
html, body, [data-testid="stAppViewContainer"]{background:radial-gradient(circle at top right, rgba(216,168,78,.18), transparent 25%),radial-gradient(circle at top left, rgba(6,78,59,.10), transparent 30%),linear-gradient(180deg,var(--hm-ivory) 0%,#FFFDF8 100%) !important;color:var(--hm-text)!important;}
.block-container{padding-top:.75rem!important;padding-bottom:1.1rem!important;max-width:1180px!important;}
html, body, [data-testid="stAppViewContainer"], .stApp, button, input, textarea, label, select, div, p, span{font-family:Inter,-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif!important;}
h1,h2,h3{letter-spacing:-.035em;color:var(--hm-heading)!important;}
h2{font-size:1.85rem!important;font-weight:880!important;}
h3{font-size:1.28rem!important;font-weight:820!important;}
p,label,.stCaption,.small-note{color:var(--hm-muted)!important;}
.stButton button,.stButton button:hover,.stButton button:active,.stButton button:focus{background:#fff!important;color:#063F32!important;border:1.5px solid #CDBB8F!important;border-radius:14px!important;font-weight:820!important;box-shadow:0 4px 12px rgba(25,36,31,.06)!important;outline:none!important;}
.stButton button[kind="primary"],button[kind="primary"],.stButton button[kind="primary"]:hover,.stButton button[kind="primary"]:active,.stButton button[kind="primary"]:focus{background:linear-gradient(135deg,#064E3B 0%,#0F766E 100%)!important;color:#fff!important;border-color:#064E3B!important;}
.stButton button[kind="primary"] *{color:#fff!important;}
.stButton button:disabled{background:#F4F1EA!important;color:#777E7A!important;border-color:#E2D7C2!important;opacity:1!important;}
.main-card{background:rgba(255,255,255,.88);padding:1.25rem;border-radius:22px;box-shadow:var(--hm-shadow);border:1px solid var(--hm-border);}
.hero-shell{background:linear-gradient(135deg,rgba(255,248,238,.95) 0%,rgba(255,255,255,.96) 66%,rgba(245,231,200,.65) 100%);border:1px solid var(--hm-border);border-radius:26px;box-shadow:var(--hm-shadow);padding:1.2rem 1.35rem;margin-bottom:1rem;}
.hero-kicker{display:inline-block;padding:.42rem .8rem;border-radius:999px;background:var(--hm-gold-soft);color:var(--hm-gold-deep);font-weight:800;font-size:.77rem;margin-bottom:.55rem;}
.hero-title{font-size:2rem;font-weight:940;margin:0;color:var(--hm-heading)!important;}
.hero-subtitle{margin-top:.3rem;color:var(--hm-muted)!important;max-width:780px;}
.meta-pill,.status-chip{display:inline-block;padding:.35rem .72rem;border-radius:999px;font-size:.77rem;font-weight:850;border:1px solid var(--hm-border);margin:.35rem .25rem 0 0;background:#fff;color:var(--hm-text);}
.status-ok{background:#E7F7EF;color:#166534}.status-info{background:#EAF5F8;color:#0F4C5C}.status-warn{background:#FFF4DE;color:#9A6700}.status-gold{background:var(--hm-gold-soft);color:var(--hm-gold-deep)}.status-neutral{background:#F7F4ED;color:#6B7280}
.kpi-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:.75rem;margin:.25rem 0 1rem 0}.kpi-card{background:linear-gradient(180deg,#fff 0%,#FFFBF4 100%);border:1px solid var(--hm-border);border-radius:20px;padding:1rem;box-shadow:0 8px 22px rgba(25,36,31,.05)}.kpi-label{font-size:.76rem;font-weight:850;text-transform:uppercase;letter-spacing:.05em;color:var(--hm-muted)!important}.kpi-value{font-size:1.9rem;line-height:1.05;font-weight:940;color:var(--hm-heading)!important}.kpi-note{color:var(--hm-muted)!important;font-size:.82rem}
.info-banner,.warning-banner,.success-banner{border-radius:16px;padding:.9rem 1rem;border:1px solid var(--hm-border);margin:.4rem 0 .75rem 0}.info-banner{background:#EAF5F8}.warning-banner{background:#FFF4DE}.success-banner{background:#E7F7EF}
.login-brand-row{display:flex;align-items:center;justify-content:space-between;gap:.8rem;margin-bottom:.75rem}.login-brand-name{font-size:1.9rem;font-weight:950;color:var(--hm-heading);letter-spacing:-.055em}.login-brand-sub{color:var(--hm-muted);font-size:.92rem}.login-secure-pill{display:inline-block;border-radius:999px;padding:.45rem .85rem;background:var(--hm-gold-soft);color:var(--hm-gold-deep);font-weight:850;font-size:.78rem;border:1px solid #E8D39E}.login-cred{background:#FFF4DE;border:1px solid #E8D39E;border-radius:16px;padding:.75rem .85rem;color:#4B3A16;font-size:.9rem;line-height:1.45;margin:.8rem 0}.login-access{background:#E7F7EF;border:1px solid #C9EAD7;border-radius:15px;padding:.65rem .8rem;color:#14532D;font-size:.84rem;margin-bottom:.8rem}.journey-card{background:linear-gradient(135deg,var(--hm-emerald) 0%,var(--hm-emerald-2) 78%);border-radius:26px;padding:1.35rem;box-shadow:0 16px 38px rgba(6,78,59,.18);color:#fff!important}.journey-card h3{color:#fff!important}.journey-card p{color:#E9FFF7!important}.journey-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:.65rem;margin-top:.65rem}.journey-item{background:rgba(255,255,255,.11);border:1px solid rgba(255,255,255,.17);border-radius:15px;padding:.7rem .8rem;color:#fff;font-weight:750;min-height:68px;display:flex;align-items:center}.login-feature-strip{display:grid;grid-template-columns:repeat(4,1fr);gap:.75rem;margin-top:.85rem}.login-feature{background:#fff;border:1px solid var(--hm-border);border-radius:18px;padding:.9rem;box-shadow:0 8px 20px rgba(25,36,31,.05)}.login-feature b{color:var(--hm-heading)}.login-feature p{font-size:.8rem;margin:.15rem 0 0 0;color:var(--hm-muted)!important}
.utility-bar{display:flex;align-items:center;justify-content:space-between;gap:.75rem;margin:.15rem 0 .65rem 0;padding:.45rem .65rem;border:1px solid var(--hm-border);border-radius:999px;background:rgba(255,255,255,.72);box-shadow:0 6px 18px rgba(25,36,31,.04)}.utility-user{color:var(--hm-muted);font-size:.82rem;font-weight:700}.utility-role{color:var(--hm-gold-deep);font-size:.75rem;font-weight:850;background:var(--hm-gold-soft);padding:.25rem .55rem;border-radius:999px;margin-left:.35rem}
.member-summary-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:.55rem;margin-top:.6rem}.member-summary-item{border:1px solid var(--hm-border);border-radius:16px;background:#fff;padding:.75rem .8rem;box-shadow:0 6px 16px rgba(25,36,31,.04)}.member-summary-label{color:var(--hm-muted);font-size:.74rem;font-weight:850;text-transform:uppercase;letter-spacing:.04em}.member-summary-value{margin-top:.25rem;font-size:.92rem;font-weight:850;color:var(--hm-heading)}.member-summary-ok{border-color:#CFE8DA;background:#F3FBF6}.member-summary-warn{border-color:#EAD6A4;background:#FFF8E8}.member-summary-info{border-color:#D9E9E3;background:#F3FAF7}
.repo-search-card,.csv-upload-panel{background:#fff;border:1px solid var(--hm-border);border-radius:18px;padding:1rem;margin:.35rem 0 1rem 0;box-shadow:0 8px 20px rgba(25,36,31,.04)}.repo-result-count{display:inline-block;padding:.38rem .75rem;border-radius:999px;background:var(--hm-gold-soft);color:var(--hm-gold-deep);font-weight:850;font-size:.8rem;margin:.25rem 0 .85rem}
@media(max-width:900px){.kpi-grid,.login-feature-strip{grid-template-columns:1fr 1fr}.block-container{max-width:96%!important}}@media(max-width:640px){.kpi-grid,.login-feature-strip,.journey-grid,.member-summary-grid{grid-template-columns:1fr}.login-brand-row{display:block}.login-secure-pill{margin-top:.5rem}.hero-title{font-size:1.4rem}.login-brand-name{font-size:1.55rem}}

/* --- Evaluation Status Multi-Member UX --- */
.member-filter-panel{
  background:#FFFFFF;
  border:1px solid var(--hm-border);
  border-radius:18px;
  padding:1rem;
  margin:.35rem 0 1rem 0;
  box-shadow:0 8px 20px rgba(25,36,31,.04);
}
.member-row-header{
  display:flex;
  justify-content:space-between;
  align-items:center;
  gap:.75rem;
  flex-wrap:wrap;
}
.member-row-name{
  font-size:1.05rem;
  font-weight:900;
  color:var(--hm-heading);
}
.member-row-email{
  font-size:.82rem;
  color:var(--hm-muted);
}
.member-count-pill{
  display:inline-block;
  padding:.38rem .75rem;
  border-radius:999px;
  background:var(--hm-gold-soft);
  color:var(--hm-gold-deep);
  font-weight:850;
  font-size:.8rem;
  margin:.25rem 0 .85rem 0;
}


/* --- Global Text Overlap Safety Patch --- */
* {
  box-sizing: border-box;
}
.stMarkdown, .stMarkdown p, .stMarkdown span, .stMarkdown div,
.stButton button, [data-testid="stExpander"] div, [data-testid="stDataFrame"] * {
  overflow-wrap: anywhere !important;
  word-break: normal !important;
}
.stButton button {
  white-space: normal !important;
  line-height: 1.2 !important;
  min-height: 2.75rem !important;
  height: auto !important;
}
.status-chip {
  white-space: normal !important;
  line-height: 1.2 !important;
  max-width: 100% !important;
}
.eval-status-grid{
  display:grid;
  grid-template-columns:repeat(3, minmax(0, 1fr));
  gap:.55rem;
  margin:.7rem 0 .9rem 0;
}
.eval-status-card{
  border:1px solid var(--hm-border);
  border-radius:16px;
  padding:.75rem .8rem;
  background:#fff;
  box-shadow:0 6px 16px rgba(25,36,31,.04);
  min-width:0;
}
.eval-status-label{
  font-size:.72rem;
  color:var(--hm-muted);
  font-weight:850;
  text-transform:uppercase;
  letter-spacing:.04em;
}
.eval-status-value{
  margin-top:.25rem;
  font-size:.9rem;
  font-weight:850;
  color:var(--hm-heading);
  overflow-wrap:anywhere;
}
.eval-ok{background:#F3FBF6;border-color:#CFE8DA;}
.eval-warn{background:#FFF8E8;border-color:#EAD6A4;}
.eval-info{background:#F3FAF7;border-color:#D9E9E3;}
.eval-gold{background:#FFF8E8;border-color:#E8D39E;}
.eval-actions-grid{
  display:grid;
  grid-template-columns:repeat(3, minmax(0, 1fr));
  gap:.65rem;
  margin-top:.75rem;
}
@media (max-width: 900px){
  .eval-status-grid{grid-template-columns:repeat(2, minmax(0, 1fr));}
  .eval-actions-grid{grid-template-columns:1fr;}
}
@media (max-width: 640px){
  .eval-status-grid{grid-template-columns:1fr;}
}


/* --- Evaluation Status Clarity Patch --- */
.eval-helper-box{
  background:#FFF8E8;
  border:1px solid #E8D39E;
  border-radius:18px;
  padding:1rem;
  margin:.6rem 0 1rem 0;
  color:#4B3A16;
  box-shadow:0 6px 16px rgba(25,36,31,.04);
}
.eval-helper-box b{
  color:var(--hm-heading);
}
.eval-section-title{
  margin-top:1.1rem;
  margin-bottom:.35rem;
  font-weight:900;
  color:var(--hm-heading);
  font-size:1.2rem;
}
.eval-section-note{
  color:var(--hm-muted);
  font-size:.92rem;
  margin-bottom:.75rem;
}


/* --- Expander Header Overlap Fix --- */
[data-testid="stExpander"] summary {
  min-height: 2.75rem !important;
  align-items: center !important;
}
[data-testid="stExpander"] summary p {
  white-space: normal !important;
  overflow-wrap: anywhere !important;
  padding-right: .75rem !important;
  line-height: 1.25 !important;
}


/* --- Final Overlap Safety Audit Patch --- */
/* Prevent text from colliding with expand/caret icons, tabs, or buttons */
[data-testid="stExpander"] summary {
  display: flex !important;
  align-items: center !important;
  gap: .45rem !important;
  min-height: 2.85rem !important;
  padding-right: .55rem !important;
}
[data-testid="stExpander"] summary p,
[data-testid="stExpander"] summary span,
[data-testid="stExpander"] summary div {
  white-space: normal !important;
  overflow-wrap: anywhere !important;
  word-break: normal !important;
  line-height: 1.25 !important;
  max-width: calc(100% - 2rem) !important;
}
[data-testid="stExpander"] details summary svg {
  flex-shrink: 0 !important;
}
button, .stButton button, .stButton button p, .stButton button span {
  white-space: normal !important;
  overflow-wrap: anywhere !important;
  word-break: normal !important;
  line-height: 1.18 !important;
}
button {
  min-width: 0 !important;
}
[data-testid="stTabs"] button,
[data-testid="stTabs"] button p {
  white-space: normal !important;
  overflow-wrap: anywhere !important;
  line-height: 1.2 !important;
}
[data-testid="stDataFrame"] * {
  white-space: normal !important;
}
.member-row-name,
.member-row-email,
.eval-status-value,
.eval-status-label,
.member-summary-value,
.member-summary-label {
  overflow-wrap: anywhere !important;
  word-break: normal !important;
  white-space: normal !important;
}


/* --- Evaluation Status Member Row Polish --- */
[data-testid="stExpander"] summary p {
  font-weight: 850 !important;
  color: var(--hm-heading) !important;
}
.eval-section-note b {
  color: var(--hm-heading) !important;
}


/* --- Custom Member Toggle Row --- */
.member-toggle-card{
  background:#FFFFFF;
  border:1px solid var(--hm-border);
  border-radius:16px;
  padding:.55rem .75rem;
  margin:.55rem 0;
  box-shadow:0 6px 16px rgba(25,36,31,.04);
}
.member-toggle-card .stButton button{
  justify-content:flex-start !important;
  text-align:left !important;
  width:100% !important;
  font-weight:900 !important;
  color:var(--hm-heading) !important;
  background:#FFFFFF !important;
  border:0 !important;
  box-shadow:none !important;
  padding:.35rem .25rem !important;
}
.member-detail-panel{
  background:#FFFDF8;
  border:1px solid var(--hm-border);
  border-radius:18px;
  padding:1rem;
  margin:.35rem 0 1rem 0;
}


/* --- LAF Guided Page Flow Patch --- */
[data-testid="stProgressBar"] {
  margin-top: .25rem !important;
  margin-bottom: .35rem !important;
}


/* --- LAF Smart Validation Patch --- */
[data-testid="stExpander"] summary p {
  color: var(--hm-heading) !important;
}
[data-testid="stNumberInput"] input {
  font-weight: 650 !important;
}


/* --- Member Form Autosave + Family History Table Patch --- */
.family-history-row{
  border-bottom:1px solid var(--hm-border);
  padding:.35rem 0;
}
.family-history-head{
  font-weight:900;
  color:var(--hm-heading);
  background:#FFF8E8;
  border:1px solid #E8D39E;
  border-radius:12px;
  padding:.5rem .65rem;
  margin-bottom:.35rem;
}
.autosave-note{
  color:var(--hm-muted);
  font-size:.86rem;
  font-weight:700;
  margin:.35rem 0 .75rem 0;
}


/* HealthyMe speed/UI cleanup: hide Streamlit's default multipage sidebar/nav flash */
section[data-testid="stSidebar"] {
    display: none !important;
    visibility: hidden !important;
    width: 0 !important;
    min-width: 0 !important;
}
button[kind="header"] {
    display: none !important;
}
div[data-testid="collapsedControl"] {
    display: none !important;
}
[data-testid="stSidebarNav"] {
    display: none !important;
}
.block-container {
    padding-top: 1.2rem !important;
}


/* UX Speed Polish Sprint: premium button hierarchy and compact controls */
div.stButton > button,
div.stDownloadButton > button,
button[data-testid="baseButton-secondary"] {
    min-height: 2.65rem !important;
    transition: transform .12s ease, box-shadow .12s ease, background .12s ease !important;
}
div.stButton > button:hover,
div.stDownloadButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 10px 22px rgba(6,78,59,.12) !important;
}
button[data-testid="baseButton-primary"],
div.stButton > button[kind="primary"],
.stButton button[kind="primary"],
button[kind="primary"] {
    background: linear-gradient(135deg, #064E3B 0%, #0F766E 100%) !important;
    color: #FFFFFF !important;
    border: 1.5px solid #064E3B !important;
    box-shadow: 0 10px 26px rgba(6,78,59,.18) !important;
}
button[data-testid="baseButton-primary"] p,
button[data-testid="baseButton-primary"] span,
div.stButton > button[kind="primary"] p,
div.stButton > button[kind="primary"] span {
    color: #FFFFFF !important;
}
button[data-testid="baseButton-secondary"],
div.stButton > button[kind="secondary"],
.stButton button[kind="secondary"] {
    background: #FFFFFF !important;
    color: #064E3B !important;
    border: 1.5px solid #D9C79F !important;
}
button:focus:not(:focus-visible) {
    outline: none !important;
    box-shadow: 0 10px 26px rgba(6,78,59,.14) !important;
}
div[data-testid="stTextInput"] input,
div[data-testid="stNumberInput"] input,
div[data-testid="stSelectbox"] div[data-baseweb="select"] {
    min-height: 2.55rem !important;
}
div[data-testid="stTextArea"] textarea {
    min-height: 5.8rem !important;
}
.hm-micro-note {
    font-size: .78rem;
    color: #64748B;
    margin-top: -.35rem;
}

</style>
"""

def inject_global_styles(): st.markdown(LUXE_CSS, unsafe_allow_html=True)
def apply_luxe_theme(): st.markdown(LUXE_CSS, unsafe_allow_html=True)
def apply_mobile_first_premium_theme(): st.markdown(LUXE_CSS, unsafe_allow_html=True)

def topbar(title, subtitle="", kicker="HealthyMe premium"):
    st.markdown(f"""<div class='hero-shell'><div class='hero-kicker'>{kicker}</div><div class='hero-title'>{title}</div><div class='hero-subtitle'>{subtitle}</div><div><span class='meta-pill'>Guided wellness workflow</span></div></div>""", unsafe_allow_html=True)

def card_start(): st.markdown("<div class='main-card'>", unsafe_allow_html=True)
def card_end(): st.markdown("</div>", unsafe_allow_html=True)

def chip(label, tone='neutral'):
    tone_map={'success':'status-ok','ok':'status-ok','info':'status-info','warning':'status-warn','warn':'status-warn','neutral':'status-neutral','gold':'status-gold'}
    st.markdown(f"<span class='status-chip {tone_map.get(tone,'status-neutral')}'>{label}</span>", unsafe_allow_html=True)

def stat_grid(stats):
    html=["<div class='kpi-grid'>"]
    for s in stats:
        html.append(f"<div class='kpi-card'><div class='kpi-label'>{s.get('label','')}</div><div class='kpi-value'>{s.get('value','')}</div><div class='kpi-note'>{s.get('note','')}</div></div>")
    html.append("</div>")
    st.markdown(''.join(html), unsafe_allow_html=True)

def utility_logout_bar():
    role=st.session_state.get("user_role","")
    name=st.session_state.get("user_name","User")
    if not st.session_state.get("logged_in"): return
    left,right=st.columns([5,1])
    with left:
        st.markdown(f"<div class='utility-bar'><div class='utility-user'>Signed in as <b>{name}</b><span class='utility-role'>{role.title()}</span></div></div>", unsafe_allow_html=True)
    with right:
        if st.button("Logout", key="global_logout", use_container_width=True):
            logout_current_user()
            st.switch_page("pages/01_Login.py")
