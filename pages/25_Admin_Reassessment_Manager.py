import streamlit as st
from datetime import date, timedelta
from components.guards import require_admin
from components.ui_common import inject_global_styles, apply_luxe_theme, topbar, card_start, card_end, utility_logout_bar, stat_grid, render_build_text_v12, render_back_to_top
from components.db import list_members
from components.assessment_instances import get_assessment_instances, create_reassessment_request
from components.flash import set_system_message, render_system_message

st.set_page_config(page_title="Task Request Manager", page_icon="💚", layout="wide", initial_sidebar_state="collapsed")
inject_global_styles(); apply_luxe_theme(); require_admin(); utility_logout_bar(); render_back_to_top()

st.markdown("<div class='info-banner'><b>Body-Mind Access:</b> Body-Mind Control is hidden from the dashboard and available here for admin access management.</div>", unsafe_allow_html=True)
st.page_link("pages/23_Admin_Body_Mind_Control.py", label="Open Body-Mind Control", icon=":material/psychology:", use_container_width=True)

topbar("Task Request Manager", "Allocate NSP Page 1, NSP Page 2 and/or Body-Mind Connection as member tasks.", "Admin task request")
render_system_message()

members = list_members()
if not members:
    st.info("No members available.")
    st.stop()

selected = st.selectbox("Select member", [f"{m['id']} — {m['name']} — {m['email']}" for m in members])
member_id = selected.split(" — ")[0]
member = next(m for m in members if m["id"] == member_id)
instances = get_assessment_instances(member_id)

open_reassessment = [
    i for i in instances
    if i.get("instance_type") == "Task Request" and not i.get("submitted_for_review") and i.get("status") in ["pending", "in_progress"]
]

stat_grid([
    {"label": "Member", "value": member["name"], "note": member["email"]},
    {"label": "Instances", "value": len(instances), "note": "Assessment history"},
    {"label": "Open Request", "value": "Yes" if open_reassessment else "No", "note": "Pending reassessment"},
    {"label": "Next Instance", "value": max([i.get("instance_number", 0) for i in instances] + [0]) + 1, "note": "If created"},
])

card_start()
st.subheader("Assessment history")
for inst in sorted(instances, key=lambda x: x.get("instance_number", 0)):
    st.markdown(
        f"""
        **Instance {inst.get('instance_number')} — {inst.get('instance_type')}**  
        Tasks: {', '.join(['NSP Page 1' if p=='nsp1' else 'NSP Page 2' if p=='nsp2' else 'Body-Mind Connection' if p=='body_mind' else p for p in inst.get('requested_pages', [])])}  
        Status: `{inst.get('status')}` | Submitted: `{inst.get('submitted_date') or '-'}`
        """
    )
card_end()

card_start()
st.subheader("Create Task Request")
if open_reassessment:
    st.warning("This member already has an open task request. Ask the member to complete it before creating another one.")
else:
    st.markdown("#### Select Task Type(s)")
    task_nsp1 = st.checkbox("NSP Page 1", key="v96_2_task_nsp1")
    task_nsp2 = st.checkbox("NSP Page 2", key="v96_2_task_nsp2")
    task_body_mind = st.checkbox("Body-Mind Connection", key="v96_2_task_body_mind")

    requested_pages = []
    if task_nsp1:
        requested_pages.append("nsp1")
    if task_nsp2:
        requested_pages.append("nsp2")
    if task_body_mind:
        requested_pages.append("body_mind")

    due = st.date_input("Due date", value=date.today() + timedelta(days=14))
    note = st.text_area("Optional note to member", placeholder="Example: Please complete the allocated task before your follow-up call.")

    if not requested_pages:
        st.info("Select at least one task before creating the request.")

    if st.button("Send Task Request", type="primary", use_container_width=True, disabled=not bool(requested_pages)):
        inst, created = create_reassessment_request(
            member_id,
            requested_pages,
            due_date=due.isoformat(),
            admin_note=note.strip(),
            admin_id=st.session_state.get("user_id", "admin"),
        )
        task_names = ", ".join(["NSP Page 1" if p == "nsp1" else "NSP Page 2" if p == "nsp2" else "Body-Mind Connection" for p in requested_pages])
        if created:
            set_system_message(f"Task request created for {member['name']} — Instance {inst.get('instance_number')} ({task_names}).", "success")
        else:
            set_system_message("An open task request already exists for this member.", "warning")
        st.rerun()
card_end()

if st.button("Back to Dashboard"):
    st.switch_page("pages/10_Admin_Dashboard.py")

