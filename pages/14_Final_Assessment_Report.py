import streamlit as st
import copy
from components.guards import require_admin
from components.ui_common import inject_global_styles, apply_luxe_theme, topbar, card_start, card_end, utility_logout_bar, stat_grid
from components.db import load_db, get_workflow, get_admin_assessment
from components.report_engine import build_full_admin_report, summary_preview_rows

st.set_page_config(page_title="Final Assessment Report", page_icon="💚", layout="wide", initial_sidebar_state="collapsed")
inject_global_styles(); apply_luxe_theme(); require_admin(); utility_logout_bar()

mid = st.session_state.get("selected_member_id")
if not mid:
    st.switch_page("pages/11_Evaluation_Status.py")

db = load_db()
selected_instance_id = st.session_state.get('selected_instance_id')
if selected_instance_id:
    db = copy.deepcopy(db)
    inst_resp = db.get('assessment_instance_responses', {}).get(selected_instance_id, {})
    if inst_resp:
        db.setdefault('nsp1_responses', {})[mid] = inst_resp.get('nsp1', db.get('nsp1_responses', {}).get(mid, {}))
        db.setdefault('nsp2_responses', {})[mid] = inst_resp.get('nsp2', db.get('nsp2_responses', {}).get(mid, {}))
users = {u["id"]: u for u in db.get("users", [])}
member = users.get(mid, {})
wf = get_workflow(mid)
admin_assessment = get_admin_assessment(mid)


if not (admin_assessment and wf.get("final_report_ready")):
    topbar(
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
    if st.button("Go to Fill Admin Page", type="primary", use_container_width=True):
        st.switch_page("pages/13_Admin_Assessment_Form.py")
    if st.button("Back to Evaluation Status", use_container_width=True):
        st.switch_page("pages/11_Evaluation_Status.py")
    card_end()
    st.stop()

topbar(
    "Final Assessment Report",
    f"Three-tab final report using NSP Systems Rating + Admin Assessment findings.{' Instance: ' + selected_instance_id if selected_instance_id else ''}",
    "Admin report engine"
)

selected_systems, subheaders, findings = summary_preview_rows(db, mid)

stat_grid([
    {"label": "Selected Systems", "value": len(selected_systems), "note": "Top 3 / Top 4 by NSP score"},
    {"label": "Final Findings", "value": len(findings), "note": "Admin items scored 2 or 3"},
    {"label": "Admin Assessment", "value": "Available" if admin_assessment else "Pending", "note": "5 admin sections"},
    {"label": "Final Status", "value": "Ready" if wf.get("final_report_ready") else "Draft", "note": "Workflow state"},
])

card_start()
st.subheader("Final report structure")
st.markdown(
    """
    <div class='info-banner'>
      <b>Final Report has 3 Excel tabs:</b><br>
      <b>1. All Details</b> — complete captured data including profile, workflow, LAF, NSP, NSP Systems Rating, Admin Assessment and Body-Mind where available.<br>
      <b>2. All 2 &amp; 3 Elements</b> — every Admin Assessment element scored 2 or 3 across all systems.<br>
      <b>3. Final Summary</b> — only the top 3 / top 4 systems based on NSP Systems Rating, with selected admin findings sorted by score 3 first, then 2.
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class='warning-banner'>
      <b>Standardized score logic:</b><br>
      The NSP Systems Rating Score is now the same score used in Partial and Final reports. Admin Assessment scores do not replace the system score; they structure the findings inside the selected top systems.
    </div>
    """,
    unsafe_allow_html=True,
)

if not admin_assessment:
    st.warning("Admin assessment has not been completed yet. Final report can still be downloaded, but final findings may be limited.")
card_end()

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

card_start()
st.subheader("Download final report")
safe_name = (member.get("name") or "member").replace(" ", "_").replace("/", "_")
final_bytes = build_full_admin_report(db, mid)

st.download_button(
    "Download Final Assessment Report Excel - 3 Tabs",
    data=final_bytes,
    file_name=f"{safe_name}_final_assessment_report_3_tabs.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    use_container_width=True,
)
card_end()

if st.button("Back to Evaluation Status"):
    st.switch_page("pages/11_Evaluation_Status.py")