import html

import streamlit as st

from components.assessment_instances import get_current_assessment_instance
from components.auth_session import logout_current_user
from components.db import (
    auto_archive_expired_nutritionist_messages,
    get_member_messages,
    get_workflow,
    hard_sync_body_mind_if_requested,
    list_upcoming_member_schedules,
    mark_member_message_read,
    queue_schedule_acknowledgement_reminders_v104b11,
    schedule_acknowledgement_notice_v104b11,
    schedule_display_status_label_v104b11,
)
from components.flash import render_system_message, set_system_message
from components.guards import require_member
from components.ui_common import (
    apply_luxe_theme,
    card_end,
    card_start,
    format_local_ts,
    inject_global_styles,
    inject_keepalive_guard_v96_11,
    stat_grid,
    topbar,
)


st.set_page_config(page_title="Member Home", page_icon="💚", layout="wide", initial_sidebar_state="collapsed")
inject_global_styles()
apply_luxe_theme()
require_member()


def _esc(value):
    return html.escape(str(value or ""))


def _workflow_finalized(wf_state):
    return bool(wf_state.get("admin_completed")) or bool(wf_state.get("final_report_ready")) or wf_state.get("workflow_status") == "finalized"


def _normalised_requested_pages(instance):
    requested = instance.get("requested_pages", ["nsp1", "nsp2"])
    if isinstance(requested, str):
        return [requested]
    if isinstance(requested, list):
        return requested
    return ["nsp1", "nsp2"]


def should_show_body_mind_next_step_v96_6(wf_state, current_inst):
    if bool(wf_state.get("body_mind_completed")) or bool(current_inst.get("body_mind_completed")):
        return False
    requested = _normalised_requested_pages(current_inst)
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


def _member_email():
    return (
        st.session_state.get("user_email")
        or st.session_state.get("oidc_email")
        or st.session_state.get("email")
        or st.session_state.get("username")
        or "member"
    )


def _render_member_utility_bar():
    identity_col, profile_col, logout_col = st.columns([5.4, 0.72, 1.05], gap="small")
    with identity_col:
        st.markdown(
            f"""
            <div class='hm-member-identity-pill'>
              <span>Signed in as: <b>{_esc(_member_email())}</b></span>
              <span class='hm-member-role-inline'>Active member</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with profile_col:
        st.markdown("<div class='hm-profile-button-anchor'></div>", unsafe_allow_html=True)
        if st.button("👤 Profile", key="hm_top_my_profile", use_container_width=True, help="My Profile"):
            st.switch_page("pages/07_My_Profile.py")
    with logout_col:
        if st.button("Logout", key="hm_top_logout", use_container_width=True):
            logout_current_user()
            st.rerun()


def _render_messages(user_id):
    auto_archive_expired_nutritionist_messages(user_id)
    messages = get_member_messages(user_id, limit=3)
    if not messages:
        return

    st.markdown("<div class='hm-b13-message-shell'>", unsafe_allow_html=True)
    st.markdown("<div class='hm-b13-message-title'>Messages from Nutritionist</div>", unsafe_allow_html=True)
    seen_msg_keys = set()
    for msg in messages:
        msg_key = f"{msg.get('member_id','')}|{msg.get('log_date','')}|{' '.join(str(msg.get('message','')).strip().split()).lower()}"
        if msg_key in seen_msg_keys:
            continue
        seen_msg_keys.add(msg_key)
        st.markdown(
            f"""
            <div class='hm-b13-message-card'>
              <div class='hm-b13-message-subject'>{_esc(msg.get('subject','Message'))}</div>
              <div class='hm-b13-message-date'>{_esc(format_local_ts(msg.get('ts','')))}</div>
              <p class='hm-b13-message-body'>{_esc(msg.get('message',''))}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Read & Archive", key=f"read_msg_{msg.get('id','')}", use_container_width=True):
            ok = mark_member_message_read(user_id, msg.get("id", ""))
            if ok:
                set_system_message("Message archived. You can find it in Daily Food Journal → Nutritionist Notes Archive.", "success")
            else:
                set_system_message("Message could not be archived. Please refresh and try again.", "error")
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


def _render_upcoming_schedules(user_id):
    queue_schedule_acknowledgement_reminders_v104b11(user_id)
    upcoming_schedules = list_upcoming_member_schedules(user_id, limit=5)
    if not upcoming_schedules:
        return

    st.markdown("<div class='hm-nutritionist-message-shell'>", unsafe_allow_html=True)
    st.markdown("<div class='hm-b13-message-title'>Upcoming Schedule</div>", unsafe_allow_html=True)
    for schedule in upcoming_schedules:
        time_text = str(schedule.get("start_time", "") or "")
        if schedule.get("end_time"):
            time_text += f" - {schedule.get('end_time')}"
        notice = schedule_acknowledgement_notice_v104b11(schedule)
        notice_html = f"<div class='hm-v101-schedule-line hm-v104b11-ack-note'>{_esc(notice)}</div>" if notice else ""
        st.markdown(
            f"""
            <div class='hm-v101-schedule-card'>
              <div class='hm-v101-schedule-title'>{_esc(schedule.get('title','Scheduled session'))}<span class='hm-v101-schedule-pill'>{_esc(schedule_display_status_label_v104b11(schedule))}</span></div>
              <div class='hm-v101-schedule-line'>{_esc(schedule.get('schedule_date',''))} · {_esc(time_text)}</div>
              <div class='hm-v101-schedule-line'>Mode: {_esc(schedule.get('mode','-'))} · Link/location: {_esc(schedule.get('location_or_link') or '-')}</div>
              {notice_html}
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)


def _render_task_progress(current_instance, wf, requested_pages):
    visible_tasks = [p for p in requested_pages if p in ["nsp1", "nsp2", "body_mind"]]
    if should_show_body_mind_next_step_v96_6(wf, current_instance) and "body_mind" not in visible_tasks:
        visible_tasks.append("body_mind")

    task_names = ", ".join([task_title_v96_2(p) for p in visible_tasks]) or "-"
    st.markdown(
        f"""
        <div class='info-banner'>
          <b>Nutritionist has allocated a Task.</b><br>
          Task allocation date: <b>{_esc(current_instance.get('created_date') or '-')}</b><br>
          Please complete: <b>{_esc(task_names)}</b><br>
          Due date: <b>{_esc(current_instance.get('due_date') or 'Not set')}</b><br>
          Note: {_esc(current_instance.get('admin_note') or '-')}<br><br>
          LAF is already completed from the original assessment and is not required again.
        </div>
        """,
        unsafe_allow_html=True,
    )

    progress_total = len(visible_tasks)
    progress_done = sum(1 for p in visible_tasks if task_status_done_v96_2(current_instance, wf, p))
    progress_width = int(round((progress_done / progress_total) * 100)) if progress_total else 100
    task_chips = []
    for p in visible_tasks:
        done = task_status_done_v96_2(current_instance, wf, p)
        chip_class = "done" if done else "pending"
        chip_label = "Done" if done else "Pending"
        task_chips.append(f"<span class='hm-v990-task-chip {chip_class}'>{_esc(task_title_v96_2(p))} · {chip_label}</span>")

    st.markdown(
        f"""
        <div class='hm-v990-task-progress'>
          <div class='hm-v990-progress-title'>Task progress: {progress_done} of {progress_total} completed</div>
          <div class='hm-v990-progress-line'><div class='hm-v990-progress-fill' style='width:{progress_width}%;'></div></div>
          <div>{''.join(task_chips)}</div>
          <div class='hm-v990-submit-note'>Use Submit / Status after completing all requested tasks to send this to admin for review.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not visible_tasks:
        st.warning("No active task is selected for this request.")
        return

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
            body_label = "Body Mind Connection" if not body_done else "Body Mind Completed"
            if st.button(body_label, use_container_width=True, disabled=body_done):
                st.switch_page("pages/19_Body_Mind_Connection.py")


def _muted_action(label: str, page: str, key: str, disabled: bool = False):
    st.markdown("<div class='hm-muted-action-anchor'></div>", unsafe_allow_html=True)
    if st.button(label, key=key, use_container_width=True, disabled=disabled):
        st.switch_page(page)


user_id = st.session_state["user_id"]
wf = get_workflow(user_id) or {}
if _workflow_finalized(wf) and wf.get("body_mind_activation_requested") and not wf.get("body_mind_unlocked"):
    hard_sync_body_mind_if_requested(user_id)
    wf = get_workflow(user_id) or {}

current_instance = get_current_assessment_instance(user_id) or {}
requested_pages = _normalised_requested_pages(current_instance)

for _repo_detail_key in ["hm_recipe_selected_id", "hm_recipe_detail_mode", "hm_exercise_selected_id", "hm_exercise_detail_mode"]:
    st.session_state.pop(_repo_detail_key, None)

_render_member_utility_bar()
topbar("Member Home", "Continue your wellness assessment and access your tools.", "Member experience")

st.markdown(
    """
<style>
.hm-member-identity-pill{min-height:2.36rem;display:flex;align-items:center;gap:.42rem;flex-wrap:wrap;color:#64748B;font-size:.80rem;font-weight:760;background:rgba(255,255,255,.70);border:1px solid #E9DFCC;border-radius:999px;padding:.30rem .64rem;}
.hm-member-role-inline{display:inline-flex;align-items:center;justify-content:center;color:#7A5A16;font-size:.68rem;font-weight:900;background:#FFF7E6;border:1px solid #D9C28F;border-radius:999px;padding:.12rem .42rem;line-height:1.1;}
.hm-profile-button-anchor + div [data-testid="stButton"] > button,
.hm-profile-button-anchor + div .stButton > button{min-height:2.18rem!important;max-height:2.18rem!important;border-radius:999px!important;padding:.22rem .52rem!important;font-size:.78rem!important;background:#FFFFFF!important;color:#064E3B!important;border-color:#D8A84E!important;box-shadow:0 4px 10px rgba(6,78,59,.045)!important;line-height:1.05!important;}
.hm-profile-button-anchor + div [data-testid="stButton"] > button *,
.hm-profile-button-anchor + div .stButton > button *{color:#064E3B!important;font-size:.78rem!important;font-weight:900!important;line-height:1.05!important;}
.hm-b13-message-shell{border:1px solid #E3C98E;background:#FFFDF8;border-radius:20px;padding:.85rem .95rem;margin:.60rem 0 1rem 0;box-shadow:0 8px 22px rgba(15,23,42,.045);}
.hm-b13-message-title{color:#064E3B;font-size:1.05rem;font-weight:760;margin-bottom:.50rem;}
.hm-b13-message-card{border:1px solid #EAD9AA;background:#FFF9EC;border-radius:16px;padding:.75rem .82rem;margin:.45rem 0;}
.hm-b13-message-subject{color:#064E3B;font-weight:700;margin-bottom:.15rem;}
.hm-b13-message-date{color:#64748B;font-size:.78rem;margin-bottom:.35rem;}
.hm-b13-message-body{color:#334155!important;font-size:.88rem;line-height:1.45;margin:0;}
.hm-v101-schedule-card{border:1px solid #E3C98E;background:linear-gradient(180deg,#FFFDF8 0%,#FFF9EC 100%);border-radius:18px;padding:.80rem .95rem;margin:.48rem 0 .72rem 0;box-shadow:0 8px 20px rgba(15,23,42,.045);}
.hm-v101-schedule-title{color:#064E3B;font-size:.96rem;font-weight:950;margin-bottom:.18rem;}
.hm-v101-schedule-line{color:#334155;font-size:.82rem;font-weight:720;margin:.08rem 0;}
.hm-v101-schedule-pill{display:inline-flex;padding:.16rem .44rem;border-radius:999px;border:1px solid #D9C28F;background:#FFF7E6;color:#7A5A16;font-size:.70rem;font-weight:850;margin-left:.22rem;}
.hm-v104b11-ack-note{border:1px solid #E3C98E;background:#FFF7E6;color:#7A5A16!important;border-radius:12px;padding:.55rem .70rem;margin-top:.45rem!important;font-weight:560!important;}
.hm-v990-task-progress{border:1px solid #E5D2A9;background:#FFFDF8;border-radius:14px;padding:.62rem .72rem;margin:.52rem 0 .62rem 0;}
.hm-v990-progress-title{color:#064E3B;font-size:.88rem;font-weight:920;margin:0 0 .38rem 0;}
.hm-v990-progress-line{height:8px;border-radius:999px;background:#EFE7D6;overflow:hidden;margin:.28rem 0 .42rem 0;}
.hm-v990-progress-fill{height:8px;border-radius:999px;background:#0F766E;}
.hm-v990-task-chip{display:inline-flex;align-items:center;gap:.25rem;margin:.12rem .22rem .12rem 0;padding:.22rem .48rem;border-radius:999px;border:1px solid #D9C28F;color:#064E3B;background:#FAF8F1;font-size:.74rem;font-weight:850;}
.hm-v990-task-chip.pending{color:#7A5A16;background:#FFF7E6;}
.hm-v990-task-chip.done{color:#065F46;background:#ECFDF5;}
.hm-v990-submit-note{color:#64748B;font-size:.80rem;font-weight:720;margin:.36rem 0 .58rem 0;}
.hm-home-group-title{color:#064E3B;font-size:.84rem;font-weight:950;text-transform:uppercase;letter-spacing:.03em;margin:.32rem 0 .42rem 0;}
.hm-home-reference-title{margin-top:.88rem;color:#64748B;}
.hm-muted-action-anchor + div [data-testid="stButton"] > button,
.hm-muted-action-anchor + div .stButton > button{background:#F4F1EA!important;color:#64748B!important;border-color:#D8D0C0!important;box-shadow:none!important;}
.hm-muted-action-anchor + div [data-testid="stButton"] > button *,
.hm-muted-action-anchor + div .stButton > button *{color:#64748B!important;}
.hm-home-soft-separator{height:1px;background:#E3D4BA;margin:1.05rem 0 .88rem 0;}
section.main > div.block-container,.main .block-container,[data-testid="stAppViewBlockContainer"],.stMainBlockContainer,.block-container{padding-top:.72rem!important;}
div[data-testid="stButton"] > button{min-height:2.84rem;height:auto!important;white-space:normal!important;overflow:visible!important;line-height:1.32!important;padding:.58rem .78rem!important;display:flex!important;align-items:center!important;justify-content:center!important;}
div[data-testid="stButton"] > button p{white-space:normal!important;overflow:visible!important;line-height:1.32!important;margin:0!important;}
</style>
""",
    unsafe_allow_html=True,
)

render_system_message()
_render_messages(user_id)
_render_upcoming_schedules(user_id)

instance_status = str(current_instance.get("status") or wf.get("workflow_status") or "not_started").replace("_", " ").title()
stat_grid([
    {"label": "LAF", "value": "Completed" if wf.get("laf_completed") else "Pending", "note": "Lifestyle intake"},
    {"label": "Current Instance", "value": current_instance.get("instance_number", "-"), "note": current_instance.get("instance_type", "-")},
    {"label": "Requested Tasks", "value": ", ".join([task_title_v96_2(p) for p in requested_pages]), "note": "Current requirement"},
    {"label": "Status", "value": instance_status, "note": "Current stage"},
])

left, right = st.columns([1.15, .85], gap="large")

with left:
    card_start()
    st.subheader("Your next steps")
    is_task_instance = current_instance.get("instance_type") in ["Task Request", "Reassessment"] and not current_instance.get("submitted_for_review")

    if is_task_instance:
        _render_task_progress(current_instance, wf, requested_pages)
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
            if st.button("Body Mind Connection", use_container_width=True):
                st.switch_page("pages/19_Body_Mind_Connection.py")

    st.markdown("<div class='hm-home-soft-separator'></div>", unsafe_allow_html=True)
    if st.button("Submit / Status — Send completed tasks for admin review", use_container_width=True):
        st.switch_page("pages/06_Submit_Status.py")
    card_end()

with right:
    card_start()
    st.subheader("Personalized content")

    plans_ready = _workflow_finalized(wf)
    st.markdown("<div class='hm-home-group-title'>Daily tools</div>", unsafe_allow_html=True)
    if st.button("Today's Plan", use_container_width=True, disabled=not plans_ready):
        st.switch_page("pages/36_Todays_Journey.py")
    if st.button("Daily Log", use_container_width=True):
        st.switch_page("pages/18_Daily_Log.py")
    if st.button("My Schedule", use_container_width=True):
        st.switch_page("pages/33_My_Schedule.py")
    if st.button("My Weekly Plan", use_container_width=True, disabled=not plans_ready):
        st.switch_page("pages/37_Member_Plan.py")

    if not plans_ready:
        st.markdown("<div class='lock-card'><b>Weekly plan, recipes, exercises and supplements unlock after expert review is complete.</b></div>", unsafe_allow_html=True)

    st.markdown("<div class='hm-home-group-title hm-home-reference-title'>Reference library</div>", unsafe_allow_html=True)
    _muted_action("Recipe Repository", "pages/08_Recipe_Repository.py", "hm_home_recipe_repo_muted", disabled=not plans_ready)
    _muted_action("Exercise Repository", "pages/09_Exercise_Repository.py", "hm_home_exercise_repo_muted", disabled=not plans_ready)
    _muted_action("Supplements", "pages/40_Member_Supplements.py", "hm_home_supplements_muted", disabled=not plans_ready)

    card_end()

inject_keepalive_guard_v96_11()
