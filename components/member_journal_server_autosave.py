from __future__ import annotations

import datetime as dt
import functools
import hashlib
import inspect
import json
from typing import Any

import streamlit as st

from components import flash


_MARKER = "_hm_member_journal_server_autosave_v2"
_FLASH_MARKER = "_hm_member_journal_silent_flash_v2"
_RERUN_MARKER = "_hm_member_journal_silent_rerun_v2"
_DAILY_LOG_PAGE = "18_Daily_Log.py"
_FOOD_BUTTON = "Save Day"
_EXERCISE_BUTTON = "Save Progress"
_SILENT_MESSAGE_KEY = "_hm_journal_autosave_silent_message"
_SILENT_RERUN_KEY = "_hm_journal_autosave_silent_rerun"

_FOOD_KEY_MARKERS = (
    "_food_",
    "_portion_",
    "_mood",
    "_energy",
    "hm_h9a4c_water_",
    "hm_h9a4c_fluid_type_",
    "hm_h9a4c_fluid_time_",
    "hm_h9a4c_fluid_qty_",
    "hm_h9a4c_fluid_notes_",
    "hm_h9a4c_poop_rounds_",
    "hm_h9a4c_poop_time_",
    "hm_h9a4c_poop_feeling_",
    "hm_h9a4c_notes_",
    "hm_daily_hour_v12_",
    "hm_daily_minute_v12_",
    "hm_daily_ampm_v12_",
)
_AUTOSAVE_CONTROL_PREFIXES = (
    "_hm_food_autosave_",
    "_hm_exercise_autosave_",
    "_hm_last_journal_autosave",
    "_hm_journal_autosave_",
)
_DEFAULT_VALUES = {
    "",
    "none",
    "select",
    "selected",
    "please select",
    "select option",
    "choose",
    "choose one",
    "hh",
    "mm",
    "am/pm",
}


def _current_page_filename() -> str:
    for frame in inspect.stack():
        filename = str(frame.filename or "").replace("\\", "/")
        if "/pages/" in filename:
            return filename.rsplit("/", 1)[-1]
    return ""


def _normalise(value: Any) -> Any:
    if isinstance(value, (dt.datetime, dt.date, dt.time)):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(key): _normalise(item) for key, item in sorted(value.items())}
    if isinstance(value, (list, tuple)):
        return [_normalise(item) for item in value]
    if value is None:
        return ""
    return value


def _is_default(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return " ".join(value.strip().lower().split()) in _DEFAULT_VALUES
    return False


def _compact_mapping(items: dict[str, Any]) -> dict[str, Any]:
    compact: dict[str, Any] = {}
    for key, value in items.items():
        if _is_default(value):
            continue
        compact[str(key)] = _normalise(value)
    return compact


def _signature(items: dict[str, Any]) -> str:
    encoded = json.dumps(
        _compact_mapping(items),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _food_date_key() -> str:
    value = st.session_state.get("hm_food_journal_date")
    if isinstance(value, (dt.datetime, dt.date)):
        return value.date().isoformat() if isinstance(value, dt.datetime) else value.isoformat()
    return str(value or "").strip()[:10]


def _food_state(date_key: str) -> dict[str, Any]:
    output: dict[str, Any] = {}
    if not date_key:
        return output
    for raw_key, value in list(st.session_state.items()):
        key = str(raw_key)
        if key.startswith(_AUTOSAVE_CONTROL_PREFIXES):
            continue
        if date_key not in key:
            continue
        if not any(marker in key for marker in _FOOD_KEY_MARKERS):
            continue
        output[key] = value
    return _compact_mapping(output)


def _exercise_state(button_key: str) -> dict[str, Any]:
    base = button_key[:-5] if button_key.endswith("_save") else button_key
    return _compact_mapping(
        {
            "status": st.session_state.get(f"{base}_status"),
            "completion_time": st.session_state.get(f"{base}_time"),
            "member_notes": st.session_state.get(f"{base}_notes"),
        }
    )


def _food_baseline_key(date_key: str) -> str:
    member_id = str(st.session_state.get("user_id") or "member")
    return f"_hm_food_autosave_baseline_{member_id}_{date_key}"


def _exercise_baseline_key(button_key: str) -> str:
    member_id = str(st.session_state.get("user_id") or "member")
    return f"_hm_exercise_autosave_baseline_{member_id}_{button_key}"


def _clear_silent_feedback() -> None:
    st.session_state.pop(_SILENT_MESSAGE_KEY, None)
    st.session_state.pop(_SILENT_RERUN_KEY, None)


def _arm_silent_feedback(kind: str) -> None:
    st.session_state[_SILENT_MESSAGE_KEY] = kind
    st.session_state[_SILENT_RERUN_KEY] = kind
    st.session_state["_hm_last_journal_autosave"] = kind


def _should_autosave_food() -> bool:
    date_key = _food_date_key()
    state = _food_state(date_key)
    signature = _signature(state)
    baseline_key = _food_baseline_key(date_key)
    baseline = st.session_state.get(baseline_key)
    if baseline is None:
        st.session_state[baseline_key] = signature
        return False
    if not state or signature == baseline:
        return False
    st.session_state[baseline_key] = signature
    _arm_silent_feedback("food")
    return True


def _should_autosave_exercise(button_key: str) -> bool:
    state = _exercise_state(button_key)
    signature = _signature(state)
    baseline_key = _exercise_baseline_key(button_key)
    baseline = st.session_state.get(baseline_key)
    if baseline is None:
        st.session_state[baseline_key] = signature
        return False
    if signature == baseline:
        return False
    st.session_state[baseline_key] = signature
    _arm_silent_feedback("exercise")
    return True


def _install_silent_feedback_wrappers() -> None:
    current_message = flash.set_system_message
    if not getattr(current_message, _FLASH_MARKER, False):
        @functools.wraps(current_message)
        def set_message_without_autosave_jump(message: str, *args: Any, **kwargs: Any):
            if st.session_state.pop(_SILENT_MESSAGE_KEY, None):
                return None
            return current_message(message, *args, **kwargs)

        setattr(set_message_without_autosave_jump, _FLASH_MARKER, True)
        set_message_without_autosave_jump._hm_original = current_message
        flash.set_system_message = set_message_without_autosave_jump

    current_rerun = st.rerun
    if not getattr(current_rerun, _RERUN_MARKER, False):
        @functools.wraps(current_rerun)
        def rerun_without_autosave_jump(*args: Any, **kwargs: Any):
            if st.session_state.pop(_SILENT_RERUN_KEY, None):
                return None
            return current_rerun(*args, **kwargs)

        setattr(rerun_without_autosave_jump, _RERUN_MARKER, True)
        rerun_without_autosave_jump._hm_original = current_rerun
        st.rerun = rerun_without_autosave_jump


def install_member_journal_server_autosave() -> None:
    """Autosave committed Daily Log changes without visible feedback or jumping.

    The wrapper is server-side. It reuses the existing Save Day and Save Progress
    handlers as the only persistence authorities. Autosave suppresses only the
    success flash and explicit rerun generated by those handlers; manual saves keep
    their existing confirmation and rerun behaviour.
    """

    _install_silent_feedback_wrappers()

    current_button = st.button
    if getattr(current_button, _MARKER, False):
        return

    @functools.wraps(current_button)
    def button_with_server_autosave(label: str, *args: Any, **kwargs: Any) -> bool:
        # Any new widget transaction clears stale feedback flags from a failed save.
        _clear_silent_feedback()
        clicked = bool(current_button(label, *args, **kwargs))
        if _current_page_filename() != _DAILY_LOG_PAGE:
            return clicked

        text = str(label or "").strip()
        button_key = str(kwargs.get("key") or "")

        if text == _FOOD_BUTTON:
            date_key = _food_date_key()
            if clicked:
                st.session_state[_food_baseline_key(date_key)] = _signature(
                    _food_state(date_key)
                )
                return True
            return _should_autosave_food()

        if text == _EXERCISE_BUTTON and button_key:
            if clicked:
                st.session_state[_exercise_baseline_key(button_key)] = _signature(
                    _exercise_state(button_key)
                )
                return True
            return _should_autosave_exercise(button_key)

        return clicked

    setattr(button_with_server_autosave, _MARKER, True)
    button_with_server_autosave._hm_original = current_button
    st.button = button_with_server_autosave
