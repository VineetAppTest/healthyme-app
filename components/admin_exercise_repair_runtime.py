from __future__ import annotations

import functools
import html
import inspect
from dataclasses import dataclass
from typing import Any

import streamlit as st


_MARKER = "_hm_admin_exercise_repair_runtime_v1"
_PAGE_SUFFIX = "pages/16_Admin_Exercise_Manager.py"
_LABELS = (
    "Current Repository",
    "Add Exercise",
    "Import CSV",
    "Edit / Delete",
    "Member Feedback",
    "Allocate to Member",
)
_VISIBLE = ("Current Repository", "Add Exercise", "Import CSV", "Edit / Delete")
_SECTION_STATE = "hm_admin_exercise_active_section"
_FLASH_KEY = "_hm_admin_exercise_repair_flash"
_RESET_KEY = "_hm_admin_exercise_repair_reset_prefixes"


def _page_in_stack() -> bool:
    for frame_info in inspect.stack():
        page_file = str(frame_info.frame.f_globals.get("__file__") or "").replace("\\", "/")
        if page_file.endswith(_PAGE_SUFFIX):
            return True
    return False


def _success_contract(message: str):
    text = str(message or "").strip()
    if text == "Exercise saved.":
        return "Add Exercise", ("new_exercise_v93",)
    if text == "Exercise updated.":
        return "Current Repository", ("edit_exercise_v93_",)
    if text == "Exercise deleted.":
        return "Current Repository", ("edit_exercise_v93_",)
    if text.startswith("CSV imported."):
        return "Import CSV", ("exercise_csv_",)
    return None


def _apply_pending_reset() -> None:
    prefixes = tuple(st.session_state.pop(_RESET_KEY, []) or [])
    if not prefixes:
        return
    for key in list(st.session_state.keys()):
        if any(str(key).startswith(prefix) for prefix in prefixes):
            st.session_state.pop(key, None)


def _stage_success(message: str, section: str, prefixes: tuple[str, ...]) -> None:
    st.session_state[_FLASH_KEY] = {"message": str(message), "section": section}
    st.session_state[_RESET_KEY] = list(prefixes)
    st.session_state[_SECTION_STATE] = section


def _render_pending_success(section: str) -> None:
    payload = st.session_state.get(_FLASH_KEY)
    if not isinstance(payload, dict):
        return
    if str(payload.get("section") or "") != section:
        return
    if str(st.session_state.get(_SECTION_STATE) or "") != section:
        return
    message = html.escape(str(payload.get("message") or ""))
    st.session_state.pop(_FLASH_KEY, None)
    st.markdown(
        f"""
<div id="hm-admin-exercise-success" style="
  background:#ECFDF5;color:#047857;border:1px solid #A7F3D0;
  border-radius:14px;padding:12px 15px;margin:.25rem 0 .8rem 0;
  font-weight:850;box-shadow:0 8px 22px rgba(15,23,42,.06);">
  ✅ <span style="margin-left:6px;">{message}</span>
</div>
        """,
        unsafe_allow_html=True,
    )


@dataclass
class _SectionContext:
    base: Any
    label: str

    def __enter__(self):
        result = self.base.__enter__()
        _render_pending_success(self.label)
        return result

    def __exit__(self, exc_type, exc, traceback):
        return self.base.__exit__(exc_type, exc, traceback)


def _input_value(args, kwargs, default=""):
    if "value" in kwargs:
        return kwargs.get("value")
    if len(args) > 1:
        return args[1]
    return default


def install_admin_exercise_repair_runtime() -> None:
    current_tabs = st.tabs
    if getattr(current_tabs, _MARKER, False):
        return

    current_success = st.success
    current_text_input = st.text_input

    @functools.wraps(current_tabs)
    def exercise_sections_with_repair(labels, *args, **kwargs):
        normalized = tuple(str(label) for label in labels)
        if normalized != _LABELS or not _page_in_stack():
            return current_tabs(labels, *args, **kwargs)
        _apply_pending_reset()
        contexts = current_tabs(labels, *args, **kwargs)
        return [
            _SectionContext(base=context, label=label)
            for context, label in zip(contexts, _LABELS)
        ]

    @functools.wraps(current_success)
    def persistent_exercise_success(body, *args, **kwargs):
        contract = _success_contract(str(body or "")) if _page_in_stack() else None
        if contract is None:
            return current_success(body, *args, **kwargs)
        section, prefixes = contract
        _stage_success(str(body), section, prefixes)
        return None

    @functools.wraps(current_text_input)
    def hide_legacy_calorie_input(label, *args, **kwargs):
        key = str(kwargs.get("key") or "")
        if (
            _page_in_stack()
            and not str(label or "").strip()
            and key.endswith("_hidden_calories_v96")
        ):
            return _input_value((label, *args), kwargs, "")
        return current_text_input(label, *args, **kwargs)

    setattr(exercise_sections_with_repair, _MARKER, True)
    setattr(persistent_exercise_success, _MARKER, True)
    setattr(hide_legacy_calorie_input, _MARKER, True)
    st.tabs = exercise_sections_with_repair
    st.success = persistent_exercise_success
    st.text_input = hide_legacy_calorie_input
