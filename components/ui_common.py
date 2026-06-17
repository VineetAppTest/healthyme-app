
import streamlit as st
from zoneinfo import ZoneInfo
import datetime
from components.auth_session import logout_current_user

# --------------------------------------------------------------------
# v53: safe shared helpers available for import by all pages
# --------------------------------------------------------------------
DEFAULT_APP_TIMEZONE = "Asia/Kolkata"

def format_local_ts(ts_value, timezone_name=None):
    """Format stored ISO timestamp in local display time.

    Current app default: Asia/Kolkata.
    """
    if not ts_value:
        return ""
    tz_name = timezone_name or DEFAULT_APP_TIMEZONE
    raw = str(ts_value)
    try:
        dt = datetime.datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=ZoneInfo(DEFAULT_APP_TIMEZONE))
        return dt.astimezone(ZoneInfo(tz_name)).strftime("%d-%b-%Y %I:%M %p")
    except Exception:
        return raw

def render_back_to_top():
    st.markdown("<a id='top'></a><a class='hm-back-to-top' href='#top'>↑ Back to Top</a>", unsafe_allow_html=True)



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


/* HealthyMe final button color normalization */
:root {
  --hm-btn-primary-bg: linear-gradient(135deg, #064E3B 0%, #0F766E 100%);
  --hm-btn-primary-text: #FFFFFF;
  --hm-btn-secondary-bg: #FFFFFF;
  --hm-btn-secondary-text: #064E3B;
  --hm-btn-border: #D8A84E;
}

/* Secondary/default buttons */
div[data-testid="stButton"] > button,
div[data-testid="stDownloadButton"] > button,
.stButton > button,
.stDownloadButton > button,
button[data-testid="baseButton-secondary"] {
  background: var(--hm-btn-secondary-bg) !important;
  color: var(--hm-btn-secondary-text) !important;
  border: 1.5px solid var(--hm-btn-border) !important;
  border-radius: 14px !important;
  font-weight: 850 !important;
  box-shadow: 0 6px 14px rgba(6,78,59,.08) !important;
}

/* Primary buttons */
button[data-testid="baseButton-primary"],
div[data-testid="stButton"] > button[kind="primary"],
.stButton > button[kind="primary"],
button[kind="primary"] {
  background: var(--hm-btn-primary-bg) !important;
  color: var(--hm-btn-primary-text) !important;
  border: 1.5px solid #064E3B !important;
  border-radius: 14px !important;
  font-weight: 900 !important;
  box-shadow: 0 12px 28px rgba(6,78,59,.20) !important;
}

/* Force nested markdown text inside buttons */
button[data-testid="baseButton-primary"] *,
div[data-testid="stButton"] > button[kind="primary"] *,
.stButton > button[kind="primary"] *,
button[kind="primary"] * {
  color: #FFFFFF !important;
}

button[data-testid="baseButton-secondary"] *,
div[data-testid="stButton"] > button:not([kind="primary"]) *,
.stButton > button:not([kind="primary"]) * {
  color: #064E3B !important;
}

div[data-testid="stButton"] > button:hover,
.stButton > button:hover,
div[data-testid="stDownloadButton"] > button:hover {
  transform: translateY(-1px) !important;
  box-shadow: 0 12px 26px rgba(6,78,59,.14) !important;
}

div[data-testid="stButton"] > button:disabled,
.stButton > button:disabled {
  background: #F4F1EA !important;
  color: #777E7A !important;
  border-color: #E2D7C2 !important;
  box-shadow: none !important;
}

div[data-testid="stButton"] > button:disabled *,
.stButton > button:disabled * {
  color: #777E7A !important;
}



/* --- UX Navigation + User Intent Patch --- */
.hm-nav-row{
  display:flex;
  gap:.55rem;
  flex-wrap:wrap;
  align-items:center;
  justify-content:space-between;
  margin:.45rem 0 .85rem 0;
}
.hm-priority-action{
  background:linear-gradient(135deg,rgba(231,247,239,.98),rgba(255,244,222,.92));
  border:1px solid rgba(216,168,78,.45);
  border-radius:20px;
  padding:1rem 1.05rem;
  margin:.65rem 0 1rem 0;
  box-shadow:0 10px 24px rgba(6,78,59,.08);
}
.hm-priority-action h3{margin-top:0!important;margin-bottom:.25rem!important;}
.hm-page-anchor{scroll-margin-top:90px;}
.hm-bottom-nav-shell{
  margin-top:1rem;
  padding-top:.8rem;
  border-top:1px solid var(--hm-border);
}
@media(max-width:640px){
  .hm-nav-row{display:block;}
  .hm-priority-action{padding:.85rem;border-radius:16px;}
}


/* --- Final Report Download + Structure Clarity Patch v2 --- */
/* Make download actions visually unmistakable, not divider-like */
div[data-testid="stDownloadButton"] > button,
.stDownloadButton > button {
  background: linear-gradient(135deg, #064E3B 0%, #0F766E 100%) !important;
  color: #FFFFFF !important;
  border: 2px solid #064E3B !important;
  border-radius: 16px !important;
  min-height: 3.25rem !important;
  font-size: 1rem !important;
  font-weight: 950 !important;
  letter-spacing: .01em !important;
  box-shadow: 0 14px 32px rgba(6,78,59,.24) !important;
}
div[data-testid="stDownloadButton"] > button *,
.stDownloadButton > button * {
  color: #FFFFFF !important;
  font-weight: 950 !important;
}
div[data-testid="stDownloadButton"] > button:hover,
.stDownloadButton > button:hover {
  background: linear-gradient(135deg, #043B2D 0%, #0B5F58 100%) !important;
  transform: translateY(-1px) !important;
  box-shadow: 0 16px 36px rgba(6,78,59,.30) !important;
}
.hm-report-download-panel{
  background: linear-gradient(135deg, #E7F7EF 0%, #FFF8E8 100%);
  border: 1.5px solid rgba(216,168,78,.55);
  border-radius: 22px;
  padding: 1.1rem;
  margin: .85rem 0 1.15rem 0;
  box-shadow: 0 12px 28px rgba(6,78,59,.10);
}
.hm-report-download-panel h3{
  margin: 0 0 .25rem 0 !important;
  color: #063F32 !important;
}
.hm-report-download-panel p{
  margin: 0 0 .8rem 0 !important;
  color: #334155 !important;
  font-weight: 650 !important;
}
.hm-structure-section{
  margin-top: 1.25rem;
  padding-top: 1rem;
  border-top: 1.5px solid #E8D39E;
}
.hm-structure-toggle-note{
  color:#475569;
  font-size:.92rem;
  margin:.2rem 0 .7rem 0;
}
.hm-structure-card{
  background:#FFFFFF;
  border:1.5px solid #E8D39E;
  border-radius:18px;
  padding:1rem;
  margin:.75rem 0 0 0;
  box-shadow:0 8px 20px rgba(25,36,31,.06);
}
/* Keep Streamlit expander readable where still used elsewhere */
[data-testid="stExpander"] {
  margin-top: .75rem !important;
  margin-bottom: .75rem !important;
}
[data-testid="stExpander"] summary {
  border: 1px solid #E8D39E !important;
  border-radius: 14px !important;
  background: #FFF8E8 !important;
  padding: .65rem .8rem !important;
}

/* --- Final Report Structure Lightweight Patch v3 --- */
.hm-structure-section-lite{
  margin-top: 1.35rem;
  padding-top: 1.1rem;
  border-top: 1px solid rgba(232,211,158,.65);
}
.hm-lite-structure-card{
  background: #FBFDF9;
  border: 1px solid rgba(15,118,110,.16);
  border-radius: 18px;
  padding: .95rem 1rem;
  box-shadow: 0 8px 18px rgba(15,23,42,.045);
}
.hm-lite-structure-title{
  color:#064E3B;
  font-weight: 900;
  font-size: 1.02rem;
  margin-bottom: .15rem;
}
.hm-lite-structure-subtitle{
  color:#64748B;
  font-size: .9rem;
  margin-bottom: .65rem;
}
.hm-lite-pill-row{
  display:flex;
  flex-wrap:wrap;
  gap:.45rem;
  margin:.35rem 0 .55rem 0;
}
.hm-lite-pill-row span{
  display:inline-flex;
  align-items:center;
  padding:.38rem .62rem;
  border-radius:999px;
  background:#ECFDF5;
  border:1px solid rgba(6,78,59,.14);
  color:#064E3B;
  font-weight:800;
  font-size:.84rem;
}
.hm-lite-note{
  color:#475569;
  font-size:.88rem;
  line-height:1.45;
}
@media(max-width:640px){
  .hm-lite-pill-row{display:block;}
  .hm-lite-pill-row span{
    display:flex;
    width:100%;
    margin-bottom:.38rem;
  }
}

/* --- Blank Element + Smooth Navigation Cleanup v4 --- */
.element-container:empty,
.stMarkdown:empty {
  display: none !important;
  min-height: 0 !important;
  margin: 0 !important;
  padding: 0 !important;
}
.hm-native-nav-shell{
  background: rgba(255,255,255,.72);
  border: 1px solid var(--hm-border);
  border-radius: 18px;
  padding: .55rem .65rem;
  margin: .35rem 0 .75rem 0;
  box-shadow: 0 6px 16px rgba(25,36,31,.045);
}
.hm-bottom-nav-shell{
  margin-top: 1rem;
  padding-top: .8rem;
  border-top: 1px solid var(--hm-border);
}
div[data-testid="stPageLink"] a {
  min-height: 2.55rem !important;
  border: 1.5px solid #D8A84E !important;
  border-radius: 14px !important;
  background: #FFFFFF !important;
  color: #064E3B !important;
  font-weight: 900 !important;
  box-shadow: 0 6px 14px rgba(6,78,59,.06) !important;
  text-decoration: none !important;
  justify-content: center !important;
}
div[data-testid="stPageLink"] a * {
  color: #064E3B !important;
  font-weight: 900 !important;
}
@media(max-width:640px){
  .hm-native-nav-shell{
    padding:.45rem;
    border-radius:16px;
  }
}

/* --- v5 Visual Hierarchy + Overlap Hardening --- */
.hm-action-grid-clean{
  display:grid;
  grid-template-columns:repeat(2,minmax(0,1fr));
  gap:1rem;
}
.hm-flow-guide-card{
  background:#FFFFFF;
  border:1px solid var(--hm-border);
  border-radius:20px;
  padding:1rem;
  box-shadow:0 10px 24px rgba(25,36,31,.055);
}
.hm-flow-guide-card h4{
  color:var(--hm-heading)!important;
  font-size:1.05rem!important;
  font-weight:900!important;
  margin:.1rem 0 .45rem 0!important;
}
.hm-flow-guide-card p,
.hm-flow-guide-card li{
  color:var(--hm-muted)!important;
  font-size:.92rem!important;
  line-height:1.45!important;
  margin:.2rem 0!important;
}
.hm-flow-guide-card ul{margin:.35rem 0 0 1rem!important;padding:0!important;}
.hm-admin-action-note{
  color:#64748B;
  font-size:.86rem;
  line-height:1.35;
  margin-bottom:.55rem;
}
.hm-gentle-reminder-card{
  background:#FFF8E8;
  border:1px solid #E8D39E;
  border-radius:18px;
  padding:.9rem 1rem;
  margin:.75rem 0 1rem 0;
}
.hm-gentle-reminder-card b{color:#064E3B!important;}
.hm-comm-card{
  background:#FFFFFF;
  border:1px solid var(--hm-border);
  border-radius:18px;
  padding:1rem;
  margin:.7rem 0;
  box-shadow:0 8px 20px rgba(25,36,31,.045);
}
.hm-comm-card b{color:#064E3B!important;}
/* Keep button/page-link text from overlapping icons or adjacent columns */
div[data-testid="stButton"] > button,
div[data-testid="stDownloadButton"] > button,
div[data-testid="stPageLink"] a{
  width:100%!important;
  min-width:0!important;
  height:auto!important;
  min-height:2.8rem!important;
  white-space:normal!important;
  line-height:1.22!important;
  padding:.65rem .8rem!important;
  display:flex!important;
  align-items:center!important;
  justify-content:center!important;
  text-align:center!important;
  gap:.35rem!important;
}
div[data-testid="stButton"] > button *,
div[data-testid="stDownloadButton"] > button *,
div[data-testid="stPageLink"] a *{
  white-space:normal!important;
  overflow-wrap:anywhere!important;
  word-break:normal!important;
  line-height:1.22!important;
  text-align:center!important;
}
/* Remove accidental black-looking first-button effect */
button[data-testid="baseButton-primary"],
div[data-testid="stButton"] > button[kind="primary"],
.stButton > button[kind="primary"],
button[kind="primary"]{
  background:linear-gradient(135deg,#064E3B 0%,#0F766E 100%)!important;
  color:#FFFFFF!important;
}
@media(max-width:900px){
  .hm-action-grid-clean{grid-template-columns:1fr;}
}

/* --- v7 Structural Reset: targeted, non-destructive styling --- */
.hm-build-marker{
  display:inline-flex;
  align-items:center;
  gap:.35rem;
  font-size:.78rem;
  font-weight:800;
  color:#065F46;
  background:#ECFDF5;
  border:1px solid rgba(6,95,70,.18);
  border-radius:999px;
  padding:.25rem .55rem;
  margin:.1rem 0 .7rem 0;
}
.hm-v7-priority-list{
  display:grid;
  grid-template-columns:1fr;
  gap:.7rem;
  margin:.5rem 0 1.1rem 0;
}
.hm-v7-priority-row{
  display:grid;
  grid-template-columns:minmax(160px, 1.1fr) minmax(220px, .9fr);
  gap:.9rem;
  align-items:center;
  background:#FFFFFF;
  border:1px solid rgba(216,168,78,.42);
  border-radius:18px;
  padding:.75rem .85rem;
  box-shadow:0 8px 20px rgba(25,36,31,.045);
}
.hm-v7-priority-title{
  color:#064E3B;
  font-weight:900;
  font-size:.98rem;
  margin:0;
}
.hm-v7-priority-sub{
  color:#64748B;
  font-size:.84rem;
  margin:.15rem 0 0 0;
}
.hm-v7-section-card{
  background:#FFFFFF;
  border:1px solid rgba(216,168,78,.42);
  border-radius:18px;
  padding:.95rem;
  box-shadow:0 8px 20px rgba(25,36,31,.045);
  margin-bottom:.95rem;
}
.hm-v7-section-card h4{
  color:#064E3B!important;
  font-size:1rem!important;
  font-weight:900!important;
  margin:0 0 .25rem 0!important;
}
.hm-v7-section-card p{
  color:#64748B!important;
  font-size:.88rem!important;
  line-height:1.45!important;
  margin:0 0 .75rem 0!important;
}
.hm-v7-guide{
  background:#FFFFFF;
  border:1px solid rgba(216,168,78,.42);
  border-radius:18px;
  padding:1rem;
  box-shadow:0 8px 20px rgba(25,36,31,.045);
  margin:1rem 0;
}
.hm-v7-guide h4{
  color:#064E3B!important;
  font-size:1rem!important;
  font-weight:900!important;
  margin:0 0 .45rem 0!important;
}
.hm-v7-guide ol{
  margin:.2rem 0 0 1.15rem!important;
  padding:0!important;
}
.hm-v7-guide li{
  color:#334155!important;
  font-size:.9rem!important;
  line-height:1.5!important;
  margin:.2rem 0!important;
}
.hm-v7-small-note{
  color:#64748B;
  font-size:.84rem;
  line-height:1.4;
}
.hm-v7-navline{
  display:flex;
  flex-wrap:wrap;
  gap:.5rem;
  align-items:center;
  margin:.35rem 0 .75rem 0;
}
.hm-v7-navline a{
  color:#064E3B!important;
  font-weight:800!important;
  text-decoration:none!important;
  border:1px solid rgba(216,168,78,.45);
  border-radius:999px;
  padding:.36rem .65rem;
  background:#FFFFFF;
}
.hm-v7-allocation-note{
  background:#ECFDF5;
  border:1px solid rgba(6,95,70,.14);
  color:#064E3B;
  border-radius:16px;
  padding:.75rem .85rem;
  margin:.55rem 0 .85rem 0;
  font-size:.9rem;
  line-height:1.45;
}
/* Safe button text wrapping only. No vertical word breaking. */
div[data-testid="stButton"] > button,
div[data-testid="stDownloadButton"] > button{
  min-height:2.65rem;
  white-space:normal!important;
  line-height:1.25!important;
  text-align:center!important;
}
/* Avoid vertical letter stacking created by older aggressive patches */
div[data-testid="stButton"] > button *,
div[data-testid="stDownloadButton"] > button *{
  white-space:normal!important;
  word-break:keep-all!important;
  overflow-wrap:normal!important;
  line-height:1.25!important;
}
@media(max-width:760px){
  .hm-v7-priority-row{
    grid-template-columns:1fr;
    gap:.55rem;
  }
}

/* --- v8 Refinement: compact cards + horizontal priority + safer buttons --- */

/* Dashboard priority cards: horizontal but responsive */
.hm-v8-priority-grid{
  display:grid;
  grid-template-columns:repeat(3,minmax(0,1fr));
  gap:.85rem;
  margin:.45rem 0 1rem 0;
}
.hm-v8-priority-card{
  background:#FFFFFF;
  border:1px solid rgba(216,168,78,.42);
  border-radius:16px;
  padding:.78rem;
  box-shadow:0 6px 16px rgba(25,36,31,.04);
}
.hm-v8-priority-card .hm-v8-priority-title{
  color:#064E3B;
  font-weight:900;
  font-size:.94rem;
  margin:0 0 .18rem 0;
}
.hm-v8-priority-card .hm-v8-priority-sub{
  color:#64748B;
  font-size:.8rem;
  line-height:1.32;
  min-height:2.1rem;
  margin:0 0 .6rem 0;
}

/* Make action cards slightly smaller on internal pages and dashboard */
div[data-testid="stVerticalBlockBorderWrapper"]{
  border-radius:14px!important;
}
div[data-testid="stVerticalBlockBorderWrapper"] > div{
  padding:.72rem .82rem!important;
}

/* Compact information/help blocks. These should not dominate the page. */
.stAlert{
  padding:.55rem .72rem!important;
  border-radius:12px!important;
}
.stAlert p{
  font-size:.86rem!important;
  line-height:1.35!important;
}
.hm-v8-info-compact{
  background:#F8FAFC;
  border:1px solid rgba(148,163,184,.28);
  border-radius:12px;
  padding:.55rem .7rem;
  margin:.35rem 0 .65rem 0;
  color:#475569;
  font-size:.84rem;
  line-height:1.35;
}

/* Safer buttons: no vertical stacking; allow text to fit naturally */
div[data-testid="stButton"] > button,
div[data-testid="stDownloadButton"] > button{
  width:100%!important;
  min-height:2.45rem!important;
  height:auto!important;
  padding:.52rem .7rem!important;
  white-space:normal!important;
  line-height:1.18!important;
  text-align:center!important;
  word-break:normal!important;
  overflow-wrap:break-word!important;
}
div[data-testid="stButton"] > button *,
div[data-testid="stDownloadButton"] > button *{
  white-space:normal!important;
  word-break:normal!important;
  overflow-wrap:break-word!important;
  line-height:1.18!important;
}

/* Remove odd primary/black look from first button on dashboard priority */
.hm-v8-priority-grid div[data-testid="stButton"] > button{
  background:#FFFFFF!important;
  color:#064E3B!important;
  border:1.5px solid #D8A84E!important;
  box-shadow:0 5px 12px rgba(6,78,59,.05)!important;
  font-weight:850!important;
}
.hm-v8-priority-grid div[data-testid="stButton"] > button *{
  color:#064E3B!important;
}

/* Keep sections tight */
h2, h3{
  margin-top:.85rem!important;
}
@media(max-width:900px){
  .hm-v8-priority-grid{
    grid-template-columns:1fr;
  }
  .hm-v8-priority-card .hm-v8-priority-sub{
    min-height:0;
  }
}

/* --- v9 Compact Headers + Tooltip-First Information --- */

/* Page header proportions */
h1{
  font-size:1.65rem!important;
  line-height:1.18!important;
  margin-bottom:.25rem!important;
}
h2{
  font-size:1.22rem!important;
  line-height:1.22!important;
  margin-top:.8rem!important;
  margin-bottom:.35rem!important;
}
h3{
  font-size:1.05rem!important;
  line-height:1.22!important;
  margin-top:.65rem!important;
  margin-bottom:.3rem!important;
}
p, li{
  line-height:1.38!important;
}

/* Reduce topbar/header visual weight where custom classes exist */
.main-title,
.page-title,
.hero-title{
  font-size:1.65rem!important;
  line-height:1.18!important;
}
.subtitle,
.page-subtitle,
.hero-subtitle{
  font-size:.9rem!important;
  line-height:1.35!important;
  max-width:920px;
}

/* Compact info: use only when info must remain visible */
.hm-v9-compact-note{
  background:#F8FAFC;
  border:1px solid rgba(148,163,184,.24);
  border-radius:12px;
  color:#475569;
  font-size:.82rem;
  line-height:1.34;
  padding:.48rem .62rem;
  margin:.3rem 0 .55rem 0;
}

/* Buttons: prevent overlap by reducing visible labels and enforcing minimum sensible width */
div[data-testid="stButton"] > button,
div[data-testid="stDownloadButton"] > button{
  min-height:2.35rem!important;
  padding:.48rem .62rem!important;
  line-height:1.15!important;
  white-space:nowrap!important;
  overflow:hidden!important;
  text-overflow:ellipsis!important;
  font-size:.88rem!important;
}
div[data-testid="stButton"] > button *,
div[data-testid="stDownloadButton"] > button *{
  white-space:nowrap!important;
  overflow:hidden!important;
  text-overflow:ellipsis!important;
  line-height:1.15!important;
}

/* Evaluation status action rows need compact controls */
.hm-v9-action-row{
  display:grid;
  grid-template-columns:repeat(3,minmax(96px,1fr));
  gap:.42rem;
}
.hm-v9-action-row .stButton button{
  font-size:.82rem!important;
  min-height:2.2rem!important;
  padding:.4rem .5rem!important;
}

/* Alerts/info blocks should not dominate */
.stAlert{
  padding:.42rem .58rem!important;
  border-radius:10px!important;
}
.stAlert p{
  font-size:.8rem!important;
  line-height:1.28!important;
}

/* Bordered cards even tighter */
div[data-testid="stVerticalBlockBorderWrapper"] > div{
  padding:.58rem .68rem!important;
}

/* Mobile: allow wrap only on narrow screens, but keep sane spacing */
@media(max-width:720px){
  h1{font-size:1.42rem!important;}
  h2{font-size:1.12rem!important;}
  div[data-testid="stButton"] > button,
  div[data-testid="stDownloadButton"] > button,
  div[data-testid="stButton"] > button *,
  div[data-testid="stDownloadButton"] > button *{
    white-space:normal!important;
    overflow:visible!important;
    text-overflow:clip!important;
  }
}

/* --- v11 Designer Stable System --- */

/* Global proportion reset: clean, compact, no forced weird boxes */
h1{
  font-size:1.72rem!important;
  line-height:1.18!important;
  margin:0 0 .25rem 0!important;
}
h2{
  font-size:1.24rem!important;
  line-height:1.22!important;
  margin:.85rem 0 .35rem 0!important;
}
h3{
  font-size:1.06rem!important;
  line-height:1.24!important;
  margin:.65rem 0 .3rem 0!important;
}
p, li{
  line-height:1.42!important;
}

/* Designer cards: compact, content-led, not oversized */
.hm-v11-card{
  background:#FFFFFF;
  border:1px solid rgba(216,168,78,.38);
  border-radius:16px;
  padding:.78rem .85rem;
  box-shadow:0 6px 16px rgba(15,23,42,.045);
  margin:.45rem 0 .75rem 0;
}
.hm-v11-card-title{
  color:#064E3B;
  font-size:.98rem;
  font-weight:900;
  line-height:1.2;
  margin:0 0 .2rem 0;
}
.hm-v11-card-sub{
  color:#64748B;
  font-size:.82rem;
  line-height:1.34;
  margin:0 0 .55rem 0;
}
.hm-v11-section-note{
  color:#64748B;
  font-size:.82rem;
  line-height:1.35;
  margin:.15rem 0 .55rem 0;
}

/* Stable dashboard grids */
.hm-v11-priority-grid{
  display:grid;
  grid-template-columns:repeat(3,minmax(0,1fr));
  gap:.8rem;
  margin:.35rem 0 .9rem 0;
}
.hm-v11-workflow-grid{
  display:grid;
  grid-template-columns:repeat(2,minmax(0,1fr));
  gap:.85rem;
  margin:.35rem 0 .85rem 0;
}

/* Button discipline: no forced one-line ellipsis, no vertical stacking */
div[data-testid="stButton"] > button,
div[data-testid="stDownloadButton"] > button{
  width:100%;
  min-height:2.38rem;
  height:auto;
  padding:.5rem .7rem;
  border-radius:999px;
  line-height:1.2;
  white-space:normal;
  word-break:normal;
  overflow-wrap:normal;
  text-align:center;
}
div[data-testid="stButton"] > button *,
div[data-testid="stDownloadButton"] > button *{
  white-space:normal!important;
  word-break:normal!important;
  overflow-wrap:normal!important;
  line-height:1.2!important;
}

/* No black-first-button effect on dashboard/action cards */
.hm-v11-card div[data-testid="stButton"] > button{
  background:#FFFFFF!important;
  color:#064E3B!important;
  border:1.4px solid #D8A84E!important;
  font-weight:850!important;
  box-shadow:0 4px 10px rgba(6,78,59,.045)!important;
}
.hm-v11-card div[data-testid="stButton"] > button *{
  color:#064E3B!important;
}

/* Compact native Streamlit bordered containers; no giant cards */
div[data-testid="stVerticalBlockBorderWrapper"] > div{
  padding:.62rem .72rem!important;
  border-radius:14px!important;
}

/* Informational blocks: minimal; use expander/help for secondary explanations */
.stAlert{
  padding:.48rem .62rem!important;
  border-radius:10px!important;
  margin:.4rem 0!important;
}
.stAlert p{
  font-size:.82rem!important;
  line-height:1.3!important;
}

/* Small non-intrusive build text, not a big tag */
.hm-v11-build-text{
  color:#94A3B8;
  font-size:.68rem;
  font-weight:700;
  margin:.05rem 0 .35rem 0;
}

/* Evaluation Status: action groups stack within each member card instead of cramped text/button rows */
.hm-v11-actions{
  display:grid;
  grid-template-columns:repeat(3,minmax(0,1fr));
  gap:.38rem;
  margin-top:.45rem;
}

/* Mobile/tablet */
@media(max-width:900px){
  .hm-v11-priority-grid,
  .hm-v11-workflow-grid{
    grid-template-columns:1fr;
  }
  .hm-v11-actions{
    grid-template-columns:1fr;
  }
}

/* --- v12 Consistent Build + Header Card Consistency --- */
.hm-current-build-text{
  color:#94A3B8;
  font-size:.68rem;
  font-weight:800;
  margin:.05rem 0 .35rem 0;
}
.hm-current-build-badge{
  display:inline-flex;
  align-items:center;
  color:#065F46;
  background:#ECFDF5;
  border:1px solid rgba(6,95,70,.18);
  border-radius:999px;
  padding:.22rem .55rem;
  font-size:.72rem;
  font-weight:900;
  margin:.05rem 0 .45rem 0;
}
/* Header cards should remain card-based, but proportionate */
.hero-card,
.hm-header-card,
div[data-testid="stVerticalBlock"] .hero-card{
  border-radius:22px!important;
}
/* Dashboard priority header cards retained and balanced */
.hm-v12-priority-grid{
  display:grid;
  grid-template-columns:repeat(3,minmax(0,1fr));
  gap:.85rem;
  margin:.35rem 0 1rem 0;
}
.hm-v12-priority-card{
  background:#FFFFFF;
  border:1px solid rgba(216,168,78,.42);
  border-radius:16px;
  padding:.85rem .9rem;
  box-shadow:0 6px 16px rgba(15,23,42,.045);
}
.hm-v12-priority-title{
  color:#064E3B;
  font-size:.98rem;
  font-weight:900;
  line-height:1.22;
  margin:0 0 .25rem 0;
}
.hm-v12-priority-sub{
  color:#64748B;
  font-size:.82rem;
  line-height:1.35;
  margin:0 0 .65rem 0;
}
.hm-v12-priority-card div[data-testid="stButton"] > button{
  background:#FFFFFF!important;
  color:#064E3B!important;
  border:1.4px solid #D8A84E!important;
  font-weight:850!important;
}
@media(max-width:900px){
  .hm-v12-priority-grid{
    grid-template-columns:1fr;
  }
}

/* --- v13 Client-Safe Dashboard Redesign --- */

/* Very small build text only. Never a dominant badge. */
.hm-v13-build-text{
  color:#94A3B8;
  font-size:.66rem;
  font-weight:700;
  margin:.05rem 0 .2rem 0;
}

/* Dashboard priority: action-first, low clutter */
.hm-v13-priority-grid{
  display:grid;
  grid-template-columns:repeat(3,minmax(0,1fr));
  gap:.9rem;
  margin:.35rem 0 1.05rem 0;
}
.hm-v13-priority-card{
  background:#FFFFFF;
  border:1px solid rgba(216,168,78,.42);
  border-radius:18px;
  padding:.85rem .9rem .9rem .9rem;
  box-shadow:0 8px 18px rgba(15,23,42,.045);
}
.hm-v13-priority-kicker{
  color:#64748B;
  font-size:.72rem;
  font-weight:800;
  text-transform:uppercase;
  letter-spacing:.04em;
  margin:0 0 .16rem 0;
}
.hm-v13-priority-number{
  color:#064E3B;
  font-size:1.55rem;
  font-weight:950;
  line-height:1;
  margin:0 0 .42rem 0;
}
.hm-v13-priority-micro{
  color:#64748B;
  font-size:.78rem;
  line-height:1.25;
  min-height:1rem;
  margin:.45rem 0 0 0;
}

/* In priority cards, action button is the focus */
.hm-v13-priority-card div[data-testid="stButton"] > button{
  background:#064E3B!important;
  color:#FFFFFF!important;
  border:1px solid #064E3B!important;
  border-radius:999px!important;
  min-height:2.55rem!important;
  font-weight:900!important;
  box-shadow:0 8px 18px rgba(6,78,59,.15)!important;
}
.hm-v13-priority-card div[data-testid="stButton"] > button *{
  color:#FFFFFF!important;
  font-weight:900!important;
}

/* Workflow cards: compact, action list first, no explanatory clutter */
.hm-v13-workflow-grid{
  display:grid;
  grid-template-columns:repeat(2,minmax(0,1fr));
  gap:.9rem;
  margin:.35rem 0 .9rem 0;
}
.hm-v13-workflow-card{
  background:#FFFFFF;
  border:1px solid rgba(216,168,78,.36);
  border-radius:18px;
  padding:.82rem .9rem;
  box-shadow:0 7px 16px rgba(15,23,42,.04);
}
.hm-v13-workflow-title{
  color:#064E3B;
  font-size:.98rem;
  font-weight:950;
  margin:0 0 .55rem 0;
}
.hm-v13-workflow-card div[data-testid="stButton"] > button{
  background:#FFFFFF!important;
  color:#064E3B!important;
  border:1.25px solid #D8A84E!important;
  border-radius:999px!important;
  min-height:2.38rem!important;
  font-weight:850!important;
  box-shadow:0 4px 10px rgba(6,78,59,.045)!important;
}
.hm-v13-workflow-card div[data-testid="stButton"] > button *{
  color:#064E3B!important;
  font-weight:850!important;
}

/* Dashboard section spacing */
.hm-v13-section-note{
  color:#64748B;
  font-size:.78rem;
  margin:.05rem 0 .4rem 0;
}

/* Header proportions: keep header cards but reduce bulk */
h1{
  font-size:1.68rem!important;
  line-height:1.18!important;
}
h2{
  font-size:1.22rem!important;
  line-height:1.22!important;
  margin-top:.85rem!important;
  margin-bottom:.35rem!important;
}
h3{
  font-size:1.05rem!important;
  line-height:1.22!important;
}
.stAlert{
  padding:.48rem .62rem!important;
  border-radius:10px!important;
}
.stAlert p{
  font-size:.82rem!important;
  line-height:1.3!important;
}

/* Generic safe button handling: avoid vertical stacking without over-forcing */
div[data-testid="stButton"] > button,
div[data-testid="stDownloadButton"] > button{
  white-space:normal!important;
  word-break:normal!important;
  overflow-wrap:normal!important;
  text-align:center!important;
  line-height:1.2!important;
}
div[data-testid="stButton"] > button *,
div[data-testid="stDownloadButton"] > button *{
  white-space:normal!important;
  word-break:normal!important;
  overflow-wrap:normal!important;
  line-height:1.2!important;
}

@media(max-width:900px){
  .hm-v13-priority-grid,
  .hm-v13-workflow-grid{
    grid-template-columns:1fr;
  }
  .hm-v13-priority-micro{
    min-height:0;
  }
}

/* --- v14 Native Cards + No Expander Dashboard --- */

/* Small build text */
.hm-v14-build-text{
  color:#94A3B8;
  font-size:.66rem;
  font-weight:700;
  margin:.05rem 0 .25rem 0;
}

/* Native Streamlit bordered containers become the card system */
.hm-v14-priority-card,
.hm-v14-workflow-card,
.hm-v14-flow-card{
  padding:.15rem 0;
}

/* Text inside cards stays visually connected */
.hm-v14-kicker{
  color:#64748B;
  font-size:.72rem;
  font-weight:900;
  text-transform:uppercase;
  letter-spacing:.04em;
  margin:0 0 .1rem 0;
}
.hm-v14-number{
  color:#064E3B;
  font-size:1.55rem;
  font-weight:950;
  line-height:1.05;
  margin:0 0 .35rem 0;
}
.hm-v14-micro{
  color:#64748B;
  font-size:.78rem;
  line-height:1.28;
  margin:.42rem 0 0 0;
}
.hm-v14-workflow-title{
  color:#064E3B;
  font-size:.98rem;
  font-weight:950;
  margin:0 0 .5rem 0;
}
.hm-v14-flow-title{
  color:#064E3B;
  font-size:.96rem;
  font-weight:950;
  margin:0 0 .4rem 0;
}
.hm-v14-flow-list{
  display:grid;
  grid-template-columns:repeat(5,minmax(0,1fr));
  gap:.45rem;
}
.hm-v14-flow-step{
  background:#F8FAFC;
  border:1px solid rgba(148,163,184,.22);
  border-radius:12px;
  padding:.48rem .52rem;
  color:#334155;
  font-size:.78rem;
  line-height:1.25;
}

/* Compact card sizing across pages */
div[data-testid="stVerticalBlockBorderWrapper"] > div{
  padding:.7rem .78rem!important;
  border-radius:16px!important;
}

/* Button style inside priority cards */
.hm-v14-priority-card div[data-testid="stButton"] > button{
  background:#064E3B!important;
  color:#FFFFFF!important;
  border:1px solid #064E3B!important;
  border-radius:999px!important;
  min-height:2.48rem!important;
  font-weight:900!important;
  box-shadow:0 8px 16px rgba(6,78,59,.14)!important;
}
.hm-v14-priority-card div[data-testid="stButton"] > button *{
  color:#FFFFFF!important;
  font-weight:900!important;
}

/* Workflow buttons */
.hm-v14-workflow-card div[data-testid="stButton"] > button{
  background:#FFFFFF!important;
  color:#064E3B!important;
  border:1.25px solid #D8A84E!important;
  border-radius:999px!important;
  min-height:2.32rem!important;
  font-weight:850!important;
  box-shadow:0 4px 10px rgba(6,78,59,.04)!important;
}
.hm-v14-workflow-card div[data-testid="stButton"] > button *{
  color:#064E3B!important;
}

/* No vertical stacking / no over-aggressive text forcing */
div[data-testid="stButton"] > button,
div[data-testid="stDownloadButton"] > button{
  white-space:normal!important;
  word-break:normal!important;
  overflow-wrap:normal!important;
  text-align:center!important;
  line-height:1.2!important;
}

/* If any Streamlit expander remains elsewhere, reduce its visual awkwardness */
details summary{
  font-size:.86rem!important;
  color:#064E3B!important;
  font-weight:850!important;
}

/* Responsive */
@media(max-width:900px){
  .hm-v14-flow-list{
    grid-template-columns:1fr;
  }
}

/* --- v15 Navigation + Action Consistency Patch --- */
.hm-v15-build-text{color:#94A3B8;font-size:.66rem;font-weight:700;margin:.05rem 0 .25rem 0;}
div[data-testid="stPageLink"] a{flex-wrap:nowrap!important;white-space:nowrap!important;overflow-wrap:normal!important;word-break:normal!important;min-height:2.55rem!important;}
div[data-testid="stPageLink"] a *{white-space:nowrap!important;overflow-wrap:normal!important;word-break:normal!important;}
div[data-testid="stFormSubmitButton"] button,div[data-testid="stFormSubmitButton"] button[kind="primary"],button[kind="primaryFormSubmit"]{background:linear-gradient(135deg,#064E3B 0%,#0F766E 100%)!important;color:#FFFFFF!important;border:1px solid #064E3B!important;font-weight:900!important;}
div[data-testid="stFormSubmitButton"] button *,button[kind="primaryFormSubmit"] *{color:#FFFFFF!important;font-weight:900!important;}
.hm-v15-action-emphasis div[data-testid="stButton"] > button{min-height:2.9rem!important;font-weight:900!important;}
.hm-v15-action-emphasis .stButton button[kind="primary"],.hm-v15-action-emphasis div[data-testid="stButton"] > button[kind="primary"]{background:linear-gradient(135deg,#064E3B 0%,#0F766E 100%)!important;color:#FFFFFF!important;border-color:#064E3B!important;}
.hm-v15-action-emphasis .stButton button[kind="primary"] *,.hm-v15-action-emphasis div[data-testid="stButton"] > button[kind="primary"] *{color:#FFFFFF!important;}
.hm-v15-compact-note{color:#64748B;font-size:.82rem;line-height:1.32;margin:.25rem 0 .55rem 0;}
.hm-v15-reminder-note{background:#FFF8E8;border:1px solid #E8D39E;border-radius:16px;padding:.65rem .8rem;margin:.75rem 0 .8rem 0;color:#4B3A16;font-size:.84rem;line-height:1.35;}

/* --- v23 Stability + Visibility Fix --- */
.hm-v23-version-line{
  margin-top:.12rem;
  color:#64748B;
  font-size:.76rem;
  font-weight:800;
  letter-spacing:.01em;
}
.hm-v23-logout-note{
  color:#64748B;
  font-size:.78rem;
  margin:.15rem 0 .4rem 0;
}

/* --- v24 BodyMind + Version Placement --- */
.hm-v24-brand{
  color:#064E3B;
  font-size:.82rem;
  font-weight:950;
  letter-spacing:.02em;
  text-transform:uppercase;
  margin-bottom:.08rem;
}
.hm-v24-version-line{
  color:#64748B;
  font-size:.72rem;
  font-weight:800;
  margin-bottom:.42rem;
}

/* --- v28 Body-Mind Final Unlock + Version Cleanup --- */
.hm-v28-brand-row{display:flex;align-items:baseline;gap:.55rem;flex-wrap:wrap;margin-bottom:.35rem;}
.hm-v28-brand{color:#064E3B;font-size:.82rem;font-weight:950;letter-spacing:.02em;text-transform:uppercase;}
.hm-v28-version-inline{color:#64748B;font-size:.72rem;font-weight:800;}

/* --- v29 Manual Body-Mind Unlock --- */
.hm-v29-brand-row{display:flex;align-items:baseline;gap:.55rem;flex-wrap:wrap;margin-bottom:.35rem;}
.hm-v29-brand{color:#064E3B;font-size:.82rem;font-weight:950;letter-spacing:.02em;text-transform:uppercase;}
.hm-v29-version-inline{color:#64748B;font-size:.72rem;font-weight:800;}

/* --- v30 Manual Body-Mind Unlock Control --- */
.hm-v30-brand-row{display:flex;align-items:baseline;gap:.55rem;flex-wrap:wrap;margin-bottom:.35rem;}
.hm-v30-brand{color:#064E3B;font-size:.82rem;font-weight:950;letter-spacing:.02em;text-transform:uppercase;}
.hm-v30-version-inline{color:#64748B;font-size:.72rem;font-weight:800;}

/* --- v31 Workflow Instance Sync --- */
.hm-v31-brand-row{display:flex;align-items:baseline;gap:.55rem;flex-wrap:wrap;margin-bottom:.35rem;}
.hm-v31-brand{color:#064E3B;font-size:.82rem;font-weight:950;letter-spacing:.02em;text-transform:uppercase;}
.hm-v31-version-inline{color:#64748B;font-size:.72rem;font-weight:800;}

/* --- v32 Manual Body-Mind Hard Sync --- */
.hm-v32-brand-row{display:flex;align-items:baseline;gap:.55rem;flex-wrap:wrap;margin-bottom:.35rem;}
.hm-v32-brand{color:#064E3B;font-size:.82rem;font-weight:950;letter-spacing:.02em;text-transform:uppercase;}
.hm-v32-version-inline{color:#64748B;font-size:.72rem;font-weight:800;}

/* --- v33 Body-Mind Explicit Access + Logout Cleanup --- */
.hm-v33-brand-row{display:flex;align-items:baseline;gap:.55rem;flex-wrap:wrap;margin-bottom:.35rem;}
.hm-v33-brand{color:#064E3B;font-size:.82rem;font-weight:950;letter-spacing:.02em;text-transform:uppercase;}
.hm-v33-version-inline{color:#64748B;font-size:.72rem;font-weight:800;}

/* --- v34 Body-Mind NameError + Logout Fix --- */
.hm-v34-brand-row{display:flex;align-items:baseline;gap:.55rem;flex-wrap:wrap;margin-bottom:.35rem;}
.hm-v34-brand{color:#064E3B;font-size:.82rem;font-weight:950;letter-spacing:.02em;text-transform:uppercase;}
.hm-v34-version-inline{color:#64748B;font-size:.72rem;font-weight:800;}

/* --- v35 Body-Mind Page Guard Fix --- */
.hm-v35-brand-row{display:flex;align-items:baseline;gap:.55rem;flex-wrap:wrap;margin-bottom:.35rem;}
.hm-v35-brand{color:#064E3B;font-size:.82rem;font-weight:950;letter-spacing:.02em;text-transform:uppercase;}
.hm-v35-version-inline{color:#64748B;font-size:.72rem;font-weight:800;}

/* --- v36 Body-Mind Text Removal + Autosave Check --- */
.hm-v36-brand-row{display:flex;align-items:baseline;gap:.55rem;flex-wrap:wrap;margin-bottom:.35rem;}
.hm-v36-brand{color:#064E3B;font-size:.82rem;font-weight:950;letter-spacing:.02em;text-transform:uppercase;}
.hm-v36-version-inline{color:#64748B;font-size:.72rem;font-weight:800;}

/* --- v37 Remove Body-Mind Activation Checkbox --- */
.hm-v37-brand-row{display:flex;align-items:baseline;gap:.55rem;flex-wrap:wrap;margin-bottom:.35rem;}
.hm-v37-brand{color:#064E3B;font-size:.82rem;font-weight:950;letter-spacing:.02em;text-transform:uppercase;}
.hm-v37-version-inline{color:#64748B;font-size:.72rem;font-weight:800;}

/* --- v38 Body-Mind Disabled Button UI --- */
.hm-v38-brand-row{display:flex;align-items:baseline;gap:.55rem;flex-wrap:wrap;margin-bottom:.35rem;}
.hm-v38-brand{color:#064E3B;font-size:.82rem;font-weight:950;letter-spacing:.02em;text-transform:uppercase;}
.hm-v38-version-inline{color:#64748B;font-size:.72rem;font-weight:800;}

/* --- v39 Admin Autosave --- */
.hm-v39-brand-row{display:flex;align-items:baseline;gap:.55rem;flex-wrap:wrap;margin-bottom:.35rem;}
.hm-v39-brand{color:#064E3B;font-size:.82rem;font-weight:950;letter-spacing:.02em;text-transform:uppercase;}
.hm-v39-version-inline{color:#64748B;font-size:.72rem;font-weight:800;}

/* --- v40 Body-Mind Status Sync --- */
.hm-v40-brand-row{display:flex;align-items:baseline;gap:.55rem;flex-wrap:wrap;margin-bottom:.35rem;}
.hm-v40-brand{color:#064E3B;font-size:.82rem;font-weight:950;letter-spacing:.02em;text-transform:uppercase;}
.hm-v40-version-inline{color:#64748B;font-size:.72rem;font-weight:800;}

/* --- v41 Daily Log Flow --- */
.hm-v41-brand-row{display:flex;align-items:baseline;gap:.55rem;flex-wrap:wrap;margin-bottom:.35rem;}
.hm-v41-brand{color:#064E3B;font-size:.82rem;font-weight:950;letter-spacing:.02em;text-transform:uppercase;}
.hm-v41-version-inline{color:#64748B;font-size:.72rem;font-weight:800;}

/* --- v42 Day-based Daily Log --- */
.hm-v42-brand-row{display:flex;align-items:baseline;gap:.55rem;flex-wrap:wrap;margin-bottom:.35rem;}
.hm-v42-brand{color:#064E3B;font-size:.82rem;font-weight:950;letter-spacing:.02em;text-transform:uppercase;}
.hm-v42-version-inline{color:#64748B;font-size:.72rem;font-weight:800;}

/* --- v43 Progressive Daily Log + Repository --- */
.hm-v43-brand-row{display:flex;align-items:baseline;gap:.55rem;flex-wrap:wrap;margin-bottom:.35rem;}
.hm-v43-brand{color:#064E3B;font-size:.82rem;font-weight:950;letter-spacing:.02em;text-transform:uppercase;}
.hm-v43-version-inline{color:#64748B;font-size:.72rem;font-weight:800;}

/* --- v44 Daily Log One Section + Other Slots --- */
.hm-v44-brand-row{display:flex;align-items:baseline;gap:.55rem;flex-wrap:wrap;margin-bottom:.35rem;}
.hm-v44-brand{color:#064E3B;font-size:.82rem;font-weight:950;letter-spacing:.02em;text-transform:uppercase;}
.hm-v44-version-inline{color:#64748B;font-size:.72rem;font-weight:800;}

/* --- v45 Daily Log Compact Other Fix --- */
.hm-v45-brand-row{display:flex;align-items:baseline;gap:.55rem;flex-wrap:wrap;margin-bottom:.35rem;}
.hm-v45-brand{color:#064E3B;font-size:.82rem;font-weight:950;letter-spacing:.02em;text-transform:uppercase;}
.hm-v45-version-inline{color:#64748B;font-size:.72rem;font-weight:800;}

/* --- v46 Admin Info Cleanup + Daily Log Layout --- */
.hm-v46-brand-row{display:flex;align-items:baseline;gap:.55rem;flex-wrap:wrap;margin-bottom:.35rem;}
.hm-v46-brand{color:#064E3B;font-size:.82rem;font-weight:950;letter-spacing:.02em;text-transform:uppercase;}
.hm-v46-version-inline{color:#64748B;font-size:.72rem;font-weight:800;}

/* --- v47 Logout + Daily Log Backcompat + Reference Toggle --- */
.hm-v47-brand-row{display:flex;align-items:baseline;gap:.55rem;flex-wrap:wrap;margin-bottom:.35rem;}
.hm-v47-brand{color:#064E3B;font-size:.82rem;font-weight:950;letter-spacing:.02em;text-transform:uppercase;}
.hm-v47-version-inline{color:#64748B;font-size:.72rem;font-weight:800;}

/* --- v48 Nutritionist Message Archive --- */
.hm-v48-brand-row{display:flex;align-items:baseline;gap:.55rem;flex-wrap:wrap;margin-bottom:.35rem;}
.hm-v48-brand{color:#064E3B;font-size:.82rem;font-weight:950;letter-spacing:.02em;text-transform:uppercase;}
.hm-v48-version-inline{color:#64748B;font-size:.72rem;font-weight:800;}

/* --- v49 Logout Session Hardening --- */
.hm-v49-brand-row{display:flex;align-items:baseline;gap:.55rem;flex-wrap:wrap;margin-bottom:.35rem;}
.hm-v49-brand{color:#064E3B;font-size:.82rem;font-weight:950;letter-spacing:.02em;text-transform:uppercase;}
.hm-v49-version-inline{color:#64748B;font-size:.72rem;font-weight:800;}

/* --- v50 Member Home Message + Journey Compact --- */
.hm-v50-brand-row{display:flex;align-items:baseline;gap:.55rem;flex-wrap:wrap;margin-bottom:.35rem;}
.hm-v50-brand{color:#064E3B;font-size:.82rem;font-weight:950;letter-spacing:.02em;text-transform:uppercase;}
.hm-v50-version-inline{color:#64748B;font-size:.72rem;font-weight:800;}
.hm-nutritionist-message-shell{
  border:1px solid #E7D8BE;
  border-radius:16px;
  background:#FFFDF8;
  padding:.65rem .85rem;
  margin:.35rem 0 1rem 0;
}
.hm-nutritionist-message-title{
  font-size:1rem;
  font-weight:900;
  color:#064E3B;
  margin-bottom:.45rem;
}
.hm-nutritionist-message-card{
  margin-top:.55rem;
  margin-bottom:.4rem;
}
.hm-journey-compact-spacer{
  height:.65rem;
  border-top:1px solid #E7D8BE;
  margin:1rem 0 .55rem 0;
}
.hm-journey-compact-title{
  font-size:1rem;
  font-weight:900;
  color:#064E3B;
  margin:.15rem 0 .45rem 0;
}
.member-summary-grid{
  margin-top:.15rem !important;
  gap:.5rem !important;
}
.member-summary-item{
  padding:.75rem .85rem !important;
  min-height:72px !important;
}

/* --- v51 Timezone + Back To Top --- */
.hm-v51-brand-row{display:flex;align-items:baseline;gap:.55rem;flex-wrap:wrap;margin-bottom:.35rem;}
.hm-v51-brand{color:#064E3B;font-size:.82rem;font-weight:950;letter-spacing:.02em;text-transform:uppercase;}
.hm-v51-version-inline{color:#64748B;font-size:.72rem;font-weight:800;}
.hm-back-to-top{
  position:fixed;
  right:18px;
  bottom:18px;
  z-index:9999;
  background:#064E3B;
  color:white !important;
  padding:.62rem .85rem;
  border-radius:999px;
  text-decoration:none !important;
  font-size:.85rem;
  font-weight:850;
  box-shadow:0 10px 25px rgba(15,23,42,.18);
}
.hm-back-to-top:hover{filter:brightness(1.05);}
.hm-page-top-anchor{height:1px;}
.hm-ts-local{color:#64748B;font-size:.85rem;}

/* --- v52 Login Logout Block Bottom --- */
.hm-v52-brand-row{display:flex;align-items:baseline;gap:.55rem;flex-wrap:wrap;margin-bottom:.35rem;}
.hm-v52-brand{color:#064E3B;font-size:.82rem;font-weight:950;letter-spacing:.02em;text-transform:uppercase;}
.hm-v52-version-inline{color:#64748B;font-size:.72rem;font-weight:800;}
.hm-logout-bottom-shell{
  margin-top:1rem;
  padding:.9rem;
  border:1px solid #E7D8BE;
  border-radius:16px;
  background:#FFFDF8;
}
.hm-logout-bottom-copy{
  color:#64748B;
  font-size:.9rem;
  line-height:1.45;
  margin:.6rem 0 .8rem 0;
}

/* --- v53 Safe Helper + Back To Top CSS --- */
.hm-v53-brand-row{display:flex;align-items:baseline;gap:.55rem;flex-wrap:wrap;margin-bottom:.35rem;}
.hm-v53-brand{color:#064E3B;font-size:.82rem;font-weight:950;letter-spacing:.02em;text-transform:uppercase;}
.hm-v53-version-inline{color:#64748B;font-size:.72rem;font-weight:800;}
.hm-back-to-top{
  position:fixed;
  right:18px;
  bottom:18px;
  z-index:9999;
  background:#064E3B;
  color:white !important;
  padding:.62rem .85rem;
  border-radius:999px;
  text-decoration:none !important;
  font-size:.85rem;
  font-weight:850;
  box-shadow:0 10px 25px rgba(15,23,42,.18);
}
.hm-back-to-top:hover{filter:brightness(1.05);}

/* --- v54 Nutritionist Read Archive Fix --- */
.hm-v54-brand-row{display:flex;align-items:baseline;gap:.55rem;flex-wrap:wrap;margin-bottom:.35rem;}
.hm-v54-brand{color:#064E3B;font-size:.82rem;font-weight:950;letter-spacing:.02em;text-transform:uppercase;}
.hm-v54-version-inline{color:#64748B;font-size:.72rem;font-weight:800;}
.hm-nutritionist-message-shell{
  border:1px solid #E7D8BE;
  border-radius:16px;
  background:#FFFDF8;
  padding:.65rem .85rem;
  margin:.35rem 0 1rem 0;
}
.hm-nutritionist-message-title{
  font-size:1rem;
  font-weight:900;
  color:#064E3B;
  margin-bottom:.45rem;
}
.hm-nutritionist-message-card{margin-top:.55rem;margin-bottom:.4rem;}

/* --- v55 Admin Dashboard Import Fix --- */
.hm-v55-brand-row{display:flex;align-items:baseline;gap:.55rem;flex-wrap:wrap;margin-bottom:.35rem;}
.hm-v55-brand{color:#064E3B;font-size:.82rem;font-weight:950;letter-spacing:.02em;text-transform:uppercase;}
.hm-v55-version-inline{color:#64748B;font-size:.72rem;font-weight:800;}

/* --- v56 Daily Log Nutritionist Notification --- */
.hm-v56-brand-row{display:flex;align-items:baseline;gap:.55rem;flex-wrap:wrap;margin-bottom:.35rem;}
.hm-v56-brand{color:#064E3B;font-size:.82rem;font-weight:950;letter-spacing:.02em;text-transform:uppercase;}
.hm-v56-version-inline{color:#64748B;font-size:.72rem;font-weight:800;}

/* --- v57 Daily Log + LAF Restructure --- */
.hm-v57-brand-row{display:flex;align-items:baseline;gap:.55rem;flex-wrap:wrap;margin-bottom:.35rem;}
.hm-v57-brand{color:#064E3B;font-size:.82rem;font-weight:950;letter-spacing:.02em;text-transform:uppercase;}
.hm-v57-version-inline{color:#64748B;font-size:.72rem;font-weight:800;}

/* --- v58 LAF Restructure Correction --- */
.hm-v58-brand-row{display:flex;align-items:baseline;gap:.55rem;flex-wrap:wrap;margin-bottom:.35rem;}
.hm-v58-brand{color:#064E3B;font-size:.82rem;font-weight:950;letter-spacing:.02em;text-transform:uppercase;}
.hm-v58-version-inline{color:#64748B;font-size:.72rem;font-weight:800;}

/* --- v59 Structured Poop Rounds --- */
.hm-v59-brand-row{display:flex;align-items:baseline;gap:.55rem;flex-wrap:wrap;margin-bottom:.35rem;}
.hm-v59-brand{color:#064E3B;font-size:.82rem;font-weight:950;letter-spacing:.02em;text-transform:uppercase;}
.hm-v59-version-inline{color:#64748B;font-size:.72rem;font-weight:800;}

/* --- v60 Poop Layout Refinement --- */
.hm-v60-brand-row{display:flex;align-items:baseline;gap:.55rem;flex-wrap:wrap;margin-bottom:.35rem;}
.hm-v60-brand{color:#064E3B;font-size:.82rem;font-weight:950;letter-spacing:.02em;text-transform:uppercase;}
.hm-v60-version-inline{color:#64748B;font-size:.72rem;font-weight:800;}

/* --- v61 Stability + Premium UX Cleanup --- */
.hm-v61-brand-row{display:flex;align-items:baseline;gap:.5rem;flex-wrap:wrap;margin-bottom:.2rem;}
.hm-v61-brand{color:#064E3B;font-size:.78rem;font-weight:950;letter-spacing:.02em;text-transform:uppercase;}
.hm-v61-version-inline{color:#64748B;font-size:.7rem;font-weight:800;}
.hero-shell{
  padding:1.05rem 1.25rem !important;
  margin-bottom:1rem !important;
  border-radius:22px !important;
}
.hero-title{font-size:1.55rem !important;line-height:1.15 !important;margin:.15rem 0 !important;}
.hero-subtitle{font-size:.92rem !important;line-height:1.35 !important;margin:.15rem 0 .55rem 0 !important;}
.hero-kicker,.meta-pill{font-size:.72rem !important;padding:.28rem .7rem !important;}
.stButton > button{
  min-height:2.45rem !important;
  border-radius:14px !important;
  font-weight:750 !important;
  white-space:normal !important;
  line-height:1.2 !important;
}
.stButton > button[kind="primary"], button[kind="primary"]{
  background:#075E4A !important;
  border-color:#075E4A !important;
  color:#FFFFFF !important;
}
.stButton > button:disabled{
  opacity:.58 !important;
  background:#EEF2F0 !important;
  color:#64748B !important;
  border-color:#D8E0DC !important;
}
[data-testid="stDataFrame"]{
  border:1px solid #E7D8BE !important;
  border-radius:16px !important;
  overflow:hidden !important;
  box-shadow:0 8px 22px rgba(15,23,42,.05) !important;
}
[data-testid="stDataFrame"] div{
  font-size:.88rem !important;
}
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea,
[data-testid="stSelectbox"] div[data-baseweb="select"]{
  border-radius:12px !important;
}
.info-banner{
  padding:.75rem .9rem !important;
  border-radius:14px !important;
  margin:.45rem 0 !important;
}
.hm-compact-page-section{margin-top:.6rem !important;margin-bottom:.6rem !important;}
.hm-table-note{font-size:.82rem;color:#64748B;margin:.25rem 0 .5rem 0;}

/* --- v62 Recent Saved Days Premium Layout --- */
.hm-v62-brand-row{display:flex;align-items:baseline;gap:.55rem;flex-wrap:wrap;margin-bottom:.35rem;}
.hm-v62-brand{color:#064E3B;font-size:.82rem;font-weight:950;letter-spacing:.02em;text-transform:uppercase;}
.hm-v62-version-inline{color:#64748B;font-size:.72rem;font-weight:800;}
.hm-rsd-card{
  border:1px solid #E7D8BE;
  border-radius:18px;
  background:#FFFDF8;
  box-shadow:0 10px 28px rgba(15,23,42,.06);
  overflow:hidden;
  margin-top:.7rem;
}
.hm-rsd-header{
  display:grid;
  grid-template-columns: 1fr 1fr 1fr 1.35fr 2fr 1fr;
  gap:.75rem;
  padding:.85rem 1rem;
  font-size:.82rem;
  font-weight:900;
  color:#064E3B;
  border-bottom:1px solid #E7D8BE;
  background:#FFFCF5;
}
.hm-rsd-row{
  display:grid;
  grid-template-columns: 1fr 1fr 1fr 1.35fr 2fr 1fr;
  gap:.75rem;
  padding:.9rem 1rem;
  align-items:center;
  border-bottom:1px solid #F0E5D2;
  font-size:.9rem;
  color:#0F2F2A;
}
.hm-rsd-row:last-child{border-bottom:none;}
.hm-rsd-date{font-weight:800;color:#064E3B;}
.hm-rsd-pill{
  display:inline-flex;
  align-items:center;
  justify-content:center;
  min-width:3.2rem;
  padding:.34rem .65rem;
  border-radius:999px;
  background:#EAF7F1;
  border:1px solid #BEE8D6;
  color:#064E3B;
  font-weight:900;
}
.hm-rsd-note{
  line-height:1.35;
  color:#253B36;
}
.hm-rsd-action-slot{
  min-height:1px;
}
@media (max-width: 760px){
  .hm-rsd-header{display:none;}
  .hm-rsd-row{
    grid-template-columns: 1fr;
    gap:.35rem;
    padding:.85rem;
  }
  .hm-rsd-row > div::before{
    display:block;
    font-size:.7rem;
    font-weight:900;
    color:#64748B;
    text-transform:uppercase;
    letter-spacing:.02em;
    margin-bottom:.1rem;
  }
  .hm-rsd-row > div:nth-child(1)::before{content:"Date";}
  .hm-rsd-row > div:nth-child(2)::before{content:"Meals Logged";}
  .hm-rsd-row > div:nth-child(3)::before{content:"Water";}
  .hm-rsd-row > div:nth-child(4)::before{content:"Notes";}
  .hm-rsd-row > div:nth-child(5)::before{content:"Nutritionist Notes";}
}

/* --- v63 Recent Saved Days Borders + Toggle --- */
.hm-v63-brand-row{display:flex;align-items:baseline;gap:.55rem;flex-wrap:wrap;margin-bottom:.35rem;}
.hm-v63-brand{color:#064E3B;font-size:.82rem;font-weight:950;letter-spacing:.02em;text-transform:uppercase;}
.hm-v63-version-inline{color:#64748B;font-size:.72rem;font-weight:800;}
.hm-rsd-card{
  border:1px solid #E3D3B9 !important;
  border-radius:18px !important;
  background:#FFFDF8 !important;
  box-shadow:0 10px 28px rgba(15,23,42,.06) !important;
  overflow:hidden !important;
}
.hm-rsd-header{
  display:grid !important;
  grid-template-columns: 1fr 1fr 1fr 1.35fr 2fr 1fr !important;
  gap:0 !important;
  padding:0 !important;
  border-bottom:1px solid #E3D3B9 !important;
  background:#FFFDF6 !important;
}
.hm-rsd-header > div{
  padding:.85rem 1rem !important;
  border-right:1px solid #EFE3CF !important;
  font-size:.82rem !important;
  font-weight:900 !important;
  color:#064E3B !important;
}
.hm-rsd-header > div:last-child{border-right:none !important;}
.hm-rsd-row{
  display:grid !important;
  grid-template-columns: 1fr 1fr 1fr 1.35fr 2fr 1fr !important;
  gap:0 !important;
  padding:0 !important;
  align-items:stretch !important;
  border-bottom:1px solid #EFE3CF !important;
  font-size:.9rem !important;
  color:#0F2F2A !important;
}
.hm-rsd-row:last-child{border-bottom:none !important;}
.hm-rsd-row > div{
  padding:.9rem 1rem !important;
  border-right:1px solid #F1E7D6 !important;
  display:flex !important;
  align-items:center !important;
  min-height:3.9rem !important;
}
.hm-rsd-row > div:last-child{border-right:none !important;}
.hm-rsd-date{font-weight:850 !important;color:#064E3B !important;}
.hm-rsd-note{line-height:1.35 !important;align-items:flex-start !important;}
.hm-rsd-action-slot{min-height:3.9rem !important;}
/* Align the Streamlit action button closer to its row while preserving logic */
.hm-rsd-card + div [data-testid="column"]:last-child .stButton > button,
.hm-rsd-card ~ div [data-testid="column"]:last-child .stButton > button{
  min-height:2.25rem !important;
  border-radius:999px !important;
  border-color:#D6B56D !important;
  color:#064E3B !important;
  background:#FFFFFF !important;
  box-shadow:0 6px 16px rgba(15,23,42,.06) !important;
}
@media (max-width: 760px){
  .hm-rsd-header{display:none !important;}
  .hm-rsd-row{
    grid-template-columns:1fr !important;
    margin:.7rem !important;
    border:1px solid #E7D8BE !important;
    border-radius:16px !important;
    overflow:hidden !important;
  }
  .hm-rsd-row > div{
    border-right:none !important;
    border-bottom:1px solid #F1E7D6 !important;
    min-height:auto !important;
    padding:.75rem .85rem !important;
    display:block !important;
  }
  .hm-rsd-row > div:last-child{border-bottom:none !important;}
}

/* --- v64 Recent Saved Days Refinement --- */
.hm-v64-brand-row{display:flex;align-items:baseline;gap:.55rem;flex-wrap:wrap;margin-bottom:.35rem;}
.hm-v64-brand{color:#064E3B;font-size:.82rem;font-weight:950;letter-spacing:.02em;text-transform:uppercase;}
.hm-v64-version-inline{color:#64748B;font-size:.72rem;font-weight:800;}

/* stronger and cleaner table boundaries */
.hm-rsd-card{
  border:1.5px solid #D9C2A0 !important;
  border-radius:18px !important;
  background:#FFFDF8 !important;
  box-shadow:0 10px 28px rgba(15,23,42,.06) !important;
  overflow:hidden !important;
}
.hm-rsd-header{
  display:grid !important;
  grid-template-columns: 1fr 1fr 1fr 1.35fr 2fr 1fr !important;
  gap:0 !important;
  padding:0 !important;
  border-bottom:1.5px solid #D9C2A0 !important;
  background:#FFFCF5 !important;
}
.hm-rsd-header > div{
  padding:.82rem .95rem !important;
  border-right:1.25px solid #E2CFB1 !important;
  font-size:.82rem !important;
  font-weight:900 !important;
  color:#064E3B !important;
}
.hm-rsd-header > div:last-child{border-right:none !important;}

.hm-rsd-row{
  display:grid !important;
  grid-template-columns: 1fr 1fr 1fr 1.35fr 2fr 1fr !important;
  gap:0 !important;
  padding:0 !important;
  align-items:stretch !important;
  border-bottom:1.25px solid #E6D5BB !important;
  font-size:.9rem !important;
  color:#0F2F2A !important;
}
.hm-rsd-row:last-child{border-bottom:none !important;}
.hm-rsd-row > div{
  padding:.72rem .95rem !important;
  border-right:1.25px solid #EADBC5 !important;
  display:flex !important;
  align-items:center !important;
  min-height:3.35rem !important;
}
.hm-rsd-row > div:last-child{border-right:none !important;}
.hm-rsd-date{font-weight:850 !important;color:#064E3B !important;}
.hm-rsd-pill{
  display:inline-flex;
  align-items:center;
  justify-content:center;
  min-width:3.1rem;
  padding:.32rem .62rem;
  border-radius:999px;
  background:#EAF7F1;
  border:1px solid #BEE8D6;
  color:#064E3B;
  font-weight:900;
}
/* smaller/more compact Nutritionist Notes */
.hm-rsd-note{
  line-height:1.28 !important;
  align-items:flex-start !important;
  font-size:.84rem !important;
  color:#253B36 !important;
}
/* button smaller and visually aligned */
.hm-rsd-action-slot{
  min-height:3.35rem !important;
}
.hm-rsd-card + div [data-testid="column"]:last-child,
.hm-rsd-card ~ div [data-testid="column"]:last-child{
  display:flex !important;
  align-items:center !important;
}
.hm-rsd-card + div [data-testid="column"]:last-child .stButton,
.hm-rsd-card ~ div [data-testid="column"]:last-child .stButton{
  width:100% !important;
  display:flex !important;
  align-items:center !important;
  justify-content:center !important;
}
.hm-rsd-card + div [data-testid="column"]:last-child .stButton > button,
.hm-rsd-card ~ div [data-testid="column"]:last-child .stButton > button{
  min-height:2rem !important;
  height:2rem !important;
  padding:.2rem .85rem !important;
  border-radius:999px !important;
  border:1.25px solid #D6B56D !important;
  color:#064E3B !important;
  background:#FFFFFF !important;
  box-shadow:0 4px 10px rgba(15,23,42,.05) !important;
  font-size:.83rem !important;
  font-weight:700 !important;
  width:auto !important;
}
@media (max-width: 760px){
  .hm-rsd-header{display:none !important;}
  .hm-rsd-row{
    grid-template-columns:1fr !important;
    margin:.7rem !important;
    border:1.25px solid #D9C2A0 !important;
    border-radius:16px !important;
    overflow:hidden !important;
  }
  .hm-rsd-row > div{
    border-right:none !important;
    border-bottom:1.1px solid #EADBC5 !important;
    min-height:auto !important;
    padding:.72rem .85rem !important;
    display:block !important;
  }
  .hm-rsd-row > div:last-child{border-bottom:none !important;}
  .hm-rsd-note{font-size:.82rem !important;}
}

/* --- v65 Daily Log + Admin UI Fixes --- */
.hm-v65-brand-row{display:flex;align-items:baseline;gap:.55rem;flex-wrap:wrap;margin-bottom:.35rem;}
.hm-v65-brand{color:#064E3B;font-size:.82rem;font-weight:950;letter-spacing:.02em;text-transform:uppercase;}
.hm-v65-version-inline{color:#64748B;font-size:.72rem;font-weight:800;}

/* Recent saved days: meal text replaces meals logged pill */
.hm-rsd-header{
  grid-template-columns: 1fr 1.6fr .9fr .9fr 2fr .9fr !important;
}
.hm-rsd-row{
  grid-template-columns: 1fr 1.6fr .9fr .9fr 2fr .9fr !important;
}
.hm-rsd-meals{
  font-size:.84rem !important;
  line-height:1.25 !important;
  color:#253B36 !important;
}
.hm-rsd-meals b{font-weight:800 !important;}
.hm-rsd-note{
  font-size:.82rem !important;
  line-height:1.22 !important;
}

/* --- v66 Nutritionist Message Dedupe --- */
.hm-v66-brand-row{display:flex;align-items:baseline;gap:.55rem;flex-wrap:wrap;margin-bottom:.35rem;}
.hm-v66-brand{color:#064E3B;font-size:.82rem;font-weight:950;letter-spacing:.02em;text-transform:uppercase;}
.hm-v66-version-inline{color:#64748B;font-size:.72rem;font-weight:800;}

/* --- v67 View History Alignment Fix --- */
.hm-v67-brand-row{display:flex;align-items:baseline;gap:.55rem;flex-wrap:wrap;margin-bottom:.35rem;}
.hm-v67-brand{color:#064E3B;font-size:.82rem;font-weight:950;letter-spacing:.02em;text-transform:uppercase;}
.hm-v67-version-inline{color:#64748B;font-size:.72rem;font-weight:800;}

/* Recent saved days tighter action column + cleaner alignment */
.hm-rsd-header{
  grid-template-columns: 1fr 1.6fr .9fr .9fr 2fr .72fr !important;
}
.hm-rsd-row{
  grid-template-columns: 1fr 1.6fr .9fr .9fr 2fr .72fr !important;
}
.hm-rsd-row > div{
  min-height:3rem !important;
  padding:.62rem .9rem !important;
}
.hm-rsd-action-slot{
  min-height:3rem !important;
}

.hm-rsd-card + div [data-testid="column"]:last-child,
.hm-rsd-card ~ div [data-testid="column"]:last-child{
  display:flex !important;
  align-items:center !important;
  justify-content:center !important;
  padding-top:.1rem !important;
}

.hm-rsd-card + div [data-testid="column"]:last-child .stButton,
.hm-rsd-card ~ div [data-testid="column"]:last-child .stButton{
  width:auto !important;
  display:flex !important;
  align-items:center !important;
  justify-content:center !important;
  margin:0 auto !important;
}

.hm-rsd-card + div [data-testid="column"]:last-child .stButton > button,
.hm-rsd-card ~ div [data-testid="column"]:last-child .stButton > button{
  min-height:1.9rem !important;
  height:1.9rem !important;
  padding:.15rem .75rem !important;
  border-radius:999px !important;
  border:1.2px solid #D6B56D !important;
  color:#064E3B !important;
  background:#FFFFFF !important;
  box-shadow:0 3px 8px rgba(15,23,42,.04) !important;
  font-size:.79rem !important;
  font-weight:700 !important;
  width:auto !important;
  white-space:nowrap !important;
}

/* --- v68 View History Micro Alignment --- */
.hm-v68-brand-row{display:flex;align-items:baseline;gap:.55rem;flex-wrap:wrap;margin-bottom:.35rem;}
.hm-v68-brand{color:#064E3B;font-size:.82rem;font-weight:950;letter-spacing:.02em;text-transform:uppercase;}
.hm-v68-version-inline{color:#64748B;font-size:.72rem;font-weight:800;}

/* Tighter action column + stronger text alignment */
.hm-rsd-header{
  grid-template-columns: 1fr 1.7fr .9fr .9fr 2fr .62fr !important;
}
.hm-rsd-row{
  grid-template-columns: 1fr 1.7fr .9fr .9fr 2fr .62fr !important;
}
.hm-rsd-row > div{
  min-height:2.9rem !important;
  padding:.56rem .85rem !important;
}
.hm-rsd-note{
  font-size:.80rem !important;
  line-height:1.18 !important;
}
.hm-rsd-meals{
  font-size:.82rem !important;
  line-height:1.2 !important;
}

/* Shift the action-button row upward to visually line up with content */
.hm-rsd-card + div,
.hm-rsd-card ~ div{
  margin-top:-2.65rem !important;
  position:relative !important;
  z-index:2 !important;
}

/* Only the action button area should remain visible/compact */
.hm-rsd-card + div [data-testid="column"]:last-child,
.hm-rsd-card ~ div [data-testid="column"]:last-child{
  display:flex !important;
  align-items:flex-start !important;
  justify-content:center !important;
  padding-top:.15rem !important;
}

.hm-rsd-card + div [data-testid="column"]:last-child .stButton,
.hm-rsd-card ~ div [data-testid="column"]:last-child .stButton{
  width:auto !important;
  display:flex !important;
  align-items:flex-start !important;
  justify-content:center !important;
  margin:0 auto !important;
}

.hm-rsd-card + div [data-testid="column"]:last-child .stButton > button,
.hm-rsd-card ~ div [data-testid="column"]:last-child .stButton > button{
  min-height:1.75rem !important;
  height:1.75rem !important;
  padding:.08rem .62rem !important;
  border-radius:16px !important;
  border:1.15px solid #D6B56D !important;
  color:#064E3B !important;
  background:#FFFFFF !important;
  box-shadow:0 2px 6px rgba(15,23,42,.035) !important;
  font-size:.74rem !important;
  font-weight:650 !important;
  width:auto !important;
  white-space:nowrap !important;
  line-height:1 !important;
}

/* Reduce dead space caused by the button row */
.hm-rsd-card + div [data-testid="column"]:first-child,
.hm-rsd-card ~ div [data-testid="column"]:first-child{
  min-height:0 !important;
}

/* --- v69 Inline History Button Alignment --- */
.hm-v69-brand-row{display:flex;align-items:baseline;gap:.55rem;flex-wrap:wrap;margin-bottom:.35rem;}
.hm-v69-brand{color:#064E3B;font-size:.82rem;font-weight:950;letter-spacing:.02em;text-transform:uppercase;}
.hm-v69-version-inline{color:#64748B;font-size:.72rem;font-weight:800;}

.hm-rsd-card{
  border:1.5px solid #D9C2A0 !important;
  border-radius:18px !important;
  background:#FFFDF8 !important;
  box-shadow:0 10px 28px rgba(15,23,42,.06) !important;
  overflow:hidden !important;
  margin-top:.7rem !important;
}
.hm-rsd-header,
.hm-rsd-row{
  display:grid !important;
  grid-template-columns: 1fr 1.7fr .9fr .9fr 2fr .78fr !important;
  gap:0 !important;
}
.hm-rsd-header{
  background:#FFFCF5 !important;
  border-bottom:1.5px solid #D9C2A0 !important;
}
.hm-rsd-header > div{
  padding:.82rem .9rem !important;
  border-right:1.25px solid #E2CFB1 !important;
  font-size:.82rem !important;
  font-weight:900 !important;
  color:#064E3B !important;
}
.hm-rsd-header > div:last-child{border-right:none !important;}

.hm-rsd-row{
  border-bottom:1.25px solid #E6D5BB !important;
  color:#0F2F2A !important;
  font-size:.86rem !important;
}
.hm-rsd-row:last-child{border-bottom:none !important;}
.hm-rsd-row > div{
  padding:.62rem .82rem !important;
  border-right:1.25px solid #EADBC5 !important;
  min-height:3.1rem !important;
  display:flex !important;
  align-items:center !important;
}
.hm-rsd-row > div:last-child{border-right:none !important;}
.hm-rsd-date{
  font-weight:850 !important;
  color:#064E3B !important;
}
.hm-rsd-meals{
  font-size:.80rem !important;
  line-height:1.18 !important;
  color:#253B36 !important;
}
.hm-rsd-note{
  font-size:.80rem !important;
  line-height:1.18 !important;
  color:#253B36 !important;
}
.hm-rsd-action-cell{
  justify-content:center !important;
  align-items:center !important;
  overflow:visible !important;
}
.hm-rsd-details{
  position:relative !important;
  width:auto !important;
}
.hm-rsd-details > summary{
  list-style:none !important;
  cursor:pointer !important;
  display:inline-flex !important;
  align-items:center !important;
  justify-content:center !important;
  border:1.15px solid #D6B56D !important;
  border-radius:999px !important;
  padding:.22rem .58rem !important;
  background:#FFFFFF !important;
  color:#064E3B !important;
  font-size:.72rem !important;
  font-weight:750 !important;
  line-height:1 !important;
  white-space:nowrap !important;
  box-shadow:0 2px 6px rgba(15,23,42,.035) !important;
}
.hm-rsd-details > summary::-webkit-details-marker{display:none !important;}
.hm-rsd-history-panel{
  grid-column:1 / -1 !important;
  position:relative !important;
  margin-top:.65rem !important;
  padding:.75rem !important;
  border:1px solid #E7D8BE !important;
  border-radius:14px !important;
  background:#EEF8F9 !important;
  min-width:280px !important;
  max-width:560px !important;
  z-index:3 !important;
}
.hm-rsd-history-title{
  font-weight:900 !important;
  color:#064E3B !important;
  margin-bottom:.45rem !important;
  font-size:.86rem !important;
}
.hm-rsd-history-item{
  padding:.55rem .65rem !important;
  margin:.4rem 0 !important;
  border-radius:12px !important;
  background:#FFFFFF !important;
  border:1px solid #DDEDEA !important;
  font-size:.82rem !important;
  line-height:1.25 !important;
}
.hm-rsd-no-history{
  color:#94A3B8 !important;
  font-weight:700 !important;
}
@media (max-width: 760px){
  .hm-rsd-header{display:none !important;}
  .hm-rsd-row{
    grid-template-columns:1fr !important;
    margin:.7rem !important;
    border:1.25px solid #D9C2A0 !important;
    border-radius:16px !important;
    overflow:hidden !important;
  }
  .hm-rsd-row > div{
    border-right:none !important;
    border-bottom:1.1px solid #EADBC5 !important;
    min-height:auto !important;
    padding:.72rem .85rem !important;
    display:block !important;
  }
  .hm-rsd-row > div:last-child{border-bottom:none !important;}
  .hm-rsd-action-cell{display:flex !important;justify-content:flex-start !important;}
  .hm-rsd-history-panel{max-width:100% !important;min-width:0 !important;}
}

/* --- v70 Streamlit Native Recent Saved Days --- */
.hm-v70-brand-row{display:flex;align-items:baseline;gap:.55rem;flex-wrap:wrap;margin-bottom:.35rem;}
.hm-v70-brand{color:#064E3B;font-size:.82rem;font-weight:950;letter-spacing:.02em;text-transform:uppercase;}
.hm-v70-version-inline{color:#64748B;font-size:.72rem;font-weight:800;}

.hm-rsd-native-shell{
  border:1.5px solid #D9C2A0;
  border-radius:18px;
  background:#FFFDF8;
  box-shadow:0 10px 28px rgba(15,23,42,.06);
  padding:.65rem .85rem .35rem .85rem;
  margin-top:.7rem;
}
.hm-rsd-native-shell [data-testid="column"]{
  display:flex;
  align-items:center;
}
.hm-rsd-native-divider{
  height:1px;
  background:#E6D5BB;
  margin:.45rem 0;
}
.hm-rsd-native-date{
  font-weight:850;
  color:#064E3B;
  font-size:.86rem;
}
.hm-rsd-native-meals{
  color:#253B36;
  font-size:.80rem;
  line-height:1.22;
}
.hm-rsd-native-cell{
  color:#0F2F2A;
  font-size:.84rem;
}
.hm-rsd-native-note{
  color:#253B36;
  font-size:.80rem;
  line-height:1.2;
}
.hm-rsd-native-shell .stButton > button{
  min-height:1.75rem !important;
  height:1.75rem !important;
  padding:.08rem .56rem !important;
  border-radius:999px !important;
  border:1.15px solid #D6B56D !important;
  color:#064E3B !important;
  background:#FFFFFF !important;
  box-shadow:0 2px 6px rgba(15,23,42,.035) !important;
  font-size:.72rem !important;
  font-weight:700 !important;
  line-height:1 !important;
  white-space:nowrap !important;
}

/* --- v71 Compact Nutritionist History Block --- */
.hm-v71-brand-row{display:flex;align-items:baseline;gap:.55rem;flex-wrap:wrap;margin-bottom:.35rem;}
.hm-v71-brand{color:#064E3B;font-size:.82rem;font-weight:950;letter-spacing:.02em;text-transform:uppercase;}
.hm-v71-version-inline{color:#64748B;font-size:.72rem;font-weight:800;}

/* Compact history section */
h4:has(+ .info-banner), h4 {
  margin-bottom:.4rem !important;
}
.info-banner{
  padding:.55rem .7rem !important;
  border-radius:12px !important;
  margin:.35rem 0 .55rem 0 !important;
  font-size:.82rem !important;
  line-height:1.22 !important;
}
.info-banner b{
  font-size:.82rem !important;
}
.info-banner p{
  margin:.18rem 0 0 0 !important;
  font-size:.80rem !important;
  line-height:1.2 !important;
}

/* --- v72 Final Report Import Fix --- */
.hm-v72-brand-row{display:flex;align-items:baseline;gap:.55rem;flex-wrap:wrap;margin-bottom:.35rem;}
.hm-v72-brand{color:#064E3B;font-size:.82rem;font-weight:950;letter-spacing:.02em;text-transform:uppercase;}
.hm-v72-version-inline{color:#64748B;font-size:.72rem;font-weight:800;}

/* --- v73 Guard Import Fix --- */
.hm-v73-brand-row{display:flex;align-items:baseline;gap:.55rem;flex-wrap:wrap;margin-bottom:.35rem;}
.hm-v73-brand{color:#064E3B;font-size:.82rem;font-weight:950;letter-spacing:.02em;text-transform:uppercase;}
.hm-v73-version-inline{color:#64748B;font-size:.72rem;font-weight:800;}

/* --- v74 Final Report JSON Import Fix --- */
.hm-v74-brand-row{display:flex;align-items:baseline;gap:.55rem;flex-wrap:wrap;margin-bottom:.35rem;}
.hm-v74-brand{color:#064E3B;font-size:.82rem;font-weight:950;letter-spacing:.02em;text-transform:uppercase;}
.hm-v74-version-inline{color:#64748B;font-size:.72rem;font-weight:800;}

/* --- v75 Final Report Diagnostics UI --- */
.hm-v75-brand-row{display:flex;align-items:baseline;gap:.55rem;flex-wrap:wrap;margin-bottom:.35rem;}
.hm-v75-brand{color:#064E3B;font-size:.82rem;font-weight:950;letter-spacing:.02em;text-transform:uppercase;}
.hm-v75-version-inline{color:#64748B;font-size:.72rem;font-weight:800;}
.hm-v75-diagnostics-action{
  margin:.55rem 0 1rem 0;
}
.hm-v75-diagnostics-action .stButton > button{
  min-height:2.2rem !important;
  border-radius:14px !important;
  background:#FFFFFF !important;
  color:#064E3B !important;
  border:1.2px solid #D6B56D !important;
  font-size:.86rem !important;
  font-weight:800 !important;
}
.hm-v75-diagnostics-card{
  border:1px solid #E7D8BE;
  background:#FFFDF8;
  border-radius:16px;
  padding:.85rem 1rem;
  margin:.45rem 0 1rem 0;
  box-shadow:0 8px 20px rgba(15,23,42,.05);
}
.hm-v75-diagnostics-title{
  font-size:.95rem;
  font-weight:900;
  color:#064E3B;
  margin-bottom:.65rem;
}
.hm-v75-diagnostics-grid{
  display:grid;
  grid-template-columns:repeat(3, minmax(0, 1fr));
  gap:.65rem;
}
.hm-v75-diagnostics-grid div{
  border:1px solid #F0E3CE;
  border-radius:12px;
  padding:.55rem .65rem;
  background:#FFFFFF;
  font-size:.82rem;
  line-height:1.25;
}
.hm-v75-diagnostics-grid b{
  color:#334155;
  font-size:.72rem;
  text-transform:uppercase;
  letter-spacing:.02em;
}
.hm-v75-diagnostics-grid span{
  color:#064E3B;
  font-weight:750;
}
@media (max-width: 760px){
  .hm-v75-diagnostics-grid{grid-template-columns:1fr;}
}

/* --- v76 Mobile Daily Log Timing Fix --- */
.hm-v76-brand-row{display:flex;align-items:baseline;gap:.55rem;flex-wrap:wrap;margin-bottom:.35rem;}
.hm-v76-brand{color:#064E3B;font-size:.82rem;font-weight:950;letter-spacing:.02em;text-transform:uppercase;}
.hm-v76-version-inline{color:#64748B;font-size:.72rem;font-weight:800;}
/* Poop timing fields are rendered row-major: 1-2-3, 4-5-6, 7-8-9.
   On mobile Streamlit stacks each row before moving to the next row, so the order remains 1,2,3,4... */
.hm-poop-timing-grid-anchor + div [data-testid="column"]{
  margin-bottom:.25rem !important;
}
@media (max-width: 760px){
  .hm-poop-timing-grid-anchor + div [data-testid="column"],
  .hm-poop-timing-grid-anchor + div + div [data-testid="column"],
  .hm-poop-timing-grid-anchor + div + div + div [data-testid="column"]{
    margin-bottom:.35rem !important;
  }
}

/* --- v77 Meal Timing + Daily Log UI Alignment Fix --- */
.hm-v77-brand-row{display:flex;align-items:baseline;gap:.55rem;flex-wrap:wrap;margin-bottom:.35rem;}
.hm-v77-brand{color:#064E3B;font-size:.82rem;font-weight:950;letter-spacing:.02em;text-transform:uppercase;}
.hm-v77-version-inline{color:#64748B;font-size:.72rem;font-weight:800;}

/* Button schema: avoid black/off-brand buttons */
.stButton > button{
  color:#064E3B !important;
  background:#FFFFFF !important;
  border:1.2px solid #D6B56D !important;
  box-shadow:0 5px 12px rgba(15,23,42,.04) !important;
}
.stButton > button[kind="primary"],
button[kind="primary"]{
  color:#FFFFFF !important;
  background:#0B6B57 !important;
  border-color:#0B6B57 !important;
}
.stButton > button:disabled{
  color:#94A3B8 !important;
  background:#F8F5EF !important;
  border-color:#E8DDCA !important;
}

/* Recent saved days row alignment */
.hm-rsd-native-shell{
  border:1.5px solid #D9C2A0 !important;
  border-radius:18px !important;
  background:#FFFDF8 !important;
  padding:.6rem .8rem .35rem .8rem !important;
}
.hm-rsd-native-shell [data-testid="column"]{
  display:flex !important;
  align-items:center !important;
  min-height:3.6rem !important;
}
.hm-rsd-native-divider{
  height:1px !important;
  background:#DCC8A8 !important;
  margin:.3rem 0 !important;
}
.hm-rsd-native-date,
.hm-rsd-native-cell{
  display:flex !important;
  align-items:center !important;
  min-height:3.4rem !important;
}
.hm-rsd-native-meals,
.hm-rsd-native-note{
  display:flex !important;
  align-items:center !important;
  min-height:3.4rem !important;
  font-size:.78rem !important;
  line-height:1.16 !important;
}
.hm-rsd-native-shell .stButton > button{
  min-height:1.9rem !important;
  height:auto !important;
  padding:.18rem .55rem !important;
  border-radius:14px !important;
  font-size:.72rem !important;
  line-height:1.05 !important;
  white-space:normal !important;
  max-width:5.4rem !important;
}

/* --- v80 Daily Log Laptop Balance Fix --- */
.hm-v80-empty-slot{
  min-height:2.35rem;
}
.hm-snack-helper{
  margin-top:.38rem !important;
  font-size:.80rem !important;
}
.hm-compact-section-note{
  margin-bottom:.35rem !important;
}
.hm-meal-title{
  margin-top:.35rem !important;
}
@media (min-width: 900px){
  div[data-testid="stVerticalBlock"] > div:has(.hm-poop-timing-grid-anchor){
    gap:.25rem !important;
  }
  .hm-poop-timing-grid-anchor + div [data-testid="stTextInput"]{
    margin-bottom:.2rem !important;
  }
}

/* --- v81 Daily Log Full-day Rebalance + Poop Zero Fix --- */
.hm-full-day-helper{
  margin-top:.08rem !important;
  margin-bottom:.28rem !important;
  color:#7C8A96 !important;
  font-size:.81rem !important;
}
@media (min-width: 900px){
  .hm-poop-timing-grid-anchor{
    margin-top:-.1rem !important;
  }
}

/* --- v82 Full-day Details HealthyMe Structure Alignment --- */
.hm-full-day-helper{margin-top:.05rem !important;margin-bottom:.35rem !important;color:#7C8A96 !important;font-size:.81rem !important;}
.hm-poop-timing-grid-anchor{margin-top:-.05rem !important;}

/* --- v84 Date + Button + Header Alignment Polish --- */
.hm-daily-date-shell{
  border:1.4px solid #E6D6BB;
  border-radius:16px;
  background:#FFFDF8;
  box-shadow:0 8px 22px rgba(15,23,42,.045);
  padding:.8rem .95rem .55rem .95rem;
  margin:.1rem 0 1rem 0;
}
.hm-daily-date-title{
  color:#064E3B;
  font-size:.84rem;
  font-weight:850;
  margin-bottom:.25rem;
}
.hm-daily-date-shell [data-testid="stDateInput"]{
  margin-top:.1rem !important;
}
.hm-daily-date-shell [data-testid="stDateInput"] input{
  font-size:1rem !important;
  font-weight:700 !important;
}
.hm-rsd-header-cell{
  display:flex !important;
  align-items:center !important;
  min-height:2rem !important;
  color:#3F4C5F !important;
  font-size:.80rem !important;
  font-weight:850 !important;
  line-height:1.15 !important;
  width:100%;
}

/* --- v85 Date Context Emphasis Polish --- */
.hm-daily-date-shell{
  position:relative;
  border:1.8px solid #DDBE7D !important;
  border-radius:18px !important;
  background:linear-gradient(180deg,#FFFDF8 0%,#FFF9ED 100%) !important;
  box-shadow:0 10px 26px rgba(15,23,42,.05), inset 0 1px 0 rgba(255,255,255,.65) !important;
  padding:1rem 1rem .8rem 1rem !important;
  margin:.15rem 0 1.1rem 0 !important;
}
.hm-daily-date-shell::before{
  content:"";
  position:absolute;
  left:0; top:0; bottom:0;
  width:6px;
  border-radius:18px 0 0 18px;
  background:linear-gradient(180deg,#0F766E 0%, #D4A63A 100%);
}
.hm-daily-date-title{
  color:#064E3B !important;
  font-size:.95rem !important;
  font-weight:900 !important;
  letter-spacing:.01em !important;
  margin:0 0 .42rem .2rem !important;
}
.hm-daily-date-shell [data-testid="stDateInput"]{
  margin:0 0 0 .15rem !important;
}
.hm-daily-date-shell [data-testid="stDateInput"] > div{
  background:transparent !important;
}
.hm-daily-date-shell [data-testid="stDateInput"] input{
  background:#FFFFFF !important;
  border:1.4px solid #E4D1AA !important;
  border-radius:14px !important;
  box-shadow:0 1px 0 rgba(255,255,255,.8), 0 6px 16px rgba(15,23,42,.045) !important;
  color:#064E3B !important;
  font-size:1.08rem !important;
  font-weight:800 !important;
  padding:.78rem .95rem !important;
}

/* --- v88.1 Mobile Visual Spacing Polish --- */
.hm-full-day-helper-tight{
  margin-top:.02rem!important;
  margin-bottom:.22rem!important;
  font-size:.78rem!important;
}
@media (max-width: 768px){
  .hm-meal-title{
    margin-top:.22rem!important;
    margin-bottom:.05rem!important;
    font-size:1rem!important;
  }
  .hm-compact-section-note{
    margin-bottom:.18rem!important;
    font-size:.79rem!important;
    line-height:1.18!important;
  }
  .hm-full-day-helper{
    font-size:.78rem!important;
    line-height:1.14!important;
    margin-bottom:.22rem!important;
  }
}

</style>
"""

def inject_global_styles(): st.markdown(LUXE_CSS, unsafe_allow_html=True)
def apply_luxe_theme():
    return None
def apply_mobile_first_premium_theme():
    inject_global_styles()

def topbar(title, subtitle="", kicker="HealthyMe premium"):
    st.markdown(f"""<div class='hero-shell'><div class='hero-kicker'>{kicker}</div><div class='hero-title'>{title}</div><div class='hero-subtitle'>{subtitle}</div><div><span class='meta-pill'>Guided wellness workflow</span></div></div>""", unsafe_allow_html=True)

def card_start():
    """
    Compatibility no-op.

    Previous versions emitted raw opening HTML and closing HTML in separate
    Streamlit elements. Streamlit can render those as empty visible boxes,
    which creates blank/hidden-looking sections.
    """
    return None

def card_end():
    """Compatibility no-op. See card_start()."""
    return None

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


# --- UX Navigation + User Intent Patch Helpers ---
def page_anchor_top():
    st.markdown("<div id='top' class='hm-page-anchor'></div>", unsafe_allow_html=True)

def nav_button(label, target_page, key, *, primary=False):
    """Compatibility wrapper for old calls."""
    if st.button(label, key=key, type='primary' if primary else 'secondary', use_container_width=True):
        st.switch_page(target_page)

def _safe_page_link(target_page, label, icon=None):
    """Use Streamlit native page links for smoother navigation."""
    try:
        st.page_link(target_page, label=label, icon=icon, use_container_width=True)
    except Exception:
        # Fallback for older Streamlit versions.
        if st.button(label, key=f"fallback_{label}_{target_page}", use_container_width=True):
            st.switch_page(target_page)

def render_page_nav(current_label='', back_page=None, dashboard_page='pages/10_Admin_Dashboard.py', evaluation_page='pages/11_Evaluation_Status.py', *, location='top', show_dashboard=True, show_evaluation=True):
    """Consistent top/bottom navigation for long admin pages.

    v4 uses native page links for Back/Evaluation/Dashboard. This avoids the
    abrupt button-triggered rerun blanking that was visible during navigation.
    """
    if location == 'top':
        page_anchor_top()
        st.markdown("<div class='hm-native-nav-shell'>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='hm-bottom-nav-shell hm-native-nav-shell'>", unsafe_allow_html=True)

    cols = st.columns(3)
    with cols[0]:
        if back_page:
            _safe_page_link(back_page, "Back", icon=":material/arrow_back:")
        else:
            st.empty()
    with cols[1]:
        if show_evaluation:
            _safe_page_link(evaluation_page, "Evaluation Status", icon=":material/fact_check:")
        else:
            st.empty()
    with cols[2]:
        if show_dashboard:
            _safe_page_link(dashboard_page, "Dashboard", icon=":material/dashboard:")
        else:
            st.empty()

    st.markdown("</div>", unsafe_allow_html=True)

    if location != 'top':
        st.markdown("<div style='margin:.45rem 0 0 0;'><a href='#top'>↑ Back to top</a></div>", unsafe_allow_html=True)
def priority_action_start(title, subtitle=''):
    st.markdown(f"""<div class='hm-priority-action'><h3>{title}</h3><div class='hero-subtitle'>{subtitle}</div>""", unsafe_allow_html=True)

def priority_action_end():
    st.markdown('</div>', unsafe_allow_html=True)


def build_marker_v7():
    st.markdown("<div class='hm-build-marker'>✅ Build v7 active · Structural reset loaded</div>", unsafe_allow_html=True)


def build_marker_v8():
    st.markdown("<div class='hm-build-marker'>✅ Build v8 active · Layout refinement loaded</div>", unsafe_allow_html=True)


def build_marker_v9():
    st.markdown("<div class='hm-build-marker'>✅ Build v9 active · Compact tooltip layout loaded</div>", unsafe_allow_html=True)


APP_BUILD_VERSION = "v95.7"
APP_BUILD_LABEL = "Admin Version + Button Template Fix"

def render_build_text_v11():
    """Small non-intrusive build text. Not a visual tag."""
    st.markdown("<div class='hm-v11-build-text'>HealthyMe v11 · Designer stable build</div>", unsafe_allow_html=True)

def build_marker_v11():
    render_build_text_v11()


# --------------------------------------------------------------------
# v12: Single source of truth for visible build marker
# --------------------------------------------------------------------
APP_BUILD_VERSION = "v12"
APP_BUILD_LABEL = "Consistent build + header card patch"

def render_current_build(compact=True):
    """Single current build marker used across all pages."""
    cls = "hm-current-build-text" if compact else "hm-current-build-badge"
    st.markdown(
        f"<div class='{cls}'>HealthyMe {APP_BUILD_VERSION} · {APP_BUILD_LABEL}</div>",
        unsafe_allow_html=True,
    )

# New preferred name
def render_build_text_v12():
    render_current_build(compact=True)

# Backward-compatible aliases.
# These intentionally override older marker functions so all pages show the same build.
def render_build_text_v11():
    render_current_build(compact=True)

def build_marker_v11():
    render_current_build(compact=True)

def build_marker_v10():
    render_current_build(compact=True)

def build_marker_v9():
    render_current_build(compact=True)

def build_marker_v8():
    render_current_build(compact=True)

def build_marker_v7():
    render_current_build(compact=True)

def render_version_tag():
    render_current_build(compact=True)


# --------------------------------------------------------------------
# v13: single current build text
# --------------------------------------------------------------------
APP_BUILD_VERSION = "v13"
APP_BUILD_LABEL = "Client-safe dashboard redesign"

def render_current_build(compact=True):
    st.markdown(
        f"<div class='hm-v13-build-text'>HealthyMe {APP_BUILD_VERSION} · {APP_BUILD_LABEL}</div>",
        unsafe_allow_html=True,
    )

def render_build_text_v13():
    render_current_build(compact=True)

# Backward-compatible aliases. All old marker calls now show v13.
def render_build_text_v12():
    render_current_build(compact=True)

def render_build_text_v11():
    render_current_build(compact=True)

def build_marker_v11():
    render_current_build(compact=True)

def build_marker_v10():
    render_current_build(compact=True)

def build_marker_v9():
    render_current_build(compact=True)

def build_marker_v8():
    render_current_build(compact=True)

def build_marker_v7():
    render_current_build(compact=True)

def render_version_tag():
    render_current_build(compact=True)


# --------------------------------------------------------------------
# v14: current build text
# --------------------------------------------------------------------
APP_BUILD_VERSION = "v14"
APP_BUILD_LABEL = "Native cards + dashboard flow fix"

def render_current_build(compact=True):
    st.markdown(
        f"<div class='hm-v14-build-text'>HealthyMe {APP_BUILD_VERSION} · {APP_BUILD_LABEL}</div>",
        unsafe_allow_html=True,
    )

def render_build_text_v14():
    render_current_build(compact=True)

# Backward-compatible aliases. All older markers now show v14.
def render_build_text_v13():
    render_current_build(compact=True)

def render_build_text_v12():
    render_current_build(compact=True)

def render_build_text_v11():
    render_current_build(compact=True)

def build_marker_v11():
    render_current_build(compact=True)

def build_marker_v10():
    render_current_build(compact=True)

def build_marker_v9():
    render_current_build(compact=True)

def build_marker_v8():
    render_current_build(compact=True)

def build_marker_v7():
    render_current_build(compact=True)

def render_version_tag():
    render_current_build(compact=True)


# --------------------------------------------------------------------
# v15: current build text + cleaner page nav labels
# --------------------------------------------------------------------
APP_BUILD_VERSION = 'v15'
APP_BUILD_LABEL = 'Navigation + action consistency patch'

def render_current_build(compact=True):
    st.markdown(f"<div class='hm-v15-build-text'>HealthyMe {APP_BUILD_VERSION} · {APP_BUILD_LABEL}</div>", unsafe_allow_html=True)

def render_build_text_v15():
    render_current_build(compact=True)

def render_build_text_v14():
    render_current_build(compact=True)
def render_build_text_v13():
    render_current_build(compact=True)
def render_build_text_v12():
    render_current_build(compact=True)
def render_build_text_v11():
    render_current_build(compact=True)
def build_marker_v11():
    render_current_build(compact=True)
def build_marker_v10():
    render_current_build(compact=True)
def build_marker_v9():
    render_current_build(compact=True)
def build_marker_v8():
    render_current_build(compact=True)
def build_marker_v7():
    render_current_build(compact=True)
def render_version_tag():
    render_current_build(compact=True)

def render_page_nav(current_label='', back_page=None, dashboard_page='pages/10_Admin_Dashboard.py', evaluation_page='pages/11_Evaluation_Status.py', *, location='top', show_dashboard=True, show_evaluation=True):
    if location == 'top':
        page_anchor_top()
    else:
        st.markdown("<div style='margin-top:.55rem;'></div>", unsafe_allow_html=True)

    cols = st.columns(3)
    with cols[0]:
        if back_page:
            _safe_page_link(back_page, '← Back')
        else:
            st.empty()
    with cols[1]:
        if show_evaluation:
            _safe_page_link(evaluation_page, 'Evaluation Status')
        else:
            st.empty()
    with cols[2]:
        if show_dashboard:
            _safe_page_link(dashboard_page, 'Dashboard')
        else:
            st.empty()

    if location != 'top':
        st.markdown("<div style='margin:.45rem 0 0 0;'><a href='#top'>↑ Back to top</a></div>", unsafe_allow_html=True)


# --------------------------------------------------------------------
# v23: version display + logout polish
# --------------------------------------------------------------------
APP_BUILD_VERSION = "v23"
APP_BUILD_LABEL = "Stability + Visibility Fix"

def render_build_text_v23():
    st.markdown(
        f"<div class='hm-v23-version-line'>{APP_BUILD_VERSION} · {APP_BUILD_LABEL}</div>",
        unsafe_allow_html=True,
    )

def topbar(title, subtitle="", kicker="HealthyMe premium"):
    st.markdown(
        f"""
        <div class='hero-shell'>
          <div class='hero-kicker'>{kicker}</div>
          <div class='hero-title'>{title}</div>
          <div class='hm-v23-version-line'>{APP_BUILD_VERSION} · {APP_BUILD_LABEL}</div>
          <div class='hero-subtitle'>{subtitle}</div>
          <div><span class='meta-pill'>Guided wellness workflow</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# Backward-compatible build aliases.
def render_build_text_v22():
    render_build_text_v23()
def render_build_text_v21():
    render_build_text_v23()
def render_build_text_v20():
    render_build_text_v23()
def render_build_text_v19():
    render_build_text_v23()
def render_build_text_v18():
    render_build_text_v23()
def render_build_text_v17():
    render_build_text_v23()
def render_build_text_v16():
    render_build_text_v23()
def render_build_text_v15():
    render_build_text_v23()
def render_build_text_v14():
    render_build_text_v23()
def render_build_text_v13():
    render_build_text_v23()
def render_build_text_v12():
    render_build_text_v23()
def render_build_text_v11():
    render_build_text_v23()
def build_marker_v11():
    render_build_text_v23()
def build_marker_v10():
    render_build_text_v23()
def build_marker_v9():
    render_build_text_v23()
def build_marker_v8():
    render_build_text_v23()
def build_marker_v7():
    render_build_text_v23()
def render_version_tag():
    render_build_text_v23()


def utility_logout_bar():
    role=st.session_state.get("user_role","")
    name=st.session_state.get("user_name","User")
    if not st.session_state.get("logged_in"):
        return
    left,right=st.columns([5,1])
    with left:
        st.markdown(f"<div class='utility-bar'><div class='utility-user'>Signed in as <b>{name}</b><span class='utility-role'>{role.title()}</span></div></div>", unsafe_allow_html=True)
    with right:
        if st.button("Logout", key="global_logout", use_container_width=True):
            st.session_state["logout_in_progress"] = True
            logout_current_user()
            st.switch_page("pages/01_Login.py")


# --------------------------------------------------------------------
# v24: brand version placement
# --------------------------------------------------------------------
APP_BUILD_VERSION = "v24"
APP_BUILD_LABEL = "Body-Mind + Version Placement Fix"

def render_build_text_v24():
    st.markdown(
        f"<div class='hm-v24-brand'>HealthyMe</div><div class='hm-v24-version-line'>{APP_BUILD_VERSION} · {APP_BUILD_LABEL}</div>",
        unsafe_allow_html=True,
    )

def topbar(title, subtitle="", kicker="HealthyMe premium"):
    st.markdown(
        f"""
        <div class='hero-shell'>
          <div class='hm-v24-brand'>HealthyMe</div>
          <div class='hm-v24-version-line'>{APP_BUILD_VERSION} · {APP_BUILD_LABEL}</div>
          <div class='hero-kicker'>{kicker}</div>
          <div class='hero-title'>{title}</div>
          <div class='hero-subtitle'>{subtitle}</div>
          <div><span class='meta-pill'>Guided wellness workflow</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# Backward-compatible build aliases.
def render_build_text_v23():
    render_build_text_v24()
def render_build_text_v22():
    render_build_text_v24()
def render_build_text_v21():
    render_build_text_v24()
def render_build_text_v20():
    render_build_text_v24()
def render_build_text_v19():
    render_build_text_v24()
def render_build_text_v18():
    render_build_text_v24()
def render_build_text_v17():
    render_build_text_v24()
def render_build_text_v16():
    render_build_text_v24()
def render_build_text_v15():
    render_build_text_v24()
def render_build_text_v14():
    render_build_text_v24()
def render_build_text_v13():
    render_build_text_v24()
def render_build_text_v12():
    render_build_text_v24()
def render_build_text_v11():
    render_build_text_v24()
def build_marker_v11():
    render_build_text_v24()
def build_marker_v10():
    render_build_text_v24()
def build_marker_v9():
    render_build_text_v24()
def build_marker_v8():
    render_build_text_v24()
def build_marker_v7():
    render_build_text_v24()
def render_version_tag():
    render_build_text_v24()


# --------------------------------------------------------------------
# v25: current build marker
# --------------------------------------------------------------------
APP_BUILD_VERSION = "v25"
APP_BUILD_LABEL = "Body-Mind State Sync Fix"

def render_build_text_v25():
    st.markdown(
        f"<div class='hm-v23-version-line'>{APP_BUILD_VERSION} · {APP_BUILD_LABEL}</div>",
        unsafe_allow_html=True,
    )

# aliases
def render_build_text_v24():
    render_build_text_v25()
def render_build_text_v23():
    render_build_text_v25()
def render_build_text_v22():
    render_build_text_v25()
def render_build_text_v21():
    render_build_text_v25()
def render_build_text_v20():
    render_build_text_v25()
def render_build_text_v19():
    render_build_text_v25()
def render_build_text_v18():
    render_build_text_v25()
def render_build_text_v17():
    render_build_text_v25()
def render_build_text_v16():
    render_build_text_v25()
def render_build_text_v15():
    render_build_text_v25()
def render_build_text_v14():
    render_build_text_v25()
def render_build_text_v13():
    render_build_text_v25()
def render_build_text_v12():
    render_build_text_v25()
def render_build_text_v11():
    render_build_text_v25()
def build_marker_v11():
    render_build_text_v25()
def build_marker_v10():
    render_build_text_v25()
def build_marker_v9():
    render_build_text_v25()
def build_marker_v8():
    render_build_text_v25()
def build_marker_v7():
    render_build_text_v25()
def render_version_tag():
    render_build_text_v25()


# --------------------------------------------------------------------
# v26: current build marker
# --------------------------------------------------------------------
APP_BUILD_VERSION = "v26"
APP_BUILD_LABEL = "Finalization Lock + Body-Mind Sync"

def render_build_text_v26():
    st.markdown(
        f"<div class='hm-v23-version-line'>{APP_BUILD_VERSION} · {APP_BUILD_LABEL}</div>",
        unsafe_allow_html=True,
    )

def render_build_text_v25():
    render_build_text_v26()
def render_build_text_v24():
    render_build_text_v26()
def render_build_text_v23():
    render_build_text_v26()
def render_build_text_v22():
    render_build_text_v26()
def render_build_text_v21():
    render_build_text_v26()
def render_build_text_v20():
    render_build_text_v26()
def render_build_text_v19():
    render_build_text_v26()
def render_build_text_v18():
    render_build_text_v26()
def render_build_text_v17():
    render_build_text_v26()
def render_build_text_v16():
    render_build_text_v26()
def render_build_text_v15():
    render_build_text_v26()
def render_build_text_v14():
    render_build_text_v26()
def render_build_text_v13():
    render_build_text_v26()
def render_build_text_v12():
    render_build_text_v26()
def render_build_text_v11():
    render_build_text_v26()
def build_marker_v11():
    render_build_text_v26()
def build_marker_v10():
    render_build_text_v26()
def build_marker_v9():
    render_build_text_v26()
def build_marker_v8():
    render_build_text_v26()
def build_marker_v7():
    render_build_text_v26()
def render_version_tag():
    render_build_text_v26()


# --------------------------------------------------------------------
# v27: current build marker
# --------------------------------------------------------------------
APP_BUILD_VERSION = "v27"
APP_BUILD_LABEL = "Final Report NSP Data Integrity + Body-Mind Carry Forward"

def render_build_text_v27():
    st.markdown(
        f"<div class='hm-v23-version-line'>{APP_BUILD_VERSION} · {APP_BUILD_LABEL}</div>",
        unsafe_allow_html=True,
    )

def render_build_text_v26():
    render_build_text_v27()
def render_build_text_v25():
    render_build_text_v27()
def render_build_text_v24():
    render_build_text_v27()
def render_build_text_v23():
    render_build_text_v27()
def render_build_text_v22():
    render_build_text_v27()
def render_build_text_v21():
    render_build_text_v27()
def render_build_text_v20():
    render_build_text_v27()
def render_build_text_v19():
    render_build_text_v27()
def render_build_text_v18():
    render_build_text_v27()
def render_build_text_v17():
    render_build_text_v27()
def render_build_text_v16():
    render_build_text_v27()
def render_build_text_v15():
    render_build_text_v27()
def render_build_text_v14():
    render_build_text_v27()
def render_build_text_v13():
    render_build_text_v27()
def render_build_text_v12():
    render_build_text_v27()
def render_build_text_v11():
    render_build_text_v27()
def build_marker_v11():
    render_build_text_v27()
def build_marker_v10():
    render_build_text_v27()
def build_marker_v9():
    render_build_text_v27()
def build_marker_v8():
    render_build_text_v27()
def build_marker_v7():
    render_build_text_v27()
def render_version_tag():
    render_build_text_v27()


# --------------------------------------------------------------------
# v28: Body-Mind final unlock + version cleanup
# --------------------------------------------------------------------
APP_BUILD_VERSION = "v28"
APP_BUILD_LABEL = "Body-Mind Final Unlock + Version Cleanup"

def topbar(title, subtitle="", kicker="HealthyMe premium"):
    st.markdown(
        f"""
        <div class='hero-shell'>
          <div class='hm-v28-brand-row'>
            <span class='hm-v28-brand'>HealthyMe</span>
            <span class='hm-v28-version-inline'>{APP_BUILD_VERSION} · {APP_BUILD_LABEL}</span>
          </div>
          <div class='hero-kicker'>{kicker}</div>
          <div class='hero-title'>{title}</div>
          <div class='hero-subtitle'>{subtitle}</div>
          <div><span class='meta-pill'>Guided wellness workflow</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_build_text_v28(): return None
def render_build_text_v27(): return None
def render_build_text_v26(): return None
def render_build_text_v25(): return None
def render_build_text_v24(): return None
def render_build_text_v23(): return None
def render_build_text_v22(): return None
def render_build_text_v21(): return None
def render_build_text_v20(): return None
def render_build_text_v19(): return None
def render_build_text_v18(): return None
def render_build_text_v17(): return None
def render_build_text_v16(): return None
def render_build_text_v15(): return None
def render_build_text_v14(): return None
def render_build_text_v13(): return None
def render_build_text_v12(): return None
def render_build_text_v11(): return None
def build_marker_v11(): return None
def build_marker_v10(): return None
def build_marker_v9(): return None
def build_marker_v8(): return None
def build_marker_v7(): return None
def render_version_tag(): return None


# --------------------------------------------------------------------
# v29: Manual Body-Mind unlock + version cleanup
# --------------------------------------------------------------------
APP_BUILD_VERSION = "v29"
APP_BUILD_LABEL = "Manual Body-Mind Unlock"

def topbar(title, subtitle="", kicker="HealthyMe premium"):
    st.markdown(
        f"""
        <div class='hero-shell'>
          <div class='hm-v29-brand-row'>
            <span class='hm-v29-brand'>HealthyMe</span>
            <span class='hm-v29-version-inline'>{APP_BUILD_VERSION} · {APP_BUILD_LABEL}</span>
          </div>
          <div class='hero-kicker'>{kicker}</div>
          <div class='hero-title'>{title}</div>
          <div class='hero-subtitle'>{subtitle}</div>
          <div><span class='meta-pill'>Guided wellness workflow</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_build_text_v29(): return None
def render_build_text_v28(): return None
def render_build_text_v27(): return None
def render_build_text_v26(): return None
def render_build_text_v25(): return None
def render_build_text_v24(): return None
def render_build_text_v23(): return None
def render_build_text_v22(): return None
def render_build_text_v21(): return None
def render_build_text_v20(): return None
def render_build_text_v19(): return None
def render_build_text_v18(): return None
def render_build_text_v17(): return None
def render_build_text_v16(): return None
def render_build_text_v15(): return None
def render_build_text_v14(): return None
def render_build_text_v13(): return None
def render_build_text_v12(): return None
def render_build_text_v11(): return None
def build_marker_v11(): return None
def build_marker_v10(): return None
def build_marker_v9(): return None
def build_marker_v8(): return None
def build_marker_v7(): return None
def render_version_tag(): return None


# --------------------------------------------------------------------
# v30: Manual Body-Mind unlock control
# --------------------------------------------------------------------
APP_BUILD_VERSION = "v30"
APP_BUILD_LABEL = "Manual Body-Mind Unlock Control"

def topbar(title, subtitle="", kicker="HealthyMe premium"):
    st.markdown(
        f"""
        <div class='hero-shell'>
          <div class='hm-v30-brand-row'>
            <span class='hm-v30-brand'>HealthyMe</span>
            <span class='hm-v30-version-inline'>{APP_BUILD_VERSION} · {APP_BUILD_LABEL}</span>
          </div>
          <div class='hero-kicker'>{kicker}</div>
          <div class='hero-title'>{title}</div>
          <div class='hero-subtitle'>{subtitle}</div>
          <div><span class='meta-pill'>Guided wellness workflow</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_build_text_v30(): return None
def render_build_text_v29(): return None
def render_build_text_v28(): return None
def render_build_text_v27(): return None
def render_build_text_v26(): return None
def render_build_text_v25(): return None
def render_build_text_v24(): return None
def render_build_text_v23(): return None
def render_build_text_v22(): return None
def render_build_text_v21(): return None
def render_build_text_v20(): return None
def render_build_text_v19(): return None
def render_build_text_v18(): return None
def render_build_text_v17(): return None
def render_build_text_v16(): return None
def render_build_text_v15(): return None
def render_build_text_v14(): return None
def render_build_text_v13(): return None
def render_build_text_v12(): return None
def render_build_text_v11(): return None
def build_marker_v11(): return None
def build_marker_v10(): return None
def build_marker_v9(): return None
def build_marker_v8(): return None
def build_marker_v7(): return None
def render_version_tag(): return None


# --------------------------------------------------------------------
# v31: Workflow + assessment instance sync
# --------------------------------------------------------------------
APP_BUILD_VERSION = "v31"
APP_BUILD_LABEL = "Workflow + Body-Mind Sync"

def topbar(title, subtitle="", kicker="HealthyMe premium"):
    st.markdown(
        f"""
        <div class='hero-shell'>
          <div class='hm-v31-brand-row'>
            <span class='hm-v31-brand'>HealthyMe</span>
            <span class='hm-v31-version-inline'>{APP_BUILD_VERSION} · {APP_BUILD_LABEL}</span>
          </div>
          <div class='hero-kicker'>{kicker}</div>
          <div class='hero-title'>{title}</div>
          <div class='hero-subtitle'>{subtitle}</div>
          <div><span class='meta-pill'>Guided wellness workflow</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_build_text_v31(): return None
def render_build_text_v30(): return None
def render_build_text_v29(): return None
def render_build_text_v28(): return None
def render_build_text_v27(): return None
def render_build_text_v26(): return None
def render_build_text_v25(): return None
def render_build_text_v24(): return None
def render_build_text_v23(): return None
def render_build_text_v22(): return None
def render_build_text_v21(): return None
def render_build_text_v20(): return None
def render_build_text_v19(): return None
def render_build_text_v18(): return None
def render_build_text_v17(): return None
def render_build_text_v16(): return None
def render_build_text_v15(): return None
def render_build_text_v14(): return None
def render_build_text_v13(): return None
def render_build_text_v12(): return None
def render_build_text_v11(): return None
def build_marker_v11(): return None
def build_marker_v10(): return None
def build_marker_v9(): return None
def build_marker_v8(): return None
def build_marker_v7(): return None
def render_version_tag(): return None


# --------------------------------------------------------------------
# v32: Manual Body-Mind hard sync
# --------------------------------------------------------------------
APP_BUILD_VERSION = "v32"
APP_BUILD_LABEL = "Manual Body-Mind Hard Sync"

def topbar(title, subtitle="", kicker="HealthyMe premium"):
    st.markdown(
        f"""
        <div class='hero-shell'>
          <div class='hm-v32-brand-row'>
            <span class='hm-v32-brand'>HealthyMe</span>
            <span class='hm-v32-version-inline'>{APP_BUILD_VERSION} · {APP_BUILD_LABEL}</span>
          </div>
          <div class='hero-kicker'>{kicker}</div>
          <div class='hero-title'>{title}</div>
          <div class='hero-subtitle'>{subtitle}</div>
          <div><span class='meta-pill'>Guided wellness workflow</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_build_text_v32(): return None
def render_build_text_v31(): return None
def render_build_text_v30(): return None
def render_build_text_v29(): return None
def render_build_text_v28(): return None
def render_build_text_v27(): return None
def render_build_text_v26(): return None
def render_build_text_v25(): return None
def render_build_text_v24(): return None
def render_build_text_v23(): return None
def render_build_text_v22(): return None
def render_build_text_v21(): return None
def render_build_text_v20(): return None
def render_build_text_v19(): return None
def render_build_text_v18(): return None
def render_build_text_v17(): return None
def render_build_text_v16(): return None
def render_build_text_v15(): return None
def render_build_text_v14(): return None
def render_build_text_v13(): return None
def render_build_text_v12(): return None
def render_build_text_v11(): return None
def build_marker_v11(): return None
def build_marker_v10(): return None
def build_marker_v9(): return None
def build_marker_v8(): return None
def build_marker_v7(): return None
def render_version_tag(): return None


# --------------------------------------------------------------------
# v33: clean logout
# --------------------------------------------------------------------
def utility_logout_bar():
    role=st.session_state.get("user_role","")
    name=st.session_state.get("user_name","User")
    if not st.session_state.get("logged_in"):
        return
    left,right=st.columns([5,1])
    with left:
        st.markdown(f"<div class='utility-bar'><div class='utility-user'>Signed in as <b>{name}</b><span class='utility-role'>{role.title()}</span></div></div>", unsafe_allow_html=True)
    with right:
        if st.button("Logout", key="global_logout", use_container_width=True):
            logout_current_user()
            st.switch_page("pages/01_Login.py")


# --------------------------------------------------------------------
# v33: Body-Mind explicit access marker
# --------------------------------------------------------------------
APP_BUILD_VERSION = "v33"
APP_BUILD_LABEL = "Body-Mind Explicit Access"

def topbar(title, subtitle="", kicker="HealthyMe premium"):
    st.markdown(
        f"""
        <div class='hero-shell'>
          <div class='hm-v33-brand-row'>
            <span class='hm-v33-brand'>HealthyMe</span>
            <span class='hm-v33-version-inline'>{APP_BUILD_VERSION} · {APP_BUILD_LABEL}</span>
          </div>
          <div class='hero-kicker'>{kicker}</div>
          <div class='hero-title'>{title}</div>
          <div class='hero-subtitle'>{subtitle}</div>
          <div><span class='meta-pill'>Guided wellness workflow</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_build_text_v33(): return None
def render_build_text_v32(): return None
def render_build_text_v31(): return None
def render_build_text_v30(): return None
def render_build_text_v29(): return None
def render_build_text_v28(): return None
def render_build_text_v27(): return None
def render_build_text_v26(): return None
def render_build_text_v25(): return None
def render_build_text_v24(): return None
def render_build_text_v23(): return None
def render_build_text_v22(): return None
def render_build_text_v21(): return None
def render_build_text_v20(): return None
def render_build_text_v19(): return None
def render_build_text_v18(): return None
def render_build_text_v17(): return None
def render_build_text_v16(): return None
def render_build_text_v15(): return None
def render_build_text_v14(): return None
def render_build_text_v13(): return None
def render_build_text_v12(): return None
def render_build_text_v11(): return None
def build_marker_v11(): return None
def build_marker_v10(): return None
def build_marker_v9(): return None
def build_marker_v8(): return None
def build_marker_v7(): return None
def render_version_tag(): return None


# --------------------------------------------------------------------
# v34: clean logout without switch_page double refresh
# --------------------------------------------------------------------
def utility_logout_bar():
    role = st.session_state.get("user_role", "")
    name = st.session_state.get("user_name", "User")
    if not st.session_state.get("logged_in"):
        return

    left, right = st.columns([5, 1])
    with left:
        st.markdown(
            f"<div class='utility-bar'><div class='utility-user'>Signed in as <b>{name}</b><span class='utility-role'>{role.title()}</span></div></div>",
            unsafe_allow_html=True,
        )
    with right:
        if st.button("Logout", key="global_logout", use_container_width=True):
            logout_current_user()
            st.session_state["logged_in"] = False
            st.session_state.pop("user_id", None)
            st.session_state.pop("user_role", None)
            st.session_state.pop("user_name", None)
            st.rerun()


# --------------------------------------------------------------------
# v34: Body-Mind NameError + logout fix
# --------------------------------------------------------------------
APP_BUILD_VERSION = "v34"
APP_BUILD_LABEL = "Body-Mind NameError + Logout Fix"

def topbar(title, subtitle="", kicker="HealthyMe premium"):
    st.markdown(
        f"""
        <div class='hero-shell'>
          <div class='hm-v34-brand-row'>
            <span class='hm-v34-brand'>HealthyMe</span>
            <span class='hm-v34-version-inline'>{APP_BUILD_VERSION} · {APP_BUILD_LABEL}</span>
          </div>
          <div class='hero-kicker'>{kicker}</div>
          <div class='hero-title'>{title}</div>
          <div class='hero-subtitle'>{subtitle}</div>
          <div><span class='meta-pill'>Guided wellness workflow</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_build_text_v34(): return None
def render_build_text_v33(): return None
def render_build_text_v32(): return None
def render_build_text_v31(): return None
def render_build_text_v30(): return None
def render_build_text_v29(): return None
def render_build_text_v28(): return None
def render_build_text_v27(): return None
def render_build_text_v26(): return None
def render_build_text_v25(): return None
def render_build_text_v24(): return None
def render_build_text_v23(): return None
def render_build_text_v22(): return None
def render_build_text_v21(): return None
def render_build_text_v20(): return None
def render_build_text_v19(): return None
def render_build_text_v18(): return None
def render_build_text_v17(): return None
def render_build_text_v16(): return None
def render_build_text_v15(): return None
def render_build_text_v14(): return None
def render_build_text_v13(): return None
def render_build_text_v12(): return None
def render_build_text_v11(): return None
def build_marker_v11(): return None
def build_marker_v10(): return None
def build_marker_v9(): return None
def build_marker_v8(): return None
def build_marker_v7(): return None
def render_version_tag(): return None


# --------------------------------------------------------------------
# v35: clean logout single-rerun path
# --------------------------------------------------------------------
def utility_logout_bar():
    role = st.session_state.get("user_role", "")
    name = st.session_state.get("user_name", "User")
    if not st.session_state.get("logged_in"):
        return

    left, right = st.columns([5, 1])
    with left:
        st.markdown(
            f"<div class='utility-bar'><div class='utility-user'>Signed in as <b>{name}</b><span class='utility-role'>{role.title()}</span></div></div>",
            unsafe_allow_html=True,
        )
    with right:
        if st.button("Logout", key="global_logout", use_container_width=True):
            logout_current_user()
            st.session_state["logged_in"] = False
            st.session_state["force_login_view"] = True
            st.rerun()


# --------------------------------------------------------------------
# v35: Body-Mind page guard fix
# --------------------------------------------------------------------
APP_BUILD_VERSION = "v35"
APP_BUILD_LABEL = "Body-Mind Page Guard Fix"

def topbar(title, subtitle="", kicker="HealthyMe premium"):
    st.markdown(
        f"""
        <div class='hero-shell'>
          <div class='hm-v35-brand-row'>
            <span class='hm-v35-brand'>HealthyMe</span>
            <span class='hm-v35-version-inline'>{APP_BUILD_VERSION} · {APP_BUILD_LABEL}</span>
          </div>
          <div class='hero-kicker'>{kicker}</div>
          <div class='hero-title'>{title}</div>
          <div class='hero-subtitle'>{subtitle}</div>
          <div><span class='meta-pill'>Guided wellness workflow</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_build_text_v35(): return None
def render_build_text_v34(): return None
def render_build_text_v33(): return None
def render_build_text_v32(): return None
def render_build_text_v31(): return None
def render_build_text_v30(): return None
def render_build_text_v29(): return None
def render_build_text_v28(): return None
def render_build_text_v27(): return None
def render_build_text_v26(): return None
def render_build_text_v25(): return None
def render_build_text_v24(): return None
def render_build_text_v23(): return None
def render_build_text_v22(): return None
def render_build_text_v21(): return None
def render_build_text_v20(): return None
def render_build_text_v19(): return None
def render_build_text_v18(): return None
def render_build_text_v17(): return None
def render_build_text_v16(): return None
def render_build_text_v15(): return None
def render_build_text_v14(): return None
def render_build_text_v13(): return None
def render_build_text_v12(): return None
def render_build_text_v11(): return None
def build_marker_v11(): return None
def build_marker_v10(): return None
def build_marker_v9(): return None
def build_marker_v8(): return None
def build_marker_v7(): return None
def render_version_tag(): return None


# --------------------------------------------------------------------
# v36: Body-Mind text removal + autosave check
# --------------------------------------------------------------------
APP_BUILD_VERSION = "v36"
APP_BUILD_LABEL = "Body-Mind Admin State + Autosave Check"

def topbar(title, subtitle="", kicker="HealthyMe premium"):
    st.markdown(
        f"""
        <div class='hero-shell'>
          <div class='hm-v36-brand-row'>
            <span class='hm-v36-brand'>HealthyMe</span>
            <span class='hm-v36-version-inline'>{APP_BUILD_VERSION} · {APP_BUILD_LABEL}</span>
          </div>
          <div class='hero-kicker'>{kicker}</div>
          <div class='hero-title'>{title}</div>
          <div class='hero-subtitle'>{subtitle}</div>
          <div><span class='meta-pill'>Guided wellness workflow</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_build_text_v36(): return None
def render_build_text_v35(): return None
def render_build_text_v34(): return None
def render_build_text_v33(): return None
def render_build_text_v32(): return None
def render_build_text_v31(): return None
def render_build_text_v30(): return None
def render_build_text_v29(): return None
def render_build_text_v28(): return None
def render_build_text_v27(): return None
def render_build_text_v26(): return None
def render_build_text_v25(): return None
def render_build_text_v24(): return None
def render_build_text_v23(): return None
def render_build_text_v22(): return None
def render_build_text_v21(): return None
def render_build_text_v20(): return None
def render_build_text_v19(): return None
def render_build_text_v18(): return None
def render_build_text_v17(): return None
def render_build_text_v16(): return None
def render_build_text_v15(): return None
def render_build_text_v14(): return None
def render_build_text_v13(): return None
def render_build_text_v12(): return None
def render_build_text_v11(): return None
def build_marker_v11(): return None
def build_marker_v10(): return None
def build_marker_v9(): return None
def build_marker_v8(): return None
def build_marker_v7(): return None
def render_version_tag(): return None


# --------------------------------------------------------------------
# v37: Remove Body-Mind activation checkbox
# --------------------------------------------------------------------
APP_BUILD_VERSION = "v37"
APP_BUILD_LABEL = "Remove Body-Mind Activation Checkbox"

def topbar(title, subtitle="", kicker="HealthyMe premium"):
    st.markdown(
        f"""
        <div class='hero-shell'>
          <div class='hm-v37-brand-row'>
            <span class='hm-v37-brand'>HealthyMe</span>
            <span class='hm-v37-version-inline'>{APP_BUILD_VERSION} · {APP_BUILD_LABEL}</span>
          </div>
          <div class='hero-kicker'>{kicker}</div>
          <div class='hero-title'>{title}</div>
          <div class='hero-subtitle'>{subtitle}</div>
          <div><span class='meta-pill'>Guided wellness workflow</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_build_text_v37(): return None
def render_build_text_v36(): return None
def render_build_text_v35(): return None
def render_build_text_v34(): return None
def render_build_text_v33(): return None
def render_build_text_v32(): return None
def render_build_text_v31(): return None
def render_build_text_v30(): return None
def render_build_text_v29(): return None
def render_build_text_v28(): return None
def render_build_text_v27(): return None
def render_build_text_v26(): return None
def render_build_text_v25(): return None
def render_build_text_v24(): return None
def render_build_text_v23(): return None
def render_build_text_v22(): return None
def render_build_text_v21(): return None
def render_build_text_v20(): return None
def render_build_text_v19(): return None
def render_build_text_v18(): return None
def render_build_text_v17(): return None
def render_build_text_v16(): return None
def render_build_text_v15(): return None
def render_build_text_v14(): return None
def render_build_text_v13(): return None
def render_build_text_v12(): return None
def render_build_text_v11(): return None
def build_marker_v11(): return None
def build_marker_v10(): return None
def build_marker_v9(): return None
def build_marker_v8(): return None
def build_marker_v7(): return None
def render_version_tag(): return None


# --------------------------------------------------------------------
# v38: Body-Mind disabled button UI
# --------------------------------------------------------------------
APP_BUILD_VERSION = "v38"
APP_BUILD_LABEL = "Body-Mind Disabled Button UI"

def topbar(title, subtitle="", kicker="HealthyMe premium"):
    st.markdown(
        f"""
        <div class='hero-shell'>
          <div class='hm-v38-brand-row'>
            <span class='hm-v38-brand'>HealthyMe</span>
            <span class='hm-v38-version-inline'>{APP_BUILD_VERSION} · {APP_BUILD_LABEL}</span>
          </div>
          <div class='hero-kicker'>{kicker}</div>
          <div class='hero-title'>{title}</div>
          <div class='hero-subtitle'>{subtitle}</div>
          <div><span class='meta-pill'>Guided wellness workflow</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_build_text_v38(): return None
def render_build_text_v37(): return None
def render_build_text_v36(): return None
def render_build_text_v35(): return None
def render_build_text_v34(): return None
def render_build_text_v33(): return None
def render_build_text_v32(): return None
def render_build_text_v31(): return None
def render_build_text_v30(): return None
def render_build_text_v29(): return None
def render_build_text_v28(): return None
def render_build_text_v27(): return None
def render_build_text_v26(): return None
def render_build_text_v25(): return None
def render_build_text_v24(): return None
def render_build_text_v23(): return None
def render_build_text_v22(): return None
def render_build_text_v21(): return None
def render_build_text_v20(): return None
def render_build_text_v19(): return None
def render_build_text_v18(): return None
def render_build_text_v17(): return None
def render_build_text_v16(): return None
def render_build_text_v15(): return None
def render_build_text_v14(): return None
def render_build_text_v13(): return None
def render_build_text_v12(): return None
def render_build_text_v11(): return None
def build_marker_v11(): return None
def build_marker_v10(): return None
def build_marker_v9(): return None
def build_marker_v8(): return None
def build_marker_v7(): return None
def render_version_tag(): return None


# --------------------------------------------------------------------
# v39: Admin 5 Pages autosave
# --------------------------------------------------------------------
APP_BUILD_VERSION = "v39"
APP_BUILD_LABEL = "Admin Autosave"

def topbar(title, subtitle="", kicker="HealthyMe premium"):
    st.markdown(
        f"""
        <div class='hero-shell'>
          <div class='hm-v39-brand-row'>
            <span class='hm-v39-brand'>HealthyMe</span>
            <span class='hm-v39-version-inline'>{APP_BUILD_VERSION} · {APP_BUILD_LABEL}</span>
          </div>
          <div class='hero-kicker'>{kicker}</div>
          <div class='hero-title'>{title}</div>
          <div class='hero-subtitle'>{subtitle}</div>
          <div><span class='meta-pill'>Guided wellness workflow</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_build_text_v39(): return None
def render_build_text_v38(): return None
def render_build_text_v37(): return None
def render_build_text_v36(): return None
def render_build_text_v35(): return None
def render_build_text_v34(): return None
def render_build_text_v33(): return None
def render_build_text_v32(): return None
def render_build_text_v31(): return None
def render_build_text_v30(): return None
def render_build_text_v29(): return None
def render_build_text_v28(): return None
def render_build_text_v27(): return None
def render_build_text_v26(): return None
def render_build_text_v25(): return None
def render_build_text_v24(): return None
def render_build_text_v23(): return None
def render_build_text_v22(): return None
def render_build_text_v21(): return None
def render_build_text_v20(): return None
def render_build_text_v19(): return None
def render_build_text_v18(): return None
def render_build_text_v17(): return None
def render_build_text_v16(): return None
def render_build_text_v15(): return None
def render_build_text_v14(): return None
def render_build_text_v13(): return None
def render_build_text_v12(): return None
def render_build_text_v11(): return None
def build_marker_v11(): return None
def build_marker_v10(): return None
def build_marker_v9(): return None
def build_marker_v8(): return None
def build_marker_v7(): return None
def render_version_tag(): return None


# --------------------------------------------------------------------
# v40: Body-Mind status sync
# --------------------------------------------------------------------
APP_BUILD_VERSION = "v40"
APP_BUILD_LABEL = "Body-Mind Status Sync"

def topbar(title, subtitle="", kicker="HealthyMe premium"):
    st.markdown(
        f"""
        <div class='hero-shell'>
          <div class='hm-v40-brand-row'>
            <span class='hm-v40-brand'>HealthyMe</span>
            <span class='hm-v40-version-inline'>{APP_BUILD_VERSION} · {APP_BUILD_LABEL}</span>
          </div>
          <div class='hero-kicker'>{kicker}</div>
          <div class='hero-title'>{title}</div>
          <div class='hero-subtitle'>{subtitle}</div>
          <div><span class='meta-pill'>Guided wellness workflow</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_build_text_v40(): return None
def render_build_text_v39(): return None
def render_build_text_v38(): return None
def render_build_text_v37(): return None
def render_build_text_v36(): return None
def render_build_text_v35(): return None
def render_build_text_v34(): return None
def render_build_text_v33(): return None
def render_build_text_v32(): return None
def render_build_text_v31(): return None
def render_build_text_v30(): return None
def render_build_text_v29(): return None
def render_build_text_v28(): return None
def render_build_text_v27(): return None
def render_build_text_v26(): return None
def render_build_text_v25(): return None
def render_build_text_v24(): return None
def render_build_text_v23(): return None
def render_build_text_v22(): return None
def render_build_text_v21(): return None
def render_build_text_v20(): return None
def render_build_text_v19(): return None
def render_build_text_v18(): return None
def render_build_text_v17(): return None
def render_build_text_v16(): return None
def render_build_text_v15(): return None
def render_build_text_v14(): return None
def render_build_text_v13(): return None
def render_build_text_v12(): return None
def render_build_text_v11(): return None
def build_marker_v11(): return None
def build_marker_v10(): return None
def build_marker_v9(): return None
def build_marker_v8(): return None
def build_marker_v7(): return None
def render_version_tag(): return None


# --------------------------------------------------------------------
# v41: Daily Log Flow
# --------------------------------------------------------------------
APP_BUILD_VERSION = "v41"
APP_BUILD_LABEL = "Daily Log Flow"

def topbar(title, subtitle="", kicker="HealthyMe premium"):
    st.markdown(
        f"""
        <div class='hero-shell'>
          <div class='hm-v41-brand-row'>
            <span class='hm-v41-brand'>HealthyMe</span>
            <span class='hm-v41-version-inline'>{APP_BUILD_VERSION} · {APP_BUILD_LABEL}</span>
          </div>
          <div class='hero-kicker'>{kicker}</div>
          <div class='hero-title'>{title}</div>
          <div class='hero-subtitle'>{subtitle}</div>
          <div><span class='meta-pill'>Guided wellness workflow</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_build_text_v41(): return None
def render_build_text_v40(): return None
def render_build_text_v39(): return None
def render_build_text_v38(): return None
def render_build_text_v37(): return None
def render_build_text_v36(): return None
def render_build_text_v35(): return None
def render_build_text_v34(): return None
def render_build_text_v33(): return None
def render_build_text_v32(): return None
def render_build_text_v31(): return None
def render_build_text_v30(): return None
def render_build_text_v29(): return None
def render_build_text_v28(): return None
def render_build_text_v27(): return None
def render_build_text_v26(): return None
def render_build_text_v25(): return None
def render_build_text_v24(): return None
def render_build_text_v23(): return None
def render_build_text_v22(): return None
def render_build_text_v21(): return None
def render_build_text_v20(): return None
def render_build_text_v19(): return None
def render_build_text_v18(): return None
def render_build_text_v17(): return None
def render_build_text_v16(): return None
def render_build_text_v15(): return None
def render_build_text_v14(): return None
def render_build_text_v13(): return None
def render_build_text_v12(): return None
def render_build_text_v11(): return None
def build_marker_v11(): return None
def build_marker_v10(): return None
def build_marker_v9(): return None
def build_marker_v8(): return None
def build_marker_v7(): return None
def render_version_tag(): return None


# --------------------------------------------------------------------
# v42: Day-based Daily Log
# --------------------------------------------------------------------
APP_BUILD_VERSION = "v42"
APP_BUILD_LABEL = "Day-based Daily Log"

def topbar(title, subtitle="", kicker="HealthyMe premium"):
    st.markdown(
        f"""
        <div class='hero-shell'>
          <div class='hm-v42-brand-row'>
            <span class='hm-v42-brand'>HealthyMe</span>
            <span class='hm-v42-version-inline'>{APP_BUILD_VERSION} · {APP_BUILD_LABEL}</span>
          </div>
          <div class='hero-kicker'>{kicker}</div>
          <div class='hero-title'>{title}</div>
          <div class='hero-subtitle'>{subtitle}</div>
          <div><span class='meta-pill'>Guided wellness workflow</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_build_text_v42(): return None
def render_build_text_v41(): return None
def render_build_text_v40(): return None
def render_build_text_v39(): return None
def render_build_text_v38(): return None
def render_build_text_v37(): return None
def render_build_text_v36(): return None
def render_build_text_v35(): return None
def render_build_text_v34(): return None
def render_build_text_v33(): return None
def render_build_text_v32(): return None
def render_build_text_v31(): return None
def render_build_text_v30(): return None
def render_build_text_v29(): return None
def render_build_text_v28(): return None
def render_build_text_v27(): return None
def render_build_text_v26(): return None
def render_build_text_v25(): return None
def render_build_text_v24(): return None
def render_build_text_v23(): return None
def render_build_text_v22(): return None
def render_build_text_v21(): return None
def render_build_text_v20(): return None
def render_build_text_v19(): return None
def render_build_text_v18(): return None
def render_build_text_v17(): return None
def render_build_text_v16(): return None
def render_build_text_v15(): return None
def render_build_text_v14(): return None
def render_build_text_v13(): return None
def render_build_text_v12(): return None
def render_build_text_v11(): return None
def build_marker_v11(): return None
def build_marker_v10(): return None
def build_marker_v9(): return None
def build_marker_v8(): return None
def build_marker_v7(): return None
def render_version_tag(): return None


# --------------------------------------------------------------------
# v43: Progressive Daily Log + Repository
# --------------------------------------------------------------------
APP_BUILD_VERSION = "v43"
APP_BUILD_LABEL = "Progressive Daily Log + Repository"

def topbar(title, subtitle="", kicker="HealthyMe premium"):
    st.markdown(
        f"""
        <div class='hero-shell'>
          <div class='hm-v43-brand-row'>
            <span class='hm-v43-brand'>HealthyMe</span>
            <span class='hm-v43-version-inline'>{APP_BUILD_VERSION} · {APP_BUILD_LABEL}</span>
          </div>
          <div class='hero-kicker'>{kicker}</div>
          <div class='hero-title'>{title}</div>
          <div class='hero-subtitle'>{subtitle}</div>
          <div><span class='meta-pill'>Guided wellness workflow</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_build_text_v43(): return None
def render_build_text_v42(): return None
def render_build_text_v41(): return None
def render_build_text_v40(): return None
def render_build_text_v39(): return None
def render_build_text_v38(): return None
def render_build_text_v37(): return None
def render_build_text_v36(): return None
def render_build_text_v35(): return None
def render_build_text_v34(): return None
def render_build_text_v33(): return None
def render_build_text_v32(): return None
def render_build_text_v31(): return None
def render_build_text_v30(): return None
def render_build_text_v29(): return None
def render_build_text_v28(): return None
def render_build_text_v27(): return None
def render_build_text_v26(): return None
def render_build_text_v25(): return None
def render_build_text_v24(): return None
def render_build_text_v23(): return None
def render_build_text_v22(): return None
def render_build_text_v21(): return None
def render_build_text_v20(): return None
def render_build_text_v19(): return None
def render_build_text_v18(): return None
def render_build_text_v17(): return None
def render_build_text_v16(): return None
def render_build_text_v15(): return None
def render_build_text_v14(): return None
def render_build_text_v13(): return None
def render_build_text_v12(): return None
def render_build_text_v11(): return None
def build_marker_v11(): return None
def build_marker_v10(): return None
def build_marker_v9(): return None
def build_marker_v8(): return None
def build_marker_v7(): return None
def render_version_tag(): return None


# --------------------------------------------------------------------
# v44: Daily Log one-section mode + Other slots
# --------------------------------------------------------------------
APP_BUILD_VERSION = "v44"
APP_BUILD_LABEL = "Daily Log One-Section + Other Slots"

def topbar(title, subtitle="", kicker="HealthyMe premium"):
    st.markdown(
        f"""
        <div class='hero-shell'>
          <div class='hm-v44-brand-row'>
            <span class='hm-v44-brand'>HealthyMe</span>
            <span class='hm-v44-version-inline'>{APP_BUILD_VERSION} · {APP_BUILD_LABEL}</span>
          </div>
          <div class='hero-kicker'>{kicker}</div>
          <div class='hero-title'>{title}</div>
          <div class='hero-subtitle'>{subtitle}</div>
          <div><span class='meta-pill'>Guided wellness workflow</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_build_text_v44(): return None
def render_build_text_v43(): return None
def render_build_text_v42(): return None
def render_build_text_v41(): return None
def render_build_text_v40(): return None
def render_build_text_v39(): return None
def render_build_text_v38(): return None
def render_build_text_v37(): return None
def render_build_text_v36(): return None
def render_build_text_v35(): return None
def render_build_text_v34(): return None
def render_build_text_v33(): return None
def render_build_text_v32(): return None
def render_build_text_v31(): return None
def render_build_text_v30(): return None
def render_build_text_v29(): return None
def render_build_text_v28(): return None
def render_build_text_v27(): return None
def render_build_text_v26(): return None
def render_build_text_v25(): return None
def render_build_text_v24(): return None
def render_build_text_v23(): return None
def render_build_text_v22(): return None
def render_build_text_v21(): return None
def render_build_text_v20(): return None
def render_build_text_v19(): return None
def render_build_text_v18(): return None
def render_build_text_v17(): return None
def render_build_text_v16(): return None
def render_build_text_v15(): return None
def render_build_text_v14(): return None
def render_build_text_v13(): return None
def render_build_text_v12(): return None
def render_build_text_v11(): return None
def build_marker_v11(): return None
def build_marker_v10(): return None
def build_marker_v9(): return None
def build_marker_v8(): return None
def build_marker_v7(): return None
def render_version_tag(): return None


# --------------------------------------------------------------------
# v45: Daily Log compact Other fix
# --------------------------------------------------------------------
APP_BUILD_VERSION = "v45"
APP_BUILD_LABEL = "Daily Log Compact Other Fix"

def topbar(title, subtitle="", kicker="HealthyMe premium"):
    st.markdown(
        f"""
        <div class='hero-shell'>
          <div class='hm-v45-brand-row'>
            <span class='hm-v45-brand'>HealthyMe</span>
            <span class='hm-v45-version-inline'>{APP_BUILD_VERSION} · {APP_BUILD_LABEL}</span>
          </div>
          <div class='hero-kicker'>{kicker}</div>
          <div class='hero-title'>{title}</div>
          <div class='hero-subtitle'>{subtitle}</div>
          <div><span class='meta-pill'>Guided wellness workflow</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_build_text_v45(): return None
def render_build_text_v44(): return None
def render_build_text_v43(): return None
def render_build_text_v42(): return None
def render_build_text_v41(): return None
def render_build_text_v40(): return None
def render_build_text_v39(): return None
def render_build_text_v38(): return None
def render_build_text_v37(): return None
def render_build_text_v36(): return None
def render_build_text_v35(): return None
def render_build_text_v34(): return None
def render_build_text_v33(): return None
def render_build_text_v32(): return None
def render_build_text_v31(): return None
def render_build_text_v30(): return None
def render_build_text_v29(): return None
def render_build_text_v28(): return None
def render_build_text_v27(): return None
def render_build_text_v26(): return None
def render_build_text_v25(): return None
def render_build_text_v24(): return None
def render_build_text_v23(): return None
def render_build_text_v22(): return None
def render_build_text_v21(): return None
def render_build_text_v20(): return None
def render_build_text_v19(): return None
def render_build_text_v18(): return None
def render_build_text_v17(): return None
def render_build_text_v16(): return None
def render_build_text_v15(): return None
def render_build_text_v14(): return None
def render_build_text_v13(): return None
def render_build_text_v12(): return None
def render_build_text_v11(): return None
def build_marker_v11(): return None
def build_marker_v10(): return None
def build_marker_v9(): return None
def build_marker_v8(): return None
def build_marker_v7(): return None
def render_version_tag(): return None


# --------------------------------------------------------------------
# v46: Admin info cleanup + Daily Log selector layout
# --------------------------------------------------------------------
APP_BUILD_VERSION = "v46"
APP_BUILD_LABEL = "Admin Info Cleanup + Daily Log Layout"

def topbar(title, subtitle="", kicker="HealthyMe premium"):
    st.markdown(
        f"""
        <div class='hero-shell'>
          <div class='hm-v46-brand-row'>
            <span class='hm-v46-brand'>HealthyMe</span>
            <span class='hm-v46-version-inline'>{APP_BUILD_VERSION} · {APP_BUILD_LABEL}</span>
          </div>
          <div class='hero-kicker'>{kicker}</div>
          <div class='hero-title'>{title}</div>
          <div class='hero-subtitle'>{subtitle}</div>
          <div><span class='meta-pill'>Guided wellness workflow</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_build_text_v46(): return None
def render_build_text_v45(): return None
def render_build_text_v44(): return None
def render_build_text_v43(): return None
def render_build_text_v42(): return None
def render_build_text_v41(): return None
def render_build_text_v40(): return None
def render_build_text_v39(): return None
def render_build_text_v38(): return None
def render_build_text_v37(): return None
def render_build_text_v36(): return None
def render_build_text_v35(): return None
def render_build_text_v34(): return None
def render_build_text_v33(): return None
def render_build_text_v32(): return None
def render_build_text_v31(): return None
def render_build_text_v30(): return None
def render_build_text_v29(): return None
def render_build_text_v28(): return None
def render_build_text_v27(): return None
def render_build_text_v26(): return None
def render_build_text_v25(): return None
def render_build_text_v24(): return None
def render_build_text_v23(): return None
def render_build_text_v22(): return None
def render_build_text_v21(): return None
def render_build_text_v20(): return None
def render_build_text_v19(): return None
def render_build_text_v18(): return None
def render_build_text_v17(): return None
def render_build_text_v16(): return None
def render_build_text_v15(): return None
def render_build_text_v14(): return None
def render_build_text_v13(): return None
def render_build_text_v12(): return None
def render_build_text_v11(): return None
def build_marker_v11(): return None
def build_marker_v10(): return None
def build_marker_v9(): return None
def build_marker_v8(): return None
def build_marker_v7(): return None
def render_version_tag(): return None


# --------------------------------------------------------------------
# v47: final logout override - no rerun/switch after st.logout
# --------------------------------------------------------------------
def utility_logout_bar():
    role = st.session_state.get("user_role", "")
    name = st.session_state.get("user_name", "User")
    if not st.session_state.get("logged_in"):
        return
    left, right = st.columns([5, 1])
    with left:
        st.markdown(
            f"<div class='utility-bar'><div class='utility-user'>Signed in as <b>{name}</b><span class='utility-role'>{role.title()}</span></div></div>",
            unsafe_allow_html=True,
        )
    with right:
        if st.button("Logout", key="global_logout", use_container_width=True):
            logout_current_user()


# --------------------------------------------------------------------
# v47: Logout + Daily Log Backcompat + Reference Toggle
# --------------------------------------------------------------------
APP_BUILD_VERSION = "v47"
APP_BUILD_LABEL = "Logout + Daily Log Backcompat"

def topbar(title, subtitle="", kicker="HealthyMe premium"):
    st.markdown(
        f"""
        <div class='hero-shell'>
          <div class='hm-v47-brand-row'>
            <span class='hm-v47-brand'>HealthyMe</span>
            <span class='hm-v47-version-inline'>{APP_BUILD_VERSION} · {APP_BUILD_LABEL}</span>
          </div>
          <div class='hero-kicker'>{kicker}</div>
          <div class='hero-title'>{title}</div>
          <div class='hero-subtitle'>{subtitle}</div>
          <div><span class='meta-pill'>Guided wellness workflow</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_build_text_v47(): return None
def render_build_text_v46(): return None
def render_build_text_v45(): return None
def render_build_text_v44(): return None
def render_build_text_v43(): return None
def render_build_text_v42(): return None
def render_build_text_v41(): return None
def render_build_text_v40(): return None
def render_build_text_v39(): return None
def render_build_text_v38(): return None
def render_build_text_v37(): return None
def render_build_text_v36(): return None
def render_build_text_v35(): return None
def render_build_text_v34(): return None
def render_build_text_v33(): return None
def render_build_text_v32(): return None
def render_build_text_v31(): return None
def render_build_text_v30(): return None
def render_build_text_v29(): return None
def render_build_text_v28(): return None
def render_build_text_v27(): return None
def render_build_text_v26(): return None
def render_build_text_v25(): return None
def render_build_text_v24(): return None
def render_build_text_v23(): return None
def render_build_text_v22(): return None
def render_build_text_v21(): return None
def render_build_text_v20(): return None
def render_build_text_v19(): return None
def render_build_text_v18(): return None
def render_build_text_v17(): return None
def render_build_text_v16(): return None
def render_build_text_v15(): return None
def render_build_text_v14(): return None
def render_build_text_v13(): return None
def render_build_text_v12(): return None
def render_build_text_v11(): return None
def build_marker_v11(): return None
def build_marker_v10(): return None
def build_marker_v9(): return None
def build_marker_v8(): return None
def build_marker_v7(): return None
def render_version_tag(): return None


# --------------------------------------------------------------------
# v48: Nutritionist Message Archive
# --------------------------------------------------------------------
APP_BUILD_VERSION = "v48"
APP_BUILD_LABEL = "Nutritionist Message Archive"

def topbar(title, subtitle="", kicker="HealthyMe premium"):
    st.markdown(
        f"""
        <div class='hero-shell'>
          <div class='hm-v48-brand-row'>
            <span class='hm-v48-brand'>HealthyMe</span>
            <span class='hm-v48-version-inline'>{APP_BUILD_VERSION} · {APP_BUILD_LABEL}</span>
          </div>
          <div class='hero-kicker'>{kicker}</div>
          <div class='hero-title'>{title}</div>
          <div class='hero-subtitle'>{subtitle}</div>
          <div><span class='meta-pill'>Guided wellness workflow</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_build_text_v48(): return None
def render_build_text_v47(): return None
def render_build_text_v46(): return None
def render_build_text_v45(): return None
def render_build_text_v44(): return None
def render_build_text_v43(): return None
def render_build_text_v42(): return None
def render_build_text_v41(): return None
def render_build_text_v40(): return None
def render_build_text_v39(): return None
def render_build_text_v38(): return None
def render_build_text_v37(): return None
def render_build_text_v36(): return None
def render_build_text_v35(): return None
def render_build_text_v34(): return None
def render_build_text_v33(): return None
def render_build_text_v32(): return None
def render_build_text_v31(): return None
def render_build_text_v30(): return None
def render_build_text_v29(): return None
def render_build_text_v28(): return None
def render_build_text_v27(): return None
def render_build_text_v26(): return None
def render_build_text_v25(): return None
def render_build_text_v24(): return None
def render_build_text_v23(): return None
def render_build_text_v22(): return None
def render_build_text_v21(): return None
def render_build_text_v20(): return None
def render_build_text_v19(): return None
def render_build_text_v18(): return None
def render_build_text_v17(): return None
def render_build_text_v16(): return None
def render_build_text_v15(): return None
def render_build_text_v14(): return None
def render_build_text_v13(): return None
def render_build_text_v12(): return None
def render_build_text_v11(): return None
def build_marker_v11(): return None
def build_marker_v10(): return None
def build_marker_v9(): return None
def build_marker_v8(): return None
def build_marker_v7(): return None
def render_version_tag(): return None


# --------------------------------------------------------------------
# v49: logout routes through Login page before OIDC logout
# --------------------------------------------------------------------
def utility_logout_bar():
    role = st.session_state.get("user_role", "")
    name = st.session_state.get("user_name", "User")
    if not st.session_state.get("logged_in"):
        return




    left, right = st.columns([5, 1])
    with left:
        st.markdown(
            f"<div class='utility-bar'><div class='utility-user'>Signed in as <b>{name}</b><span class='utility-role'>{role.title()}</span></div></div>",
            unsafe_allow_html=True,
        )
    with right:
        if st.button("Logout", key="global_logout", use_container_width=True):
            # Clear app-level state first, then move to login page.
            # Login page performs the final native OIDC logout if still authenticated.
            for k in list(st.session_state.keys()):
                try:
                    del st.session_state[k]
                except Exception:
                    pass
            st.session_state["signed_out"] = True
            st.session_state["logout_requested"] = True
            try:
                st.query_params["logout"] = "1"
            except Exception:
                pass
            st.switch_page("pages/01_Login.py")


# --------------------------------------------------------------------
# v49: Logout Session Hardening
# --------------------------------------------------------------------
APP_BUILD_VERSION = "v49"
APP_BUILD_LABEL = "Logout Session Hardening"

def topbar(title, subtitle="", kicker="HealthyMe premium"):
    st.markdown(
        f"""
        <div class='hero-shell'>
          <div class='hm-v49-brand-row'>
            <span class='hm-v49-brand'>HealthyMe</span>
            <span class='hm-v49-version-inline'>{APP_BUILD_VERSION} · {APP_BUILD_LABEL}</span>
          </div>
          <div class='hero-kicker'>{kicker}</div>
          <div class='hero-title'>{title}</div>
          <div class='hero-subtitle'>{subtitle}</div>
          <div><span class='meta-pill'>Guided wellness workflow</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_build_text_v49(): return None
def render_build_text_v48(): return None
def render_build_text_v47(): return None
def render_build_text_v46(): return None
def render_build_text_v45(): return None
def render_build_text_v44(): return None
def render_build_text_v43(): return None
def render_build_text_v42(): return None
def render_build_text_v41(): return None
def render_build_text_v40(): return None
def render_build_text_v39(): return None
def render_build_text_v38(): return None
def render_build_text_v37(): return None
def render_build_text_v36(): return None
def render_build_text_v35(): return None
def render_build_text_v34(): return None
def render_build_text_v33(): return None
def render_build_text_v32(): return None
def render_build_text_v31(): return None
def render_build_text_v30(): return None
def render_build_text_v29(): return None
def render_build_text_v28(): return None
def render_build_text_v27(): return None
def render_build_text_v26(): return None
def render_build_text_v25(): return None
def render_build_text_v24(): return None
def render_build_text_v23(): return None
def render_build_text_v22(): return None
def render_build_text_v21(): return None
def render_build_text_v20(): return None
def render_build_text_v19(): return None
def render_build_text_v18(): return None
def render_build_text_v17(): return None
def render_build_text_v16(): return None
def render_build_text_v15(): return None
def render_build_text_v14(): return None
def render_build_text_v13(): return None
def render_build_text_v12(): return None
def render_build_text_v11(): return None
def build_marker_v11(): return None
def build_marker_v10(): return None
def build_marker_v9(): return None
def build_marker_v8(): return None
def build_marker_v7(): return None
def render_version_tag(): return None


# --------------------------------------------------------------------
# v50: Member Home Message + Journey Compact
# --------------------------------------------------------------------
APP_BUILD_VERSION = "v50"
APP_BUILD_LABEL = "Member Home Message + Journey Compact"

def topbar(title, subtitle="", kicker="HealthyMe premium"):
    st.markdown(
        f"""
        <div class='hero-shell'>
          <div class='hm-v50-brand-row'>
            <span class='hm-v50-brand'>HealthyMe</span>
            <span class='hm-v50-version-inline'>{APP_BUILD_VERSION} · {APP_BUILD_LABEL}</span>
          </div>
          <div class='hero-kicker'>{kicker}</div>
          <div class='hero-title'>{title}</div>
          <div class='hero-subtitle'>{subtitle}</div>
          <div><span class='meta-pill'>Guided wellness workflow</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_build_text_v50(): return None
def render_build_text_v49(): return None
def render_build_text_v48(): return None
def render_build_text_v47(): return None
def render_build_text_v46(): return None
def render_build_text_v45(): return None
def render_build_text_v44(): return None
def render_build_text_v43(): return None
def render_build_text_v42(): return None
def render_build_text_v41(): return None
def render_build_text_v40(): return None
def render_build_text_v39(): return None
def render_build_text_v38(): return None
def render_build_text_v37(): return None
def render_build_text_v36(): return None
def render_build_text_v35(): return None
def render_build_text_v34(): return None
def render_build_text_v33(): return None
def render_build_text_v32(): return None
def render_build_text_v31(): return None
def render_build_text_v30(): return None
def render_build_text_v29(): return None
def render_build_text_v28(): return None
def render_build_text_v27(): return None
def render_build_text_v26(): return None
def render_build_text_v25(): return None
def render_build_text_v24(): return None
def render_build_text_v23(): return None
def render_build_text_v22(): return None
def render_build_text_v21(): return None
def render_build_text_v20(): return None
def render_build_text_v19(): return None
def render_build_text_v18(): return None
def render_build_text_v17(): return None
def render_build_text_v16(): return None
def render_build_text_v15(): return None
def render_build_text_v14(): return None
def render_build_text_v13(): return None
def render_build_text_v12(): return None
def render_build_text_v11(): return None
def build_marker_v11(): return None
def build_marker_v10(): return None
def build_marker_v9(): return None
def build_marker_v8(): return None
def build_marker_v7(): return None
def render_version_tag(): return None




# --------------------------------------------------------------------
# v51: Timezone + Notes Archive + Back to Top
# --------------------------------------------------------------------
APP_BUILD_VERSION = "v51"
APP_BUILD_LABEL = "Timezone + Notes Archive + Back to Top"

def topbar(title, subtitle="", kicker="HealthyMe premium"):
    st.markdown(
        f"""
        <div class='hero-shell'>
          <div class='hm-v51-brand-row'>
            <span class='hm-v51-brand'>HealthyMe</span>
            <span class='hm-v51-version-inline'>{APP_BUILD_VERSION} · {APP_BUILD_LABEL}</span>
          </div>
          <div class='hero-kicker'>{kicker}</div>
          <div class='hero-title'>{title}</div>
          <div class='hero-subtitle'>{subtitle}</div>
          <div><span class='meta-pill'>Guided wellness workflow</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_build_text_v51(): return None
def render_build_text_v50(): return None
def render_build_text_v49(): return None
def render_build_text_v48(): return None
def render_build_text_v47(): return None
def render_build_text_v46(): return None
def render_build_text_v45(): return None
def render_build_text_v44(): return None
def render_build_text_v43(): return None
def render_build_text_v42(): return None
def render_build_text_v41(): return None
def render_build_text_v40(): return None
def render_build_text_v39(): return None
def render_build_text_v38(): return None
def render_build_text_v37(): return None
def render_build_text_v36(): return None
def render_build_text_v35(): return None
def render_build_text_v34(): return None
def render_build_text_v33(): return None
def render_build_text_v32(): return None
def render_build_text_v31(): return None
def render_build_text_v30(): return None
def render_build_text_v29(): return None
def render_build_text_v28(): return None
def render_build_text_v27(): return None
def render_build_text_v26(): return None
def render_build_text_v25(): return None
def render_build_text_v24(): return None
def render_build_text_v23(): return None
def render_build_text_v22(): return None
def render_build_text_v21(): return None
def render_build_text_v20(): return None
def render_build_text_v19(): return None
def render_build_text_v18(): return None
def render_build_text_v17(): return None
def render_build_text_v16(): return None
def render_build_text_v15(): return None
def render_build_text_v14(): return None
def render_build_text_v13(): return None
def render_build_text_v12(): return None
def render_build_text_v11(): return None
def build_marker_v11(): return None
def build_marker_v10(): return None
def build_marker_v9(): return None
def build_marker_v8(): return None
def build_marker_v7(): return None
def render_version_tag(): return None


# --------------------------------------------------------------------
# v52: Login Logout Block Bottom
# --------------------------------------------------------------------
APP_BUILD_VERSION = "v52"
APP_BUILD_LABEL = "Login Logout Block Bottom"

def topbar(title, subtitle="", kicker="HealthyMe premium"):
    st.markdown(
        f"""
        <div class='hero-shell'>
          <div class='hm-v52-brand-row'>
            <span class='hm-v52-brand'>HealthyMe</span>
            <span class='hm-v52-version-inline'>{APP_BUILD_VERSION} · {APP_BUILD_LABEL}</span>
          </div>
          <div class='hero-kicker'>{kicker}</div>
          <div class='hero-title'>{title}</div>
          <div class='hero-subtitle'>{subtitle}</div>
          <div><span class='meta-pill'>Guided wellness workflow</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_build_text_v52(): return None
def render_build_text_v51(): return None
def render_build_text_v50(): return None
def render_build_text_v49(): return None
def render_build_text_v48(): return None
def render_build_text_v47(): return None
def render_build_text_v46(): return None
def render_build_text_v45(): return None
def render_build_text_v44(): return None
def render_build_text_v43(): return None
def render_build_text_v42(): return None
def render_build_text_v41(): return None
def render_build_text_v40(): return None
def render_build_text_v39(): return None
def render_build_text_v38(): return None
def render_build_text_v37(): return None
def render_build_text_v36(): return None
def render_build_text_v35(): return None
def render_build_text_v34(): return None
def render_build_text_v33(): return None
def render_build_text_v32(): return None
def render_build_text_v31(): return None
def render_build_text_v30(): return None
def render_build_text_v29(): return None
def render_build_text_v28(): return None
def render_build_text_v27(): return None
def render_build_text_v26(): return None
def render_build_text_v25(): return None
def render_build_text_v24(): return None
def render_build_text_v23(): return None
def render_build_text_v22(): return None
def render_build_text_v21(): return None
def render_build_text_v20(): return None
def render_build_text_v19(): return None
def render_build_text_v18(): return None
def render_build_text_v17(): return None
def render_build_text_v16(): return None
def render_build_text_v15(): return None
def render_build_text_v14(): return None
def render_build_text_v13(): return None
def render_build_text_v12(): return None
def render_build_text_v11(): return None
def build_marker_v11(): return None
def build_marker_v10(): return None
def build_marker_v9(): return None
def build_marker_v8(): return None
def build_marker_v7(): return None
def render_version_tag(): return None


# --------------------------------------------------------------------
# v53: ImportError UI helper fix
# --------------------------------------------------------------------
APP_BUILD_VERSION = "v53"
APP_BUILD_LABEL = "UI Helper Import Fix"

def topbar(title, subtitle="", kicker="HealthyMe premium"):
    st.markdown(
        f"""
        <div class='hero-shell'>
          <div class='hm-v53-brand-row'>
            <span class='hm-v53-brand'>HealthyMe</span>
            <span class='hm-v53-version-inline'>{APP_BUILD_VERSION} · {APP_BUILD_LABEL}</span>
          </div>
          <div class='hero-kicker'>{kicker}</div>
          <div class='hero-title'>{title}</div>
          <div class='hero-subtitle'>{subtitle}</div>
          <div><span class='meta-pill'>Guided wellness workflow</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_build_text_v53(): return None
def render_build_text_v52(): return None
def render_build_text_v51(): return None
def render_build_text_v50(): return None
def render_build_text_v49(): return None
def render_build_text_v48(): return None
def render_build_text_v47(): return None
def render_build_text_v46(): return None
def render_build_text_v45(): return None
def render_build_text_v44(): return None
def render_build_text_v43(): return None
def render_build_text_v42(): return None
def render_build_text_v41(): return None
def render_build_text_v40(): return None
def render_build_text_v39(): return None
def render_build_text_v38(): return None
def render_build_text_v37(): return None
def render_build_text_v36(): return None
def render_build_text_v35(): return None
def render_build_text_v34(): return None
def render_build_text_v33(): return None
def render_build_text_v32(): return None
def render_build_text_v31(): return None
def render_build_text_v30(): return None
def render_build_text_v29(): return None
def render_build_text_v28(): return None
def render_build_text_v27(): return None
def render_build_text_v26(): return None
def render_build_text_v25(): return None
def render_build_text_v24(): return None
def render_build_text_v23(): return None
def render_build_text_v22(): return None
def render_build_text_v21(): return None
def render_build_text_v20(): return None
def render_build_text_v19(): return None
def render_build_text_v18(): return None
def render_build_text_v17(): return None
def render_build_text_v16(): return None
def render_build_text_v15(): return None
def render_build_text_v14(): return None
def render_build_text_v13(): return None
def render_build_text_v12(): return None
def render_build_text_v11(): return None
def build_marker_v11(): return None
def build_marker_v10(): return None
def build_marker_v9(): return None
def build_marker_v8(): return None
def build_marker_v7(): return None
def render_version_tag(): return None


# --------------------------------------------------------------------
# v54: Nutritionist Read Archive Fix
# --------------------------------------------------------------------
APP_BUILD_VERSION = "v54"
APP_BUILD_LABEL = "Nutritionist Read Archive Fix"

def topbar(title, subtitle="", kicker="HealthyMe premium"):
    st.markdown(
        f"""
        <div class='hero-shell'>
          <div class='hm-v54-brand-row'>
            <span class='hm-v54-brand'>HealthyMe</span>
            <span class='hm-v54-version-inline'>{APP_BUILD_VERSION} · {APP_BUILD_LABEL}</span>
          </div>
          <div class='hero-kicker'>{kicker}</div>
          <div class='hero-title'>{title}</div>
          <div class='hero-subtitle'>{subtitle}</div>
          <div><span class='meta-pill'>Guided wellness workflow</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_build_text_v54(): return None
def render_build_text_v53(): return None
def render_build_text_v52(): return None
def render_build_text_v51(): return None
def render_build_text_v50(): return None
def render_build_text_v49(): return None
def render_build_text_v48(): return None
def render_build_text_v47(): return None
def render_build_text_v46(): return None
def render_build_text_v45(): return None
def render_build_text_v44(): return None
def render_build_text_v43(): return None
def render_build_text_v42(): return None
def render_build_text_v41(): return None
def render_build_text_v40(): return None
def render_build_text_v39(): return None
def render_build_text_v38(): return None
def render_build_text_v37(): return None
def render_build_text_v36(): return None
def render_build_text_v35(): return None
def render_build_text_v34(): return None
def render_build_text_v33(): return None
def render_build_text_v32(): return None
def render_build_text_v31(): return None
def render_build_text_v30(): return None
def render_build_text_v29(): return None
def render_build_text_v28(): return None
def render_build_text_v27(): return None
def render_build_text_v26(): return None
def render_build_text_v25(): return None
def render_build_text_v24(): return None
def render_build_text_v23(): return None
def render_build_text_v22(): return None
def render_build_text_v21(): return None
def render_build_text_v20(): return None
def render_build_text_v19(): return None
def render_build_text_v18(): return None
def render_build_text_v17(): return None
def render_build_text_v16(): return None
def render_build_text_v15(): return None
def render_build_text_v14(): return None
def render_build_text_v13(): return None
def render_build_text_v12(): return None
def render_build_text_v11(): return None
def build_marker_v11(): return None
def build_marker_v10(): return None
def build_marker_v9(): return None
def build_marker_v8(): return None
def build_marker_v7(): return None
def render_version_tag(): return None


# --------------------------------------------------------------------
# v55: Admin Dashboard Import Fix
# --------------------------------------------------------------------
APP_BUILD_VERSION = "v55"
APP_BUILD_LABEL = "Admin Dashboard Import Fix"

def topbar(title, subtitle="", kicker="HealthyMe premium"):
    st.markdown(
        f"""
        <div class='hero-shell'>
          <div class='hm-v55-brand-row'>
            <span class='hm-v55-brand'>HealthyMe</span>
            <span class='hm-v55-version-inline'>{APP_BUILD_VERSION} · {APP_BUILD_LABEL}</span>
          </div>
          <div class='hero-kicker'>{kicker}</div>
          <div class='hero-title'>{title}</div>
          <div class='hero-subtitle'>{subtitle}</div>
          <div><span class='meta-pill'>Guided wellness workflow</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_build_text_v55(): return None
def render_build_text_v54(): return None
def render_build_text_v53(): return None
def render_build_text_v52(): return None
def render_build_text_v51(): return None
def render_build_text_v50(): return None
def render_build_text_v49(): return None
def render_build_text_v48(): return None
def render_build_text_v47(): return None
def render_build_text_v46(): return None
def render_build_text_v45(): return None
def render_build_text_v44(): return None
def render_build_text_v43(): return None
def render_build_text_v42(): return None
def render_build_text_v41(): return None
def render_build_text_v40(): return None
def render_build_text_v39(): return None
def render_build_text_v38(): return None
def render_build_text_v37(): return None
def render_build_text_v36(): return None
def render_build_text_v35(): return None
def render_build_text_v34(): return None
def render_build_text_v33(): return None
def render_build_text_v32(): return None
def render_build_text_v31(): return None
def render_build_text_v30(): return None
def render_build_text_v29(): return None
def render_build_text_v28(): return None
def render_build_text_v27(): return None
def render_build_text_v26(): return None
def render_build_text_v25(): return None
def render_build_text_v24(): return None
def render_build_text_v23(): return None
def render_build_text_v22(): return None
def render_build_text_v21(): return None
def render_build_text_v20(): return None
def render_build_text_v19(): return None
def render_build_text_v18(): return None
def render_build_text_v17(): return None
def render_build_text_v16(): return None
def render_build_text_v15(): return None
def render_build_text_v14(): return None
def render_build_text_v13(): return None
def render_build_text_v12(): return None
def render_build_text_v11(): return None
def build_marker_v11(): return None
def build_marker_v10(): return None
def build_marker_v9(): return None
def build_marker_v8(): return None
def build_marker_v7(): return None
def render_version_tag(): return None


# --------------------------------------------------------------------
# v56: Daily Log Nutritionist Notification
# --------------------------------------------------------------------
APP_BUILD_VERSION = "v56"
APP_BUILD_LABEL = "Daily Log Nutritionist Notification"

def topbar(title, subtitle="", kicker="HealthyMe premium"):
    st.markdown(
        f"""
        <div class='hero-shell'>
          <div class='hm-v56-brand-row'>
            <span class='hm-v56-brand'>HealthyMe</span>
            <span class='hm-v56-version-inline'>{APP_BUILD_VERSION} · {APP_BUILD_LABEL}</span>
          </div>
          <div class='hero-kicker'>{kicker}</div>
          <div class='hero-title'>{title}</div>
          <div class='hero-subtitle'>{subtitle}</div>
          <div><span class='meta-pill'>Guided wellness workflow</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_build_text_v56(): return None
def render_build_text_v55(): return None
def render_build_text_v54(): return None
def render_build_text_v53(): return None
def render_build_text_v52(): return None
def render_build_text_v51(): return None
def render_build_text_v50(): return None
def render_build_text_v49(): return None
def render_build_text_v48(): return None
def render_build_text_v47(): return None
def render_build_text_v46(): return None
def render_build_text_v45(): return None
def render_build_text_v44(): return None
def render_build_text_v43(): return None
def render_build_text_v42(): return None
def render_build_text_v41(): return None
def render_build_text_v40(): return None
def render_build_text_v39(): return None
def render_build_text_v38(): return None
def render_build_text_v37(): return None
def render_build_text_v36(): return None
def render_build_text_v35(): return None
def render_build_text_v34(): return None
def render_build_text_v33(): return None
def render_build_text_v32(): return None
def render_build_text_v31(): return None
def render_build_text_v30(): return None
def render_build_text_v29(): return None
def render_build_text_v28(): return None
def render_build_text_v27(): return None
def render_build_text_v26(): return None
def render_build_text_v25(): return None
def render_build_text_v24(): return None
def render_build_text_v23(): return None
def render_build_text_v22(): return None
def render_build_text_v21(): return None
def render_build_text_v20(): return None
def render_build_text_v19(): return None
def render_build_text_v18(): return None
def render_build_text_v17(): return None
def render_build_text_v16(): return None
def render_build_text_v15(): return None
def render_build_text_v14(): return None
def render_build_text_v13(): return None
def render_build_text_v12(): return None
def render_build_text_v11(): return None
def build_marker_v11(): return None
def build_marker_v10(): return None
def build_marker_v9(): return None
def build_marker_v8(): return None
def build_marker_v7(): return None
def render_version_tag(): return None


# --------------------------------------------------------------------
# v57: Daily Log + LAF Restructure
# --------------------------------------------------------------------
APP_BUILD_VERSION = "v57"
APP_BUILD_LABEL = "Daily Log + LAF Restructure"

def topbar(title, subtitle="", kicker="HealthyMe premium"):
    st.markdown(
        f"""
        <div class='hero-shell'>
          <div class='hm-v57-brand-row'>
            <span class='hm-v57-brand'>HealthyMe</span>
            <span class='hm-v57-version-inline'>{APP_BUILD_VERSION} · {APP_BUILD_LABEL}</span>
          </div>
          <div class='hero-kicker'>{kicker}</div>
          <div class='hero-title'>{title}</div>
          <div class='hero-subtitle'>{subtitle}</div>
          <div><span class='meta-pill'>Guided wellness workflow</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_build_text_v57(): return None
def render_build_text_v56(): return None
def render_build_text_v55(): return None
def render_build_text_v54(): return None
def render_build_text_v53(): return None
def render_build_text_v52(): return None
def render_build_text_v51(): return None
def render_build_text_v50(): return None
def render_build_text_v49(): return None
def render_build_text_v48(): return None
def render_build_text_v47(): return None
def render_build_text_v46(): return None
def render_build_text_v45(): return None
def render_build_text_v44(): return None
def render_build_text_v43(): return None
def render_build_text_v42(): return None
def render_build_text_v41(): return None
def render_build_text_v40(): return None
def render_build_text_v39(): return None
def render_build_text_v38(): return None
def render_build_text_v37(): return None
def render_build_text_v36(): return None
def render_build_text_v35(): return None
def render_build_text_v34(): return None
def render_build_text_v33(): return None
def render_build_text_v32(): return None
def render_build_text_v31(): return None
def render_build_text_v30(): return None
def render_build_text_v29(): return None
def render_build_text_v28(): return None
def render_build_text_v27(): return None
def render_build_text_v26(): return None
def render_build_text_v25(): return None
def render_build_text_v24(): return None
def render_build_text_v23(): return None
def render_build_text_v22(): return None
def render_build_text_v21(): return None
def render_build_text_v20(): return None
def render_build_text_v19(): return None
def render_build_text_v18(): return None
def render_build_text_v17(): return None
def render_build_text_v16(): return None
def render_build_text_v15(): return None
def render_build_text_v14(): return None
def render_build_text_v13(): return None
def render_build_text_v12(): return None
def render_build_text_v11(): return None
def build_marker_v11(): return None
def build_marker_v10(): return None
def build_marker_v9(): return None
def build_marker_v8(): return None
def build_marker_v7(): return None
def render_version_tag(): return None


# --------------------------------------------------------------------
# v58: LAF Restructure Correction
# --------------------------------------------------------------------
APP_BUILD_VERSION = "v58"
APP_BUILD_LABEL = "LAF Restructure Correction"

def topbar(title, subtitle="", kicker="HealthyMe premium"):
    st.markdown(
        f"""
        <div class='hero-shell'>
          <div class='hm-v58-brand-row'>
            <span class='hm-v58-brand'>HealthyMe</span>
            <span class='hm-v58-version-inline'>{APP_BUILD_VERSION} · {APP_BUILD_LABEL}</span>
          </div>
          <div class='hero-kicker'>{kicker}</div>
          <div class='hero-title'>{title}</div>
          <div class='hero-subtitle'>{subtitle}</div>
          <div><span class='meta-pill'>Guided wellness workflow</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_build_text_v58(): return None
def render_build_text_v57(): return None
def render_build_text_v56(): return None
def render_build_text_v55(): return None
def render_build_text_v54(): return None
def render_build_text_v53(): return None
def render_build_text_v52(): return None
def render_build_text_v51(): return None
def render_build_text_v50(): return None
def render_build_text_v49(): return None
def render_build_text_v48(): return None
def render_build_text_v47(): return None
def render_build_text_v46(): return None
def render_build_text_v45(): return None
def render_build_text_v44(): return None
def render_build_text_v43(): return None
def render_build_text_v42(): return None
def render_build_text_v41(): return None
def render_build_text_v40(): return None
def render_build_text_v39(): return None
def render_build_text_v38(): return None
def render_build_text_v37(): return None
def render_build_text_v36(): return None
def render_build_text_v35(): return None
def render_build_text_v34(): return None
def render_build_text_v33(): return None
def render_build_text_v32(): return None
def render_build_text_v31(): return None
def render_build_text_v30(): return None
def render_build_text_v29(): return None
def render_build_text_v28(): return None
def render_build_text_v27(): return None
def render_build_text_v26(): return None
def render_build_text_v25(): return None
def render_build_text_v24(): return None
def render_build_text_v23(): return None
def render_build_text_v22(): return None
def render_build_text_v21(): return None
def render_build_text_v20(): return None
def render_build_text_v19(): return None
def render_build_text_v18(): return None
def render_build_text_v17(): return None
def render_build_text_v16(): return None
def render_build_text_v15(): return None
def render_build_text_v14(): return None
def render_build_text_v13(): return None
def render_build_text_v12(): return None
def render_build_text_v11(): return None
def build_marker_v11(): return None
def build_marker_v10(): return None
def build_marker_v9(): return None
def build_marker_v8(): return None
def build_marker_v7(): return None
def render_version_tag(): return None


# --------------------------------------------------------------------
# v59: Structured Poop Rounds
# --------------------------------------------------------------------
APP_BUILD_VERSION = "v59"
APP_BUILD_LABEL = "Structured Poop Rounds"

def topbar(title, subtitle="", kicker="HealthyMe premium"):
    st.markdown(
        f"""
        <div class='hero-shell'>
          <div class='hm-v59-brand-row'>
            <span class='hm-v59-brand'>HealthyMe</span>
            <span class='hm-v59-version-inline'>{APP_BUILD_VERSION} · {APP_BUILD_LABEL}</span>
          </div>
          <div class='hero-kicker'>{kicker}</div>
          <div class='hero-title'>{title}</div>
          <div class='hero-subtitle'>{subtitle}</div>
          <div><span class='meta-pill'>Guided wellness workflow</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_build_text_v59(): return None
def render_build_text_v58(): return None
def render_build_text_v57(): return None
def render_build_text_v56(): return None
def render_build_text_v55(): return None
def render_build_text_v54(): return None
def render_build_text_v53(): return None
def render_build_text_v52(): return None
def render_build_text_v51(): return None
def render_build_text_v50(): return None
def render_build_text_v49(): return None
def render_build_text_v48(): return None
def render_build_text_v47(): return None
def render_build_text_v46(): return None
def render_build_text_v45(): return None
def render_build_text_v44(): return None
def render_build_text_v43(): return None
def render_build_text_v42(): return None
def render_build_text_v41(): return None
def render_build_text_v40(): return None
def render_build_text_v39(): return None
def render_build_text_v38(): return None
def render_build_text_v37(): return None
def render_build_text_v36(): return None
def render_build_text_v35(): return None
def render_build_text_v34(): return None
def render_build_text_v33(): return None
def render_build_text_v32(): return None
def render_build_text_v31(): return None
def render_build_text_v30(): return None
def render_build_text_v29(): return None
def render_build_text_v28(): return None
def render_build_text_v27(): return None
def render_build_text_v26(): return None
def render_build_text_v25(): return None
def render_build_text_v24(): return None
def render_build_text_v23(): return None
def render_build_text_v22(): return None
def render_build_text_v21(): return None
def render_build_text_v20(): return None
def render_build_text_v19(): return None
def render_build_text_v18(): return None
def render_build_text_v17(): return None
def render_build_text_v16(): return None
def render_build_text_v15(): return None
def render_build_text_v14(): return None
def render_build_text_v13(): return None
def render_build_text_v12(): return None
def render_build_text_v11(): return None
def build_marker_v11(): return None
def build_marker_v10(): return None
def build_marker_v9(): return None
def build_marker_v8(): return None
def build_marker_v7(): return None
def render_version_tag(): return None


# --------------------------------------------------------------------
# v60: Poop Layout Refinement
# --------------------------------------------------------------------
APP_BUILD_VERSION = "v60"
APP_BUILD_LABEL = "Poop Layout Refinement"

def topbar(title, subtitle="", kicker="HealthyMe premium"):
    st.markdown(
        f"""
        <div class='hero-shell'>
          <div class='hm-v60-brand-row'>
            <span class='hm-v60-brand'>HealthyMe</span>
            <span class='hm-v60-version-inline'>{APP_BUILD_VERSION} · {APP_BUILD_LABEL}</span>
          </div>
          <div class='hero-kicker'>{kicker}</div>
          <div class='hero-title'>{title}</div>
          <div class='hero-subtitle'>{subtitle}</div>
          <div><span class='meta-pill'>Guided wellness workflow</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_build_text_v60(): return None
def render_build_text_v59(): return None
def render_build_text_v58(): return None
def render_build_text_v57(): return None
def render_build_text_v56(): return None
def render_build_text_v55(): return None
def render_build_text_v54(): return None
def render_build_text_v53(): return None
def render_build_text_v52(): return None
def render_build_text_v51(): return None
def render_build_text_v50(): return None
def render_build_text_v49(): return None
def render_build_text_v48(): return None
def render_build_text_v47(): return None
def render_build_text_v46(): return None
def render_build_text_v45(): return None
def render_build_text_v44(): return None
def render_build_text_v43(): return None
def render_build_text_v42(): return None
def render_build_text_v41(): return None
def render_build_text_v40(): return None
def render_build_text_v39(): return None
def render_build_text_v38(): return None
def render_build_text_v37(): return None
def render_build_text_v36(): return None
def render_build_text_v35(): return None
def render_build_text_v34(): return None
def render_build_text_v33(): return None
def render_build_text_v32(): return None
def render_build_text_v31(): return None
def render_build_text_v30(): return None
def render_build_text_v29(): return None
def render_build_text_v28(): return None
def render_build_text_v27(): return None
def render_build_text_v26(): return None
def render_build_text_v25(): return None
def render_build_text_v24(): return None
def render_build_text_v23(): return None
def render_build_text_v22(): return None
def render_build_text_v21(): return None
def render_build_text_v20(): return None
def render_build_text_v19(): return None
def render_build_text_v18(): return None
def render_build_text_v17(): return None
def render_build_text_v16(): return None
def render_build_text_v15(): return None
def render_build_text_v14(): return None
def render_build_text_v13(): return None
def render_build_text_v12(): return None
def render_build_text_v11(): return None
def build_marker_v11(): return None
def build_marker_v10(): return None
def build_marker_v9(): return None
def build_marker_v8(): return None
def build_marker_v7(): return None
def render_version_tag(): return None


# --------------------------------------------------------------------
# v61: Stability + Premium UX Cleanup
# --------------------------------------------------------------------
APP_BUILD_VERSION = "v61"
APP_BUILD_LABEL = "Stability + Premium UX Cleanup"

def topbar(title, subtitle="", kicker="HealthyMe premium"):
    st.markdown(
        f"""
        <div class='hero-shell'>
          <div class='hm-v61-brand-row'>
            <span class='hm-v61-brand'>HealthyMe</span>
            <span class='hm-v61-version-inline'>{APP_BUILD_VERSION} · {APP_BUILD_LABEL}</span>
          </div>
          <div class='hero-kicker'>{kicker}</div>
          <div class='hero-title'>{title}</div>
          <div class='hero-subtitle'>{subtitle}</div>
          <div><span class='meta-pill'>Guided wellness workflow</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def compact_topbar(title, subtitle="", kicker="HealthyMe"):
    """Compact header for internal working pages."""
    st.markdown(
        f"""
        <div class='hero-shell hm-compact-page-section'>
          <div class='hm-v61-brand-row'>
            <span class='hm-v61-brand'>HealthyMe</span>
            <span class='hm-v61-version-inline'>{APP_BUILD_VERSION} · {APP_BUILD_LABEL}</span>
          </div>
          <div class='hero-kicker'>{kicker}</div>
          <div class='hero-title'>{title}</div>
          {f"<div class='hero-subtitle'>{subtitle}</div>" if subtitle else ""}
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_build_text_v61(): return None
def render_build_text_v60(): return None
def render_build_text_v59(): return None
def render_build_text_v58(): return None
def render_build_text_v57(): return None
def render_build_text_v56(): return None
def render_build_text_v55(): return None
def render_build_text_v54(): return None
def render_build_text_v53(): return None
def render_build_text_v52(): return None
def render_build_text_v51(): return None
def render_build_text_v50(): return None
def render_build_text_v49(): return None
def render_build_text_v48(): return None
def render_build_text_v47(): return None
def render_build_text_v46(): return None
def render_build_text_v45(): return None
def render_build_text_v44(): return None
def render_build_text_v43(): return None
def render_build_text_v42(): return None
def render_build_text_v41(): return None
def render_build_text_v40(): return None
def render_build_text_v39(): return None
def render_build_text_v38(): return None
def render_build_text_v37(): return None
def render_build_text_v36(): return None
def render_build_text_v35(): return None
def render_build_text_v34(): return None
def render_build_text_v33(): return None
def render_build_text_v32(): return None
def render_build_text_v31(): return None
def render_build_text_v30(): return None
def render_build_text_v29(): return None
def render_build_text_v28(): return None
def render_build_text_v27(): return None
def render_build_text_v26(): return None
def render_build_text_v25(): return None
def render_build_text_v24(): return None
def render_build_text_v23(): return None
def render_build_text_v22(): return None
def render_build_text_v21(): return None
def render_build_text_v20(): return None
def render_build_text_v19(): return None
def render_build_text_v18(): return None
def render_build_text_v17(): return None
def render_build_text_v16(): return None
def render_build_text_v15(): return None
def render_build_text_v14(): return None
def render_build_text_v13(): return None
def render_build_text_v12(): return None
def render_build_text_v11(): return None
def build_marker_v11(): return None
def build_marker_v10(): return None
def build_marker_v9(): return None
def build_marker_v8(): return None
def build_marker_v7(): return None
def render_version_tag(): return None


# --------------------------------------------------------------------
# v62: Recent Saved Days Premium Layout
# --------------------------------------------------------------------
APP_BUILD_VERSION = "v62"
APP_BUILD_LABEL = "Recent Saved Days Premium Layout"

def topbar(title, subtitle="", kicker="HealthyMe premium"):
    st.markdown(
        f"""
        <div class='hero-shell'>
          <div class='hm-v62-brand-row'>
            <span class='hm-v62-brand'>HealthyMe</span>
            <span class='hm-v62-version-inline'>{APP_BUILD_VERSION} · {APP_BUILD_LABEL}</span>
          </div>
          <div class='hero-kicker'>{kicker}</div>
          <div class='hero-title'>{title}</div>
          <div class='hero-subtitle'>{subtitle}</div>
          <div><span class='meta-pill'>Guided wellness workflow</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def compact_topbar(title, subtitle="", kicker="HealthyMe"):
    st.markdown(
        f"""
        <div class='hero-shell hm-compact-page-section'>
          <div class='hm-v62-brand-row'>
            <span class='hm-v62-brand'>HealthyMe</span>
            <span class='hm-v62-version-inline'>{APP_BUILD_VERSION} · {APP_BUILD_LABEL}</span>
          </div>
          <div class='hero-kicker'>{kicker}</div>
          <div class='hero-title'>{title}</div>
          {f"<div class='hero-subtitle'>{subtitle}</div>" if subtitle else ""}
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_build_text_v62(): return None
def render_build_text_v61(): return None
def render_build_text_v60(): return None
def render_build_text_v59(): return None
def render_build_text_v58(): return None
def render_build_text_v57(): return None
def render_build_text_v56(): return None
def render_build_text_v55(): return None
def render_build_text_v54(): return None
def render_build_text_v53(): return None
def render_build_text_v52(): return None
def render_build_text_v51(): return None
def render_build_text_v50(): return None
def render_build_text_v49(): return None
def render_build_text_v48(): return None
def render_build_text_v47(): return None
def render_build_text_v46(): return None
def render_build_text_v45(): return None
def render_build_text_v44(): return None
def render_build_text_v43(): return None
def render_build_text_v42(): return None
def render_build_text_v41(): return None
def render_build_text_v40(): return None
def render_build_text_v39(): return None
def render_build_text_v38(): return None
def render_build_text_v37(): return None
def render_build_text_v36(): return None
def render_build_text_v35(): return None
def render_build_text_v34(): return None
def render_build_text_v33(): return None
def render_build_text_v32(): return None
def render_build_text_v31(): return None
def render_build_text_v30(): return None
def render_build_text_v29(): return None
def render_build_text_v28(): return None
def render_build_text_v27(): return None
def render_build_text_v26(): return None
def render_build_text_v25(): return None
def render_build_text_v24(): return None
def render_build_text_v23(): return None
def render_build_text_v22(): return None
def render_build_text_v21(): return None
def render_build_text_v20(): return None
def render_build_text_v19(): return None
def render_build_text_v18(): return None
def render_build_text_v17(): return None
def render_build_text_v16(): return None
def render_build_text_v15(): return None
def render_build_text_v14(): return None
def render_build_text_v13(): return None
def render_build_text_v12(): return None
def render_build_text_v11(): return None
def build_marker_v11(): return None
def build_marker_v10(): return None
def build_marker_v9(): return None
def build_marker_v8(): return None
def build_marker_v7(): return None
def render_version_tag(): return None


# --------------------------------------------------------------------
# v63: Recent Saved Days Borders + Toggle
# --------------------------------------------------------------------
APP_BUILD_VERSION = "v63"
APP_BUILD_LABEL = "Recent Saved Days Borders + Toggle"

def topbar(title, subtitle="", kicker="HealthyMe premium"):
    st.markdown(
        f"""
        <div class='hero-shell'>
          <div class='hm-v63-brand-row'>
            <span class='hm-v63-brand'>HealthyMe</span>
            <span class='hm-v63-version-inline'>{APP_BUILD_VERSION} · {APP_BUILD_LABEL}</span>
          </div>
          <div class='hero-kicker'>{kicker}</div>
          <div class='hero-title'>{title}</div>
          <div class='hero-subtitle'>{subtitle}</div>
          <div><span class='meta-pill'>Guided wellness workflow</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def compact_topbar(title, subtitle="", kicker="HealthyMe"):
    st.markdown(
        f"""
        <div class='hero-shell hm-compact-page-section'>
          <div class='hm-v63-brand-row'>
            <span class='hm-v63-brand'>HealthyMe</span>
            <span class='hm-v63-version-inline'>{APP_BUILD_VERSION} · {APP_BUILD_LABEL}</span>
          </div>
          <div class='hero-kicker'>{kicker}</div>
          <div class='hero-title'>{title}</div>
          {f"<div class='hero-subtitle'>{subtitle}</div>" if subtitle else ""}
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_build_text_v63(): return None
def render_build_text_v62(): return None
def render_build_text_v61(): return None
def render_build_text_v60(): return None
def render_build_text_v59(): return None
def render_build_text_v58(): return None
def render_build_text_v57(): return None
def render_build_text_v56(): return None
def render_build_text_v55(): return None
def render_build_text_v54(): return None
def render_build_text_v53(): return None
def render_build_text_v52(): return None
def render_build_text_v51(): return None
def render_build_text_v50(): return None
def render_build_text_v49(): return None
def render_build_text_v48(): return None
def render_build_text_v47(): return None
def render_build_text_v46(): return None
def render_build_text_v45(): return None
def render_build_text_v44(): return None
def render_build_text_v43(): return None
def render_build_text_v42(): return None
def render_build_text_v41(): return None
def render_build_text_v40(): return None
def render_build_text_v39(): return None
def render_build_text_v38(): return None
def render_build_text_v37(): return None
def render_build_text_v36(): return None
def render_build_text_v35(): return None
def render_build_text_v34(): return None
def render_build_text_v33(): return None
def render_build_text_v32(): return None
def render_build_text_v31(): return None
def render_build_text_v30(): return None
def render_build_text_v29(): return None
def render_build_text_v28(): return None
def render_build_text_v27(): return None
def render_build_text_v26(): return None
def render_build_text_v25(): return None
def render_build_text_v24(): return None
def render_build_text_v23(): return None
def render_build_text_v22(): return None
def render_build_text_v21(): return None
def render_build_text_v20(): return None
def render_build_text_v19(): return None
def render_build_text_v18(): return None
def render_build_text_v17(): return None
def render_build_text_v16(): return None
def render_build_text_v15(): return None
def render_build_text_v14(): return None
def render_build_text_v13(): return None
def render_build_text_v12(): return None
def render_build_text_v11(): return None
def build_marker_v11(): return None
def build_marker_v10(): return None
def build_marker_v9(): return None
def build_marker_v8(): return None
def build_marker_v7(): return None
def render_version_tag(): return None


# --------------------------------------------------------------------
# v64: Recent Saved Days Refinement
# --------------------------------------------------------------------
APP_BUILD_VERSION = "v64"
APP_BUILD_LABEL = "Recent Saved Days Refinement"

def topbar(title, subtitle="", kicker="HealthyMe premium"):
    st.markdown(
        f"""
        <div class='hero-shell'>
          <div class='hm-v64-brand-row'>
            <span class='hm-v64-brand'>HealthyMe</span>
            <span class='hm-v64-version-inline'>{APP_BUILD_VERSION} · {APP_BUILD_LABEL}</span>
          </div>
          <div class='hero-kicker'>{kicker}</div>
          <div class='hero-title'>{title}</div>
          <div class='hero-subtitle'>{subtitle}</div>
          <div><span class='meta-pill'>Guided wellness workflow</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def compact_topbar(title, subtitle="", kicker="HealthyMe"):
    st.markdown(
        f"""
        <div class='hero-shell hm-compact-page-section'>
          <div class='hm-v64-brand-row'>
            <span class='hm-v64-brand'>HealthyMe</span>
            <span class='hm-v64-version-inline'>{APP_BUILD_VERSION} · {APP_BUILD_LABEL}</span>
          </div>
          <div class='hero-kicker'>{kicker}</div>
          <div class='hero-title'>{title}</div>
          {f"<div class='hero-subtitle'>{subtitle}</div>" if subtitle else ""}
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_build_text_v64(): return None
def render_build_text_v63(): return None
def render_build_text_v62(): return None
def render_build_text_v61(): return None
def render_build_text_v60(): return None
def render_build_text_v59(): return None
def render_build_text_v58(): return None
def render_build_text_v57(): return None
def render_build_text_v56(): return None
def render_build_text_v55(): return None
def render_build_text_v54(): return None
def render_build_text_v53(): return None
def render_build_text_v52(): return None
def render_build_text_v51(): return None
def render_build_text_v50(): return None
def render_build_text_v49(): return None
def render_build_text_v48(): return None
def render_build_text_v47(): return None
def render_build_text_v46(): return None
def render_build_text_v45(): return None
def render_build_text_v44(): return None
def render_build_text_v43(): return None
def render_build_text_v42(): return None
def render_build_text_v41(): return None
def render_build_text_v40(): return None
def render_build_text_v39(): return None
def render_build_text_v38(): return None
def render_build_text_v37(): return None
def render_build_text_v36(): return None
def render_build_text_v35(): return None
def render_build_text_v34(): return None
def render_build_text_v33(): return None
def render_build_text_v32(): return None
def render_build_text_v31(): return None
def render_build_text_v30(): return None
def render_build_text_v29(): return None
def render_build_text_v28(): return None
def render_build_text_v27(): return None
def render_build_text_v26(): return None
def render_build_text_v25(): return None
def render_build_text_v24(): return None
def render_build_text_v23(): return None
def render_build_text_v22(): return None
def render_build_text_v21(): return None
def render_build_text_v20(): return None
def render_build_text_v19(): return None
def render_build_text_v18(): return None
def render_build_text_v17(): return None
def render_build_text_v16(): return None
def render_build_text_v15(): return None
def render_build_text_v14(): return None
def render_build_text_v13(): return None
def render_build_text_v12(): return None
def render_build_text_v11(): return None
def build_marker_v11(): return None
def build_marker_v10(): return None
def build_marker_v9(): return None
def build_marker_v8(): return None
def build_marker_v7(): return None
def render_version_tag(): return None


# --------------------------------------------------------------------
# v65: Daily Log + Admin UI Fixes
# --------------------------------------------------------------------
APP_BUILD_VERSION = "v65"
APP_BUILD_LABEL = "Daily Log + Admin UI Fixes"

def topbar(title, subtitle="", kicker="HealthyMe premium"):
    st.markdown(
        f"""
        <div class='hero-shell'>
          <div class='hm-v65-brand-row'>
            <span class='hm-v65-brand'>HealthyMe</span>
            <span class='hm-v65-version-inline'>{APP_BUILD_VERSION} · {APP_BUILD_LABEL}</span>
          </div>
          <div class='hero-kicker'>{kicker}</div>
          <div class='hero-title'>{title}</div>
          <div class='hero-subtitle'>{subtitle}</div>
          <div><span class='meta-pill'>Guided wellness workflow</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def compact_topbar(title, subtitle="", kicker="HealthyMe"):
    st.markdown(
        f"""
        <div class='hero-shell hm-compact-page-section'>
          <div class='hm-v65-brand-row'>
            <span class='hm-v65-brand'>HealthyMe</span>
            <span class='hm-v65-version-inline'>{APP_BUILD_VERSION} · {APP_BUILD_LABEL}</span>
          </div>
          <div class='hero-kicker'>{kicker}</div>
          <div class='hero-title'>{title}</div>
          {f"<div class='hero-subtitle'>{subtitle}</div>" if subtitle else ""}
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_build_text_v65(): return None
def render_build_text_v64(): return None
def render_build_text_v63(): return None
def render_build_text_v62(): return None
def render_build_text_v61(): return None
def render_build_text_v60(): return None
def render_build_text_v59(): return None
def render_build_text_v58(): return None
def render_build_text_v57(): return None
def render_build_text_v56(): return None
def render_build_text_v55(): return None
def render_build_text_v54(): return None
def render_build_text_v53(): return None
def render_build_text_v52(): return None
def render_build_text_v51(): return None
def render_build_text_v50(): return None
def render_build_text_v49(): return None
def render_build_text_v48(): return None
def render_build_text_v47(): return None
def render_build_text_v46(): return None
def render_build_text_v45(): return None
def render_build_text_v44(): return None
def render_build_text_v43(): return None
def render_build_text_v42(): return None
def render_build_text_v41(): return None
def render_build_text_v40(): return None
def render_build_text_v39(): return None
def render_build_text_v38(): return None
def render_build_text_v37(): return None
def render_build_text_v36(): return None
def render_build_text_v35(): return None
def render_build_text_v34(): return None
def render_build_text_v33(): return None
def render_build_text_v32(): return None
def render_build_text_v31(): return None
def render_build_text_v30(): return None
def render_build_text_v29(): return None
def render_build_text_v28(): return None
def render_build_text_v27(): return None
def render_build_text_v26(): return None
def render_build_text_v25(): return None
def render_build_text_v24(): return None
def render_build_text_v23(): return None
def render_build_text_v22(): return None
def render_build_text_v21(): return None
def render_build_text_v20(): return None
def render_build_text_v19(): return None
def render_build_text_v18(): return None
def render_build_text_v17(): return None
def render_build_text_v16(): return None
def render_build_text_v15(): return None
def render_build_text_v14(): return None
def render_build_text_v13(): return None
def render_build_text_v12(): return None
def render_build_text_v11(): return None
def build_marker_v11(): return None
def build_marker_v10(): return None
def build_marker_v9(): return None
def build_marker_v8(): return None
def build_marker_v7(): return None
def render_version_tag(): return None


# --------------------------------------------------------------------
# v66: Nutritionist Message Dedupe
# --------------------------------------------------------------------
APP_BUILD_VERSION = "v66"
APP_BUILD_LABEL = "Nutritionist Message Dedupe"

def topbar(title, subtitle="", kicker="HealthyMe premium"):
    st.markdown(
        f"""
        <div class='hero-shell'>
          <div class='hm-v66-brand-row'>
            <span class='hm-v66-brand'>HealthyMe</span>
            <span class='hm-v66-version-inline'>{APP_BUILD_VERSION} · {APP_BUILD_LABEL}</span>
          </div>
          <div class='hero-kicker'>{kicker}</div>
          <div class='hero-title'>{title}</div>
          <div class='hero-subtitle'>{subtitle}</div>
          <div><span class='meta-pill'>Guided wellness workflow</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def compact_topbar(title, subtitle="", kicker="HealthyMe"):
    st.markdown(
        f"""
        <div class='hero-shell hm-compact-page-section'>
          <div class='hm-v66-brand-row'>
            <span class='hm-v66-brand'>HealthyMe</span>
            <span class='hm-v66-version-inline'>{APP_BUILD_VERSION} · {APP_BUILD_LABEL}</span>
          </div>
          <div class='hero-kicker'>{kicker}</div>
          <div class='hero-title'>{title}</div>
          {f"<div class='hero-subtitle'>{subtitle}</div>" if subtitle else ""}
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_build_text_v66(): return None
def render_build_text_v65(): return None
def render_build_text_v64(): return None
def render_build_text_v63(): return None
def render_build_text_v62(): return None
def render_build_text_v61(): return None
def render_build_text_v60(): return None
def render_build_text_v59(): return None
def render_build_text_v58(): return None
def render_build_text_v57(): return None
def render_build_text_v56(): return None
def render_build_text_v55(): return None
def render_build_text_v54(): return None
def render_build_text_v53(): return None
def render_build_text_v52(): return None
def render_build_text_v51(): return None
def render_build_text_v50(): return None
def render_build_text_v49(): return None
def render_build_text_v48(): return None
def render_build_text_v47(): return None
def render_build_text_v46(): return None
def render_build_text_v45(): return None
def render_build_text_v44(): return None
def render_build_text_v43(): return None
def render_build_text_v42(): return None
def render_build_text_v41(): return None
def render_build_text_v40(): return None
def render_build_text_v39(): return None
def render_build_text_v38(): return None
def render_build_text_v37(): return None
def render_build_text_v36(): return None
def render_build_text_v35(): return None
def render_build_text_v34(): return None
def render_build_text_v33(): return None
def render_build_text_v32(): return None
def render_build_text_v31(): return None
def render_build_text_v30(): return None
def render_build_text_v29(): return None
def render_build_text_v28(): return None
def render_build_text_v27(): return None
def render_build_text_v26(): return None
def render_build_text_v25(): return None
def render_build_text_v24(): return None
def render_build_text_v23(): return None
def render_build_text_v22(): return None
def render_build_text_v21(): return None
def render_build_text_v20(): return None
def render_build_text_v19(): return None
def render_build_text_v18(): return None
def render_build_text_v17(): return None
def render_build_text_v16(): return None
def render_build_text_v15(): return None
def render_build_text_v14(): return None
def render_build_text_v13(): return None
def render_build_text_v12(): return None
def render_build_text_v11(): return None
def build_marker_v11(): return None
def build_marker_v10(): return None
def build_marker_v9(): return None
def build_marker_v8(): return None
def build_marker_v7(): return None
def render_version_tag(): return None


# --------------------------------------------------------------------
# v67: View History Alignment Fix
# --------------------------------------------------------------------
APP_BUILD_VERSION = "v67"
APP_BUILD_LABEL = "View History Alignment Fix"

def topbar(title, subtitle="", kicker="HealthyMe premium"):
    st.markdown(
        f"""
        <div class='hero-shell'>
          <div class='hm-v67-brand-row'>
            <span class='hm-v67-brand'>HealthyMe</span>
            <span class='hm-v67-version-inline'>{APP_BUILD_VERSION} · {APP_BUILD_LABEL}</span>
          </div>
          <div class='hero-kicker'>{kicker}</div>
          <div class='hero-title'>{title}</div>
          <div class='hero-subtitle'>{subtitle}</div>
          <div><span class='meta-pill'>Guided wellness workflow</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def compact_topbar(title, subtitle="", kicker="HealthyMe"):
    st.markdown(
        f"""
        <div class='hero-shell hm-compact-page-section'>
          <div class='hm-v67-brand-row'>
            <span class='hm-v67-brand'>HealthyMe</span>
            <span class='hm-v67-version-inline'>{APP_BUILD_VERSION} · {APP_BUILD_LABEL}</span>
          </div>
          <div class='hero-kicker'>{kicker}</div>
          <div class='hero-title'>{title}</div>
          {f"<div class='hero-subtitle'>{subtitle}</div>" if subtitle else ""}
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_build_text_v67(): return None
def render_build_text_v66(): return None
def render_build_text_v65(): return None
def render_build_text_v64(): return None
def render_build_text_v63(): return None
def render_build_text_v62(): return None
def render_build_text_v61(): return None
def render_build_text_v60(): return None
def render_build_text_v59(): return None
def render_build_text_v58(): return None
def render_build_text_v57(): return None
def render_build_text_v56(): return None
def render_build_text_v55(): return None
def render_build_text_v54(): return None
def render_build_text_v53(): return None
def render_build_text_v52(): return None
def render_build_text_v51(): return None
def render_build_text_v50(): return None
def render_build_text_v49(): return None
def render_build_text_v48(): return None
def render_build_text_v47(): return None
def render_build_text_v46(): return None
def render_build_text_v45(): return None
def render_build_text_v44(): return None
def render_build_text_v43(): return None
def render_build_text_v42(): return None
def render_build_text_v41(): return None
def render_build_text_v40(): return None
def render_build_text_v39(): return None
def render_build_text_v38(): return None
def render_build_text_v37(): return None
def render_build_text_v36(): return None
def render_build_text_v35(): return None
def render_build_text_v34(): return None
def render_build_text_v33(): return None
def render_build_text_v32(): return None
def render_build_text_v31(): return None
def render_build_text_v30(): return None
def render_build_text_v29(): return None
def render_build_text_v28(): return None
def render_build_text_v27(): return None
def render_build_text_v26(): return None
def render_build_text_v25(): return None
def render_build_text_v24(): return None
def render_build_text_v23(): return None
def render_build_text_v22(): return None
def render_build_text_v21(): return None
def render_build_text_v20(): return None
def render_build_text_v19(): return None
def render_build_text_v18(): return None
def render_build_text_v17(): return None
def render_build_text_v16(): return None
def render_build_text_v15(): return None
def render_build_text_v14(): return None
def render_build_text_v13(): return None
def render_build_text_v12(): return None
def render_build_text_v11(): return None
def build_marker_v11(): return None
def build_marker_v10(): return None
def build_marker_v9(): return None
def build_marker_v8(): return None
def build_marker_v7(): return None
def render_version_tag(): return None


# --------------------------------------------------------------------
# v68: View History Micro Alignment
# --------------------------------------------------------------------
APP_BUILD_VERSION = "v68"
APP_BUILD_LABEL = "View History Micro Alignment"

def topbar(title, subtitle="", kicker="HealthyMe premium"):
    st.markdown(
        f"""
        <div class='hero-shell'>
          <div class='hm-v68-brand-row'>
            <span class='hm-v68-brand'>HealthyMe</span>
            <span class='hm-v68-version-inline'>{APP_BUILD_VERSION} · {APP_BUILD_LABEL}</span>
          </div>
          <div class='hero-kicker'>{kicker}</div>
          <div class='hero-title'>{title}</div>
          <div class='hero-subtitle'>{subtitle}</div>
          <div><span class='meta-pill'>Guided wellness workflow</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def compact_topbar(title, subtitle="", kicker="HealthyMe"):
    st.markdown(
        f"""
        <div class='hero-shell hm-compact-page-section'>
          <div class='hm-v68-brand-row'>
            <span class='hm-v68-brand'>HealthyMe</span>
            <span class='hm-v68-version-inline'>{APP_BUILD_VERSION} · {APP_BUILD_LABEL}</span>
          </div>
          <div class='hero-kicker'>{kicker}</div>
          <div class='hero-title'>{title}</div>
          {f"<div class='hero-subtitle'>{subtitle}</div>" if subtitle else ""}
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_build_text_v68(): return None
def render_build_text_v67(): return None
def render_build_text_v66(): return None
def render_build_text_v65(): return None
def render_build_text_v64(): return None
def render_build_text_v63(): return None
def render_build_text_v62(): return None
def render_build_text_v61(): return None
def render_build_text_v60(): return None
def render_build_text_v59(): return None
def render_build_text_v58(): return None
def render_build_text_v57(): return None
def render_build_text_v56(): return None
def render_build_text_v55(): return None
def render_build_text_v54(): return None
def render_build_text_v53(): return None
def render_build_text_v52(): return None
def render_build_text_v51(): return None
def render_build_text_v50(): return None
def render_build_text_v49(): return None
def render_build_text_v48(): return None
def render_build_text_v47(): return None
def render_build_text_v46(): return None
def render_build_text_v45(): return None
def render_build_text_v44(): return None
def render_build_text_v43(): return None
def render_build_text_v42(): return None
def render_build_text_v41(): return None
def render_build_text_v40(): return None
def render_build_text_v39(): return None
def render_build_text_v38(): return None
def render_build_text_v37(): return None
def render_build_text_v36(): return None
def render_build_text_v35(): return None
def render_build_text_v34(): return None
def render_build_text_v33(): return None
def render_build_text_v32(): return None
def render_build_text_v31(): return None
def render_build_text_v30(): return None
def render_build_text_v29(): return None
def render_build_text_v28(): return None
def render_build_text_v27(): return None
def render_build_text_v26(): return None
def render_build_text_v25(): return None
def render_build_text_v24(): return None
def render_build_text_v23(): return None
def render_build_text_v22(): return None
def render_build_text_v21(): return None
def render_build_text_v20(): return None
def render_build_text_v19(): return None
def render_build_text_v18(): return None
def render_build_text_v17(): return None
def render_build_text_v16(): return None
def render_build_text_v15(): return None
def render_build_text_v14(): return None
def render_build_text_v13(): return None
def render_build_text_v12(): return None
def render_build_text_v11(): return None
def build_marker_v11(): return None
def build_marker_v10(): return None
def build_marker_v9(): return None
def build_marker_v8(): return None
def build_marker_v7(): return None
def render_version_tag(): return None


# --------------------------------------------------------------------
# v69: Inline History Button Alignment
# --------------------------------------------------------------------
APP_BUILD_VERSION = "v69"
APP_BUILD_LABEL = "Inline History Button Alignment"

def topbar(title, subtitle="", kicker="HealthyMe premium"):
    st.markdown(
        f"""
        <div class='hero-shell'>
          <div class='hm-v69-brand-row'>
            <span class='hm-v69-brand'>HealthyMe</span>
            <span class='hm-v69-version-inline'>{APP_BUILD_VERSION} · {APP_BUILD_LABEL}</span>
          </div>
          <div class='hero-kicker'>{kicker}</div>
          <div class='hero-title'>{title}</div>
          <div class='hero-subtitle'>{subtitle}</div>
          <div><span class='meta-pill'>Guided wellness workflow</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def compact_topbar(title, subtitle="", kicker="HealthyMe"):
    st.markdown(
        f"""
        <div class='hero-shell hm-compact-page-section'>
          <div class='hm-v69-brand-row'>
            <span class='hm-v69-brand'>HealthyMe</span>
            <span class='hm-v69-version-inline'>{APP_BUILD_VERSION} · {APP_BUILD_LABEL}</span>
          </div>
          <div class='hero-kicker'>{kicker}</div>
          <div class='hero-title'>{title}</div>
          {f"<div class='hero-subtitle'>{subtitle}</div>" if subtitle else ""}
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_build_text_v69(): return None
def render_build_text_v68(): return None
def render_build_text_v67(): return None
def render_build_text_v66(): return None
def render_build_text_v65(): return None
def render_build_text_v64(): return None
def render_build_text_v63(): return None
def render_build_text_v62(): return None
def render_build_text_v61(): return None
def render_build_text_v60(): return None
def render_build_text_v59(): return None
def render_build_text_v58(): return None
def render_build_text_v57(): return None
def render_build_text_v56(): return None
def render_build_text_v55(): return None
def render_build_text_v54(): return None
def render_build_text_v53(): return None
def render_build_text_v52(): return None
def render_build_text_v51(): return None
def render_build_text_v50(): return None
def render_build_text_v49(): return None
def render_build_text_v48(): return None
def render_build_text_v47(): return None
def render_build_text_v46(): return None
def render_build_text_v45(): return None
def render_build_text_v44(): return None
def render_build_text_v43(): return None
def render_build_text_v42(): return None
def render_build_text_v41(): return None
def render_build_text_v40(): return None
def render_build_text_v39(): return None
def render_build_text_v38(): return None
def render_build_text_v37(): return None
def render_build_text_v36(): return None
def render_build_text_v35(): return None
def render_build_text_v34(): return None
def render_build_text_v33(): return None
def render_build_text_v32(): return None
def render_build_text_v31(): return None
def render_build_text_v30(): return None
def render_build_text_v29(): return None
def render_build_text_v28(): return None
def render_build_text_v27(): return None
def render_build_text_v26(): return None
def render_build_text_v25(): return None
def render_build_text_v24(): return None
def render_build_text_v23(): return None
def render_build_text_v22(): return None
def render_build_text_v21(): return None
def render_build_text_v20(): return None
def render_build_text_v19(): return None
def render_build_text_v18(): return None
def render_build_text_v17(): return None
def render_build_text_v16(): return None
def render_build_text_v15(): return None
def render_build_text_v14(): return None
def render_build_text_v13(): return None
def render_build_text_v12(): return None
def render_build_text_v11(): return None
def build_marker_v11(): return None
def build_marker_v10(): return None
def build_marker_v9(): return None
def build_marker_v8(): return None
def build_marker_v7(): return None
def render_version_tag(): return None


# --------------------------------------------------------------------
# v70: Streamlit Native Recent Saved Days
# --------------------------------------------------------------------
APP_BUILD_VERSION = "v70"
APP_BUILD_LABEL = "Streamlit Native Recent Saved Days"

def topbar(title, subtitle="", kicker="HealthyMe premium"):
    st.markdown(
        f"""
        <div class='hero-shell'>
          <div class='hm-v70-brand-row'>
            <span class='hm-v70-brand'>HealthyMe</span>
            <span class='hm-v70-version-inline'>{APP_BUILD_VERSION} · {APP_BUILD_LABEL}</span>
          </div>
          <div class='hero-kicker'>{kicker}</div>
          <div class='hero-title'>{title}</div>
          <div class='hero-subtitle'>{subtitle}</div>
          <div><span class='meta-pill'>Guided wellness workflow</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def compact_topbar(title, subtitle="", kicker="HealthyMe"):
    st.markdown(
        f"""
        <div class='hero-shell hm-compact-page-section'>
          <div class='hm-v70-brand-row'>
            <span class='hm-v70-brand'>HealthyMe</span>
            <span class='hm-v70-version-inline'>{APP_BUILD_VERSION} · {APP_BUILD_LABEL}</span>
          </div>
          <div class='hero-kicker'>{kicker}</div>
          <div class='hero-title'>{title}</div>
          {f"<div class='hero-subtitle'>{subtitle}</div>" if subtitle else ""}
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_build_text_v70(): return None
def render_build_text_v69(): return None
def render_build_text_v68(): return None
def render_build_text_v67(): return None
def render_build_text_v66(): return None
def render_build_text_v65(): return None
def render_build_text_v64(): return None
def render_build_text_v63(): return None
def render_build_text_v62(): return None
def render_build_text_v61(): return None
def render_build_text_v60(): return None
def render_build_text_v59(): return None
def render_build_text_v58(): return None
def render_build_text_v57(): return None
def render_build_text_v56(): return None
def render_build_text_v55(): return None
def render_build_text_v54(): return None
def render_build_text_v53(): return None
def render_build_text_v52(): return None
def render_build_text_v51(): return None
def render_build_text_v50(): return None
def render_build_text_v49(): return None
def render_build_text_v48(): return None
def render_build_text_v47(): return None
def render_build_text_v46(): return None
def render_build_text_v45(): return None
def render_build_text_v44(): return None
def render_build_text_v43(): return None
def render_build_text_v42(): return None
def render_build_text_v41(): return None
def render_build_text_v40(): return None
def render_build_text_v39(): return None
def render_build_text_v38(): return None
def render_build_text_v37(): return None
def render_build_text_v36(): return None
def render_build_text_v35(): return None
def render_build_text_v34(): return None
def render_build_text_v33(): return None
def render_build_text_v32(): return None
def render_build_text_v31(): return None
def render_build_text_v30(): return None
def render_build_text_v29(): return None
def render_build_text_v28(): return None
def render_build_text_v27(): return None
def render_build_text_v26(): return None
def render_build_text_v25(): return None
def render_build_text_v24(): return None
def render_build_text_v23(): return None
def render_build_text_v22(): return None
def render_build_text_v21(): return None
def render_build_text_v20(): return None
def render_build_text_v19(): return None
def render_build_text_v18(): return None
def render_build_text_v17(): return None
def render_build_text_v16(): return None
def render_build_text_v15(): return None
def render_build_text_v14(): return None
def render_build_text_v13(): return None
def render_build_text_v12(): return None
def render_build_text_v11(): return None
def build_marker_v11(): return None
def build_marker_v10(): return None
def build_marker_v9(): return None
def build_marker_v8(): return None
def build_marker_v7(): return None
def render_version_tag(): return None


# --------------------------------------------------------------------
# v71: Compact Nutritionist History Block
# --------------------------------------------------------------------
APP_BUILD_VERSION = "v71"
APP_BUILD_LABEL = "Compact Nutritionist History Block"

def topbar(title, subtitle="", kicker="HealthyMe premium"):
    st.markdown(
        f"""
        <div class='hero-shell'>
          <div class='hm-v71-brand-row'>
            <span class='hm-v71-brand'>HealthyMe</span>
            <span class='hm-v71-version-inline'>{APP_BUILD_VERSION} · {APP_BUILD_LABEL}</span>
          </div>
          <div class='hero-kicker'>{kicker}</div>
          <div class='hero-title'>{title}</div>
          <div class='hero-subtitle'>{subtitle}</div>
          <div><span class='meta-pill'>Guided wellness workflow</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def compact_topbar(title, subtitle="", kicker="HealthyMe"):
    st.markdown(
        f"""
        <div class='hero-shell hm-compact-page-section'>
          <div class='hm-v71-brand-row'>
            <span class='hm-v71-brand'>HealthyMe</span>
            <span class='hm-v71-version-inline'>{APP_BUILD_VERSION} · {APP_BUILD_LABEL}</span>
          </div>
          <div class='hero-kicker'>{kicker}</div>
          <div class='hero-title'>{title}</div>
          {f"<div class='hero-subtitle'>{subtitle}</div>" if subtitle else ""}
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_build_text_v71(): return None
def render_build_text_v70(): return None
def render_build_text_v69(): return None
def render_build_text_v68(): return None
def render_build_text_v67(): return None
def render_build_text_v66(): return None
def render_build_text_v65(): return None
def render_build_text_v64(): return None
def render_build_text_v63(): return None
def render_build_text_v62(): return None
def render_build_text_v61(): return None
def render_build_text_v60(): return None
def render_build_text_v59(): return None
def render_build_text_v58(): return None
def render_build_text_v57(): return None
def render_build_text_v56(): return None
def render_build_text_v55(): return None
def render_build_text_v54(): return None
def render_build_text_v53(): return None
def render_build_text_v52(): return None
def render_build_text_v51(): return None
def render_build_text_v50(): return None
def render_build_text_v49(): return None
def render_build_text_v48(): return None
def render_build_text_v47(): return None
def render_build_text_v46(): return None
def render_build_text_v45(): return None
def render_build_text_v44(): return None
def render_build_text_v43(): return None
def render_build_text_v42(): return None
def render_build_text_v41(): return None
def render_build_text_v40(): return None
def render_build_text_v39(): return None
def render_build_text_v38(): return None
def render_build_text_v37(): return None
def render_build_text_v36(): return None
def render_build_text_v35(): return None
def render_build_text_v34(): return None
def render_build_text_v33(): return None
def render_build_text_v32(): return None
def render_build_text_v31(): return None
def render_build_text_v30(): return None
def render_build_text_v29(): return None
def render_build_text_v28(): return None
def render_build_text_v27(): return None
def render_build_text_v26(): return None
def render_build_text_v25(): return None
def render_build_text_v24(): return None
def render_build_text_v23(): return None
def render_build_text_v22(): return None
def render_build_text_v21(): return None
def render_build_text_v20(): return None
def render_build_text_v19(): return None
def render_build_text_v18(): return None
def render_build_text_v17(): return None
def render_build_text_v16(): return None
def render_build_text_v15(): return None
def render_build_text_v14(): return None
def render_build_text_v13(): return None
def render_build_text_v12(): return None
def render_build_text_v11(): return None
def build_marker_v11(): return None
def build_marker_v10(): return None
def build_marker_v9(): return None
def build_marker_v8(): return None
def build_marker_v7(): return None
def render_version_tag(): return None


# --------------------------------------------------------------------
# v72: Final Report Import Fix
# --------------------------------------------------------------------
APP_BUILD_VERSION = "v72"
APP_BUILD_LABEL = "Final Report Import Fix"

def topbar(title, subtitle="", kicker="HealthyMe premium"):
    st.markdown(
        f"""
        <div class='hero-shell'>
          <div class='hm-v72-brand-row'>
            <span class='hm-v72-brand'>HealthyMe</span>
            <span class='hm-v72-version-inline'>{APP_BUILD_VERSION} · {APP_BUILD_LABEL}</span>
          </div>
          <div class='hero-kicker'>{kicker}</div>
          <div class='hero-title'>{title}</div>
          <div class='hero-subtitle'>{subtitle}</div>
          <div><span class='meta-pill'>Guided wellness workflow</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def compact_topbar(title, subtitle="", kicker="HealthyMe"):
    st.markdown(
        f"""
        <div class='hero-shell hm-compact-page-section'>
          <div class='hm-v72-brand-row'>
            <span class='hm-v72-brand'>HealthyMe</span>
            <span class='hm-v72-version-inline'>{APP_BUILD_VERSION} · {APP_BUILD_LABEL}</span>
          </div>
          <div class='hero-kicker'>{kicker}</div>
          <div class='hero-title'>{title}</div>
          {f"<div class='hero-subtitle'>{subtitle}</div>" if subtitle else ""}
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_build_text_v72(): return None
def render_build_text_v71(): return None
def render_build_text_v70(): return None
def render_build_text_v69(): return None
def render_build_text_v68(): return None
def render_build_text_v67(): return None
def render_build_text_v66(): return None
def render_build_text_v65(): return None
def render_build_text_v64(): return None
def render_build_text_v63(): return None
def render_build_text_v62(): return None
def render_build_text_v61(): return None
def render_build_text_v60(): return None
def render_build_text_v59(): return None
def render_build_text_v58(): return None
def render_build_text_v57(): return None
def render_build_text_v56(): return None
def render_build_text_v55(): return None
def render_build_text_v54(): return None
def render_build_text_v53(): return None
def render_build_text_v52(): return None
def render_build_text_v51(): return None
def render_build_text_v50(): return None
def render_build_text_v49(): return None
def render_build_text_v48(): return None
def render_build_text_v47(): return None
def render_build_text_v46(): return None
def render_build_text_v45(): return None
def render_build_text_v44(): return None
def render_build_text_v43(): return None
def render_build_text_v42(): return None
def render_build_text_v41(): return None
def render_build_text_v40(): return None
def render_build_text_v39(): return None
def render_build_text_v38(): return None
def render_build_text_v37(): return None
def render_build_text_v36(): return None
def render_build_text_v35(): return None
def render_build_text_v34(): return None
def render_build_text_v33(): return None
def render_build_text_v32(): return None
def render_build_text_v31(): return None
def render_build_text_v30(): return None
def render_build_text_v29(): return None
def render_build_text_v28(): return None
def render_build_text_v27(): return None
def render_build_text_v26(): return None
def render_build_text_v25(): return None
def render_build_text_v24(): return None
def render_build_text_v23(): return None
def render_build_text_v22(): return None
def render_build_text_v21(): return None
def render_build_text_v20(): return None
def render_build_text_v19(): return None
def render_build_text_v18(): return None
def render_build_text_v17(): return None
def render_build_text_v16(): return None
def render_build_text_v15(): return None
def render_build_text_v14(): return None
def render_build_text_v13(): return None
def render_build_text_v12(): return None
def render_build_text_v11(): return None
def build_marker_v11(): return None
def build_marker_v10(): return None
def build_marker_v9(): return None
def build_marker_v8(): return None
def build_marker_v7(): return None
def render_version_tag(): return None


# --------------------------------------------------------------------
# v73: Guard Import Fix
# --------------------------------------------------------------------
APP_BUILD_VERSION = "v73"
APP_BUILD_LABEL = "Guard Import Fix"

def topbar(title, subtitle="", kicker="HealthyMe premium"):
    st.markdown(
        f"""
        <div class='hero-shell'>
          <div class='hm-v73-brand-row'>
            <span class='hm-v73-brand'>HealthyMe</span>
            <span class='hm-v73-version-inline'>{APP_BUILD_VERSION} · {APP_BUILD_LABEL}</span>
          </div>
          <div class='hero-kicker'>{kicker}</div>
          <div class='hero-title'>{title}</div>
          <div class='hero-subtitle'>{subtitle}</div>
          <div><span class='meta-pill'>Guided wellness workflow</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def compact_topbar(title, subtitle="", kicker="HealthyMe"):
    st.markdown(
        f"""
        <div class='hero-shell hm-compact-page-section'>
          <div class='hm-v73-brand-row'>
            <span class='hm-v73-brand'>HealthyMe</span>
            <span class='hm-v73-version-inline'>{APP_BUILD_VERSION} · {APP_BUILD_LABEL}</span>
          </div>
          <div class='hero-kicker'>{kicker}</div>
          <div class='hero-title'>{title}</div>
          {f"<div class='hero-subtitle'>{subtitle}</div>" if subtitle else ""}
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_build_text_v73(): return None
def render_build_text_v72(): return None
def render_build_text_v71(): return None
def render_build_text_v70(): return None
def render_build_text_v69(): return None
def render_build_text_v68(): return None
def render_build_text_v67(): return None
def render_build_text_v66(): return None
def render_build_text_v65(): return None
def render_build_text_v64(): return None
def render_build_text_v63(): return None
def render_build_text_v62(): return None
def render_build_text_v61(): return None
def render_build_text_v60(): return None
def render_build_text_v59(): return None
def render_build_text_v58(): return None
def render_build_text_v57(): return None
def render_build_text_v56(): return None
def render_build_text_v55(): return None
def render_build_text_v54(): return None
def render_build_text_v53(): return None
def render_build_text_v52(): return None
def render_build_text_v51(): return None
def render_build_text_v50(): return None
def render_build_text_v49(): return None
def render_build_text_v48(): return None
def render_build_text_v47(): return None
def render_build_text_v46(): return None
def render_build_text_v45(): return None
def render_build_text_v44(): return None
def render_build_text_v43(): return None
def render_build_text_v42(): return None
def render_build_text_v41(): return None
def render_build_text_v40(): return None
def render_build_text_v39(): return None
def render_build_text_v38(): return None
def render_build_text_v37(): return None
def render_build_text_v36(): return None
def render_build_text_v35(): return None
def render_build_text_v34(): return None
def render_build_text_v33(): return None
def render_build_text_v32(): return None
def render_build_text_v31(): return None
def render_build_text_v30(): return None
def render_build_text_v29(): return None
def render_build_text_v28(): return None
def render_build_text_v27(): return None
def render_build_text_v26(): return None
def render_build_text_v25(): return None
def render_build_text_v24(): return None
def render_build_text_v23(): return None
def render_build_text_v22(): return None
def render_build_text_v21(): return None
def render_build_text_v20(): return None
def render_build_text_v19(): return None
def render_build_text_v18(): return None
def render_build_text_v17(): return None
def render_build_text_v16(): return None
def render_build_text_v15(): return None
def render_build_text_v14(): return None
def render_build_text_v13(): return None
def render_build_text_v12(): return None
def render_build_text_v11(): return None
def build_marker_v11(): return None
def build_marker_v10(): return None
def build_marker_v9(): return None
def build_marker_v8(): return None
def build_marker_v7(): return None
def render_version_tag(): return None


# --------------------------------------------------------------------
# v74: Final Report JSON Import Fix
# --------------------------------------------------------------------
APP_BUILD_VERSION = "v74"
APP_BUILD_LABEL = "Final Report JSON Import Fix"

def topbar(title, subtitle="", kicker="HealthyMe premium"):
    st.markdown(
        f"""
        <div class='hero-shell'>
          <div class='hm-v74-brand-row'>
            <span class='hm-v74-brand'>HealthyMe</span>
            <span class='hm-v74-version-inline'>{APP_BUILD_VERSION} · {APP_BUILD_LABEL}</span>
          </div>
          <div class='hero-kicker'>{kicker}</div>
          <div class='hero-title'>{title}</div>
          <div class='hero-subtitle'>{subtitle}</div>
          <div><span class='meta-pill'>Guided wellness workflow</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def compact_topbar(title, subtitle="", kicker="HealthyMe"):
    st.markdown(
        f"""
        <div class='hero-shell hm-compact-page-section'>
          <div class='hm-v74-brand-row'>
            <span class='hm-v74-brand'>HealthyMe</span>
            <span class='hm-v74-version-inline'>{APP_BUILD_VERSION} · {APP_BUILD_LABEL}</span>
          </div>
          <div class='hero-kicker'>{kicker}</div>
          <div class='hero-title'>{title}</div>
          {f"<div class='hero-subtitle'>{subtitle}</div>" if subtitle else ""}
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_build_text_v74(): return None
def render_build_text_v73(): return None
def render_build_text_v72(): return None
def render_build_text_v71(): return None
def render_build_text_v70(): return None
def render_build_text_v69(): return None
def render_build_text_v68(): return None
def render_build_text_v67(): return None
def render_build_text_v66(): return None
def render_build_text_v65(): return None
def render_build_text_v64(): return None
def render_build_text_v63(): return None
def render_build_text_v62(): return None
def render_build_text_v61(): return None
def render_build_text_v60(): return None
def render_build_text_v59(): return None
def render_build_text_v58(): return None
def render_build_text_v57(): return None
def render_build_text_v56(): return None
def render_build_text_v55(): return None
def render_build_text_v54(): return None
def render_build_text_v53(): return None
def render_build_text_v52(): return None
def render_build_text_v51(): return None
def render_build_text_v50(): return None
def render_build_text_v49(): return None
def render_build_text_v48(): return None
def render_build_text_v47(): return None
def render_build_text_v46(): return None
def render_build_text_v45(): return None
def render_build_text_v44(): return None
def render_build_text_v43(): return None
def render_build_text_v42(): return None
def render_build_text_v41(): return None
def render_build_text_v40(): return None
def render_build_text_v39(): return None
def render_build_text_v38(): return None
def render_build_text_v37(): return None
def render_build_text_v36(): return None
def render_build_text_v35(): return None
def render_build_text_v34(): return None
def render_build_text_v33(): return None
def render_build_text_v32(): return None
def render_build_text_v31(): return None
def render_build_text_v30(): return None
def render_build_text_v29(): return None
def render_build_text_v28(): return None
def render_build_text_v27(): return None
def render_build_text_v26(): return None
def render_build_text_v25(): return None
def render_build_text_v24(): return None
def render_build_text_v23(): return None
def render_build_text_v22(): return None
def render_build_text_v21(): return None
def render_build_text_v20(): return None
def render_build_text_v19(): return None
def render_build_text_v18(): return None
def render_build_text_v17(): return None
def render_build_text_v16(): return None
def render_build_text_v15(): return None
def render_build_text_v14(): return None
def render_build_text_v13(): return None
def render_build_text_v12(): return None
def render_build_text_v11(): return None
def build_marker_v11(): return None
def build_marker_v10(): return None
def build_marker_v9(): return None
def build_marker_v8(): return None
def build_marker_v7(): return None
def render_version_tag(): return None


# --------------------------------------------------------------------
# v75: Final Report Diagnostics UI
# --------------------------------------------------------------------
APP_BUILD_VERSION = "v75"
APP_BUILD_LABEL = "Final Report Diagnostics UI"

def topbar(title, subtitle="", kicker="HealthyMe premium"):
    st.markdown(
        f"""
        <div class='hero-shell'>
          <div class='hm-v75-brand-row'>
            <span class='hm-v75-brand'>HealthyMe</span>
            <span class='hm-v75-version-inline'>{APP_BUILD_VERSION} · {APP_BUILD_LABEL}</span>
          </div>
          <div class='hero-kicker'>{kicker}</div>
          <div class='hero-title'>{title}</div>
          <div class='hero-subtitle'>{subtitle}</div>
          <div><span class='meta-pill'>Guided wellness workflow</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def compact_topbar(title, subtitle="", kicker="HealthyMe"):
    st.markdown(
        f"""
        <div class='hero-shell hm-compact-page-section'>
          <div class='hm-v75-brand-row'>
            <span class='hm-v75-brand'>HealthyMe</span>
            <span class='hm-v75-version-inline'>{APP_BUILD_VERSION} · {APP_BUILD_LABEL}</span>
          </div>
          <div class='hero-kicker'>{kicker}</div>
          <div class='hero-title'>{title}</div>
          {f"<div class='hero-subtitle'>{subtitle}</div>" if subtitle else ""}
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_build_text_v75(): return None
def render_build_text_v74(): return None
def render_build_text_v73(): return None
def render_build_text_v72(): return None
def render_build_text_v71(): return None
def render_build_text_v70(): return None
def render_build_text_v69(): return None
def render_build_text_v68(): return None
def render_build_text_v67(): return None
def render_build_text_v66(): return None
def render_build_text_v65(): return None
def render_build_text_v64(): return None
def render_build_text_v63(): return None
def render_build_text_v62(): return None
def render_build_text_v61(): return None
def render_build_text_v60(): return None
def render_build_text_v59(): return None
def render_build_text_v58(): return None
def render_build_text_v57(): return None
def render_build_text_v56(): return None
def render_build_text_v55(): return None
def render_build_text_v54(): return None
def render_build_text_v53(): return None
def render_build_text_v52(): return None
def render_build_text_v51(): return None
def render_build_text_v50(): return None
def render_build_text_v49(): return None
def render_build_text_v48(): return None
def render_build_text_v47(): return None
def render_build_text_v46(): return None
def render_build_text_v45(): return None
def render_build_text_v44(): return None
def render_build_text_v43(): return None
def render_build_text_v42(): return None
def render_build_text_v41(): return None
def render_build_text_v40(): return None
def render_build_text_v39(): return None
def render_build_text_v38(): return None
def render_build_text_v37(): return None
def render_build_text_v36(): return None
def render_build_text_v35(): return None
def render_build_text_v34(): return None
def render_build_text_v33(): return None
def render_build_text_v32(): return None
def render_build_text_v31(): return None
def render_build_text_v30(): return None
def render_build_text_v29(): return None
def render_build_text_v28(): return None
def render_build_text_v27(): return None
def render_build_text_v26(): return None
def render_build_text_v25(): return None
def render_build_text_v24(): return None
def render_build_text_v23(): return None
def render_build_text_v22(): return None
def render_build_text_v21(): return None
def render_build_text_v20(): return None
def render_build_text_v19(): return None
def render_build_text_v18(): return None
def render_build_text_v17(): return None
def render_build_text_v16(): return None
def render_build_text_v15(): return None
def render_build_text_v14(): return None
def render_build_text_v13(): return None
def render_build_text_v12(): return None
def render_build_text_v11(): return None
def build_marker_v11(): return None
def build_marker_v10(): return None
def build_marker_v9(): return None
def build_marker_v8(): return None
def build_marker_v7(): return None
def render_version_tag(): return None


# --------------------------------------------------------------------
# v76: Mobile Daily Log Timing Fix
# --------------------------------------------------------------------
APP_BUILD_VERSION = "v76"
APP_BUILD_LABEL = "Mobile Daily Log Timing Fix"

def topbar(title, subtitle="", kicker="HealthyMe premium"):
    st.markdown(
        f"""
        <div class='hero-shell'>
          <div class='hm-v76-brand-row'>
            <span class='hm-v76-brand'>HealthyMe</span>
            <span class='hm-v76-version-inline'>{APP_BUILD_VERSION} · {APP_BUILD_LABEL}</span>
          </div>
          <div class='hero-kicker'>{kicker}</div>
          <div class='hero-title'>{title}</div>
          <div class='hero-subtitle'>{subtitle}</div>
          <div><span class='meta-pill'>Guided wellness workflow</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def compact_topbar(title, subtitle="", kicker="HealthyMe"):
    st.markdown(
        f"""
        <div class='hero-shell hm-compact-page-section'>
          <div class='hm-v76-brand-row'>
            <span class='hm-v76-brand'>HealthyMe</span>
            <span class='hm-v76-version-inline'>{APP_BUILD_VERSION} · {APP_BUILD_LABEL}</span>
          </div>
          <div class='hero-kicker'>{kicker}</div>
          <div class='hero-title'>{title}</div>
          {f"<div class='hero-subtitle'>{subtitle}</div>" if subtitle else ""}
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_build_text_v76(): return None
def render_build_text_v75(): return None
def render_build_text_v74(): return None
def render_build_text_v73(): return None
def render_build_text_v72(): return None
def render_build_text_v71(): return None
def render_build_text_v70(): return None
def render_build_text_v69(): return None
def render_build_text_v68(): return None
def render_build_text_v67(): return None
def render_build_text_v66(): return None
def render_build_text_v65(): return None
def render_build_text_v64(): return None
def render_build_text_v63(): return None
def render_build_text_v62(): return None
def render_build_text_v61(): return None
def render_build_text_v60(): return None
def render_build_text_v59(): return None
def render_build_text_v58(): return None
def render_build_text_v57(): return None
def render_build_text_v56(): return None
def render_build_text_v55(): return None
def render_build_text_v54(): return None
def render_build_text_v53(): return None
def render_build_text_v52(): return None
def render_build_text_v51(): return None
def render_build_text_v50(): return None
def render_build_text_v49(): return None
def render_build_text_v48(): return None
def render_build_text_v47(): return None
def render_build_text_v46(): return None
def render_build_text_v45(): return None
def render_build_text_v44(): return None
def render_build_text_v43(): return None
def render_build_text_v42(): return None
def render_build_text_v41(): return None
def render_build_text_v40(): return None
def render_build_text_v39(): return None
def render_build_text_v38(): return None
def render_build_text_v37(): return None
def render_build_text_v36(): return None
def render_build_text_v35(): return None
def render_build_text_v34(): return None
def render_build_text_v33(): return None
def render_build_text_v32(): return None
def render_build_text_v31(): return None
def render_build_text_v30(): return None
def render_build_text_v29(): return None
def render_build_text_v28(): return None
def render_build_text_v27(): return None
def render_build_text_v26(): return None
def render_build_text_v25(): return None
def render_build_text_v24(): return None
def render_build_text_v23(): return None
def render_build_text_v22(): return None
def render_build_text_v21(): return None
def render_build_text_v20(): return None
def render_build_text_v19(): return None
def render_build_text_v18(): return None
def render_build_text_v17(): return None
def render_build_text_v16(): return None
def render_build_text_v15(): return None
def render_build_text_v14(): return None
def render_build_text_v13(): return None
def render_build_text_v12(): return None
def render_build_text_v11(): return None
def build_marker_v11(): return None
def build_marker_v10(): return None
def build_marker_v9(): return None
def build_marker_v8(): return None
def build_marker_v7(): return None
def render_version_tag(): return None


# --------------------------------------------------------------------
# v77: Meal Timing + Daily Log UI Alignment Fix
# --------------------------------------------------------------------
APP_BUILD_VERSION = "v100.11"
APP_BUILD_LABEL = "Layout Structure Finalization"


def admin_version_line_v98_1():
    """Admin-only version line displayed under HealthyMe brand/top header."""
    try:
        if st.session_state.get("user_role") == "admin":
            return (
                "<div style='"
                "color:#7A5A16;"
                "font-size:.74rem;"
                "font-weight:850;"
                "letter-spacing:.02em;"
                "margin-top:.12rem;"
                "line-height:1.05;"
                "'>"
                f"HealthyMe {APP_BUILD_VERSION} · {APP_BUILD_LABEL}"
                "</div>"
            )
    except Exception:
        pass
    return ""


def topbar(title, subtitle="", kicker="HealthyMe premium"):
    st.markdown(
        f"""
        <div class='hero-shell'>
          <div class='hm-v77-brand-row'>
            <span class='hm-v77-brand'>HealthyMe</span>
            {admin_version_line_v98_1()}
          </div>
          <div class='hero-kicker'>{kicker}</div>
          <div class='hero-title'>{title}</div>
          <div class='hero-subtitle'>{subtitle}</div>
          <div><span class='meta-pill'>Guided wellness workflow</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def compact_topbar(title, subtitle="", kicker="HealthyMe"):
    st.markdown(
        f"""
        <div class='hero-shell hm-compact-page-section'>
          <div class='hm-v77-brand-row'>
            <span class='hm-v77-brand'>HealthyMe</span>
            {admin_version_line_v98_1()}
          </div>
          <div class='hero-kicker'>{kicker}</div>
          <div class='hero-title'>{title}</div>
          {f"<div class='hero-subtitle'>{subtitle}</div>" if subtitle else ""}
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_build_text_v77(): return None
def render_build_text_v76(): return None
def render_build_text_v75(): return None
def render_build_text_v74(): return None
def render_build_text_v73(): return None
def render_build_text_v72(): return None
def render_build_text_v71(): return None
def render_build_text_v70(): return None
def render_build_text_v69(): return None
def render_build_text_v68(): return None
def render_build_text_v67(): return None
def render_build_text_v66(): return None
def render_build_text_v65(): return None
def render_build_text_v64(): return None
def render_build_text_v63(): return None
def render_build_text_v62(): return None
def render_build_text_v61(): return None
def render_build_text_v60(): return None
def render_build_text_v59(): return None
def render_build_text_v58(): return None
def render_build_text_v57(): return None
def render_build_text_v56(): return None
def render_build_text_v55(): return None
def render_build_text_v54(): return None
def render_build_text_v53(): return None
def render_build_text_v52(): return None
def render_build_text_v51(): return None
def render_build_text_v50(): return None
def render_build_text_v49(): return None
def render_build_text_v48(): return None
def render_build_text_v47(): return None
def render_build_text_v46(): return None
def render_build_text_v45(): return None
def render_build_text_v44(): return None
def render_build_text_v43(): return None
def render_build_text_v42(): return None
def render_build_text_v41(): return None
def render_build_text_v40(): return None
def render_build_text_v39(): return None
def render_build_text_v38(): return None
def render_build_text_v37(): return None
def render_build_text_v36(): return None
def render_build_text_v35(): return None
def render_build_text_v34(): return None
def render_build_text_v33(): return None
def render_build_text_v32(): return None
def render_build_text_v31(): return None
def render_build_text_v30(): return None
def render_build_text_v29(): return None
def render_build_text_v28(): return None
def render_build_text_v27(): return None
def render_build_text_v26(): return None
def render_build_text_v25(): return None
def render_build_text_v24(): return None
def render_build_text_v23(): return None
def render_build_text_v22(): return None
def render_build_text_v21(): return None
def render_build_text_v20(): return None
def render_build_text_v19(): return None
def render_build_text_v18(): return None
def render_build_text_v17(): return None
def render_build_text_v16(): return None
def render_build_text_v15(): return None
def render_build_text_v14(): return None
def render_build_text_v13(): return None
def render_build_text_v12(): return None
def render_build_text_v11(): return None
def build_marker_v11(): return None
def build_marker_v10(): return None
def build_marker_v9(): return None
def build_marker_v8(): return None
def build_marker_v7(): return None
def render_version_tag(): return None

def render_build_text_v80(): return None

def render_build_text_v81(): return None


def render_build_text_v82(): return None


def render_build_text_v83(): return None


def render_build_text_v84(): return None


def render_build_text_v85(): return None


def render_build_text_v86(): return None


def render_build_text_v87(): return None


def render_build_text_v88(): return None


def render_build_text_v88_1(): return None


def render_build_text_v89R(): return None


def render_build_text_v90(): return None


def render_build_text_v90A(): return None


def render_build_text_v90A_1(): return None


def render_build_text_v91(): return None


def render_build_text_v91_1(): return None


def render_build_text_v91_2(): return None


def render_build_text_v91_3(): return None


def render_build_text_v92(): return None


def render_build_text_v92_1(): return None


def render_build_text_v92_2(): return None


def render_build_text_v92_3(): return None


def render_build_text_v92_4(): return None


def render_build_text_v92_5(): return None


def render_build_text_v92_6(): return None


def render_build_text_v92_7(): return None


def render_build_text_v92_8(): return None


def render_build_text_v92_9(): return None


def render_build_text_v92_10(): return None


def render_build_text_v92_11(): return None


def render_build_text_v93(): return None


def render_build_text_v94(): return None


def render_build_text_v94_1(): return None


def render_build_text_v94_2(): return None


def render_build_text_v94_3(): return None


def render_build_text_v94_4(): return None


def render_build_text_v94_5(): return None


def render_build_text_v94_6(): return None


def render_build_text_v95(): return None


def render_build_text_v95_1(): return None


def render_build_text_v95_2(): return None


def render_build_text_v95_5(): return None


def render_build_text_v95_6(): return None


def render_admin_build_version(location="top"):
    """Visible admin-side build/version marker for deployment verification."""
    try:
        st.markdown(
            f"""
            <div style="
                display:inline-flex;
                align-items:center;
                gap:.4rem;
                padding:.28rem .7rem;
                margin:.25rem 0 .65rem 0;
                border-radius:999px;
                border:1px solid #E5D2A9;
                background:#FFFDF8;
                color:#064E3B;
                font-size:.78rem;
                font-weight:800;
                box-shadow:0 4px 12px rgba(25,36,31,.045);
            ">
                Admin Build · {APP_BUILD_VERSION} · {APP_BUILD_LABEL}
            </div>
            """,
            unsafe_allow_html=True,
        )
    except Exception:
        pass



def render_build_text_v95_7(): return None


# --------------------------------------------------------------------
# v96.11: lightweight browser keep-alive guard
# --------------------------------------------------------------------
def inject_keepalive_guard_v96_11():
    """Keep the Streamlit app warm while a browser tab is open.

    Note: no client-side code can prevent sleep when nobody has the app open.
    """
    import streamlit.components.v1 as components
    components.html(
        """
        <script>
        (function(){
          if (window.__healthymeKeepAliveV9611) return;
          window.__healthymeKeepAliveV9611 = true;

          async function pingHealthyMe(){
            try {
              await fetch(window.location.origin + "/_stcore/health", {cache: "no-store", credentials: "same-origin"});
            } catch(e) {}
            try {
              await fetch(window.location.pathname + "?hm_keepalive=" + Date.now(), {cache: "no-store", credentials: "same-origin"});
            } catch(e) {}
          }

          pingHealthyMe();
          setInterval(pingHealthyMe, 240000);
          document.addEventListener("visibilitychange", function(){
            if (!document.hidden) pingHealthyMe();
          });
        })();
        </script>
        """,
        height=0,
    )
