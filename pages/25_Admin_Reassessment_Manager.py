import streamlit as st
from datetime import date, timedelta
from components.guards import require_admin
from components.ui_common import inject_global_styles, apply_luxe_theme, topbar, card_start, card_end, utility_logout_bar, stat_grid, render_back_to_top, inject_keepalive_guard_v96_11
from components.db import list_members
from components.assessment_instances import get_assessment_instances, create_reassessment_request
from components.flash import set_system_message, render_system_message

st.set_page_config(page_title="Task Request Manager", page_icon="💚", layout="wide", initial_sidebar_state="collapsed")
inject_global_styles(); apply_luxe_theme(); require_admin(); utility_logout_bar(); inject_keepalive_guard_v96_11(); render_back_to_top()

st.markdown("""
<style>
/* v96.11 compact Task Request Manager */
.block-container{padding-top:.35rem!important;max-width:1120px!important;}
.hero-shell{margin:.45rem 0 .65rem 0!important;padding:.9rem 1.05rem!important;}
.hero-title{font-size:1.75rem!important;}
.hero-subtitle{font-size:.92rem!important;margin-top:.2rem!important;}
.kpi-grid{margin:.15rem 0 .55rem 0!important;gap:.45rem!important;}
.kpi-card{padding:.65rem .75rem!important;border-radius:14px!important;}
.kpi-value{font-size:1.3rem!important;}
.kpi-label{font-size:.68rem!important;}
.kpi-note{font-size:.72rem!important;}
.hm-task-card-compact{font-size:.88rem;line-height:1.32;}
.hm-task-card-compact div[data-testid="stCheckbox"]{margin-bottom:.2rem!important;}
.hm-task-card-compact div[data-testid="stCheckbox"] label p{font-size:.9rem!important;}
.hm-task-card-compact div[data-testid="stTextArea"], .hm-task-card-compact div[data-testid="stDateInput"]{margin-bottom:.35rem!important;}
.hm-task-card-compact textarea{min-height:78px!important;}
.hm-bodymind-control-box{background:#FFFDF8;border:1px solid #E5D2A9;border-radius:14px;padding:.75rem .85rem;margin-top:.65rem;}
.hm-bodymind-control-box b{color:#064E3B;}
.hm-bodymind-control-box p{font-size:.82rem;color:#4B5A57;margin:.2rem 0 .6rem 0;}
</style>
""", unsafe_allow_html=True)

topbar("Task Request Manager", "Allocate NSP Page 1, NSP Page 2 and/or Body-Mind Connection as member tasks.", "Admin task request")
render_system_message()

def task_title(task_key):
    return {
        "nsp1": "NSP Page 1",
        "nsp2": "NSP Page 2",
        "body_mind": "Body-Mind Connection",
    }.get(str(task_key), str(task_key))

def is_instance_open(inst):
    return (not inst.get("submitted_for_review")) and inst.get("status") in ["pending", "in_progress"]

def is_instance_complete_enough(inst):
    if not inst:
        return True
    status = str(inst.get("status", "")).lower()
    if inst.get("submitted_for_review"):
        return True
    if status in ["review_required", "admin_completed", "final_report_ready", "finalized", "completed", "complete"]:
        return True
    return False

members = list_members()
if not members:
    st.info("No members available.")
    st.stop()

selected = st.selectbox("Select member", [f"{m['id']} — {m['name']} — {m['email']}" for m in members])
member_id = selected.split(" — ")[0]
member = next(m for m in members if m["id"] == member_id)
instances = get_assessment_instances(member_id)
instances_sorted = sorted(instances, key=lambda x: x.get("instance_number", 0))

latest_instance = instances_sorted[-1] if instances_sorted else None
open_task_requests = [
    i for i in instances
    if i.get("instance_type") == "Task Request" and is_instance_open(i)
]
current_assessment_incomplete = bool(latest_instance) and not is_instance_complete_enough(latest_instance)

stat_grid([
    {"label": "Member", "value": member["name"], "note": member["email"]},
    {"label": "Instances", "value": len(instances), "note": "History"},
    {"label": "Open Request", "value": "Yes" if open_task_requests else "No", "note": "Pending"},
    {"label": "Next Instance", "value": max([i.get("instance_number", 0) for i in instances] + [0]) + 1, "note": "If created"},
])

left, right = st.columns([1, 1], gap="large")

with left:
    card_start()
    st.markdown("<div class='hm-task-card-compact'>", unsafe_allow_html=True)
    st.subheader("Create Task Request")

    if current_assessment_incomplete:
        st.warning("Current assessment/instance is not completed yet. Complete and submit it before allocating a new task.")
        can_create = False
    elif open_task_requests:
        st.warning("This member already has an open task request. Ask the member to complete it before creating another one.")
        can_create = False
    else:
        can_create = True

    c1, c2, c3 = st.columns(3)
    with c1:
        task_nsp1 = st.checkbox("NSP Page 1", key="v96_11_task_nsp1", disabled=not can_create)
    with c2:
        task_nsp2 = st.checkbox("NSP Page 2", key="v96_11_task_nsp2", disabled=not can_create)
    with c3:
        task_body_mind = st.checkbox("Body-Mind Connection", key="v96_11_task_body_mind", disabled=not can_create)

    requested_pages = []
    if task_nsp1:
        requested_pages.append("nsp1")
    if task_nsp2:
        requested_pages.append("nsp2")
    if task_body_mind:
        requested_pages.append("body_mind")

    due = st.date_input("Due date", value=date.today() + timedelta(days=14), disabled=not can_create)
    note = st.text_area(
        "Optional note to member",
        placeholder="Example: Please complete the allocated task before your follow-up call.",
        disabled=not can_create,
    )

    if st.button("Send Task Request", type="primary", use_container_width=True, disabled=(not can_create or not bool(requested_pages))):
        inst, created = create_reassessment_request(
            member_id,
            requested_pages,
            due_date=due.isoformat(),
            admin_note=note.strip(),
            admin_id=st.session_state.get("user_id", "admin"),
        )
        task_names = ", ".join(task_title(p) for p in requested_pages)
        if created:
            set_system_message(f"Task request created for {member['name']} — Instance {inst.get('instance_number')} ({task_names}).", "success")
        else:
            set_system_message("An open task request already exists for this member.", "warning")
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)
    card_end()

with right:
    card_start()
    st.subheader("Assessment history")
    if not instances_sorted:
        st.info("No assessment history available.")
    else:
        for inst in instances_sorted:
            tasks = ", ".join(task_title(p) for p in inst.get("requested_pages", [])) or "-"
            st.markdown(
                f"""
                **Instance {inst.get('instance_number')} — {inst.get('instance_type')}**  
                Tasks: {tasks}  
                Task allocation date: `{inst.get('created_date') or '-'}`  
                Status: `{inst.get('status')}` | Submitted: `{inst.get('submitted_date') or '-'}`
                """
            )
    card_end()

    st.markdown(
        """
        <div class='hm-bodymind-control-box'>
          <b>Body-Mind Control</b>
          <p>Admin-only access control for activating or reviewing Body-Mind Connection access.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("Open Body-Mind Control", key="open_body_mind_control_v96_11", use_container_width=True):
        st.switch_page("pages/23_Admin_Body_Mind_Control.py")

if st.button("Back to Dashboard"):
    st.switch_page("pages/10_Admin_Dashboard.py")
