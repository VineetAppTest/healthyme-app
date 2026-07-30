from __future__ import annotations

import datetime as dt
import functools
from typing import Any, Callable

import streamlit as st


_FLUID_TIME_PREFIX = "hm_h9a4c_fluid_time_"
_TIME_FIELD_MARKER = "_hm_member_fluid_time_field_v2"
_TABS_MARKER = "_hm_member_shell_tabs_v1"
_TOPBAR_MARKER = "_hm_member_shell_topbar_v1"
_BACK_TO_TOP_MARKER = "_hm_member_shell_footer_v1"
_DIAGNOSTICS_MARKER = "_hm_production_diagnostics_hidden_v1"


def _parse_time(value: object) -> dt.time | None:
    if isinstance(value, dt.time):
        return value.replace(second=0, microsecond=0)
    text = str(value or "").strip().upper()
    if not text:
        return None
    for fmt in ("%I:%M %p", "%H:%M", "%I %p"):
        try:
            return dt.datetime.strptime(text, fmt).time()
        except ValueError:
            pass
    return None


def _display_time(value: object) -> str:
    parsed = _parse_time(value)
    if parsed is None:
        return str(value or "").strip()
    return parsed.strftime("%I:%M %p").lstrip("0")


def _member_shell_css() -> None:
    """Match shared Member header/footer spacing to the accepted Member Home shell."""

    if str(st.session_state.get("user_role") or "").strip().lower() != "member":
        return
    st.markdown(
        """
<style id="hm-member-shell-production-cleanup-v1">
html,body,#root{margin-top:0!important;padding-top:0!important;}
header[data-testid="stHeader"],[data-testid="stToolbar"],[data-testid="stDecoration"],[data-testid="stStatusWidget"]{
  display:none!important;visibility:hidden!important;height:0!important;min-height:0!important;
  margin:0!important;padding:0!important;
}
[data-testid="stAppViewContainer"],[data-testid="stMain"],section.main,
[data-testid="stMainBlockContainer"],[data-testid="stAppViewBlockContainer"],
section.main > div.block-container,.main .block-container,.stMainBlockContainer,.block-container{
  padding-top:0!important;padding-block-start:0!important;margin-top:0!important;
}
div[data-testid="stElementContainer"]:has(style#hm-member-shell-production-cleanup-v1){
  display:none!important;height:0!important;min-height:0!important;margin:0!important;padding:0!important;overflow:hidden!important;
}
div[data-testid="stHorizontalBlock"]:has(.utility-bar){
  position:static!important;top:0!important;align-items:center!important;gap:.72rem!important;
  margin:0 0 .52rem 0!important;padding:0!important;
}
div[data-testid="stHorizontalBlock"]:has(.utility-bar) > div[data-testid="column"]{
  display:flex!important;align-items:center!important;min-height:2.46rem!important;
}
div[data-testid="stHorizontalBlock"]:has(.utility-bar) .utility-bar{
  width:100%!important;height:2.46rem!important;min-height:2.46rem!important;
  display:flex!important;align-items:center!important;margin:0!important;padding:.24rem .64rem!important;
}
div[data-testid="stHorizontalBlock"]:has(.utility-bar) div[data-testid="stButton"],
div[data-testid="stHorizontalBlock"]:has(.utility-bar) .stButton{
  width:100%!important;margin:0!important;padding:0!important;
}
div[data-testid="stHorizontalBlock"]:has(.utility-bar) div[data-testid="stButton"] > button,
div[data-testid="stHorizontalBlock"]:has(.utility-bar) .stButton > button{
  height:2.46rem!important;min-height:2.46rem!important;max-height:2.46rem!important;
  margin:0!important;padding:.36rem .78rem!important;border-radius:12px!important;
}
input[placeholder="Example: 10:30 PM"]{
  width:100%!important;min-width:0!important;min-height:2.70rem!important;
  height:2.70rem!important;border-radius:13px!important;
}
div[data-testid="stElementContainer"]:has(.hm-back-to-top){
  height:0!important;min-height:0!important;margin:0!important;padding:0!important;overflow:visible!important;
}
.hm-back-to-top{right:18px!important;bottom:18px!important;}
</style>
        """,
        unsafe_allow_html=True,
    )


def _install_fluid_time_field() -> None:
    """Replace only Daily Log Other Fluid native time widgets with one stable field."""

    current_time_input = st.time_input
    if getattr(current_time_input, _TIME_FIELD_MARKER, False):
        return
    current_text_input = st.text_input

    @functools.wraps(current_time_input)
    def corrected_time_input(label: str, *args: Any, **kwargs: Any):
        key = str(kwargs.get("key") or "")
        if not key.startswith(_FLUID_TIME_PREFIX):
            return current_time_input(label, *args, **kwargs)

        text_kwargs: dict[str, Any] = {
            "key": f"{key}_text_v2",
            "value": _display_time(kwargs.get("value")),
            "placeholder": "Example: 10:30 PM",
            "max_chars": 8,
        }
        for optional_name in ("disabled", "label_visibility", "help"):
            if optional_name in kwargs:
                text_kwargs[optional_name] = kwargs[optional_name]

        raw_value = current_text_input(label, **text_kwargs)
        parsed = _parse_time(raw_value)
        if str(raw_value or "").strip() and parsed is None:
            st.caption("Enter time as HH:MM or HH:MM AM/PM, for example 10:30 PM.")
        _member_shell_css()
        return parsed

    setattr(corrected_time_input, _TIME_FIELD_MARKER, True)
    corrected_time_input._hm_original = current_time_input
    st.time_input = corrected_time_input


def _install_tabs_shell_refresh() -> None:
    """Re-apply accepted shell spacing after Daily Log's local tab/layout CSS."""

    current_tabs = st.tabs
    if getattr(current_tabs, _TABS_MARKER, False):
        return

    @functools.wraps(current_tabs)
    def tabs_with_member_shell(*args: Any, **kwargs: Any):
        result = current_tabs(*args, **kwargs)
        _member_shell_css()
        return result

    setattr(tabs_with_member_shell, _TABS_MARKER, True)
    tabs_with_member_shell._hm_original = current_tabs
    st.tabs = tabs_with_member_shell


def _unwrap_performance_footer(func: Callable[..., Any]) -> Callable[..., Any]:
    seen: set[int] = set()
    current = func
    while hasattr(current, "_hm_perf_original") and id(current) not in seen:
        seen.add(id(current))
        current = getattr(current, "_hm_perf_original")
    return current


def _install_no_visible_diagnostics() -> None:
    """Retain dormant measurement helpers but remove all production-page panels."""

    from components import performance_diagnostics as diagnostics
    from components import ui_common

    current_finish = diagnostics.finish_and_render_page_diagnostics
    if not getattr(current_finish, _DIAGNOSTICS_MARKER, False):

        @functools.wraps(current_finish)
        def finish_without_visible_panel(page_name: str):
            if not diagnostics.measurement_enabled():
                return None
            return diagnostics.finish_page_measurement(page_name)

        setattr(finish_without_visible_panel, _DIAGNOSTICS_MARKER, True)
        finish_without_visible_panel._hm_original = current_finish
        diagnostics.finish_and_render_page_diagnostics = finish_without_visible_panel

    diagnostics.set_measurement_enabled(False)
    diagnostics.clear_measurement_history()

    # The temporary measurement gate wrapped these two footer functions to display
    # start/download controls. Restore their accepted production implementations.
    ui_common.render_back_to_top = _unwrap_performance_footer(ui_common.render_back_to_top)
    ui_common.inject_keepalive_guard_v96_11 = _unwrap_performance_footer(
        ui_common.inject_keepalive_guard_v96_11
    )


def _install_member_shell_hooks() -> None:
    from components import ui_common

    current_topbar = ui_common.topbar
    if not getattr(current_topbar, _TOPBAR_MARKER, False):

        @functools.wraps(current_topbar)
        def topbar_with_member_shell(*args: Any, **kwargs: Any):
            result = current_topbar(*args, **kwargs)
            _member_shell_css()
            return result

        setattr(topbar_with_member_shell, _TOPBAR_MARKER, True)
        topbar_with_member_shell._hm_original = current_topbar
        ui_common.topbar = topbar_with_member_shell

    current_back_to_top = ui_common.render_back_to_top
    if not getattr(current_back_to_top, _BACK_TO_TOP_MARKER, False):

        @functools.wraps(current_back_to_top)
        def back_to_top_with_member_shell(*args: Any, **kwargs: Any):
            result = current_back_to_top(*args, **kwargs)
            _member_shell_css()
            return result

        setattr(back_to_top_with_member_shell, _BACK_TO_TOP_MARKER, True)
        back_to_top_with_member_shell._hm_original = current_back_to_top
        ui_common.render_back_to_top = back_to_top_with_member_shell


def install_member_post_optimization_cleanup() -> None:
    """Install the final production-only Member corrections after temporary tooling."""

    _install_no_visible_diagnostics()
    _install_fluid_time_field()
    _install_tabs_shell_refresh()
    _install_member_shell_hooks()
