from components.ui_common import render_page_nav, render_back_to_top
import pandas as pd
import streamlit as st

from components.guards import require_admin
from components.ui_common import (
    inject_global_styles,
    apply_luxe_theme,
    utility_logout_bar,
    topbar,
    render_back_to_top,
    render_page_nav,
)
from components.db import (
    list_members,
    recalculate_all_nsp_system_scores,
    recalculate_member_nsp_system_scores,
    list_nsp_recalculation_status,
)

st.set_page_config(page_title="NSP Score Recalculation", page_icon="💚", layout="wide", initial_sidebar_state="collapsed")

inject_global_styles()
apply_luxe_theme()
require_admin()
utility_logout_bar()
topbar("NSP Score Recalculation", "Recalculate existing member system scores using the Excel-aligned NSP mapping.", "Admin system tool")

st.markdown("""
<style>
/* v101.4 NSP recalculation page */
.hm-v1014-card{
  border:1px solid #E3C98E;
  background:linear-gradient(180deg,#FFFDF8 0%,#FFF9EC 100%);
  border-radius:20px;
  padding:1rem 1.08rem;
  box-shadow:0 10px 24px rgba(15,23,42,.05);
  margin:.42rem 0 .90rem 0;
}
.hm-v1014-title{
  color:#003C36;
  font-size:1.12rem;
  font-weight:980;
  margin:0 0 .25rem 0;
}
.hm-v1014-sub{
  color:#475569;
  font-size:.86rem;
  font-weight:700;
  margin:0 0 .90rem 0;
}
.hm-v1014-note{
  border:1px solid #E3C98E;
  background:#FFF7E6;
  border-radius:14px;
  padding:.75rem .86rem;
  color:#7A5A16;
  font-size:.86rem;
  font-weight:760;
  margin:.45rem 0 .90rem 0;
}
div[data-testid="stButton"] > button{
  min-height:2.72rem!important;
  border-radius:14px!important;
  border:1.25px solid #D9C28F!important;
  background:#FFFDF8!important;
  color:#064E3B!important;
  font-weight:850!important;
}
div[data-testid="stButton"] > button:hover{
  border-color:#B89345!important;
  background:#FFF7E6!important;
}
</style>
""", unsafe_allow_html=True)

st.markdown("<div class='hm-v1014-card'>", unsafe_allow_html=True)
st.markdown("<div class='hm-v1014-title'>What this does</div>", unsafe_allow_html=True)
st.markdown(
    """
    <div class='hm-v1014-note'>
      This recalculates existing members' NSP system-score snapshots using the v101.3 Excel-derived mapping.
      Raw NSP answers are not changed. Reports already calculate dynamically from the current mapping; this utility creates stored snapshots and an audit trail for existing members and assessment instances.
    </div>
    """,
    unsafe_allow_html=True,
)
st.markdown("</div>", unsafe_allow_html=True)

left, right = st.columns([1, 1], gap="large")

with left:
    st.markdown("<div class='hm-v1014-card'>", unsafe_allow_html=True)
    st.markdown("<div class='hm-v1014-title'>Recalculate all members</div>", unsafe_allow_html=True)
    st.markdown("<div class='hm-v1014-sub'>Use this once after deploying v101.3+ to align all stored snapshots.</div>", unsafe_allow_html=True)
    if st.button("Recalculate All Existing Members", use_container_width=True):
        results = recalculate_all_nsp_system_scores(actor_id=st.session_state.get("user_id", "admin"))
        st.success(f"Recalculation completed for {len(results)} member(s).")
        st.dataframe(pd.DataFrame(results), use_container_width=True, hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)

with right:
    st.markdown("<div class='hm-v1014-card'>", unsafe_allow_html=True)
    st.markdown("<div class='hm-v1014-title'>Recalculate selected member</div>", unsafe_allow_html=True)
    members = list_members()
    if not members:
        st.info("No members available.")
    else:
        member_options = {f"{m.get('name','')} — {m.get('email','')}": m.get("id") for m in members}
        selected_label = st.selectbox("Select member", list(member_options.keys()))
        selected_member_id = member_options[selected_label]
        if st.button("Recalculate Selected Member", use_container_width=True):
            result = recalculate_member_nsp_system_scores(selected_member_id, actor_id=st.session_state.get("user_id", "admin"))
            st.success("Selected member recalculated.")
            st.json(result)
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div class='hm-v1014-card'>", unsafe_allow_html=True)
st.markdown("<div class='hm-v1014-title'>Current recalculation status</div>", unsafe_allow_html=True)
status_rows = list_nsp_recalculation_status()
if status_rows:
    st.dataframe(pd.DataFrame(status_rows), use_container_width=True, hide_index=True)
else:
    st.info("No member records found.")
st.markdown("</div>", unsafe_allow_html=True)

render_page_nav("NSP Score Recalculation", back_page="pages/10_Admin_Dashboard.py", show_evaluation=False, location="bottom")
render_back_to_top()

# v101.4: Existing member NSP score recalculation utility.
