import streamlit as st
from components.guards import require_member
from components.ui_common import inject_global_styles, apply_luxe_theme, topbar, card_start, card_end, stat_grid, utility_logout_bar, render_build_text_v12, format_local_ts, render_back_to_top
from components.db import get_workflow, get_member_messages, sync_body_mind_after_admin_completion, hard_sync_body_mind_if_requested, has_explicit_body_mind_access, mark_member_message_read, mark_member_message_read, auto_archive_expired_nutritionist_messages
from components.assessment_instances import get_current_assessment_instance
from components.flash import render_system_message, set_system_message

st.set_page_config(page_title="Member Home", page_icon="💚", layout="wide", initial_sidebar_state="collapsed")
inject_global_styles(); apply_luxe_theme(); require_member(); utility_logout_bar(); render_back_to_top()

st.markdown("""
<style>
/* --- v94.4 Body-Mind button normalization --- */
.hm-bodymind-btn-anchor + div [data-testid="stButton"] > button,
.hm-bodymind-btn-anchor + div .stButton > button{
  background:#FFFFFF!important;
  color:#064E3B!important;
  border:1.5px solid #CDBB8F!important;
  border-radius:14px!important;
  box-shadow:0 4px 12px rgba(25,36,31,.06)!important;
}
.hm-bodymind-btn-anchor + div [data-testid="stButton"] > button *,
.hm-bodymind-btn-anchor + div .stButton > button *{
  color:#064E3B!important;
}
</style>
""", unsafe_allow_html=True)


user_id = st.session_state["user_id"]
wf = get_workflow(user_id)
# v32 hard sync:
# If finalization is complete and manual activation request exists, repair body_mind_unlocked.
if (wf.get("admin_completed") or wf.get("final_report_ready") or wf.get("workflow_status") == "finalized") and wf.get("body_mind_activation_requested") and not wf.get("body_mind_unlocked"):
    hard_sync_body_mind_if_requested(user_id)
    wf = get_workflow(user_id)

current_instance = get_current_assessment_instance(user_id)



def should_show_body_mind_next_step_v96_6(wf_state, current_inst):
    """Body-Mind remains a member next-step until completed.

    It should be visible under Your next steps if:
    - it is explicitly requested in the active task instance, OR
    - it is unlocked/activated for the member, OR
    - admin/final review is complete and Body-Mind is still not completed.
    """
    if bool(wf_state.get("body_mind_completed")) or bool(current_inst.get("body_mind_completed")):
        return False
    requested = current_inst.get("requested_pages", []) or []
    if "body_mind" in requested:
        return True
    if bool(wf_state.get("body_mind_unlocked")) or bool(wf_state.get("admin_completed")):
        return True
    return False

def task_title_v96_2(task_key):
    return {
        "nsp1": "NSP Page 1",
        "nsp2": "NSP Page 2",
        "body_mind": "Body-Mind Connection",
    }.get(str(task_key), str(task_key))

def task_status_done_v96_2(instance, wf_state, task_key):
    if task_key == "nsp1":
        return bool(instance.get("nsp1_completed"))
    if task_key == "nsp2":
        return bool(instance.get("nsp2_completed"))
    if task_key == "body_mind":
        return bool(instance.get("body_mind_completed")) or bool(wf_state.get("body_mind_completed"))
    return False

# v31: workflow finalization overrides stale instance review status.
workflow_finalized = bool(wf.get("admin_completed")) or bool(wf.get("final_report_ready")) or wf.get("workflow_status") == "finalized"
requested_pages = current_instance.get("requested_pages", ["nsp1", "nsp2"])
is_task_instance = current_instance.get("instance_type") in ["Task Request", "Reassessment"] and not current_instance.get("submitted_for_review")
is_reassessment = is_task_instance

topbar("Member Home", "Continue your wellness assessment and access your tools.", "Member experience")
render_system_message()
auto_archive_expired_nutritionist_messages(user_id)

messages = get_member_messages(user_id, limit=3)
if messages:
    st.markdown("<div class='hm-nutritionist-message-shell'>", unsafe_allow_html=True)
    st.markdown("<div class='hm-nutritionist-message-title'>Messages from Nutritionist</div>", unsafe_allow_html=True)

    v66_seen_msg_keys = set()
    for msg in messages:
        v66_key = f"{msg.get('member_id','')}|{msg.get('log_date','')}|{' '.join(str(msg.get('message','')).strip().split()).lower()}"
        if v66_key in v66_seen_msg_keys:
            continue
        v66_seen_msg_keys.add(v66_key)
        st.markdown(
            f"""
            <div class='info-banner hm-nutritionist-message-card'>
              <b>{msg.get('subject','Message')}</b><br>
              <small>{format_local_ts(msg.get('ts',''))}</small><br>
              <p>{msg.get('message','')}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Read / Archive message from Nutritionist", key=f"read_msg_{msg.get('id','')}", use_container_width=True):
            ok = mark_member_message_read(user_id, msg.get("id", ""))
            if ok:
                set_system_message("Message archived. You can find it in Daily Food Journal → Nutritionist Notes Archive.", "success")
            else:
                set_system_message("Message could not be archived. Please refresh and try again.", "error")
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

stat_grid([
    {"label": "LAF", "value": "Completed" if wf.get("laf_completed") else "Pending", "note": "Lifestyle intake"},
    {"label": "Current Instance", "value": current_instance.get("instance_number"), "note": current_instance.get("instance_type")},
    {"label": "Requested Tasks", "value": ", ".join([task_title_v96_2(p) for p in requested_pages]), "note": "Current requirement"},
    {"label": "Status", "value": current_instance.get("status", wf.get("workflow_status")).replace("_", " ").title(), "note": "Current stage"},
])


# v96.3: Redundant task-request card removed; details now live under Your next steps.
left, right = st.columns([1.15, .85], gap="large")

with left:
    card_start()
    st.subheader("Your next steps")

    if is_task_instance:
        visible_tasks = [p for p in requested_pages if p in ["nsp1", "nsp2", "body_mind"]]
        if should_show_body_mind_next_step_v96_6(wf, current_instance) and "body_mind" not in visible_tasks:
            visible_tasks.append("body_mind")
        st.markdown(
            f"""
            <div class='info-banner'>
              <b>Nutritionist has allocated a Task.</b><br>
              Task allocation date: <b>{current_instance.get('created_date') or '-'}</b><br>
              Please complete: <b>{', '.join([task_title_v96_2(p) for p in visible_tasks])}</b><br>
              Due date: <b>{current_instance.get('due_date') or 'Not set'}</b><br>
              Note: {current_instance.get('admin_note') or '-'}<br><br>
              LAF is already completed from the original assessment and is not required again.
            </div>
            """,
            unsafe_allow_html=True,
        )

        if not visible_tasks:
            st.warning("No active task is selected for this request.")
        else:
            task_cols = st.columns(max(1, min(3, len(visible_tasks))))
            col_index = 0

            if "nsp1" in visible_tasks:
                with task_cols[col_index]:
                    if st.button("Start NSP Page 1", use_container_width=True):
                        st.switch_page("pages/04_NSP_Page1.py")
                col_index += 1

            if "nsp2" in visible_tasks:
                with task_cols[col_index]:
                    if st.button("Start NSP Page 2", use_container_width=True):
                        st.switch_page("pages/05_NSP_Page2.py")
                col_index += 1

            if "body_mind" in visible_tasks:
                with task_cols[col_index]:
                    body_done = task_status_done_v96_2(current_instance, wf, "body_mind")
                    body_label = "Start Body-Mind Connection" if not body_done else "Body-Mind Completed"
                    if st.button(body_label, use_container_width=True, disabled=body_done):
                        st.switch_page("pages/19_Body_Mind_Connection.py")

    elif not wf.get("laf_completed"):
        if st.button("1. Fill LAF", type="primary", use_container_width=True):
            st.switch_page("pages/03_LAF_Form.py")

    elif current_instance.get("submitted_for_review"):
        st.info("Your latest evaluation has been submitted and is under review.")

    else:
        b1, b2, b3 = st.columns(3)
        with b1:
            if st.button("1. Fill LAF", use_container_width=True):
                st.switch_page("pages/03_LAF_Form.py")
        with b2:
            if st.button("2. Fill NSP Pg 1", use_container_width=True, disabled=("nsp1" not in requested_pages)):
                st.switch_page("pages/04_NSP_Page1.py")
        with b3:
            if st.button("3. Fill NSP Pg 2", use_container_width=True, disabled=("nsp2" not in requested_pages)):
                st.switch_page("pages/05_NSP_Page2.py")

        if should_show_body_mind_next_step_v96_6(wf, current_instance):
            if st.button("Start Body-Mind Connection", use_container_width=True):
                st.switch_page("pages/19_Body_Mind_Connection.py")

    st.divider()
    if st.button("Submit / Status", use_container_width=True):
        st.switch_page("pages/06_Submit_Status.py")

    card_end()

with right:
    card_start()
    st.subheader("Personalized content")

    admin_completed = bool(wf.get("admin_completed"))

    if st.button("My Profile", use_container_width=True):
        st.switch_page("pages/07_My_Profile.py")

    if st.button("Daily Log", use_container_width=True):
        st.switch_page("pages/18_Daily_Log.py")

    if not admin_completed:
        st.markdown(
            "<div class='lock-card'><b>Recipes and exercises are locked until expert review is complete.</b></div>",
            unsafe_allow_html=True,
        )
    else:
        if st.button("Recipe Repository", use_container_width=True):
            st.switch_page("pages/08_Recipe_Repository.py")
        if st.button("Exercise Repository", use_container_width=True):
            st.switch_page("pages/09_Exercise_Repository.py")

    card_end()

# v96.3: Progress/status summary block removed from Member Home because it duplicated member-facing task/action information.
# v96.3: Body-Mind Connection removed from Personalized Content; it appears under Your next steps only when requested.
