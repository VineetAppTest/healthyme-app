from __future__ import annotations

import functools
import inspect

import streamlit as st


_MARKER = "_hm_member_home_side_by_side_runtime_v4"


def _frame_file(frame) -> str:
    return str((frame.f_globals if frame is not None else {}).get("__file__") or "").replace("\\", "/")


def _is_member_home_frame(frame) -> bool:
    page_file = _frame_file(frame)
    return page_file.endswith("/pages/02_Member_Home.py") or page_file.endswith("pages/02_Member_Home.py")


def _frame_function(frame) -> str:
    return str((frame.f_code.co_name if frame is not None else "") or "")


def _member_home_stack_has(function_name: str) -> bool:
    frame = inspect.currentframe().f_back
    for _ in range(14):
        if frame is None:
            break
        if _is_member_home_frame(frame) and _frame_function(frame) == function_name:
            return True
        frame = frame.f_back
    return False


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
            left.markdown("<span class='hm-home-side-col-anchor-v4'></span>", unsafe_allow_html=True)
            right.markdown("<span class='hm-home-side-col-anchor-v4'></span>", unsafe_allow_html=True)
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
<style id="hm-member-home-real-columns-v4">
.hm-home-side-col-anchor-v4,.hm-messages-nutritionist-anchor-v4{display:none!important;height:0!important;margin:0!important;padding:0!important;overflow:hidden!important;}
div[data-testid="stHorizontalBlock"]:has(.hm-home-side-col-anchor-v4){align-items:flex-start!important;gap:1.25rem!important;margin:.42rem 0 .82rem 0!important;}
div[data-testid="stHorizontalBlock"]:has(.hm-home-side-col-anchor-v4)>div[data-testid="column"]{min-width:0!important;align-self:flex-start!important;}
.hm-b13-message-shell{float:none!important;width:100%!important;max-width:none!important;margin:0!important;padding:0!important;border:0!important;background:transparent!important;box-shadow:none!important;}
.hm-b13-message-title{display:none!important;}
.hm-b13-message-card{width:100%!important;max-width:none!important;margin:.42rem 0!important;}
div[data-testid="stExpander"]:has(.hm-upcoming-schedule-anchor),div[data-testid="stExpander"]:has(.hm-messages-nutritionist-anchor-v4){float:none!important;width:100%!important;max-width:none!important;margin:0!important;border:0!important;background:transparent!important;box-shadow:none!important;}
div[data-testid="stExpander"]:has(.hm-upcoming-schedule-anchor) .hm-v101-schedule-card{width:100%!important;max-width:none!important;margin:.42rem 0!important;}
div[data-testid="stExpander"]:has(.hm-upcoming-schedule-anchor) summary,div[data-testid="stExpander"]:has(.hm-messages-nutritionist-anchor-v4) summary{
  width:285px!important;max-width:100%!important;min-height:2.12rem!important;height:2.12rem!important;
  padding:.30rem .72rem!important;border:1px solid #E3C98E!important;border-radius:999px!important;
  background:#FFFDF8!important;color:#064E3B!important;box-shadow:0 3px 8px rgba(6,78,59,.05)!important;
  display:flex!important;align-items:center!important;gap:.44rem!important;overflow:hidden!important;
}
div[data-testid="stExpander"]:has(.hm-upcoming-schedule-anchor) summary,div[data-testid="stExpander"]:has(.hm-upcoming-schedule-anchor) summary *,div[data-testid="stExpander"]:has(.hm-messages-nutritionist-anchor-v4) summary,div[data-testid="stExpander"]:has(.hm-messages-nutritionist-anchor-v4) summary *{
  white-space:nowrap!important;overflow-wrap:normal!important;word-break:keep-all!important;line-height:1.10!important;
}
div[data-testid="stExpander"]:has(.hm-upcoming-schedule-anchor) summary p,div[data-testid="stExpander"]:has(.hm-messages-nutritionist-anchor-v4) summary p{margin:0!important;font-size:.88rem!important;font-weight:900!important;color:#064E3B!important;}
div[data-testid="stExpander"]:has(.hm-upcoming-schedule-anchor) summary [data-testid="stExpanderToggleIcon"],div[data-testid="stExpander"]:has(.hm-upcoming-schedule-anchor) summary [data-testid="stIconMaterial"],div[data-testid="stExpander"]:has(.hm-upcoming-schedule-anchor) summary svg,div[data-testid="stExpander"]:has(.hm-messages-nutritionist-anchor-v4) summary [data-testid="stExpanderToggleIcon"],div[data-testid="stExpander"]:has(.hm-messages-nutritionist-anchor-v4) summary [data-testid="stIconMaterial"],div[data-testid="stExpander"]:has(.hm-messages-nutritionist-anchor-v4) summary svg{display:none!important;width:0!important;height:0!important;min-width:0!important;margin:0!important;padding:0!important;overflow:hidden!important;font-size:0!important;}
div[data-testid="stExpander"]:has(.hm-upcoming-schedule-anchor) summary::before,div[data-testid="stExpander"]:has(.hm-messages-nutritionist-anchor-v4) summary::before{content:"›";display:inline-flex;align-items:center;justify-content:center;width:.78rem;height:.78rem;min-width:.78rem;color:#064E3B;font-size:1rem;font-weight:900;line-height:1;transform:rotate(0deg);transition:transform .16s ease;}
div[data-testid="stExpander"]:has(.hm-upcoming-schedule-anchor) details[open] summary::before,div[data-testid="stExpander"]:has(.hm-messages-nutritionist-anchor-v4) details[open] summary::before{transform:rotate(90deg);}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.hm-v990-task-progress){border:2px solid #D8A84E!important;background:linear-gradient(135deg,#FFFDF8 0%,#FFF4DE 100%)!important;box-shadow:0 14px 30px rgba(138,95,16,.13)!important;}
.hm-v990-task-progress{position:relative!important;border:1px solid rgba(216,168,78,.62)!important;background:#FFFFFF!important;box-shadow:0 8px 20px rgba(138,95,16,.08)!important;padding:.80rem .86rem!important;}
.hm-v990-task-progress::before{content:"Action required";display:inline-flex;align-items:center;margin:0 0 .48rem 0;padding:.22rem .52rem;border-radius:999px;background:#FDECC8;border:1px solid #D8A84E;color:#7A4F00;font-size:.72rem;font-weight:950;letter-spacing:.02em;text-transform:uppercase;}
.hm-v990-due-date{font-size:.78rem!important;padding:.26rem .56rem!important;background:#FFF1CC!important;border-color:#D8A84E!important;}
.hm-v990-task-chip.pending{border-color:#D8A84E!important;background:#FFF1CC!important;color:#7A4F00!important;}
@media(max-width:900px){
  div[data-testid="stHorizontalBlock"]:has(.hm-home-side-col-anchor-v4){display:flex!important;flex-direction:column!important;gap:.8rem!important;}
  div[data-testid="stHorizontalBlock"]:has(.hm-home-side-col-anchor-v4)>div{width:100%!important;min-width:100%!important;}
  div[data-testid="stExpander"]:has(.hm-upcoming-schedule-anchor) summary,div[data-testid="stExpander"]:has(.hm-messages-nutritionist-anchor-v4) summary{width:min(285px,100%)!important;}
}
</style>
                """,
                unsafe_allow_html=True,
            )
        return result

    @functools.wraps(current_markdown)
    def markdown_in_message_expander(body, *args, **kwargs):
        if not _member_home_stack_has("_render_messages"):
            return current_markdown(body, *args, **kwargs)

        _, right = ensure_pair()
        text = str(body or "").strip()

        if "hm-b13-message-shell" in text or text == "</div>":
            return None

        if "hm-b13-message-title" in text:
            box = right.expander("Messages from Nutritionist", expanded=True)
            box.markdown("<span class='hm-messages-nutritionist-anchor-v4'></span>", unsafe_allow_html=True)
            pair_state["message_expander"] = box
            return None

        box = pair_state.get("message_expander")
        if box is not None:
            return box.markdown(body, *args, **kwargs)
        return right.markdown(body, *args, **kwargs)

    @functools.wraps(current_button)
    def button_in_message_expander(label, *args, **kwargs):
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
