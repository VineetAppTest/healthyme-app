from __future__ import annotations

import functools
import inspect
import re
from typing import Any, Callable

import streamlit as st


_MARKER = "_hm_repository_create_form_success_v1"
_PAGE_SUFFIXES = {
    "recipe": "pages/15_Admin_Recipe_Manager.py",
    "exercise": "pages/16_Admin_Exercise_Manager.py",
    "supplement": "pages/39_Admin_Supplement_Manager.py",
}
_CONFIG = {
    "recipe": {
        "form_function": "recipe_form",
        "base_prefix": "new_recipe_repository",
        "version_key": "_hm_recipe_repository_create_version",
        "flash_key": "hm_recipe_repository_flash",
        "saved_message": "Recipe saved.",
        "pending_key": "_hm_recipe_repository_create_success",
        "save_label": "Save Recipe",
        "display_message": "Recipe saved successfully. The form is ready for a new recipe.",
        "uploaded_meta_key": "new_recipe_repository_uploaded_image_meta",
    },
    "exercise": {
        "form_function": "exercise_form",
        "base_prefix": "new_exercise_repository",
        "version_key": "_hm_exercise_repository_create_version",
        "flash_key": "hm_exercise_repository_flash",
        "saved_message": "Exercise saved.",
        "pending_key": "_hm_exercise_repository_create_success",
        "save_label": "Save Exercise",
        "display_message": "Exercise saved successfully. The form is ready for a new exercise.",
        "uploaded_meta_key": "new_exercise_repository_uploaded_image_meta",
    },
    "supplement": {
        "flash_key": "hm_supplement_repository_flash",
        "saved_message": "Supplement added to repository.",
        "pending_key": "_hm_supplement_repository_create_success",
        "save_label": "Add to Repository",
        # Do not begin with "Supplement added" because the established hygiene
        # wrapper uses that exact prefix to advance its form version.
        "display_message": "Saved successfully. The form is ready for a new supplement.",
    },
}


def _page_context() -> tuple[str, Any | None]:
    frame = inspect.currentframe()
    frame = frame.f_back if frame is not None else None
    while frame is not None:
        path = str((frame.f_globals or {}).get("__file__") or "").replace("\\", "/")
        for kind, suffix in _PAGE_SUFFIXES.items():
            if path.endswith(suffix):
                return kind, frame
        frame = frame.f_back
    return "", None


def _page_kind() -> str:
    return _page_context()[0]


def _inside_create_form(kind: str) -> bool:
    config = _CONFIG.get(kind) or {}
    function_name = str(config.get("form_function") or "")
    base_prefix = str(config.get("base_prefix") or "")
    if not function_name or not base_prefix:
        return False

    frame = inspect.currentframe()
    frame = frame.f_back if frame is not None else None
    while frame is not None:
        path = str((frame.f_globals or {}).get("__file__") or "").replace("\\", "/")
        if path.endswith(_PAGE_SUFFIXES[kind]):
            if frame.f_code.co_name == function_name:
                return str(frame.f_locals.get("prefix") or "") == base_prefix
            if frame.f_code.co_name == "<module>":
                return False
        frame = frame.f_back
    return False


def _version(kind: str) -> int:
    key = str((_CONFIG.get(kind) or {}).get("version_key") or "")
    if not key:
        return 1
    try:
        return max(int(st.session_state.get(key, 1) or 1), 1)
    except Exception:
        return 1


def _advance(kind: str) -> None:
    if kind == "supplement":
        raw_scope = st.session_state.get("hm_v1023a_supp_member", "member")
        scope = re.sub(r"[^A-Za-z0-9]+", "_", str(raw_scope or "")).strip("_") or "member"
        key = f"_hm_supplement_create_version_{scope}"
        try:
            current = max(int(st.session_state.get(key, 1) or 1), 1)
        except Exception:
            current = 1
        st.session_state[key] = current + 1
        return

    key = str((_CONFIG.get(kind) or {}).get("version_key") or "")
    if key:
        st.session_state[key] = _version(kind) + 1


def _label(args: tuple[Any, ...], kwargs: dict[str, Any]) -> str:
    return str(args[0] if args else kwargs.get("label", ""))


def _version_widget_key(kind: str, kwargs: dict[str, Any]) -> dict[str, Any]:
    if kind not in {"recipe", "exercise"} or not _inside_create_form(kind):
        return kwargs
    key = kwargs.get("key")
    base_prefix = str(_CONFIG[kind]["base_prefix"])
    if key and str(key).startswith(base_prefix):
        kwargs = dict(kwargs)
        kwargs["key"] = f"{key}__v{_version(kind)}"
    return kwargs


def _flash_message(payload: Any) -> str:
    if isinstance(payload, (tuple, list)) and len(payload) >= 2:
        return str(payload[1] or "")
    return str(payload or "")


def install_repository_create_form_success() -> None:
    current_button = st.button
    if getattr(current_button, _MARKER, False):
        return

    current_text_input = st.text_input
    current_text_area = st.text_area
    current_selectbox = st.selectbox
    current_multiselect = st.multiselect
    current_file_uploader = st.file_uploader
    current_form_submit_button = st.form_submit_button
    current_success = st.success
    current_rerun = st.rerun

    def wrap_widget(current_widget: Callable[..., Any]):
        @functools.wraps(current_widget)
        def widget_with_create_version(*args, **kwargs):
            kind = _page_kind()
            kwargs = _version_widget_key(kind, kwargs)
            return current_widget(*args, **kwargs)

        setattr(widget_with_create_version, _MARKER, True)
        return widget_with_create_version

    @functools.wraps(current_button)
    def button_with_create_feedback(*args, **kwargs):
        kind = _page_kind()
        label = _label(args, kwargs)
        config = _CONFIG.get(kind) or {}

        if kind in {"recipe", "exercise"}:
            key = kwargs.get("key")
            base_prefix = str(config.get("base_prefix") or "")
            if key and str(key).startswith(base_prefix):
                kwargs = dict(kwargs)
                kwargs["key"] = f"{key}__v{_version(kind)}"

        result = current_button(*args, **kwargs)
        if label == str(config.get("save_label") or ""):
            message = str(st.session_state.pop(str(config.get("pending_key") or ""), "") or "")
            if message:
                current_success(message)
        return result

    @functools.wraps(current_form_submit_button)
    def form_submit_with_create_feedback(*args, **kwargs):
        kind = _page_kind()
        label = _label(args, kwargs)
        config = _CONFIG.get(kind) or {}
        result = current_form_submit_button(*args, **kwargs)
        if kind == "supplement" and label == str(config.get("save_label") or ""):
            message = str(st.session_state.pop(str(config.get("pending_key") or ""), "") or "")
            if message:
                current_success(message)
        return result

    @functools.wraps(current_rerun)
    def rerun_with_confirmed_create_reset(*args, **kwargs):
        kind = _page_kind()
        config = _CONFIG.get(kind) or {}
        flash_key = str(config.get("flash_key") or "")
        saved_message = str(config.get("saved_message") or "")
        payload = st.session_state.get(flash_key) if flash_key else None

        if saved_message and _flash_message(payload) == saved_message:
            _advance(kind)
            pending_key = str(config.get("pending_key") or "")
            if pending_key:
                st.session_state[pending_key] = str(config.get("display_message") or saved_message)
            if flash_key:
                st.session_state.pop(flash_key, None)
            uploaded_meta_key = str(config.get("uploaded_meta_key") or "")
            if uploaded_meta_key:
                st.session_state.pop(uploaded_meta_key, None)

        return current_rerun(*args, **kwargs)

    st.text_input = wrap_widget(current_text_input)
    st.text_area = wrap_widget(current_text_area)
    st.selectbox = wrap_widget(current_selectbox)
    st.multiselect = wrap_widget(current_multiselect)
    st.file_uploader = wrap_widget(current_file_uploader)
    st.button = button_with_create_feedback
    st.form_submit_button = form_submit_with_create_feedback
    st.rerun = rerun_with_confirmed_create_reset
