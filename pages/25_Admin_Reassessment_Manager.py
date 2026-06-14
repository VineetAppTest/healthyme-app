import streamlit as st
from datetime import date, timedelta
from components.guards import require_admin
from components.ui_common import inject_global_styles, apply_luxe_theme, topbar, card_start, card_end, utility_logout_bar, stat_grid, render_back_to_top, inject_keepalive_guard_v96_11
from components.db import list_members, get_workflow, load_db, get_admin_assessment, manually_unlock_body_mind_after_finalization, clear_body_mind_activation, sync_member_finalization_state, has_explicit_body_mind_access
from components.assessment_instances import get_assessment_instances, create_reassessment_request
from components.flash import set_system_message, render_system_message

st.set_page_config(page_title="Task Request Manager", page_icon="💚", layout="wide", initial_sidebar_state="collapsed")
inject_global_styles(); apply_luxe_theme(); require_admin(); utility_logout_bar(); inject_keepalive_guard_v96_11(); render_back_to_top()

st.markdown("""
<style>
/* v96.12 compact Task Request Manager with inline Body-Mind control */
.block-container{padding-top:.35rem!important;max-width:1120px!important;}
.hero-shell{margin:.45rem 0 .6rem 0!important;padding:.85rem 1rem!important;}
.hero-title{font-size:1.65rem!important;}
.hero-subtitle{font-size:.9rem!important;margin-top:.15rem!important;}
.kpi-grid{margin:.1rem 0 .45rem 0!important;gap:.42rem!important;}
.kpi-card{padding:.55rem .68rem!important;border-radius:13px!important;}
.kpi-value{font-size:1.18rem!important;}
.kpi-label{font-size:.64rem!important;}
.kpi-note{font-size:.68rem!important;}
.hm-task-card-compact{font-size:.86rem;line-height:1.26;}
.hm-task-card-compact div[data-testid="stCheckbox"]{margin-bottom:.18rem!important;}
.hm-task-card-compact div[data-testid="stCheckbox"] label p{font-size:.88rem!important;}
.hm-task-card-compact div[data-testid="stTextArea"], .hm-task-card-compact div[data-testid="stDateInput"]{margin-bottom:.28rem!important;}
.hm-task-card-compact textarea{min-height:70px!important;}
.hm-bodymind-control-box{background:#FFFDF8;border:1px solid #E5D2A9;border-radius:14px;padding:.7rem .8rem;margin-top:.55rem;}
.hm-bodymind-control-title{color:#064E3B;font-weight:900;margin:0 0 .4rem 0;font-size:1rem;}
.hm-bodymind-mini-grid{display:grid;grid-template-columns:1fr 1fr;gap:.35rem;margin:.2rem 0 .55rem 0;}
.hm-bodymind-mini{border:1px solid #E5D2A9;background:#fff;border-radius:10px;padding:.45rem .5rem;}
.hm-bodymind-mini b{display:block;color:#064E3B;font-size:.9rem;line-height:1.1;}
.hm-bodymind-mini span{display:block;color:#5B675D;font-size:.68rem;margin-top:.12rem;}
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

wf = get_workflow(member_id)
if wf.get("admin_completed") or wf.get("final_report_ready") or wf.get("workflow_status") == "finalized":
    wf = sync_member_finalization_state(member_id, body_mind_unlock=None)
explicit_body_mind_access = has_explicit_body_mind_access(member_id)
if explicit_body_mind_access:
    wf["body_mind_unlocked"] = True
admin_assessment = get_admin_assessment(member_id)
admin_final_completed = bool(wf.get("admin_completed")) or bool(wf.get("final_report_ready"))
body_response = load_db().get("body_mind_responses", {}).get(member_id, {})
body_mind_active = bool(wf.get("body_mind_unlocked")) or explicit_body_mind_access

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
        task_nsp1 = st.checkbox("NSP Page 1", key="v96_12_task_nsp1", disabled=not can_create)
    with c2:
        task_nsp2 = st.checkbox("NSP Page 2", key="v96_12_task_nsp2", disabled=not can_create)
    with c3:
        task_body_mind = st.checkbox("Body-Mind Connection", key="v96_12_task_body_mind", disabled=not can_create)

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

    st.markdown("<div class='hm-bodymind-control-box'>", unsafe_allow_html=True)
    st.markdown("<div class='hm-bodymind-control-title'>Body-Mind Control</div>", unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class='hm-bodymind-mini-grid'>
          <div class='hm-bodymind-mini'><b>{'Active' if body_mind_active else 'Hidden'}</b><span>Member access</span></div>
          <div class='hm-bodymind-mini'><b>{'Completed' if wf.get('body_mind_completed') else 'Pending'}</b><span>Member progress</span></div>
          <div class='hm-bodymind-mini'><b>{'Yes' if admin_final_completed else 'No'}</b><span>Final report/admin complete</span></div>
          <div class='hm-bodymind-mini'><b>{'Available' if body_response else 'No response'}</b><span>Stored response</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if body_mind_active:
        if st.button("Disable Body-Mind Visibility", key="disable_body_mind_v96_12", use_container_width=True):
            clear_body_mind_activation(member_id)
            set_system_message("Body-Mind Connection disabled for this member.", "warning")
            st.rerun()
    else:
        if st.button("Activate Body-Mind Connection", key="activate_body_mind_v96_12", type="primary", use_container_width=True, disabled=not admin_final_completed):
            ok, msg = manually_unlock_body_mind_after_finalization(member_id)
            set_system_message(msg, "success" if ok else "error", celebrate=ok)
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

if st.button("Back to Dashboard"):
    st.switch_page("pages/10_Admin_Dashboard.py")
