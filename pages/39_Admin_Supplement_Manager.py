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

st.set_page_config(page_title="Supplement Management", page_icon="💚", layout="wide", initial_sidebar_state="collapsed")

inject_global_styles()
apply_luxe_theme()
require_admin()
utility_logout_bar()
topbar(
    "Supplement Management",
    "Create, review and manage a member’s supplement regimen. This is a v102.3 shell; persistence can be added after workflow acceptance.",
    "Admin supplements",
)

st.markdown("""
<style>
.hm-sup-page{max-width:1120px;margin:0 auto;}
.hm-sup-sub{color:#475569;font-size:.90rem;font-weight:660;line-height:1.45;margin:.10rem 0 1rem 0;max-width:640px;}
.hm-sup-layout{display:grid;grid-template-columns:1.25fr .75fr;gap:1rem;margin:.8rem 0 1rem 0;}
.hm-sup-panel{border:1px solid #E3C98E;background:linear-gradient(180deg,#FFFDF8 0%,#FFF9EC 100%);border-radius:20px;padding:1rem;box-shadow:0 10px 24px rgba(15,23,42,.05);}
.hm-sup-title-row{display:flex;align-items:center;justify-content:space-between;margin-bottom:.75rem;}
.hm-sup-title{color:#064E3B;font-size:1.02rem;font-weight:950;}
.hm-sup-badge{background:#DDF7F3;color:#006D6F;border-radius:999px;padding:.22rem .58rem;font-size:.72rem;font-weight:900;}
.hm-sup-card{border:1px solid #E6D4A8;background:#FFFDF8;border-radius:16px;padding:.85rem;margin:.72rem 0;display:grid;grid-template-columns:40px 1fr auto;gap:.75rem;align-items:center;}
.hm-sup-icon{width:34px;height:34px;border-radius:999px;background:#FFF0EA;color:#B35C4D;display:flex;align-items:center;justify-content:center;font-weight:950;}
.hm-sup-icon.blue{background:#DDF7F3;color:#006D6F;}
.hm-sup-name{color:#1F2937;font-size:.92rem;font-weight:920;margin-bottom:.15rem;}
.hm-sup-dose{color:#64748B;font-size:.78rem;font-weight:760;}
.hm-sup-mini{display:inline-flex;background:#F8F5EE;border:1px solid #E6D4A8;border-radius:999px;padding:.12rem .40rem;font-size:.66rem;font-weight:850;color:#475569;margin:.28rem .15rem 0 0;}
.hm-sup-action{font-size:.72rem;font-weight:900;color:#006D6F;margin-left:.6rem;}
.hm-sup-stop{color:#B4233A;}
.hm-sup-formgrid{display:grid;grid-template-columns:1fr 1fr;gap:.7rem;}
.hm-sup-note{border:1px dashed #D9C28F;background:#FFF9EC;border-radius:16px;padding:.85rem;color:#7A5A16;font-size:.82rem;font-weight:790;margin:.85rem 0;}
.hm-sup-footer-actions{display:flex;gap:.65rem;justify-content:flex-end;margin-top:.75rem;}
.hm-sup-btn{border-radius:999px;border:1px solid #006D6F;padding:.55rem 1rem;font-size:.78rem;font-weight:900;text-align:center;}
.hm-sup-btn.primary{background:#006D6F;color:white;}
.hm-sup-btn.secondary{background:white;color:#006D6F;}
@media(max-width:850px){.hm-sup-layout,.hm-sup-formgrid{grid-template-columns:1fr}.hm-sup-card{grid-template-columns:34px 1fr}}
</style>
""", unsafe_allow_html=True)

st.markdown("<div class='hm-sup-page'>", unsafe_allow_html=True)
st.markdown("<div class='hm-sup-sub'>Curate and manage nutritional support. Add supplements, adjust dosage/timing, stop an item, and prepare the regimen for member visibility.</div>", unsafe_allow_html=True)

member_col, date_col = st.columns([1.3, .7], gap="medium")
with member_col:
    selected_member = st.selectbox(
        "Select Member",
        ["Elena R. / Protocol", "Shweta Mishra", "Demo Member"],
        key="hm_v1023_supp_member",
    )
with date_col:
    plan_date = st.date_input("Plan Date", key="hm_v1023_supp_date")

# Session-state shell data
if "hm_v1023_supplements" not in st.session_state:
    st.session_state.hm_v1023_supplements = [
        {"name": "Vitamin D3 + K2", "dose": "5000 IU / 100 mcg", "unit": "Capsule", "timing": ["Morning", "With Food"], "icon": "sun"},
        {"name": "Magnesium Glycinate", "dose": "400 mg", "unit": "Powder", "timing": ["Evening", "Before Bed"], "icon": "drop"},
    ]

st.markdown("<div class='hm-sup-layout'>", unsafe_allow_html=True)

st.markdown("<div class='hm-sup-panel'>", unsafe_allow_html=True)
st.markdown("<div class='hm-sup-title-row'><div class='hm-sup-title'>Active Regimen</div><div class='hm-sup-badge'>%s Active</div></div>" % len(st.session_state.hm_v1023_supplements), unsafe_allow_html=True)

for idx, item in enumerate(st.session_state.hm_v1023_supplements):
    icon_class = "blue" if item.get("icon") == "drop" else ""
    timing_html = "".join([f"<span class='hm-sup-mini'>{t}</span>" for t in item.get("timing", [])])
    st.markdown(f"""
    <div class='hm-sup-card'>
      <div class='hm-sup-icon {icon_class}'>◉</div>
      <div>
        <div class='hm-sup-name'>{item['name']}</div>
        <div class='hm-sup-dose'>{item['dose']} · {item['unit']}</div>
        <div>{timing_html}</div>
      </div>
      <div><span class='hm-sup-action'>Edit</span><span class='hm-sup-action hm-sup-stop'>Stop</span></div>
    </div>
    """, unsafe_allow_html=True)

with st.expander("+ View Stopped Supplements", expanded=False):
    st.info("Stopped supplement history will be connected after workflow acceptance.")

st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div class='hm-sup-panel'>", unsafe_allow_html=True)
st.markdown("<div class='hm-sup-title'>Add Supplement</div>", unsafe_allow_html=True)

name = st.text_input("Supplement Name", placeholder="e.g. Ashwagandha", key="hm_v1023_supp_name")
c1, c2 = st.columns(2, gap="small")
with c1:
    dosage = st.text_input("Dosage", placeholder="e.g. 500", key="hm_v1023_supp_dose")
with c2:
    unit = st.selectbox("Unit", ["mg", "mcg", "IU", "Capsule", "Tablet", "Powder", "Drops"], key="hm_v1023_supp_unit")

timing_options = st.multiselect(
    "Timing",
    ["Morning", "Midday", "Evening", "Before Bed", "With Food", "Empty Stomach"],
    default=["Evening"],
    key="hm_v1023_supp_timing",
)
notes = st.text_area("Notes for Patient", placeholder="Add specific instructions...", key="hm_v1023_supp_notes")

if st.button("Add to Regimen", key="hm_v1023_add_regimen", use_container_width=True):
    if name.strip():
        st.session_state.hm_v1023_supplements.append({
            "name": name.strip(),
            "dose": dosage.strip() or "Not specified",
            "unit": unit,
            "timing": timing_options or ["As advised"],
            "icon": "drop",
        })
        st.success("Supplement added to the working regimen for this session.")
    else:
        st.warning("Please enter a supplement name.")

st.markdown("</div>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div class='hm-sup-note'>v102.3 is a workflow shell. Add/Edit/Stop is session-based for testing. Database persistence and member-specific publishing should be added after workflow acceptance.</div>", unsafe_allow_html=True)
st.markdown("<div class='hm-sup-footer-actions'><div class='hm-sup-btn secondary'>Back to Profile</div><div class='hm-sup-btn primary'>Save Regimen</div></div>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

render_page_nav("Supplement Management", back_page="pages/10_Admin_Dashboard.py", dashboard_page="pages/10_Admin_Dashboard.py", show_evaluation=False, show_dashboard=True, location="bottom")
render_back_to_top()

# v102.3: Admin Supplement Management shell.
