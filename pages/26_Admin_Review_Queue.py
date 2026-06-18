import streamlit as st
import pandas as pd
from components.guards import require_admin
from components.ui_common import inject_global_styles, apply_luxe_theme, topbar, card_start, card_end, utility_logout_bar, stat_grid, build_marker_v9, render_build_text_v14, render_back_to_top
from components.assessment_instances import list_review_queue, get_assessment_instances, task_progress_summary_v99
from components.db import get_workflow
from components.flash import render_system_message

st.set_page_config(page_title="Admin Review", page_icon="💚", layout="wide", initial_sidebar_state="collapsed")
inject_global_styles(); apply_luxe_theme(); require_admin(); utility_logout_bar()
render_build_text_v14()


st.markdown("""
<style>
/* v100.0 Admin Review Queue hardening */
.hm-v100-review-card{
  border:1px solid #E5D2A9;
  border-radius:14px;
  background:#FFFDF8;
  padding:.68rem .78rem;
  margin:.45rem 0 .65rem 0;
}
.hm-v100-review-title{
  color:#064E3B;
  font-weight:920;
  font-size:.92rem;
  margin-bottom:.20rem;
}
.hm-v100-review-line{
  color:#334155;
  font-size:.82rem;
  font-weight:720;
  margin:.10rem 0;
}
</style>
""", unsafe_allow_html=True)

topbar("Admin Review", "Review initial assessments and reassessments separately.", "Admin workflow")
render_build_text_v14()
render_system_message()


def review_progress_v100(row):
    try:
        instances = get_assessment_instances(row["member_id"])
        match = next((x for x in instances if x.get("instance_id") == row.get("instance_id")), {})
        return task_progress_summary_v99(match)
    except Exception:
        return {"done": 0, "total": 0, "percent": 0}


queue = list_review_queue()
initial = [r for r in queue if r.get("instance_type") == "Initial Assessment"]
reassess = [r for r in queue if r.get("instance_type") == "Reassessment"]

stat_grid([
    {"label": "Total Pending", "value": len(queue), "note": "Submitted instances"},
    {"label": "Initial Reviews", "value": len(initial), "note": "Initial assessment"},
    {"label": "Reassessments", "value": len(reassess), "note": "Follow-up instances"},
    {"label": "Action", "value": "Open", "note": "Use buttons below"},
])

card_start()
st.subheader("Pending review queue")
if not queue:
    st.info("No assessments are pending review.")
else:
    df = pd.DataFrame(queue)
    st.dataframe(df[["member_name", "email", "instance_number", "instance_type", "requested_pages", "submitted_date", "status"]], use_container_width=True, hide_index=True)

    for row in queue:
        progress_v100 = review_progress_v100(row)
        st.markdown(
            f"""
            <div class='hm-v100-review-card'>
              <div class='hm-v100-review-title'>{row['member_name']} — Instance {row['instance_number']} ({row['instance_type']})</div>
              <div class='hm-v100-review-line'>Requested: {row.get('requested_pages') or '-'} · Progress: {progress_v100.get('done', 0)} of {progress_v100.get('total', 0)} completed</div>
              <div class='hm-v100-review-line'>Submitted: {row.get('submitted_date') or '-'} · Status: {str(row.get('status', '-')).replace('_', ' ').title()}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
        with c1:
            st.caption("Choose the next review action")
        with c2:
            if st.button("Partial Report", key=f"pr_{row['instance_id']}", use_container_width=True):
                st.session_state["selected_member_id"] = row["member_id"]
                st.session_state["selected_instance_id"] = row["instance_id"]
                st.switch_page("pages/12_Partial_Assessment_Report.py")
        with c3:
            if st.button("Admin Page", key=f"ap_{row['instance_id']}", use_container_width=True):
                st.session_state["selected_member_id"] = row["member_id"]
                st.session_state["selected_instance_id"] = row["instance_id"]
                st.switch_page("pages/13_Admin_Assessment_Form.py")
        with c4:
            final_unlocked = bool(row.get("final_report_ready"))
            if st.button("Final Report", key=f"fr_{row['instance_id']}", use_container_width=True, disabled=not final_unlocked):
                st.session_state["selected_member_id"] = row["member_id"]
                st.session_state["selected_instance_id"] = row["instance_id"]
                st.switch_page("pages/14_Final_Assessment_Report.py")
            if not final_unlocked:
                st.caption("Locked until Admin Assessment is completed.")
card_end()

if st.button("Back to Dashboard"):
    st.switch_page("pages/10_Admin_Dashboard.py")

# v101.8: standard bottom navigation
render_page_nav("Admin Review", back_page="pages/10_Admin_Dashboard.py", show_evaluation=False, show_dashboard=True, location="bottom")
render_back_to_top()
