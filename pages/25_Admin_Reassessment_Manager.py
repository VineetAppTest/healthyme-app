import streamlit as st
from datetime import date, timedelta
from components.guards import require_admin
from components.ui_common import inject_global_styles, apply_luxe_theme, topbar, card_start, card_end, utility_logout_bar, stat_grid
from components.db import list_members
from components.assessment_instances import get_assessment_instances, create_reassessment_request
from components.flash import set_system_message, render_system_message

st.set_page_config(page_title="Reassessment Manager", page_icon="💚", layout="wide", initial_sidebar_state="collapsed")
inject_global_styles(); apply_luxe_theme(); require_admin(); utility_logout_bar()

topbar("Reassessment Manager", "Request NSP Page 1, NSP Page 2, or both for follow-up assessment.", "Admin reassessment")
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
    if i.get("instance_type") == "Reassessment" and not i.get("submitted_for_review") and i.get("status") in ["pending", "in_progress"]
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
        Pages: {', '.join(['NSP Page 1' if p=='nsp1' else 'NSP Page 2' for p in inst.get('requested_pages', [])])}  
        Status: `{inst.get('status')}` | Submitted: `{inst.get('submitted_date') or '-'}`
        """
    )
card_end()

card_start()
st.subheader("Create reassessment request")
if open_reassessment:
    st.warning("This member already has an open reassessment request. Ask the member to complete it before creating another one.")
else:
    option = st.radio(
        "What should the member refill?",
        ["Both NSP Page 1 and NSP Page 2", "NSP Page 1 only", "NSP Page 2 only"],
        horizontal=False,
    )
    if option == "Both NSP Page 1 and NSP Page 2":
        requested_pages = ["nsp1", "nsp2"]
    elif option == "NSP Page 1 only":
        requested_pages = ["nsp1"]
    else:
        requested_pages = ["nsp2"]

    due = st.date_input("Due date", value=date.today() + timedelta(days=14))
    note = st.text_area("Optional note to member", placeholder="Example: Please complete this 2-month reassessment before your follow-up call.")

    if st.button("Send Reassessment Request", type="primary", use_container_width=True):
        inst, created = create_reassessment_request(
            member_id,
            requested_pages,
            due_date=due.isoformat(),
            admin_note=note.strip(),
            admin_id=st.session_state.get("user_id", "admin"),
        )
        if created:
            set_system_message(f"Reassessment request created for {member['name']} — Instance {inst.get('instance_number')}.", "success")
        else:
            set_system_message("An open reassessment request already exists for this member.", "warning")
        st.rerun()
card_end()

if st.button("Back to Dashboard"):
    st.switch_page("pages/10_Admin_Dashboard.py")