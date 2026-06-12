import streamlit as st
import json
from components.guards import require_admin
from components.ui_common import inject_global_styles, apply_luxe_theme, topbar, card_start, card_end, utility_logout_bar, stat_grid, render_page_nav, priority_action_start, priority_action_end, render_build_text_v14, render_back_to_top, compact_topbar
from components.db import load_db, get_workflow, get_admin_assessment, is_instance_final_report_ready
from components.report_engine import build_full_admin_report, summary_preview_rows, prepare_report_db, report_data_diagnostics

@st.cache_data(show_spinner=False, ttl=300)
def build_full_admin_report_cached(db_payload_json: str, member_id: str):
    """Cache final report bytes so UI-only actions do not regenerate the Excel file."""
    return build_full_admin_report(json.loads(db_payload_json), member_id)

st.set_page_config(page_title="Final Assessment Report", page_icon="💚", layout="wide", initial_sidebar_state="collapsed")
inject_global_styles(); apply_luxe_theme(); require_admin(); utility_logout_bar(); render_back_to_top()

mid = st.session_state.get("selected_member_id")
if not mid:
    st.switch_page("pages/11_Evaluation_Status.py")

render_page_nav("Final Assessment Report", back_page="pages/11_Evaluation_Status.py", location="top")

db_raw = load_db()
selected_instance_id = st.session_state.get('selected_instance_id')
db, report_diag = prepare_report_db(db_raw, mid, selected_instance_id)
selected_instance_id = report_diag.get("selected_instance_id", selected_instance_id or "")

users = {u["id"]: u for u in db.get("users", [])}
member = users.get(mid, {})
wf = get_workflow(mid)
admin_assessment = get_admin_assessment(mid, selected_instance_id)
final_report_ready = is_instance_final_report_ready(mid, selected_instance_id)
member_name = member.get("name") or member.get("email") or "Selected member"

if not (admin_assessment and final_report_ready):
    compact_topbar(
        "Final Assessment Report",
        "Locked until Admin Assessment is completed.",
        "Admin report engine"
    )
    card_start()
    st.warning("Final Assessment Report will be available only after the Admin Assessment page is filled and 'Save and Generate Final Report' is completed.")
    st.markdown(
        """
        <div class='info-banner'>
          <b>Next step:</b><br>
          Go to <b>Fill Admin Page</b>, complete/save the admin assessment, and click <b>Save and Generate Final Report</b>. After that, this report will unlock.
        </div>
        """,
        unsafe_allow_html=True,
    )
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Go to Fill Admin Page", type="primary", use_container_width=True):
            st.switch_page("pages/13_Admin_Assessment_Form.py")
    with c2:
        if st.button("Back to Evaluation Status", use_container_width=True):
            st.switch_page("pages/11_Evaluation_Status.py")
    card_end()
    render_page_nav("Final Assessment Report", back_page="pages/11_Evaluation_Status.py", location="bottom")
    st.stop()

compact_topbar(
    "Final Assessment Report",
    f"Final report for {member_name}. The download action is placed first for faster user completion.{ ' Instance: ' + selected_instance_id if selected_instance_id else ''}",
    "Admin report engine"
)

selected_systems, subheaders, findings = summary_preview_rows(db, mid)

stat_grid([
    {"label": "NSP1 Used", "value": report_diag.get("nsp1_answer_count", 0), "note": report_diag.get("nsp_source", "source")},
    {"label": "NSP2 Used", "value": report_diag.get("nsp2_answer_count", 0), "note": f"Instance: {report_diag.get('selected_instance_id','') or 'legacy'}"},
    {"label": "Digestive Score", "value": report_diag.get("digestive_score", 0), "note": "NSP system score"},
    {"label": "Final Status", "value": "Ready" if final_report_ready else "Draft", "note": "Instance/workflow state"},
])


# User-first priority action: show the download button before explanatory structure.
safe_name = (member.get("name") or "member").replace(" ", "_").replace("/", "_")
# Build once and reuse. This prevents the Final Report page from feeling slow
# when the user interacts with lightweight sections below.
db_payload_json = json.dumps(db, sort_keys=True, default=str)
final_bytes = build_full_admin_report_cached(db_payload_json, mid)

st.download_button(
    "⬇ Download Final Assessment Report — Excel, 3 Tabs",
    data=final_bytes,
    file_name=f"{safe_name}_final_assessment_report_3_tabs.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    type="primary",
    use_container_width=True,
)

st.markdown("<div class='hm-v75-diagnostics-action'>", unsafe_allow_html=True)
if "show_report_data_diagnostics" not in st.session_state:
    st.session_state["show_report_data_diagnostics"] = False

diag_label = "Hide report data diagnostics" if st.session_state["show_report_data_diagnostics"] else "Show report data diagnostics"
if st.button(diag_label, key="toggle_report_data_diagnostics", use_container_width=True):
    st.session_state["show_report_data_diagnostics"] = not st.session_state["show_report_data_diagnostics"]
    st.rerun()
st.markdown("</div>", unsafe_allow_html=True)

if st.session_state.get("show_report_data_diagnostics"):
    st.markdown(
        f"""
        <div class='hm-v75-diagnostics-card'>
          <div class='hm-v75-diagnostics-title'>Report data diagnostics</div>
          <div class='hm-v75-diagnostics-grid'>
            <div><b>NSP Source</b><br><span>{report_diag.get('nsp_source')}</span></div>
            <div><b>Selected Instance</b><br><span>{report_diag.get('selected_instance_id') or 'legacy/latest'}</span></div>
            <div><b>NSP1 answers used</b><br><span>{report_diag.get('nsp1_answer_count')}</span></div>
            <div><b>NSP2 answers used</b><br><span>{report_diag.get('nsp2_answer_count')}</span></div>
            <div><b>Digestive score</b><br><span>{report_diag.get('digestive_score')}</span></div>
            <div><b>Legacy NSP1 / NSP2 counts</b><br><span>{report_diag.get('legacy_nsp1_answer_count')} / {report_diag.get('legacy_nsp2_answer_count')}</span></div>
            <div><b>Instance NSP1 / NSP2 counts</b><br><span>{report_diag.get('instance_nsp1_answer_count')} / {report_diag.get('instance_nsp2_answer_count')}</span></div>
            <div><b>Admin Source</b><br><span>{report_diag.get('admin_source', 'legacy')}</span></div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

card_start()
st.subheader("Selected top systems preview")
if not selected_systems:
    st.info("No NSP system score available yet.")
else:
    for idx, (system, score) in enumerate(selected_systems, start=1):
        st.markdown(f"**{idx}. {system}** — NSP System Score: `{score}`")
card_end()

card_start()
st.subheader("Final summary findings preview")
if not findings:
    st.info("No score 2 or 3 findings available for the selected top systems yet.")
else:
    for r in findings[:50]:
        st.markdown(f"- **{r['System']} → {r['Subheader']}**: {r['Question']} — **Score {r['Score']}**")
    if len(findings) > 50:
        st.caption(f"Showing first 50 of {len(findings)} findings. Download the final report for the full list.")
card_end()

# Supporting information goes last, per client feedback.
# Keep this section lightweight. Do not use a toggle/expander here because it causes a Streamlit rerun.
st.markdown("<div class='hm-structure-section-lite'></div>", unsafe_allow_html=True)
card_start()
st.markdown(
    """
    <div class='hm-lite-structure-card'>
      <div class='hm-lite-structure-title'>Final report structure</div>
      <div class='hm-lite-structure-subtitle'>
        Lightweight reference only. Detailed Excel content is available in the downloaded final report.
      </div>
      <div class='hm-lite-pill-row'>
        <span>Tab 1: All Details</span>
        <span>Tab 2: All 2 &amp; 3 Elements</span>
        <span>Tab 3: Final Summary</span>
      </div>
      <div class='hm-lite-note'>
        Scoring remains standardized: NSP Systems Rating selects the top systems; Admin Assessment scores structure findings inside those systems.
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)
card_end()

render_page_nav("Final Assessment Report", back_page="pages/11_Evaluation_Status.py", location="bottom")
