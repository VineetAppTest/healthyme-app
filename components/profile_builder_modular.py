import streamlit as st

from components.active_profile_preview_contract import render_active_profile_preview_contract
from components.pbm_core import (
    APP_BUILD_LABEL, APP_BUILD_VERSION, NAV_LABELS, SECTIONS,
    ensure_state, safe, safe_key,
)
from components.pbm_modules import render_module, render_preview
from components.pbm_setup import render_setup
from components.profile_publish_control import render_profile_publish_control
from components.recommendation_profile_store import (
    check_profile_builder_store, load_profile_builder_sources,
)


def _render_css() -> None:
    st.markdown("""
<style>
.hm-title{color:#064E3B;font-size:1.04rem;font-weight:950;margin:0 0 .25rem}.hm-sub{color:#64748B;font-size:.82rem;font-weight:720;margin:0 0 .7rem}
.hm-section-rule{height:1px;background:linear-gradient(90deg,transparent,rgba(216,168,78,.8),transparent);margin:.3rem 0 .72rem}
.hm-tab-nav [data-testid="stButton"]>button{width:100%!important;height:2.82rem!important;min-height:2.82rem!important;border-radius:15px!important;font-weight:930!important;border:1.15px solid rgba(216,180,98,.72)!important;background:#fff!important;color:#064E3B!important;white-space:nowrap!important;padding:.35rem!important}
.hm-tab-nav [data-testid="stButton"]>button[kind="primary"]{background:linear-gradient(135deg,#064E3B,#0F766E)!important;border-color:#064E3B!important;color:#fff!important}
.hm-readiness-strip{border-radius:15px;padding:.62rem .78rem;margin:.25rem 0 1rem;font-size:.84rem;font-weight:780}.hm-ready-ok{background:#ECFDF5;border:1px solid #A7F3D0;color:#065F46}.hm-ready-warn{background:#FFF7ED;border:1px solid #FED7AA;color:#9A3412}
.hm-load-label{min-height:1.22rem}.hm-slot{font-size:.80rem;color:#72551A;font-weight:900;margin:.8rem 0 .3rem}
.hm-preview{border:1px dashed #D8A84E;background:#FFF9EC;border-radius:16px;padding:.75rem .85rem;margin:.45rem 0;color:#475569;font-size:.83rem;line-height:1.5}
.hm-source-box{border:1px solid #D8A84E;background:#FFFDF7;border-radius:12px;padding:.48rem .65rem;margin:.35rem 0;color:#475569;font-size:.78rem}.hm-source-box b{color:#064E3B}.hm-source-box span{color:#64748B;font-weight:720}
.hm-count-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:.65rem;margin:.55rem 0 1rem}.hm-count-card{background:#fff;border:1px solid #E3C98E;border-radius:15px;padding:.7rem .8rem}.hm-count-card b{display:block;color:#064E3B}.hm-count-card span{color:#64748B;font-size:.78rem;font-weight:780}
@media(max-width:900px){.hm-count-grid{grid-template-columns:1fr 1fr}.hm-tab-nav [data-testid="stButton"]>button{font-size:.76rem!important}}
</style>
""", unsafe_allow_html=True)


def render_modular_profile_builder() -> None:
    ensure_state(); _render_css(); status = check_profile_builder_store(); sources, source_message = load_profile_builder_sources()
    options = {"recipe": list(sources.get("recipe") or []), "exercise": list(sources.get("exercise") or []), "supplement": list(sources.get("supplement") or []), "age_band": list(sources.get("age_band") or []), "health_concern": list(sources.get("health_concern") or []), "diet_type": list(sources.get("diet_type") or [])}
    st.markdown(f"<div class='hero-shell'><div class='hero-kicker'>Admin recommendations</div><div class='hero-title'>Recommendation Profile Builder</div><div class='hero-subtitle'>Profile shell creation with member-filtered, module-specific recommendation saves.</div><div><span class='meta-pill'>{APP_BUILD_VERSION} · {APP_BUILD_LABEL}</span></div></div>", unsafe_allow_html=True)
    st.markdown("<div class='hm-tab-nav'>", unsafe_allow_html=True); columns = st.columns(len(SECTIONS), gap="small")
    for column, section in zip(columns, SECTIONS):
        if column.button(NAV_LABELS[section], key=f"pbm_nav_{safe_key(section)}", type="primary" if st.session_state["pbm_section"] == section else "secondary", use_container_width=True): st.session_state["pbm_section"] = section; st.rerun()
    st.markdown("</div><div class='hm-section-rule'></div>", unsafe_allow_html=True)
    if status.get("ok"): st.markdown("<div class='hm-readiness-strip hm-ready-ok'><b>Profile Builder store is ready.</b> Setup and recommendation modules now save independently.</div>", unsafe_allow_html=True)
    else: st.markdown(f"<div class='hm-readiness-strip hm-ready-warn'><b>Profile Builder store is not ready.</b> {safe(status.get('message'))}</div>", unsafe_allow_html=True)
    st.caption(source_message); section = st.session_state["pbm_section"]
    if section == "Profile Setup": render_setup(options)
    elif section == "Meal Structure": render_module("meal", options)
    elif section == "Exercise Regime": render_module("exercise", options)
    elif section == "Supplement Regime": render_module("supplement", options)
    elif section == "Preview & End-to-End Flow": render_preview()
    elif section == "Publish Control": render_profile_publish_control()
    else: render_active_profile_preview_contract()
