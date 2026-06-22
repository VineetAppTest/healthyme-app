import html
import re

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


def _plain(value):
    raw = str(value or "").strip()
    if not raw:
        return ""
    text = raw
    for _ in range(8):
        decoded = html.unescape(text)
        decoded = decoded.replace("\\u003c", "<").replace("\\u003e", ">")
        decoded = decoded.replace("\\x3c", "<").replace("\\x3e", ">")
        if decoded == text:
            break
        text = decoded
    text = text.replace("`", " ")
    text = re.sub(r"<\s*br\s*/?\s*>", ", ", text, flags=re.I)
    text = re.sub(r"<\s*/\s*(div|p|span|li|td|th)\s*>", ", ", text, flags=re.I)
    text = re.sub(r"<\s*[^>]*>", " ", text)
    text = re.sub(r"</?\s*(div|span|p|li|td|th)[^>]*", " ", text, flags=re.I)
    text = re.sub(r"class\s*=\s*['\"][^'\"]*['\"]", " ", text, flags=re.I)
    text = re.sub(r"style\s*=\s*['\"][^'\"]*['\"]", " ", text, flags=re.I)
    text = re.sub(r"hm[-_](ms|tj)[-_](chip|dose|meta|item)", " ", text, flags=re.I)
    text = text.replace("\u00a0", " ").replace("&nbsp;", " ")
    text = re.sub(r"\s*,\s*", ", ", text)
    text = re.sub(r",\s*,+", ", ", text)
    text = re.sub(r"\s+", " ", text).strip(" ,;:-")
    return text


def _split_instruction(value, before_marker=False):
    text = _plain(value)
    marker = re.search(r"instructions\s*:", text, flags=re.I)
    if not marker:
        return text
    return text[:marker.start()].strip(" ,") if before_marker else text[marker.end():].strip(" ,")


def _timing_parts(*values):
    merged = []
    for value in values:
        clean = _split_instruction(value, before_marker=True)
        for part in clean.replace("|", ",").split(","):
            part = _plain(part)
            if part and part.lower() not in {"none", "na", "n/a", "null"} and part not in merged:
                merged.append(part)
    return merged


def _instructions(item):
    primary = _split_instruction(item.get("instructions") or item.get("member_instructions") or "", before_marker=False)
    if primary:
        return primary
    return _split_instruction(item.get("timing") or "", before_marker=False)


st.markdown("""
<style>
.hero-shell{margin-bottom:.20rem!important;}
div[data-testid="stVerticalBlock"] > div:has(.hero-shell){margin-bottom:.05rem!important;padding-bottom:.05rem!important;}
.hm-ms-page{max-width:960px;margin:-.18rem auto 0 auto;}
.hm-ms-card{border:1px solid #E3C98E;background:linear-gradient(180deg,#FFFDF8 0%,#FFF9EC 100%);border-radius:20px;padding:1rem;box-shadow:0 10px 24px rgba(15,23,42,.05);margin:.25rem 0 .55rem 0;}
.hm-ms-title{color:#064E3B;font-size:1.05rem;font-weight:950;margin-bottom:.25rem;}
.hm-ms-sub{color:#475569;font-size:.86rem;font-weight:700;line-height:1.45;}
.hm-ms-chip{display:inline-flex;background:#F8F5EE;border:1px solid #E6D4A8;border-radius:999px;padding:.12rem .42rem;font-size:.72rem;font-weight:780;color:#475569;margin:.18rem .16rem .08rem 0;}
.hm-ms-icon{width:32px;height:32px;border-radius:999px;background:#FFF0EA;color:#B35C4D;display:flex;align-items:center;justify-content:center;font-weight:850;margin-top:.15rem;}
.hm-ms-empty{border:1px dashed #D9C28F;background:#FFFDF8;border-radius:18px;padding:1.1rem;color:#64748B;font-size:.88rem;font-weight:760;margin:.85rem 0;}
.hm-ms-name{color:#1F2937;font-size:1.02rem;font-weight:850;margin-bottom:.05rem;}
.hm-ms-meta{color:#64748B;font-size:.86rem;font-weight:650;margin:.08rem 0;}
.hm-ms-note{color:#475569;font-size:.84rem;font-weight:550;margin-top:.28rem;}
@media(max-width:760px){.hm-ms-page{max-width:100%;}.hm-ms-name{font-size:.98rem}.hm-ms-meta{font-size:.82rem}.hm-ms-card{margin-top:.1rem}}
</style>
""", unsafe_allow_html=True)

user_id = st.session_state.get("user_id", "")
supplements = list_active_member_supplements(user_id)

st.markdown("<div class='hm-ms-page'>", unsafe_allow_html=True)
st.markdown("""
<div class='hm-ms-card'>
  <div class='hm-ms-title'>My Supplement Regimen</div>
  <div class='hm-ms-sub'>Showing only your currently active supplements assigned by your nutritionist. Stopped items are removed from this view automatically.</div>
</div>
""", unsafe_allow_html=True)

if not supplements:
    st.markdown("<div class='hm-ms-empty'>No supplements have been assigned yet. Your nutritionist will update this section when applicable.</div>", unsafe_allow_html=True)
else:
    for item in supplements:
        name = _plain(item.get("supplement_name") or "Supplement") or "Supplement"
        dosage = _plain(item.get("dosage") or "Dosage not specified") or "Dosage not specified"
        frequency = _plain(item.get("frequency") or "Frequency not specified") or "Frequency not specified"
        start_date = _plain(item.get("start_date") or "As advised") or "As advised"
        end_date = _plain(item.get("end_date") or "")
        timing_values = _timing_parts(item.get("timing"), item.get("additional_timing"))
        instruction_value = _instructions(item) or "Follow as advised by your nutritionist."
        with st.container(border=True):
            c_icon, c_body = st.columns([0.08, 0.92], gap="small")
            with c_icon:
                st.markdown("<div class='hm-ms-icon'>◉</div>", unsafe_allow_html=True)
            with c_body:
                st.markdown(f"<div class='hm-ms-name'>{html.escape(name)}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='hm-ms-meta'>{html.escape(dosage)} · {html.escape(frequency)}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='hm-ms-meta'>Start date: {html.escape(start_date)}</div>", unsafe_allow_html=True)
                if end_date:
                    st.markdown(f"<div class='hm-ms-meta'>End date: {html.escape(end_date)}</div>", unsafe_allow_html=True)
                chips = timing_values or ["As advised"]
                chip_html = "".join([f"<span class='hm-ms-chip'>{html.escape(x)}</span>" for x in chips])
                st.markdown(chip_html, unsafe_allow_html=True)
                st.markdown(f"<div class='hm-ms-note'>Instructions: {html.escape(instruction_value)}</div>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

render_page_nav("My Supplements", back_page="pages/02_Member_Home.py", dashboard_page="pages/02_Member_Home.py", show_evaluation=False, show_dashboard=True, location="bottom")
render_back_to_top()

# v102.4B14H: Mobile-safe supplement regimen rendering. Dynamic supplement fields are cleaned and rendered natively so old persisted HTML fragments cannot appear on member mobile.
