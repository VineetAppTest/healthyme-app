from __future__ import annotations

import datetime as dt
import functools
import inspect
from zoneinfo import ZoneInfo

import streamlit as st


_MARKER = "_hm_member_home_side_by_side_runtime_v5"
_MEMBER_TIMEZONE = ZoneInfo("Asia/Kolkata")


def _frame_file(frame) -> str:
    return str((frame.f_globals if frame is not None else {}).get("__file__") or "").replace("\\", "/")


def _is_member_home_frame(frame) -> bool:
    page_file = _frame_file(frame)
    return page_file.endswith("/pages/02_Member_Home.py") or page_file.endswith("pages/02_Member_Home.py")


def _frame_function(frame) -> str:
    return str((frame.f_code.co_name if frame is not None else "") or "")


def _member_home_frame(function_name: str):
    frame = inspect.currentframe().f_back
    for _ in range(24):
        if frame is None:
            break
        if _is_member_home_frame(frame) and _frame_function(frame) == function_name:
            return frame
        frame = frame.f_back
    return None


def _member_home_stack_has(function_name: str) -> bool:
    return _member_home_frame(function_name) is not None


def _parse_due_date(value) -> dt.date | None:
    if isinstance(value, dt.datetime):
        return value.date()
    if isinstance(value, dt.date):
        return value
    text = str(value or "").strip()
    if not text or text.lower() in {"not set", "none", "nan"}:
        return None
    candidate = text[:10] if "T" in text else text
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y", "%d %b %Y", "%d %B %Y"):
        try:
            return dt.datetime.strptime(candidate, fmt).date()
        except ValueError:
            continue
    try:
        return dt.date.fromisoformat(candidate)
    except ValueError:
        return None


def _task_due_state_class() -> str:
    frame = _member_home_frame("_render_task_progress")
    current_instance = dict((frame.f_locals.get("current_instance") if frame is not None else {}) or {})
    due_date = _parse_due_date(current_instance.get("due_date"))
    today = dt.datetime.now(_MEMBER_TIMEZONE).date()
    return "hm-task-overdue" if due_date is not None and due_date < today else "hm-task-before-due"


def _completed_task_button_label(label: object) -> str | None:
    text = str(label or "").strip()
    task_map = {
        "Start NSP Page 1": ("nsp1_completed", "NSP Page 1 Completed"),
        "Start NSP Page 2": ("nsp2_completed", "NSP Page 2 Completed"),
    }
    task = task_map.get(text)
    if task is None:
        return None
    frame = _member_home_frame("_render_task_progress")
    if frame is None:
        return None
    current_instance = dict(frame.f_locals.get("current_instance") or {})
    completed_key, completed_label = task
    return completed_label if bool(current_instance.get(completed_key)) else None


def install_member_home_side_by_side_runtime() -> None:
    from components import ui_common

    current_columns = st.columns
    current_markdown = st.markdown
    current_button = st.button
    current_expander = st.expander
    current_topbar = ui_common.topbar
    pair_state = {"pair": None, "message_expander": None}

    if getattr(current_topbar, _MARKER, False):
        return

    def ensure_pair():
        if pair_state["pair"] is None:
            left, right = current_columns([1, 1], gap="large")
            left.markdown("<span class='hm-home-side-col-anchor-v5'></span>", unsafe_allow_html=True)
            right.markdown("<span class='hm-home-side-col-anchor-v5'></span>", unsafe_allow_html=True)
            pair_state["pair"] = (left, right)
        return pair_state["pair"]

    @functools.wraps(current_topbar)
    def topbar_with_real_home_columns(title, *args, **kwargs):
        if str(title or "").strip() == "Member Home":
            pair_state["pair"] = None
            pair_state["message_expander"] = None
        result = current_topbar(title, *args, **kwargs)
        if str(title or "").strip() == "Member Home":
            current_markdown(
                """
<style id="hm-member-home-real-columns-v5">
.hm-home-side-col-anchor-v5,.hm-messages-nutritionist-anchor-v5{display:none!important;height:0!important;margin:0!important;padding:0!important;overflow:hidden!important;}
.hero-shell{margin-bottom:.20rem!important;}
div[data-testid="stHorizontalBlock"]:has(.hm-home-side-col-anchor-v5){align-items:flex-start!important;gap:1.25rem!important;margin:-1.05rem 0 .82rem 0!important;}
div[data-testid="stHorizontalBlock"]:has(.hm-home-side-col-anchor-v5)>div[data-testid="column"]{min-width:0!important;align-self:flex-start!important;}
.hm-b13-message-shell{float:none!important;width:100%!important;max-width:none!important;margin:0!important;padding:0!important;border:0!important;background:transparent!important;box-shadow:none!important;}
.hm-b13-message-title{display:none!important;}
.hm-b13-message-card{width:100%!important;max-width:none!important;border:1px solid #E3C98E!important;background:linear-gradient(180deg,#FFFDF8 0%,#FFF9EC 100%)!important;border-radius:18px!important;padding:.80rem .95rem!important;margin:.42rem 0 .72rem 0!important;box-shadow:0 8px 20px rgba(15,23,42,.045)!important;}
div[data-testid="stExpander"]:has(.hm-upcoming-schedule-anchor),div[data-testid="stExpander"]:has(.hm-messages-nutritionist-anchor-v5),div[data-testid="stExpander"]:has(.hm-upcoming-schedule-anchor)>div,div[data-testid="stExpander"]:has(.hm-messages-nutritionist-anchor-v5)>div,div[data-testid="stExpander"]:has(.hm-upcoming-schedule-anchor) details,div[data-testid="stExpander"]:has(.hm-messages-nutritionist-anchor-v5) details,div[data-testid="stExpander"]:has(.hm-upcoming-schedule-anchor) [data-testid="stExpanderDetails"],div[data-testid="stExpander"]:has(.hm-messages-nutritionist-anchor-v5) [data-testid="stExpanderDetails"]{float:none!important;width:100%!important;max-width:none!important;margin:0!important;border:0!important;border-top:0!important;border-bottom:0!important;outline:0!important;background:transparent!important;box-shadow:none!important;padding-left:0!important;padding-right:0!important;}
div[data-testid="stExpander"]:has(.hm-upcoming-schedule-anchor) summary+div,div[data-testid="stExpander"]:has(.hm-messages-nutritionist-anchor-v5) summary+div{border:0!important;border-top:0!important;border-bottom:0!important;box-shadow:none!important;margin-top:0!important;padding:.28rem 0 0 0!important;}
div[data-testid="stExpander"]:has(.hm-upcoming-schedule-anchor) .hm-v101-schedule-card{width:100%!important;max-width:none!important;margin:.42rem 0 .72rem 0!important;}
div[data-testid="stExpander"]:has(.hm-upcoming-schedule-anchor) summary,div[data-testid="stExpander"]:has(.hm-messages-nutritionist-anchor-v5) summary{
  width:285px!important;max-width:100%!important;min-height:2.12rem!important;height:2.12rem!important;
  padding:.30rem .72rem!important;border:1px solid #E3C98E!important;border-radius:999px!important;
  background:#FFFDF8!important;color:#064E3B!important;box-shadow:0 3px 8px rgba(6,78,59,.05)!important;
  display:flex!important;align-items:center!important;gap:.44rem!important;overflow:hidden!important;
}
div[data-testid="stExpander"]:has(.hm-upcoming-schedule-anchor) summary,div[data-testid="stExpander"]:has(.hm-upcoming-schedule-anchor) summary *,div[data-testid="stExpander"]:has(.hm-messages-nutritionist-anchor-v5) summary,div[data-testid="stExpander"]:has(.hm-messages-nutritionist-anchor-v5) summary *{white-space:nowrap!important;overflow-wrap:normal!important;word-break:keep-all!important;line-height:1.10!important;}
div[data-testid="stExpander"]:has(.hm-upcoming-schedule-anchor) summary p,div[data-testid="stExpander"]:has(.hm-messages-nutritionist-anchor-v5) summary p{margin:0!important;font-size:.88rem!important;font-weight:900!important;color:#064E3B!important;}
div[data-testid="stExpander"]:has(.hm-upcoming-schedule-anchor) summary [data-testid="stExpanderToggleIcon"],div[data-testid="stExpander"]:has(.hm-upcoming-schedule-anchor) summary [data-testid="stIconMaterial"],div[data-testid="stExpander"]:has(.hm-upcoming-schedule-anchor) summary svg,div[data-testid="stExpander"]:has(.hm-messages-nutritionist-anchor-v5) summary [data-testid="stExpanderToggleIcon"],div[data-testid="stExpander"]:has(.hm-messages-nutritionist-anchor-v5) summary [data-testid="stIconMaterial"],div[data-testid="stExpander"]:has(.hm-messages-nutritionist-anchor-v5) summary svg{display:none!important;width:0!important;height:0!important;min-width:0!important;margin:0!important;padding:0!important;overflow:hidden!important;font-size:0!important;}
div[data-testid="stExpander"]:has(.hm-upcoming-schedule-anchor) summary::before,div[data-testid="stExpander"]:has(.hm-messages-nutritionist-anchor-v5) summary::before{content:"›";display:inline-flex;align-items:center;justify-content:center;width:.78rem;height:.78rem;min-width:.78rem;color:#064E3B;font-size:1rem;font-weight:900;line-height:1;transform:rotate(0deg);transition:transform .16s ease;}
div[data-testid="stExpander"]:has(.hm-upcoming-schedule-anchor) details[open] summary::before,div[data-testid="stExpander"]:has(.hm-messages-nutritionist-anchor-v5) details[open] summary::before{transform:rotate(90deg);}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.hm-v990-task-progress.hm-task-before-due){border:2px solid #22C55E!important;background:linear-gradient(135deg,#F0FDF4 0%,#FFFFFF 100%)!important;box-shadow:0 12px 26px rgba(22,163,74,.11)!important;}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.hm-v990-task-progress.hm-task-overdue){border:2px solid #DC2626!important;background:linear-gradient(135deg,#FEF2F2 0%,#FFFFFF 100%)!important;box-shadow:0 14px 30px rgba(220,38,38,.15)!important;}
.hm-v990-task-progress{position:relative!important;background:#FFFFFF!important;padding:.80rem .86rem!important;}
.hm-v990-task-progress.hm-task-before-due{border:1px solid #86EFAC!important;box-shadow:0 8px 20px rgba(22,163,74,.08)!important;}
.hm-v990-task-progress.hm-task-overdue{border:1px solid #FCA5A5!important;box-shadow:0 8px 20px rgba(220,38,38,.10)!important;}
.hm-v990-task-progress::before{content:"Action required";display:inline-flex;align-items:center;margin:0 0 .48rem 0;border-radius:999px;font-weight:950;letter-spacing:.02em;text-transform:uppercase;}
.hm-v990-task-progress.hm-task-before-due::before{padding:.22rem .52rem;background:#DCFCE7;border:1px solid #22C55E;color:#166534;font-size:.72rem;}
.hm-v990-task-progress.hm-task-overdue::before{padding:.30rem .64rem;background:#FEE2E2;border:1px solid #DC2626;color:#B91C1C;font-size:.92rem;}
.hm-v990-task-progress.hm-task-before-due .hm-v990-due-date{font-size:.74rem!important;padding:.20rem .46rem!important;background:#DCFCE7!important;border-color:#22C55E!important;color:#166534!important;}
.hm-v990-task-progress.hm-task-overdue .hm-v990-due-date{font-size:.90rem!important;padding:.30rem .62rem!important;background:#FEE2E2!important;border-color:#DC2626!important;color:#B91C1C!important;font-weight:950!important;}
.hm-v990-task-progress.hm-task-before-due .hm-v990-task-chip.pending{font-size:.74rem!important;border-color:#22C55E!important;background:#DCFCE7!important;color:#166534!important;}
.hm-v990-task-progress.hm-task-overdue .hm-v990-task-chip.pending{font-size:.84rem!important;padding:.28rem .56rem!important;border-color:#DC2626!important;background:#FEE2E2!important;color:#B91C1C!important;font-weight:950!important;}
@media(max-width:900px){
  div[data-testid="stHorizontalBlock"]:has(.hm-home-side-col-anchor-v5){display:flex!important;flex-direction:column!important;gap:.8rem!important;margin:-.35rem 0 .72rem 0!important;}
  div[data-testid="stHorizontalBlock"]:has(.hm-home-side-col-anchor-v5)>div{width:100%!important;min-width:100%!important;}
  div[data-testid="stExpander"]:has(.hm-upcoming-schedule-anchor) summary,div[data-testid="stExpander"]:has(.hm-messages-nutritionist-anchor-v5) summary{width:min(285px,100%)!important;}
}
</style>
                """,
                unsafe_allow_html=True,
            )
        return result

    @functools.wraps(current_markdown)
    def markdown_in_message_expander(body, *args, **kwargs):
        if _member_home_stack_has("_render_task_progress") and isinstance(body, str) and "hm-v990-task-progress" in body:
            state_class = _task_due_state_class()
            body = body.replace("hm-v990-task-progress", f"hm-v990-task-progress {state_class}", 1)

        if not _member_home_stack_has("_render_messages"):
            return current_markdown(body, *args, **kwargs)

        _, right = ensure_pair()
        text = str(body or "").strip()

        if "hm-b13-message-shell" in text or text == "</div>":
            return None

        if "hm-b13-message-title" in text:
            box = right.expander("Messages from Nutritionist", expanded=True)
            box.markdown("<span class='hm-messages-nutritionist-anchor-v5'></span>", unsafe_allow_html=True)
            pair_state["message_expander"] = box
            return None

        box = pair_state.get("message_expander")
        if box is not None:
            return box.markdown(body, *args, **kwargs)
        return right.markdown(body, *args, **kwargs)

    @functools.wraps(current_button)
    def button_in_message_expander(label, *args, **kwargs):
        completed_label = _completed_task_button_label(label)
        if completed_label is not None:
            label = completed_label
            kwargs = dict(kwargs)
            kwargs["disabled"] = True

        if _member_home_stack_has("_render_messages"):
            box = pair_state.get("message_expander")
            if box is not None:
                return box.button(label, *args, **kwargs)
            _, right = ensure_pair()
            return right.button(label, *args, **kwargs)
        return current_button(label, *args, **kwargs)

    @functools.wraps(current_expander)
    def expander_in_home_columns(label, *args, **kwargs):
        if _member_home_stack_has("_render_upcoming_schedules"):
            left, _ = ensure_pair()
            return left.expander(label, *args, **kwargs)
        return current_expander(label, *args, **kwargs)

    setattr(topbar_with_real_home_columns, _MARKER, True)
    setattr(markdown_in_message_expander, _MARKER, True)
    setattr(button_in_message_expander, _MARKER, True)
    setattr(expander_in_home_columns, _MARKER, True)
    ui_common.topbar = topbar_with_real_home_columns
    st.markdown = markdown_in_message_expander
    st.button = button_in_message_expander
    st.expander = expander_in_home_columns
