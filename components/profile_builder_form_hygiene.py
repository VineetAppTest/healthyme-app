from __future__ import annotations

from typing import Any, Dict

import streamlit as st

from components.form_hygiene import (
    clear_prefixed_widget_state,
    clear_widget_state,
)


_INSTALLED = False

_SETUP_SAVE_PENDING = "pbm_hygiene_setup_save_pending"
_CLONE_SUCCESS_PENDING = "pbm_hygiene_clone_success_pending"
_CLONE_CLEAR_PENDING = "pbm_hygiene_clone_clear_pending"
_MODULE_SAVE_PENDING = "pbm_hygiene_module_save_pending"
_PUBLISH_SUCCESS_PENDING = "pbm_hygiene_publish_success_pending"
_WIDGET_CLEANUP_PENDING = "pbm_hygiene_widget_cleanup_pending"

_SETUP_FLASH = "pbm_hygiene_setup_flash"
_MODULE_FLASH = "pbm_hygiene_module_flash"
_PUBLISH_FLASH = "pbm_hygiene_publish_flash"

_PROFILE_WIDGET_PREFIXES = (
    "pbm_row_",
    "pbm_profile_name_",
    "pbm_profile_change_note_",
    "pbm_profile_region_",
    "pbm_profile_age_band_",
    "pbm_profile_health_concerns_",
    "pbm_profile_diet_type_",
    "pbm_profile_member_",
    "pbm_profile_note_",
    "pbm_profile_start_date_",
)


def _text(value: object) -> str:
    return str(value or "").strip()


def _set_flash(key: str, message: str, kind: str = "success") -> None:
    st.session_state[key] = {"kind": kind, "message": _text(message)}


def _render_flash(key: str) -> None:
    flash = st.session_state.pop(key, None)
    if not isinstance(flash, dict):
        return
    message = _text(flash.get("message"))
    if not message:
        return
    kind = _text(flash.get("kind"))
    if kind == "warning":
        st.warning(message)
    elif kind == "error":
        st.error(message)
    else:
        st.success(message)


def _schedule_widget_cleanup() -> None:
    st.session_state[_WIDGET_CLEANUP_PENDING] = True


def _consume_widget_cleanup() -> None:
    if not st.session_state.pop(_WIDGET_CLEANUP_PENDING, False):
        return
    # The saved profile remains in pbm_profile/pbm_items. Only stale widget copies
    # from the previous epoch are removed before the canonical values render again.
    clear_prefixed_widget_state(_PROFILE_WIDGET_PREFIXES)


def _clear_clone_selector() -> None:
    clear_prefixed_widget_state(("pbm_profile_clone_source",))


def install_profile_builder_form_hygiene() -> None:
    """Install success-only reset behaviour for Recommendation Profile Builder.

    Profile Builder is a continuing edit workflow, so successful saves reload the
    persisted profile rather than opening a blank form. Validation and persistence
    failures never schedule cleanup and therefore retain all entered values.
    """

    global _INSTALLED
    if _INSTALLED:
        return

    import components.pbm_core as pbm_core
    import components.pbm_modules as pbm_modules
    import components.pbm_setup as pbm_setup
    import components.profile_publish_control_v2 as publish_control

    original_setup_save = pbm_setup.save_profile_shell
    original_setup_load_profile = pbm_setup.load_profile
    original_render_setup = pbm_setup.render_setup

    def save_profile_shell_with_hygiene(profile: Dict[str, Any]):
        result = original_setup_save(profile)
        ok, profile_id, message = result
        if ok:
            st.session_state[_SETUP_SAVE_PENDING] = {
                "profile_id": _text(profile_id),
                "message": _text(message),
            }
        return result

    def load_clone_source_with_hygiene(profile_id: str):
        result = original_setup_load_profile(profile_id)
        if result and bool(result[0]):
            st.session_state[_CLONE_SUCCESS_PENDING] = True
        return result

    def render_setup_with_hygiene(options) -> None:
        _consume_widget_cleanup()
        if st.session_state.pop(_CLONE_CLEAR_PENDING, False):
            _clear_clone_selector()
        if st.session_state.pop(_CLONE_SUCCESS_PENDING, False):
            _clear_clone_selector()
            clear_prefixed_widget_state(_PROFILE_WIDGET_PREFIXES)
            _set_flash(
                _SETUP_FLASH,
                "Profile Setup cloned as a new Draft. Recommendation rows were not copied.",
            )
        _render_flash(_SETUP_FLASH)

        original_render_setup(options)

        pending = st.session_state.pop(_SETUP_SAVE_PENDING, None)
        if not isinstance(pending, dict):
            return
        profile_id = _text(pending.get("profile_id"))
        reload_ok, reload_message = pbm_core.load_selected(profile_id, shell_only=False)
        if reload_ok:
            st.session_state[_CLONE_CLEAR_PENDING] = True
            _schedule_widget_cleanup()
            _set_flash(_SETUP_FLASH, _text(pending.get("message")))
            st.rerun()
        st.success(_text(pending.get("message")))
        st.warning(
            "The profile was saved, but its canonical values could not be reloaded. "
            f"Your current screen has been retained. {_text(reload_message)}"
        )

    pbm_setup.save_profile_shell = save_profile_shell_with_hygiene
    pbm_setup.load_profile = load_clone_source_with_hygiene
    pbm_setup.render_setup = render_setup_with_hygiene

    original_module_save = pbm_modules.save_profile_module
    original_render_module = pbm_modules.render_module

    def save_profile_module_with_hygiene(
        profile_id: str,
        member_id: str,
        item_type: str,
        items,
        **kwargs,
    ):
        result = original_module_save(
            profile_id,
            member_id,
            item_type,
            items,
            **kwargs,
        )
        ok, message = result
        if ok:
            st.session_state[_MODULE_SAVE_PENDING] = {
                "module": _text(item_type),
                "profile_id": _text(profile_id),
                "message": _text(message),
            }
        return result

    def render_module_with_hygiene(kind: str, options) -> None:
        _consume_widget_cleanup()
        flash = st.session_state.get(_MODULE_FLASH)
        if isinstance(flash, dict) and _text(flash.get("module")) == _text(kind):
            st.session_state.pop(_MODULE_FLASH, None)
            message = _text(flash.get("message"))
            if message:
                st.success(message)

        original_render_module(kind, options)

        pending = st.session_state.get(_MODULE_SAVE_PENDING)
        if not isinstance(pending, dict) or _text(pending.get("module")) != _text(kind):
            return
        st.session_state.pop(_MODULE_SAVE_PENDING, None)
        profile_id = _text(pending.get("profile_id"))
        reload_ok, reload_message = pbm_core.load_selected(profile_id, shell_only=False)
        if reload_ok:
            _schedule_widget_cleanup()
            st.session_state[_MODULE_FLASH] = {
                "module": _text(kind),
                "message": _text(pending.get("message")),
            }
            st.rerun()
        st.success(_text(pending.get("message")))
        st.warning(
            "The module was saved, but its canonical values could not be reloaded. "
            f"Your current screen has been retained. {_text(reload_message)}"
        )

    pbm_modules.save_profile_module = save_profile_module_with_hygiene
    pbm_modules.render_module = render_module_with_hygiene

    original_activate_profile = publish_control.activate_profile
    original_render_publish = publish_control.render_profile_publish_control

    def activate_profile_with_hygiene(profile, confirm_text: str):
        result = original_activate_profile(profile, confirm_text)
        success, message = result
        if success:
            st.session_state[_PUBLISH_SUCCESS_PENDING] = {
                "profile_id": _text((profile or {}).get("id")),
                "message": _text(message),
            }
        return result

    def render_publish_with_hygiene() -> None:
        _consume_widget_cleanup()
        pending = st.session_state.pop(_PUBLISH_SUCCESS_PENDING, None)
        if isinstance(pending, dict):
            clear_widget_state(("publish_draft_choice", "hm_publish_review_rows_open"))
            profile_id = _text(pending.get("profile_id"))
            loaded_profile_id = _text(st.session_state.get("pbm_loaded_profile_id"))
            if profile_id and loaded_profile_id == profile_id:
                reload_ok, reload_message = pbm_core.load_selected(
                    profile_id,
                    shell_only=False,
                )
                if reload_ok:
                    clear_prefixed_widget_state(_PROFILE_WIDGET_PREFIXES)
                else:
                    _set_flash(
                        _PUBLISH_FLASH,
                        "Profile activation succeeded, but the loaded Builder copy could not "
                        f"be refreshed. {_text(reload_message)}",
                        kind="warning",
                    )
            if _PUBLISH_FLASH not in st.session_state:
                _set_flash(_PUBLISH_FLASH, _text(pending.get("message")))
        _render_flash(_PUBLISH_FLASH)
        original_render_publish()

    publish_control.activate_profile = activate_profile_with_hygiene
    publish_control.render_profile_publish_control = render_publish_with_hygiene

    _INSTALLED = True
