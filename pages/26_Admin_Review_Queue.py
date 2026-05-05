import streamlit as st
import pandas as pd
from components.guards import require_admin
from components.ui_common import inject_global_styles, apply_luxe_theme, topbar, card_start, card_end, utility_logout_bar, stat_grid
from components.assessment_instances import list_review_queue
from components.db import get_workflow
from components.flash import render_system_message

st.set_page_config(page_title="Admin Review Queue", page_icon="💚", layout="wide", initial_sidebar_state="collapsed")
inject_global_styles(); apply_luxe_theme(); require_admin(); utility_logout_bar()

topbar("Admin Review Queue", "Review initial assessments and reassessments separately.", "Admin workflow")
render_system_message()

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
        c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
        with c1:
            st.markdown(f"**{row['member_name']}** — Instance {row['instance_number']} ({row['instance_type']})")
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
            wf = get_workflow(row["member_id"])
            final_unlocked = bool(wf.get("final_report_ready"))
            if st.button("Final Report", key=f"fr_{row['instance_id']}", use_container_width=True, disabled=not final_unlocked):
                st.session_state["selected_member_id"] = row["member_id"]
                st.session_state["selected_instance_id"] = row["instance_id"]
                st.switch_page("pages/14_Final_Assessment_Report.py")
            if not final_unlocked:
                st.caption("Locked until Admin Assessment is completed.")
card_end()

if st.button("Back to Dashboard"):
    st.switch_page("pages/10_Admin_Dashboard.py")