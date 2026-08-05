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
    format_local_ts,
    inject_global_styles,
    inject_keepalive_guard_v96_11,
    stat_grid,
    topbar,
)


SHOW_MEMBER_REFERENCE_LIBRARY = False


st.set_page_config(
    page_title="Member Home",
    page_icon="💚",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_global_styles()
apply_luxe_theme()
require_member()


def _esc(value):
    return html.escape(str(value or ""))


def _member_message_text(value):
    """Remove only the redundant allocation sentence from Member Home."""

    return str(value or "").replace("Nutritionist has allocated a Task.", "").strip()


def _workflow_finalized(wf_state):
    return (
        bool(wf_state.get("admin_completed"))
        or bool(wf_state.get("final_report_ready"))
        or wf_state.get("workflow_status") == "finalized"
    )


def _normalised_requested_pages(instance):
    requested = instance.get("requested_pages", ["nsp1", "nsp2"])
    if isinstance(requested, str):
        return [requested]
    if isinstance(requested, list):
        return requested
    return ["nsp1", "nsp2"]


def should_show_body_mind_next_step_v96_6(wf_state, current_inst):
    if bool(wf_state.get("body_mind_completed")) or bool(
        current_inst.get("body_mind_completed")
    ):
        return False
    requested = _normalised_requested_pages(current_inst)
    if "body_mind" in requested:
        return True
    if bool(wf_state.get("body_mind_unlocked")) or bool(
        wf_state.get("admin_completed")
    ):
        return True
    return False


def task_title_v96_2(task_key):
    return {
        "nsp1": "NSP Page 1",
        "nsp2": "NSP Page 2",
        "body_mind": "Body Mind",
    }.get(str(task_key), str(task_key))


def task_status_done_v96_2(instance, wf_state, task_key):
    if task_key == "nsp1":
        return bool(instance.get("nsp1_completed"))
    if task_key == "nsp2":
        return bool(instance.get("nsp2_completed"))
    if task_key == "body_mind":
        return bool(instance.get("body_mind_completed")) or bool(
            wf_state.get("body_mind_completed")
        )
    return False


def _member_email():
    return (
        st.session_state.get("user_email")
        or st.session_state.get("oidc_email")
        or st.session_state.get("email")
        or st.session_state.get("username")
        or "member"
    )


def _render_member_home_css():
    st.markdown(
        """
<style id="hm-member-home-local-style-v3">
/* One structural shell owns the identity row and hero spacing. */
header[data-testid="stHeader"],[data-testid="stToolbar"],[data-testid="stDecoration"],[data-testid="stStatusWidget"]{display:none!important;visibility:hidden!important;height:0!important;min-height:0!important;margin:0!important;padding:0!important;}
.hm-member-home-root-anchor{display:none!important;height:0!important;min-height:0!important;margin:0!important;padding:0!important;overflow:hidden!important;}
div[data-testid="stElementContainer"]:has(.hm-member-home-root-anchor),div.element-container:has(.hm-member-home-root-anchor),div[data-testid="stElementContainer"]:has(style#hm-member-home-local-style-v3),div.element-container:has(style#hm-member-home-local-style-v3){display:none!important;height:0!important;min-height:0!important;margin:0!important;padding:0!important;overflow:hidden!important;}
div[data-testid="stAppViewContainer"] .block-container:has(.hm-member-home-root-anchor){padding-top:.18rem!important;padding-block-start:.18rem!important;margin-top:0!important;}
div[data-testid="stVerticalBlock"]:has(.hm-member-home-root-anchor):has(.hm-member-identity-pill):has(.hero-shell){gap:.28rem!important;margin:0!important;padding:0!important;}
div[data-testid="stVerticalBlock"]:has(.hm-member-home-root-anchor) .hero-shell{margin-top:0!important;}
div[data-testid="stHorizontalBlock"]:has(.hm-member-home-balanced-card){align-items:stretch!important;}
div[data-testid="stHorizontalBlock"]:has(.hm-member-home-balanced-card)>div[data-testid="column"]{display:flex!important;align-self:stretch!important;}
div[data-testid="stHorizontalBlock"]:has(.hm-member-home-balanced-card)>div[data-testid="column"]>div[data-testid="stVerticalBlock"]{width:100%!important;height:100%!important;}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.hm-member-home-balanced-card){height:100%!important;min-height:100%!important;}
.hm-member-identity-pill{height:2.46rem;min-height:2.46rem;display:flex;align-items:center;gap:.42rem;flex-wrap:wrap;color:#64748B;font-size:.80rem;font-weight:760;background:rgba(255,255,255,.76);border:1px solid #E9DFCC;border-radius:999px;padding:.24rem .64rem;margin:0!important;}
.hm-member-role-inline{display:inline-flex;align-items:center;justify-content:center;color:#7A5A16;font-size:.68rem;font-weight:900;background:#FFF7E6;border:1px solid #D9C28F;border-radius:999px;padding:.12rem .42rem;line-height:1.1;white-space:nowrap;}
.hm-top-profile-anchor,.hm-top-logout-anchor,.hm-task-action-anchor,.hm-home-action-anchor,.hm-member-home-balanced-card{display:none!important;height:0!important;min-height:0!important;margin:0!important;padding:0!important;overflow:hidden!important;line-height:0!important;}
div[data-testid="stHorizontalBlock"]:has(.hm-member-identity-pill){align-items:center!important;gap:.72rem!important;margin:0!important;padding:0!important;}
div[data-testid="stHorizontalBlock"]:has(.hm-member-identity-pill) > div[data-testid="column"]{display:flex!important;align-items:center!important;height:2.46rem!important;min-height:2.46rem!important;}
div[data-testid="stHorizontalBlock"]:has(.hm-member-identity-pill) > div[data-testid="column"] > div[data-testid="stVerticalBlock"]{width:100%!important;height:2.46rem!important;min-height:2.46rem!important;display:flex!important;flex-direction:column!important;justify-content:center!important;gap:0!important;margin:0!important;padding:0!important;}
.hm-top-profile-anchor + div,.hm-top-logout-anchor + div{display:flex!important;align-items:center!important;justify-content:center!important;height:2.46rem!important;min-height:2.46rem!important;margin:0!important;padding:0!important;}
.hm-top-profile-anchor + div [data-testid="stButton"] > button,.hm-top-profile-anchor + div .stButton > button{width:2.34rem!important;min-width:2.34rem!important;max-width:2.34rem!important;height:2.34rem!important;min-height:2.34rem!important;max-height:2.34rem!important;border-radius:999px!important;padding:0!important;font-size:.92rem!important;background:#FFFFFF!important;color:#064E3B!important;border:1.4px solid #D8A84E!important;box-shadow:0 4px 10px rgba(6,78,59,.055)!important;margin:0 auto!important;line-height:1!important;display:flex!important;align-items:center!important;justify-content:center!important;}
.hm-top-profile-anchor + div [data-testid="stButton"] > button *,.hm-top-profile-anchor + div .stButton > button *{color:#064E3B!important;font-size:.92rem!important;line-height:1!important;}
.hm-top-logout-anchor + div [data-testid="stButton"] > button,.hm-top-logout-anchor + div .stButton > button{height:2.46rem!important;min-height:2.46rem!important;max-height:2.46rem!important;border-radius:12px!important;padding:.36rem .78rem!important;margin:0!important;display:flex!important;align-items:center!important;justify-content:center!important;}
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
div[data-testid="stExpander"]:has(.hm-upcoming-schedule-anchor){margin:.45rem 0 .85rem 0!important;}
div[data-testid="stExpander"]:has(.hm-upcoming-schedule-anchor) summary{border:1.4px solid #D8A84E!important;border-radius:16px!important;background:#FFFDF8!important;color:#064E3B!important;font-weight:950!important;}
.hm-upcoming-schedule-anchor{display:none!important;height:0!important;margin:0!important;padding:0!important;}
.hm-home-section-head{display:flex;align-items:center;justify-content:space-between;gap:.75rem;margin:.42rem 0 .48rem 0;padding:.44rem .12rem .38rem .12rem;color:#064E3B;font-size:1rem;font-weight:950;}
.hm-home-section-head span{display:inline-flex;align-items:center;padding:.14rem .42rem;border:1px solid #D9C28F;border-radius:999px;background:#FFF7E6;color:#7A5A16;font-size:.68rem;font-weight:850;white-space:nowrap;}
.hm-home-section-divider{height:1px;background:linear-gradient(90deg,transparent 0%,#D8A84E 12%,#D8A84E 88%,transparent 100%);margin:.88rem 0 .72rem 0;}
.hm-home-grid-anchor,.hm-message-grid-anchor{display:none!important;height:0!important;min-height:0!important;margin:0!important;padding:0!important;overflow:hidden!important;}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.hm-home-grid-anchor){height:auto!important;min-height:0!important;align-self:flex-start!important;padding:.52rem .60rem .58rem!important;border:1px solid #E3C98E!important;border-radius:14px!important;background:#FFFDF8!important;box-shadow:0 5px 14px rgba(15,23,42,.035)!important;}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.hm-message-grid-anchor){height:100%!important;padding:.58rem .64rem .64rem!important;border:1px solid #E3C98E!important;border-radius:14px!important;background:#FFFDF8!important;box-shadow:0 5px 14px rgba(15,23,42,.035)!important;}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.hm-home-grid-anchor) > div,div[data-testid="stVerticalBlockBorderWrapper"]:has(.hm-message-grid-anchor) > div{padding:0!important;gap:.32rem!important;}
.hm-b13-message-card{border:0!important;background:transparent!important;border-radius:0!important;padding:0!important;margin:0!important;min-height:6.65rem;box-shadow:none!important;}
.hm-b13-message-subject{font-size:.88rem!important;font-weight:900!important;margin-bottom:.10rem!important;}
.hm-b13-message-date{font-size:.70rem!important;margin-bottom:.24rem!important;}
.hm-b13-message-body{font-size:.79rem!important;line-height:1.34!important;margin:0!important;}
.hm-v101-schedule-card{border:0!important;background:transparent!important;border-radius:0!important;padding:0!important;margin:0!important;min-height:0!important;box-shadow:none!important;}
.hm-v101-schedule-title{font-size:.78rem!important;margin-bottom:.14rem!important;}
.hm-v101-schedule-line{font-size:.70rem!important;line-height:1.28!important;margin:.06rem 0!important;}
.hm-v101-schedule-pill{font-size:.64rem!important;padding:.12rem .34rem!important;}
.hm-v104b11-ack-note{font-size:.72rem!important;line-height:1.34!important;padding:.38rem .46rem!important;margin-top:.34rem!important;}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.hm-message-grid-anchor) button{min-height:2.08rem!important;height:2.08rem!important;padding:.28rem .46rem!important;font-size:.74rem!important;border-radius:9px!important;}
@media(max-width:900px){.hm-home-section-head{font-size:.94rem;}}
.hm-v990-task-progress{border:1px solid #E5D2A9;background:#FFFDF8;border-radius:14px;padding:1rem 1rem 1.04rem;margin:.58rem 0 .78rem 0;min-height:0;box-sizing:border-box;}
.hm-v990-progress-head{display:flex;align-items:center;justify-content:space-between;gap:.78rem;flex-wrap:wrap;margin:0 0 .52rem 0;}
.hm-v990-progress-title{color:#064E3B;font-size:.88rem;font-weight:920;margin:0;}
.hm-v990-due-date{display:inline-flex;align-items:center;padding:.20rem .46rem;border-radius:999px;background:#FFF7E6;border:1px solid #D9C28F;color:#7A5A16;font-size:.74rem;font-weight:850;white-space:nowrap;}
.hm-v990-progress-line{height:8px;border-radius:999px;background:#EFE7D6;overflow:hidden;margin:.38rem 0 .56rem 0;}
.hm-v990-progress-fill{height:8px;border-radius:999px;background:#0F766E;}
.hm-v990-task-chip{display:inline-flex;align-items:center;gap:.25rem;margin:.12rem .22rem .12rem 0;padding:.22rem .48rem;border-radius:999px;border:1px solid #D9C28F;color:#064E3B;background:#FAF8F1;font-size:.74rem;font-weight:850;}
.hm-v990-task-chip.pending{color:#7A5A16;background:#FFF7E6;}
.hm-v990-task-chip.done{color:#065F46;background:#ECFDF5;}
.hm-v990-admin-note{color:#334155;font-size:.80rem;line-height:1.48;background:#F8FAFC;border:1px solid #E2E8F0;border-radius:10px;padding:.56rem .64rem;margin:.56rem 0 .24rem 0;}
.hm-v990-admin-note strong{color:#064E3B;}
.hm-v990-submit-note{color:#64748B;font-size:.80rem;font-weight:720;line-height:1.42;margin:.48rem 0 .32rem 0;}
.hm-task-action-anchor + div [data-testid="stButton"] > button,.hm-task-action-anchor + div .stButton > button{min-height:2.68rem!important;height:2.68rem!important;padding:.48rem .50rem!important;white-space:nowrap!important;display:flex!important;align-items:center!important;justify-content:center!important;}
.hm-task-action-anchor + div [data-testid="stButton"] > button *,.hm-task-action-anchor + div .stButton > button *{white-space:nowrap!important;overflow:visible!important;text-overflow:clip!important;font-size:.80rem!important;line-height:1.05!important;word-break:keep-all!important;}
.hm-home-group-title{color:#064E3B;font-size:.82rem;font-weight:950;text-transform:uppercase;letter-spacing:.03em;margin:.34rem 0 .30rem 0;}
.hm-home-action-anchor + div [data-testid="stButton"] > button,.hm-home-action-anchor + div .stButton > button{width:82%!important;min-height:2.30rem!important;margin:.08rem auto .30rem auto!important;padding:.42rem .64rem!important;border-radius:12px!important;box-shadow:0 4px 10px rgba(6,78,59,.045)!important;}
.hm-home-action-anchor + div [data-testid="stButton"] > button *,.hm-home-action-anchor + div .stButton > button *{font-size:.82rem!important;line-height:1.18!important;}
.hm-home-soft-separator{height:1px;background:#E3D4BA;margin:.95rem 0!important;}
.hm-member-panel-heading{color:#064E3B;font-size:1rem;font-weight:900;line-height:1.2;margin:0!important;padding:0!important;}
div[data-testid="stHorizontalBlock"]:has(.hm-member-home-balanced-card){align-items:stretch!important;gap:1.5rem!important;width:100%!important;}
div[data-testid="stHorizontalBlock"]:has(.hm-member-home-balanced-card) > div[data-testid="column"]{display:flex!important;flex:1 1 0!important;width:0!important;min-width:0!important;align-items:stretch!important;align-self:stretch!important;}
div[data-testid="stHorizontalBlock"]:has(.hm-member-home-balanced-card) > div[data-testid="column"] > div[data-testid="stVerticalBlock"]{display:flex!important;flex:1 1 auto!important;flex-direction:column!important;width:100%!important;height:100%!important;align-self:stretch!important;}
div[data-testid="stHorizontalBlock"]:has(.hm-member-home-balanced-card) div[data-testid="stVerticalBlockBorderWrapper"]:has(.hm-member-home-balanced-card){display:flex!important;flex:1 1 auto!important;align-self:stretch!important;height:100%!important;min-height:100%!important;padding:.70rem .85rem .85rem!important;}
div[data-testid="stHorizontalBlock"]:has(.hm-member-home-balanced-card) div[data-testid="stVerticalBlockBorderWrapper"]:has(.hm-member-home-balanced-card) > div{display:flex!important;flex:1 1 auto!important;flex-direction:column!important;width:100%!important;height:100%!important;padding:0!important;margin:0!important;}
div[data-testid="stHorizontalBlock"]:has(.hm-member-home-balanced-card) div[data-testid="stVerticalBlockBorderWrapper"]:has(.hm-member-home-balanced-card) div[data-testid="stVerticalBlock"]{padding-top:0!important;margin-top:0!important;gap:.55rem!important;}
div[data-testid="stHorizontalBlock"]:has(.hm-member-home-balanced-card) div[data-testid="stElementContainer"]:has(.hm-member-panel-heading),div[data-testid="stHorizontalBlock"]:has(.hm-member-home-balanced-card) div[data-testid="stElementContainer"]:has(.hm-home-soft-separator){margin:0!important;padding:0!important;min-height:0!important;}
div[data-testid="stButton"] > button{height:auto!important;display:flex!important;align-items:center!important;justify-content:center!important;}
@media(max-width:900px){div[data-testid="stHorizontalBlock"]:has(.hm-member-home-balanced-card){display:flex!important;flex-direction:column!important;gap:1rem!important;}div[data-testid="stHorizontalBlock"]:has(.hm-member-home-balanced-card) > div[data-testid="column"]{display:block!important;flex:none!important;width:100%!important;min-width:100%!important;height:auto!important;align-self:auto!important;}div[data-testid="stHorizontalBlock"]:has(.hm-member-home-balanced-card) div[data-testid="stVerticalBlockBorderWrapper"]:has(.hm-member-home-balanced-card){height:auto!important;min-height:0!important;}}
</style>
""",
        unsafe_allow_html=True,
    )


def _render_member_utility_bar():
    identity_col, profile_col, logout_col = st.columns(
        [6.65, 0.42, 1.0],
        gap="small",
        vertical_alignment="center",
    )
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
        st.markdown(
            "<span class='hm-top-profile-anchor'></span>",
            unsafe_allow_html=True,
        )
        if st.button(
            "👤",
            key="hm_top_my_profile",
            use_container_width=True,
            help="My Profile",
        ):
            st.switch_page("pages/07_My_Profile.py")
    with logout_col:
        st.markdown(
            "<span class='hm-top-logout-anchor'></span>",
            unsafe_allow_html=True,
        )
        if st.button("Logout", key="hm_top_logout", use_container_width=True):
            logout_current_user()
            st.rerun()


def _render_messages(user_id, show_divider=False):
    auto_archive_expired_nutritionist_messages(user_id)
    messages = get_member_messages(user_id, limit=6)
    if not messages:
        return False

    unique_messages = []
    seen_msg_keys = set()
    for msg in messages:
        msg_key = (
            f"{msg.get('member_id','')}|{msg.get('log_date','')}|"
            f"{' '.join(str(msg.get('message','')).strip().split()).lower()}"
        )
        if msg_key in seen_msg_keys:
            continue
        seen_msg_keys.add(msg_key)
        unique_messages.append(msg)
        if len(unique_messages) == 6:
            break

    if not unique_messages:
        return False
    if show_divider:
        st.markdown(
            "<div class='hm-home-section-divider'></div>",
            unsafe_allow_html=True,
        )
    st.markdown(
        f"<div class='hm-home-section-head'><div>Messages from Nutritionist</div><span>{len(unique_messages)} recent</span></div>",
        unsafe_allow_html=True,
    )

    for row_start in range(0, len(unique_messages), 3):
        cols = st.columns(3, gap="small")
        for col, msg in zip(cols, unique_messages[row_start : row_start + 3]):
            with col:
                with st.container(border=True):
                    st.markdown(
                        f"""
                        <span class='hm-message-grid-anchor'></span>
                        <div class='hm-b13-message-card'>
                          <div class='hm-b13-message-subject'>{_esc(msg.get('subject','Message'))}</div>
                          <div class='hm-b13-message-date'>{_esc(format_local_ts(msg.get('ts','')))}</div>
                          <p class='hm-b13-message-body'>{_esc(_member_message_text(msg.get('message','')))}</p>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    if st.button(
                        "Read & Archive",
                        key=f"read_msg_{msg.get('id','')}",
                        use_container_width=True,
                    ):
                        ok = mark_member_message_read(user_id, msg.get("id", ""))
                        if ok:
                            set_system_message(
                                "Message archived. You can find it in Daily Food Journal → "
                                "Nutritionist Notes Archive.",
                                "success",
                            )
                        else:
                            set_system_message(
                                "Message could not be archived. Please refresh and try again.",
                                "error",
                            )
                        st.rerun()
    return True


def _render_upcoming_schedules(user_id):
    queue_schedule_acknowledgement_reminders_v104b11(user_id)
    upcoming_schedules = list_upcoming_member_schedules(user_id, limit=6)
    if not upcoming_schedules:
        return False

    with st.expander(
        f"Upcoming Schedule ({len(upcoming_schedules)})",
        expanded=True,
    ):
        st.markdown(
            "<span class='hm-upcoming-schedule-anchor'></span>",
            unsafe_allow_html=True,
        )
        for row_start in range(0, len(upcoming_schedules), 2):
            cols = st.columns(2, gap="medium")
            for col, schedule in zip(cols, upcoming_schedules[row_start : row_start + 2]):
                with col:
                    with st.container(border=True):
                        time_text = str(schedule.get("start_time", "") or "")
                        if schedule.get("end_time"):
                            time_text += f" - {schedule.get('end_time')}"
                        notice = schedule_acknowledgement_notice_v104b11(schedule)
                        notice_html = (
                            "<div class='hm-v101-schedule-line hm-v104b11-ack-note'>"
                            f"{_esc(notice)}</div>"
                            if notice
                            else ""
                        )
                        st.markdown(
                            f"""
                            <span class='hm-home-grid-anchor'></span>
                            <div class='hm-v101-schedule-card'>
                              <div class='hm-v101-schedule-title'>{_esc(schedule.get('title','Scheduled session'))}<span class='hm-v101-schedule-pill'>{_esc(schedule_display_status_label_v104b11(schedule))}</span></div>
                              <div class='hm-v101-schedule-line'>{_esc(schedule.get('schedule_date',''))} · {_esc(time_text)}</div>
                              <div class='hm-v101-schedule-line'>Mode: {_esc(schedule.get('mode','-'))} · Link/location: {_esc(schedule.get('location_or_link') or '-')}</div>
                              {notice_html}
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
    return True


def _render_task_button(label, key, page, disabled=False):
    st.markdown(
        "<span class='hm-task-action-anchor'></span>",
        unsafe_allow_html=True,
    )
    if st.button(label, key=key, use_container_width=True, disabled=disabled):
        st.switch_page(page)


def _render_task_progress(current_instance, wf, requested_pages):
    visible_tasks = [
        page
        for page in requested_pages
        if page in ["nsp1", "nsp2", "body_mind"]
    ]
    if (
        should_show_body_mind_next_step_v96_6(wf, current_instance)
        and "body_mind" not in visible_tasks
    ):
        visible_tasks.append("body_mind")
    due_date = _esc(current_instance.get("due_date") or "Not set")
    admin_note = _esc(current_instance.get("admin_note") or "Not provided")
    progress_total = len(visible_tasks)
    progress_done = sum(
        1
        for page in visible_tasks
        if task_status_done_v96_2(current_instance, wf, page)
    )
    progress_width = (
        int(round((progress_done / progress_total) * 100))
        if progress_total
        else 100
    )
    task_chips = []
    for page in visible_tasks:
        done = task_status_done_v96_2(current_instance, wf, page)
        chip_class = "done" if done else "pending"
        chip_label = "Done" if done else "Pending"
        task_chips.append(
            f"<span class='hm-v990-task-chip {chip_class}'>"
            f"{_esc(task_title_v96_2(page))} · {chip_label}</span>"
        )
    st.markdown(
        f"""
        <div class='hm-v990-task-progress'>
          <div class='hm-v990-progress-head'>
            <div class='hm-v990-progress-title'>Task progress: {progress_done} of {progress_total} completed</div>
            <div class='hm-v990-due-date'>Due date: <b>&nbsp;{due_date}</b></div>
          </div>
          <div class='hm-v990-progress-line'><div class='hm-v990-progress-fill' style='width:{progress_width}%;'></div></div>
          <div>{''.join(task_chips)}</div>
          <div class='hm-v990-admin-note'><strong>Admin note:</strong> {admin_note}</div>
          <div class='hm-v990-submit-note'>Use Submit / Status after completing all requested tasks to send this to admin for review.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if not visible_tasks:
        st.warning("No active task is selected for this request.")
        return
    task_cols = st.columns(
        [1, 1, 1],
        gap="medium",
        vertical_alignment="center",
    )
    with task_cols[0]:
        if "nsp1" in visible_tasks:
            _render_task_button(
                "Start NSP Page 1",
                "hm_task_nsp1",
                "pages/04_NSP_Page1.py",
            )
    with task_cols[1]:
        if "nsp2" in visible_tasks:
            _render_task_button(
                "Start NSP Page 2",
                "hm_task_nsp2",
                "pages/05_NSP_Page2.py",
            )
    with task_cols[2]:
        if "body_mind" in visible_tasks:
            body_done = task_status_done_v96_2(
                current_instance,
                wf,
                "body_mind",
            )
            label = "Body Mind Done" if body_done else "Body Mind"
            _render_task_button(
                label,
                "hm_task_body_mind",
                "pages/19_Body_Mind_Connection.py",
                disabled=body_done,
            )


def _home_action(
    label: str,
    page: str,
    key: str,
    muted: bool = False,
    disabled: bool = False,
):
    anchor_class = (
        "hm-home-action-anchor hm-home-muted-anchor"
        if muted
        else "hm-home-action-anchor"
    )
    st.markdown(
        f"<span class='{anchor_class}'></span>",
        unsafe_allow_html=True,
    )
    if st.button(label, key=key, use_container_width=True, disabled=disabled):
        st.switch_page(page)


# Render one structural header shell before slower page reads.
with st.container():
    st.markdown(
        "<span class='hm-member-home-root-anchor'></span>",
        unsafe_allow_html=True,
    )
    _render_member_home_css()
    _render_member_utility_bar()
    topbar(
        "Member Home",
        "Continue your wellness assessment and access your tools.",
        "Member experience",
    )

user_id = st.session_state["user_id"]
wf = get_workflow(user_id) or {}
if (
    _workflow_finalized(wf)
    and wf.get("body_mind_activation_requested")
    and not wf.get("body_mind_unlocked")
):
    hard_sync_body_mind_if_requested(user_id)
    wf = get_workflow(user_id) or {}

current_instance = get_current_assessment_instance(user_id) or {}
requested_pages = _normalised_requested_pages(current_instance)

for _repo_detail_key in [
    "hm_recipe_selected_id",
    "hm_recipe_detail_mode",
    "hm_exercise_selected_id",
    "hm_exercise_detail_mode",
]:
    st.session_state.pop(_repo_detail_key, None)

render_system_message()
_has_upcoming_schedule = _render_upcoming_schedules(user_id)
_render_messages(user_id, show_divider=_has_upcoming_schedule)

instance_status = str(
    current_instance.get("status")
    or wf.get("workflow_status")
    or "not_started"
).replace("_", " ").title()
stat_grid(
    [
        {
            "label": "LAF",
            "value": "Completed" if wf.get("laf_completed") else "Pending",
            "note": "Lifestyle intake",
        },
        {
            "label": "Current Instance",
            "value": current_instance.get("instance_number", "-"),
            "note": current_instance.get("instance_type", "-"),
        },
        {
            "label": "Requested Tasks",
            "value": ", ".join(
                [task_title_v96_2(page) for page in requested_pages]
            ),
            "note": "Current requirement",
        },
        {
            "label": "Status",
            "value": instance_status,
            "note": "Current stage",
        },
    ]
)

left, right = st.columns([1, 1], gap="large")

with left:
    with st.container(border=True, height="stretch"):
        st.markdown(
            "<span class='hm-member-home-balanced-card'></span>"
            "<div class='hm-member-panel-heading'>Your next steps</div>",
            unsafe_allow_html=True,
        )
        is_task_instance = (
            current_instance.get("instance_type")
            in ["Task Request", "Reassessment"]
            and not current_instance.get("submitted_for_review")
        )
        if is_task_instance:
            _render_task_progress(current_instance, wf, requested_pages)
        elif not wf.get("laf_completed"):
            _render_task_button(
                "1. Fill LAF",
                "hm_fill_laf",
                "pages/03_LAF_Form.py",
            )
        elif current_instance.get("submitted_for_review"):
            st.info(
                "Your latest evaluation has been submitted and is under review."
            )
        else:
            action_cols = st.columns(
                [1, 1, 1],
                gap="medium",
                vertical_alignment="center",
            )
            with action_cols[0]:
                _render_task_button(
                    "Start NSP Page 1",
                    "hm_home_nsp1",
                    "pages/04_NSP_Page1.py",
                    disabled=("nsp1" not in requested_pages),
                )
            with action_cols[1]:
                _render_task_button(
                    "Start NSP Page 2",
                    "hm_home_nsp2",
                    "pages/05_NSP_Page2.py",
                    disabled=("nsp2" not in requested_pages),
                )
            with action_cols[2]:
                if should_show_body_mind_next_step_v96_6(
                    wf,
                    current_instance,
                ):
                    _render_task_button(
                        "Body Mind",
                        "hm_home_body_mind",
                        "pages/19_Body_Mind_Connection.py",
                    )
        st.markdown(
            "<div class='hm-home-soft-separator'></div>",
            unsafe_allow_html=True,
        )
        if st.button(
            "Submit / Status — Send completed tasks for admin review",
            use_container_width=True,
        ):
            st.switch_page("pages/06_Submit_Status.py")

with right:
    with st.container(border=True, height="stretch"):
        st.markdown(
            "<span class='hm-member-home-balanced-card'></span>"
            "<div class='hm-member-panel-heading'>Personalized content</div>",
            unsafe_allow_html=True,
        )
        plans_ready = _workflow_finalized(wf)
        st.markdown(
            "<div class='hm-home-group-title'>Daily tools</div>",
            unsafe_allow_html=True,
        )
        _home_action(
            "Today's Plan",
            "pages/36_Todays_Journey.py",
            "hm_home_today_plan",
            disabled=not plans_ready,
        )
        _home_action(
            "Daily Log",
            "pages/18_Daily_Log.py",
            "hm_home_daily_log",
        )
        _home_action(
            "My Schedule",
            "pages/33_My_Schedule.py",
            "hm_home_schedule",
        )
        _home_action(
            "My Weekly Plan",
            "pages/37_Member_Plan.py",
            "hm_home_weekly_plan",
            disabled=not plans_ready,
        )
        if not plans_ready:
            st.markdown(
                "<div class='lock-card'><b>Weekly plan, recipes, exercises and "
                "supplements unlock after expert review is complete.</b></div>",
                unsafe_allow_html=True,
            )
        if SHOW_MEMBER_REFERENCE_LIBRARY:
            st.markdown(
                "<div class='hm-home-group-title hm-home-reference-title'>"
                "Reference library</div>",
                unsafe_allow_html=True,
            )
            _home_action(
                "Recipe Repository",
                "pages/08_Recipe_Repository.py",
                "hm_home_recipe_repo",
                muted=True,
                disabled=not plans_ready,
            )
            _home_action(
                "Exercise Repository",
                "pages/09_Exercise_Repository.py",
                "hm_home_exercise_repo",
                muted=True,
                disabled=not plans_ready,
            )
            _home_action(
                "Supplements",
                "pages/40_Member_Supplements.py",
                "hm_home_supplements",
                muted=True,
                disabled=not plans_ready,
            )

inject_keepalive_guard_v96_11()
