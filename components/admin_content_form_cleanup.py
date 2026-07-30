from __future__ import annotations

import functools
import inspect
from dataclasses import dataclass
from typing import Any

import streamlit as st


_MARKER = "_hm_admin_content_form_cleanup_v1"
_PENDING_MESSAGE = "_hm_admin_content_pending_success"
_PENDING_PAGE = "_hm_admin_content_pending_page"
_PENDING_SECTION = "_hm_admin_content_pending_section"
_PENDING_RESET_PREFIXES = "_hm_admin_content_pending_reset_prefixes"

_PAGE_CONFIG = {
    "recipe": {
        "suffix": "pages/15_Admin_Recipe_Manager.py",
        "labels": (
            "Current Repository",
            "Add Recipe",
            "Import CSV",
            "Edit / Delete",
            "Member Feedback",
            "Allocate to Member",
        ),
        "visible": ("Current Repository", "Add Recipe", "Import CSV", "Edit / Delete"),
        "state_key": "hm_admin_recipe_active_section",
    },
    "exercise": {
        "suffix": "pages/16_Admin_Exercise_Manager.py",
        "labels": (
            "Current Repository",
            "Add Exercise",
            "Import CSV",
            "Edit / Delete",
            "Member Feedback",
            "Allocate to Member",
        ),
        "visible": ("Current Repository", "Add Exercise", "Import CSV", "Edit / Delete"),
        "state_key": "hm_admin_exercise_active_section",
    },
    "supplement": {
        "suffix": "pages/39_Admin_Supplement_Manager.py",
    },
}


def _frame_page(frame) -> str:
    return str((frame.f_globals if frame is not None else {}).get("__file__") or "").replace("\\", "/")


def _page_key(frame) -> str:
    page_file = _frame_page(frame)
    for key, config in _PAGE_CONFIG.items():
        if page_file.endswith(str(config["suffix"])):
            return key
    return ""


def _activate_section(page_key: str, label: str) -> None:
    config = _PAGE_CONFIG.get(page_key, {})
    if label in tuple(config.get("visible") or ()):
        st.session_state[str(config.get("state_key"))] = label


def _stage_reset(prefixes: tuple[str, ...]) -> None:
    st.session_state[_PENDING_RESET_PREFIXES] = list(prefixes)


def _apply_staged_reset() -> None:
    prefixes = tuple(st.session_state.pop(_PENDING_RESET_PREFIXES, []) or [])
    if not prefixes:
        return
    for key in list(st.session_state.keys()):
        if any(str(key).startswith(prefix) for prefix in prefixes):
            st.session_state.pop(key, None)


def _success_contract(page_key: str, message: str) -> tuple[str, tuple[str, ...]] | None:
    text = str(message or "").strip()
    if page_key == "recipe":
        if text == "Recipe saved.":
            return "Add Recipe", ("new_recipe_v93",)
        if text == "Recipe updated.":
            return "Current Repository", ("edit_recipe_v93_",)
        if text == "Recipe deleted.":
            return "Current Repository", ("edit_recipe_v93_",)
        if text.startswith("CSV imported."):
            return "Import CSV", ("recipe_csv_",)
    if page_key == "exercise":
        if text == "Exercise saved.":
            return "Add Exercise", ("new_exercise_v93",)
        if text == "Exercise updated.":
            return "Current Repository", ("edit_exercise_v93_",)
        if text == "Exercise deleted.":
            return "Current Repository", ("edit_exercise_v93_",)
        if text.startswith("CSV imported."):
            return "Import CSV", ("exercise_csv_",)
    if page_key == "supplement":
        if text.startswith("Supplement added"):
            return "Add Supplement", ("hm_v1023a_add_",)
        if text.startswith("Supplement updated"):
            return "Active Supplements", ("edit_",)
        if text.startswith("Supplement stopped"):
            return "Active Supplements", ("stop_",)
    return None


def _stage_success(page_key: str, message: str, section: str, prefixes: tuple[str, ...]) -> None:
    st.session_state[_PENDING_MESSAGE] = str(message)
    st.session_state[_PENDING_PAGE] = page_key
    st.session_state[_PENDING_SECTION] = section
    _stage_reset(prefixes)
    config = _PAGE_CONFIG.get(page_key, {})
    state_key = str(config.get("state_key") or "")
    if state_key and section in tuple(config.get("visible") or ()):
        st.session_state[state_key] = section


def _pop_success(page_key: str, section: str) -> str:
    if st.session_state.get(_PENDING_PAGE) != page_key:
        return ""
    target = str(st.session_state.get(_PENDING_SECTION) or "")
    if target and target != section:
        return ""
    message = str(st.session_state.pop(_PENDING_MESSAGE, "") or "")
    st.session_state.pop(_PENDING_PAGE, None)
    st.session_state.pop(_PENDING_SECTION, None)
    return message


@dataclass
class _AdminSectionContext:
    page_key: str
    label: str
    active: bool
    original_success: Any
    _context: Any = None

    def __enter__(self):
        container = st.container(border=True)
        self._context = container.__enter__()
        marker = "active" if self.active else "inactive"
        st.markdown(
            f"<span class='hm-admin-content-section-{marker}'></span>",
            unsafe_allow_html=True,
        )
        if self.active:
            message = _pop_success(self.page_key, self.label)
            if message:
                self.original_success(message)
        return self._context

    def __exit__(self, exc_type, exc, traceback):
        return self._context.__exit__(exc_type, exc, traceback)


def _render_selector(page_key: str, original_success: Any) -> list[_AdminSectionContext]:
    config = _PAGE_CONFIG[page_key]
    _apply_staged_reset()
    visible = tuple(config["visible"])
    state_key = str(config["state_key"])
    selected = str(st.session_state.get(state_key) or visible[0])
    if selected not in visible:
        selected = visible[0]
        st.session_state[state_key] = selected

    st.markdown(
        """
<style id="hm-admin-content-selector-v1">
div[data-testid="stVerticalBlockBorderWrapper"]:has(.hm-admin-content-section-inactive){display:none!important;}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.hm-admin-content-section-active){border:0!important;background:transparent!important;box-shadow:none!important;padding:0!important;margin:.30rem 0 0 0!important;}
.hm-admin-content-section-active,.hm-admin-content-section-inactive{display:none!important;height:0!important;margin:0!important;padding:0!important;}
.hm-admin-content-selector-anchor{display:block;height:0;margin:0;padding:0;overflow:hidden;}
.hm-admin-content-selector-anchor + div[data-testid="stHorizontalBlock"]{gap:.45rem!important;margin:.25rem 0 .42rem 0!important;}
.hm-admin-content-selector-anchor + div[data-testid="stHorizontalBlock"] button{min-height:2.55rem!important;padding:.42rem .55rem!important;border-radius:12px!important;font-size:.80rem!important;font-weight:900!important;}
@media(max-width:760px){.hm-admin-content-selector-anchor + div[data-testid="stHorizontalBlock"]{display:grid!important;grid-template-columns:1fr 1fr!important}.hm-admin-content-selector-anchor + div[data-testid="stHorizontalBlock"]>div{width:100%!important}}
</style>
<span class="hm-admin-content-selector-anchor"></span>
        """,
        unsafe_allow_html=True,
    )
    columns = st.columns(4, gap="small")
    for column, label in zip(columns, visible):
        with column:
            st.button(
                label,
                key=f"hm_admin_{page_key}_section_{label.lower().replace(' ', '_').replace('/', '_')}",
                type="primary" if selected == label else "secondary",
                use_container_width=True,
                on_click=_activate_section,
                args=(page_key, label),
            )

    return [
        _AdminSectionContext(
            page_key=page_key,
            label=label,
            active=(label == selected and label in visible),
            original_success=original_success,
        )
        for label in tuple(config["labels"])
    ]


def install_admin_content_form_cleanup() -> None:
    current_tabs = st.tabs
    current_success = st.success
    if getattr(current_tabs, _MARKER, False):
        return

    @functools.wraps(current_tabs)
    def stable_admin_content_sections(labels, *args, **kwargs):
        caller = inspect.currentframe().f_back
        page_key = _page_key(caller)
        config = _PAGE_CONFIG.get(page_key, {})
        if page_key not in {"recipe", "exercise"} or tuple(str(x) for x in labels) != tuple(config.get("labels") or ()):
            return current_tabs(labels, *args, **kwargs)
        return _render_selector(page_key, current_success)

    @functools.wraps(current_success)
    def success_with_persistent_reset(body, *args, **kwargs):
        caller = inspect.currentframe().f_back
        page_key = _page_key(caller)
        contract = _success_contract(page_key, str(body or "")) if page_key else None
        if contract is not None:
            section, prefixes = contract
            _stage_success(page_key, str(body), section, prefixes)
        return current_success(body, *args, **kwargs)

    setattr(stable_admin_content_sections, _MARKER, True)
    setattr(success_with_persistent_reset, _MARKER, True)
    st.tabs = stable_admin_content_sections
    st.success = success_with_persistent_reset

    from components import ui_common

    current_topbar = ui_common.topbar
    if not getattr(current_topbar, _MARKER, False):
        @functools.wraps(current_topbar)
        def topbar_with_supplement_success(title, *args, **kwargs):
            _apply_staged_reset()
            result = current_topbar(title, *args, **kwargs)
            if str(title or "").strip() == "Supplement Management":
                message = _pop_success("supplement", str(st.session_state.get(_PENDING_SECTION) or ""))
                if message:
                    current_success(message)
            return result

        setattr(topbar_with_supplement_success, _MARKER, True)
        ui_common.topbar = topbar_with_supplement_success
