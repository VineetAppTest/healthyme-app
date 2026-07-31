from __future__ import annotations

import functools
import inspect
import re
from typing import Any

import streamlit as st


_MARKER = "_hm_notes_supplement_form_hygiene_v1"
_NOTES_PAGE = "pages/36_Admin_Nutritionist_Notes_Workbench.py"
_SUPPLEMENT_PAGE = "pages/39_Admin_Supplement_Manager.py"
_NOTES_MEMBER_KEY = "hm_h9a4_note_member"
_PENDING_NOTES_SUCCESS = "_hm_h9a4_pending_success"


def _page_kind() -> str:
    """Walk outward until the actual Streamlit page frame is found."""
    frame = inspect.currentframe()
    frame = frame.f_back if frame is not None else None
    while frame is not None:
        path = str((frame.f_globals or {}).get("__file__") or "").replace("\\", "/")
        if path.endswith(_NOTES_PAGE):
            return "notes"
        if path.endswith(_SUPPLEMENT_PAGE):
            return "supplement"
        frame = frame.f_back
    return ""


def _slug(value: Any) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", str(value or "")).strip("_") or "default"


def _scope(kind: str) -> str:
    if kind == "notes":
        return _slug(st.session_state.get(_NOTES_MEMBER_KEY, "member"))
    if kind == "supplement":
        return _slug(st.session_state.get("hm_v1023a_supp_member", "member"))
    return "default"


def _version_key(kind: str, scope: str) -> str:
    return f"_hm_{kind}_create_version_{scope}"


def _version(kind: str, scope: str) -> int:
    key = _version_key(kind, scope)
    return max(int(st.session_state.get(key, 1) or 1), 1)


def _advance(kind: str, scope: str) -> None:
    key = _version_key(kind, scope)
    st.session_state[key] = _version(kind, scope) + 1


def _replace_first_arg(args: tuple[Any, ...], value: Any) -> tuple[Any, ...]:
    if not args:
        return (value,)
    return (value, *args[1:])


def install_notes_supplement_form_hygiene() -> None:
    current_form = st.form
    if getattr(current_form, _MARKER, False):
        return

    current_selectbox = st.selectbox
    current_checkbox = st.checkbox
    current_date_input = st.date_input
    current_success = st.success
    current_rerun = st.rerun

    @functools.wraps(current_form)
    def form_with_success_version(*args, **kwargs):
        kind = _page_kind()
        form_key = kwargs.get("key") if "key" in kwargs else (args[0] if args else "")
        if kind == "notes" and str(form_key) == "h9a4_structured_note_form":
            scope = _scope(kind)
            version = _version(kind, scope)
            args = _replace_first_arg(args, f"h9a4_structured_note_form_{scope}_{version}")
            kwargs.pop("key", None)
            kwargs["clear_on_submit"] = False
        elif kind == "supplement" and str(form_key) == "hm_v1023a_add_supplement_form":
            scope = _scope(kind)
            version = _version(kind, scope)
            args = _replace_first_arg(args, f"hm_v1023a_add_supplement_form_{scope}_{version}")
            kwargs.pop("key", None)
            kwargs["clear_on_submit"] = False
        return current_form(*args, **kwargs)

    @functools.wraps(current_selectbox)
    def selectbox_with_stable_context(*args, **kwargs):
        kind = _page_kind()
        label = str(args[0] if args else kwargs.get("label", ""))
        if kind == "notes" and label == "Member":
            kwargs.setdefault("key", _NOTES_MEMBER_KEY)
        elif kind == "supplement" and kwargs.get("key") == "hm_v1023a_add_frequency":
            scope = _scope(kind)
            version = _version(kind, scope)
            kwargs["key"] = f"hm_v1023a_add_frequency_{scope}_{version}"
        return current_selectbox(*args, **kwargs)

    @functools.wraps(current_checkbox)
    def checkbox_with_success_version(*args, **kwargs):
        kind = _page_kind()
        if kind == "supplement" and kwargs.get("key") == "hm_v1023a_add_end_enabled":
            scope = _scope(kind)
            version = _version(kind, scope)
            kwargs["key"] = f"hm_v1023a_add_end_enabled_{scope}_{version}"
        return current_checkbox(*args, **kwargs)

    @functools.wraps(current_date_input)
    def date_input_with_success_version(*args, **kwargs):
        kind = _page_kind()
        if kind == "supplement" and kwargs.get("key") == "hm_v1023a_add_end_date":
            scope = _scope(kind)
            version = _version(kind, scope)
            kwargs["key"] = f"hm_v1023a_add_end_date_{scope}_{version}"
        return current_date_input(*args, **kwargs)

    @functools.wraps(current_success)
    def success_with_confirmed_reset(body, *args, **kwargs):
        kind = _page_kind()
        text = str(body or "")
        if kind == "notes" and text.startswith("Published note "):
            scope = _scope(kind)
            _advance(kind, scope)
            st.session_state[_PENDING_NOTES_SUCCESS] = text
            current_rerun()
            return None
        if kind == "supplement" and text.startswith("Supplement added"):
            scope = _scope(kind)
            _advance(kind, scope)
        return current_success(body, *args, **kwargs)

    setattr(form_with_success_version, _MARKER, True)
    setattr(selectbox_with_stable_context, _MARKER, True)
    setattr(checkbox_with_success_version, _MARKER, True)
    setattr(date_input_with_success_version, _MARKER, True)
    setattr(success_with_confirmed_reset, _MARKER, True)

    st.form = form_with_success_version
    st.selectbox = selectbox_with_stable_context
    st.checkbox = checkbox_with_success_version
    st.date_input = date_input_with_success_version
    st.success = success_with_confirmed_reset

    from components import ui_common

    current_topbar = ui_common.topbar
    if not getattr(current_topbar, _MARKER, False):
        @functools.wraps(current_topbar)
        def topbar_with_notes_success(title, *args, **kwargs):
            result = current_topbar(title, *args, **kwargs)
            if str(title or "").strip() == "Nutritionist Notes Workbench":
                message = str(st.session_state.pop(_PENDING_NOTES_SUCCESS, "") or "")
                if message:
                    current_success(message)
            return result

        setattr(topbar_with_notes_success, _MARKER, True)
        ui_common.topbar = topbar_with_notes_success
