from __future__ import annotations

import datetime as dt
from contextlib import contextmanager
from typing import Any, Iterator

import streamlit as st


_CREATE_KEY_PREFIX = "hm_admin_sched_create_v"
_START_SUFFIX = "_start"
_END_SUFFIX = "_end"
_SUBMIT_SUFFIX = "_submit"


def _add_minutes_to_time(value: dt.time, minutes: int = 30) -> dt.time:
    """Return a clock time shifted by minutes, matching the existing same-day UI rule."""

    combined = dt.datetime.combine(dt.date(2000, 1, 1), value)
    shifted = combined + dt.timedelta(minutes=minutes)
    return shifted.time().replace(second=0, microsecond=0)


def _resolve_end_after_start_change(
    start_time: dt.time,
    current_end: dt.time | None,
    previous_auto_end: dt.time | None,
) -> tuple[dt.time | None, dt.time | None, bool]:
    """Advance an untouched default end time while preserving a manual end time."""

    proposed_end = _add_minutes_to_time(start_time, 30)
    if current_end is None or (
        previous_auto_end is not None and current_end == previous_auto_end
    ):
        return proposed_end, proposed_end, True
    return current_end, previous_auto_end, False


def _paired_schedule_keys(start_key: str) -> tuple[str, str]:
    prefix = start_key[: -len(_START_SUFFIX)]
    return prefix + _END_SUFFIX, prefix + "_end_auto_value"


def _sync_schedule_end_from_start(
    start_key: str,
    end_key: str,
    auto_key: str,
) -> None:
    start_time = st.session_state.get(start_key)
    if not isinstance(start_time, dt.time):
        return
    current_end = st.session_state.get(end_key)
    previous_auto = st.session_state.get(auto_key)
    next_end, next_auto, changed = _resolve_end_after_start_change(
        start_time,
        current_end if isinstance(current_end, dt.time) else None,
        previous_auto if isinstance(previous_auto, dt.time) else None,
    )
    if changed:
        st.session_state[end_key] = next_end
        st.session_state[auto_key] = next_auto


def render_admin_packages_uiux_styles() -> None:
    """Make the active-package decision visually prominent without changing behavior."""

    st.markdown(
        """
<style id="hm-admin-package-uiux-v1">
.st-key-hm_pkg_assign_package{
  border:2px solid #D8A84E!important;
  background:linear-gradient(135deg,#FFF7E6 0%,#FFFDF8 100%)!important;
  border-radius:16px!important;
  padding:.78rem .88rem .68rem!important;
  margin:.75rem 0 .95rem!important;
  box-shadow:0 8px 20px rgba(138,100,29,.10)!important;
}
.st-key-hm_pkg_assign_package label p{
  color:#064E3B!important;
  font-size:1rem!important;
  font-weight:950!important;
  letter-spacing:.01em!important;
}
.st-key-hm_pkg_assign_package::after{
  content:"Choose the active package to assign, replace or renew for this member.";
  display:block;
  color:#72551A;
  font-size:.76rem;
  font-weight:680;
  line-height:1.35;
  margin-top:.38rem;
}
</style>
""",
        unsafe_allow_html=True,
    )


@contextmanager
def admin_scheduling_uiux_scope(scheduling_module: Any) -> Iterator[None]:
    """Apply Create Schedule UX corrections only for the current page render."""

    original_time_input = st.time_input
    original_button = st.button
    original_render_flash = scheduling_module._render_flash

    def current_section() -> str:
        return str(
            st.session_state.get(scheduling_module._SECTION_KEY) or "create"
        ).strip().lower()

    def render_flash_near_submit() -> None:
        flash = st.session_state.get(scheduling_module._FLASH_KEY)
        kind = str((flash or {}).get("kind") or "").strip().lower()
        if current_section() == "create" and kind == "success":
            return
        original_render_flash()

    def time_input_with_default_duration(label: str, *args: Any, **kwargs: Any):
        key = str(kwargs.get("key") or "")
        if key.startswith(_CREATE_KEY_PREFIX) and key.endswith(_START_SUFFIX):
            end_key, auto_key = _paired_schedule_keys(key)
            start_value = st.session_state.get(key, kwargs.get("value"))
            if auto_key not in st.session_state and isinstance(start_value, dt.time):
                st.session_state[auto_key] = _add_minutes_to_time(start_value, 30)

            existing_callback = kwargs.get("on_change")
            existing_args = tuple(kwargs.pop("args", ()) or ())
            existing_kwargs = dict(kwargs.pop("kwargs", {}) or {})

            def on_start_change() -> None:
                if existing_callback:
                    existing_callback(*existing_args, **existing_kwargs)
                _sync_schedule_end_from_start(key, end_key, auto_key)

            kwargs["on_change"] = on_start_change

        elif key.startswith(_CREATE_KEY_PREFIX) and key.endswith(_END_SUFFIX):
            prefix = key[: -len(_END_SUFFIX)]
            auto_key = prefix + "_end_auto_value"
            default_end = kwargs.get("value")
            if auto_key not in st.session_state and isinstance(default_end, dt.time):
                st.session_state[auto_key] = default_end

        return original_time_input(label, *args, **kwargs)

    def button_with_nearby_success(label: str, *args: Any, **kwargs: Any):
        clicked = original_button(label, *args, **kwargs)
        key = str(kwargs.get("key") or "")
        if (
            current_section() == "create"
            and key.startswith(_CREATE_KEY_PREFIX)
            and key.endswith(_SUBMIT_SUFFIX)
        ):
            original_render_flash()
        return clicked

    scheduling_module._render_flash = render_flash_near_submit
    st.time_input = time_input_with_default_duration
    st.button = button_with_nearby_success
    try:
        yield
    finally:
        if scheduling_module._render_flash is render_flash_near_submit:
            scheduling_module._render_flash = original_render_flash
        if st.time_input is time_input_with_default_duration:
            st.time_input = original_time_input
        if st.button is button_with_nearby_success:
            st.button = original_button
