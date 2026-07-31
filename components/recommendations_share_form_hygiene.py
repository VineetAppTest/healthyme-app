from __future__ import annotations

import functools
import inspect
import re
from typing import Any

import streamlit as st


_MARKER = "_hm_recommendations_share_form_hygiene_v1"
_PAGE = "pages/35_Admin_Recommendations_Share.py"
_PAGE_TITLE = "Recommendations Share"
_MEMBER_SELECTOR_KEY = "hm_v1024_rec_member"
_WIDGET_PREFIX = "hm_v1024_"
_ACTIVE_KEY = "_hm_v1024_recommendations_page_active"
_SCOPE_LABEL_KEY = "_hm_v1024_scope_label"
_SCOPE_ID_KEY = "_hm_v1024_scope_id"
_PENDING_SUCCESS_KEY = "_hm_v1024_pending_success"


def _slug(value: Any) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", str(value or "")).strip("_")


def _page_frame():
    frame = inspect.currentframe()
    frame = frame.f_back if frame is not None else None
    while frame is not None:
        path = str((frame.f_globals or {}).get("__file__") or "").replace("\\", "/")
        if path.endswith(_PAGE):
            return frame
        frame = frame.f_back
    return None


def _active() -> bool:
    return bool(st.session_state.get(_ACTIVE_KEY, False))


def _member_scope() -> str:
    label = str(st.session_state.get(_MEMBER_SELECTOR_KEY, "") or "")
    cached_label = str(st.session_state.get(_SCOPE_LABEL_KEY, "") or "")
    cached_scope = str(st.session_state.get(_SCOPE_ID_KEY, "") or "")
    if label and cached_scope and cached_label == label:
        return cached_scope

    frame = _page_frame()
    member_id = ""
    if frame is not None:
        member_id = str(frame.f_locals.get("member_id") or "").strip()
        if not member_id:
            member = frame.f_locals.get("member")
            if isinstance(member, dict):
                member_id = str(member.get("id") or "").strip()

    scope = _slug(member_id or label)
    if scope:
        st.session_state[_SCOPE_LABEL_KEY] = label
        st.session_state[_SCOPE_ID_KEY] = scope
    return scope


def _version_key(scope: str) -> str:
    return f"_hm_v1024_version_{scope}"


def _version(scope: str) -> int:
    try:
        return max(int(st.session_state.get(_version_key(scope), 1) or 1), 1)
    except Exception:
        return 1


def _advance(scope: str) -> None:
    st.session_state[_version_key(scope)] = _version(scope) + 1


def _scoped_widget_key(key: Any) -> Any:
    text = str(key or "")
    if not _active() or not text.startswith(_WIDGET_PREFIX):
        return key
    if text == _MEMBER_SELECTOR_KEY or "__member_" in text:
        return key
    scope = _member_scope()
    if not scope:
        return key
    return f"{text}__member_{scope}__v{_version(scope)}"


def install_recommendations_share_form_hygiene() -> None:
    current_selectbox = st.selectbox
    if getattr(current_selectbox, _MARKER, False):
        return

    widget_names = (
        "selectbox",
        "multiselect",
        "text_input",
        "text_area",
        "date_input",
        "checkbox",
    )
    originals = {name: getattr(st, name) for name in widget_names}
    current_success = st.success

    for name, original in originals.items():
        @functools.wraps(original)
        def scoped_widget(*args, __original=original, **kwargs):
            key = kwargs.get("key")
            if key is not None:
                kwargs = dict(kwargs)
                kwargs["key"] = _scoped_widget_key(key)
            return __original(*args, **kwargs)

        setattr(scoped_widget, _MARKER, True)
        setattr(st, name, scoped_widget)

    @functools.wraps(current_success)
    def success_with_canonical_reload(body, *args, **kwargs):
        text = str(body or "").strip()
        is_completed_save = text == "Draft saved." or text.startswith("Recommendations shared.")
        if is_completed_save and _page_frame() is not None:
            scope = _member_scope()
            if scope:
                _advance(scope)
                st.session_state[_PENDING_SUCCESS_KEY] = {
                    "scope": scope,
                    "message": text,
                }
        return current_success(body, *args, **kwargs)

    setattr(success_with_canonical_reload, _MARKER, True)
    st.success = success_with_canonical_reload

    from components import ui_common

    current_topbar = ui_common.topbar
    if not getattr(current_topbar, _MARKER, False):
        @functools.wraps(current_topbar)
        def topbar_with_recommendation_success(title, *args, **kwargs):
            is_page = str(title or "").strip() == _PAGE_TITLE
            st.session_state[_ACTIVE_KEY] = is_page
            result = current_topbar(title, *args, **kwargs)
            if is_page:
                pending = st.session_state.pop(_PENDING_SUCCESS_KEY, None)
                if isinstance(pending, dict):
                    message = str(pending.get("message") or "Recommendations saved.")
                    current_success(message)
            return result

        setattr(topbar_with_recommendation_success, _MARKER, True)
        ui_common.topbar = topbar_with_recommendation_success
