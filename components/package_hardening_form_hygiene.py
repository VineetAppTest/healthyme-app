from __future__ import annotations

from contextlib import contextmanager
from typing import Any

import streamlit as st

from components.form_hygiene import clear_prefixed_widget_state


_INSTALLED = False

_LIBRARY_VERSION = "hm_pkg_hygiene_library_version"
_ASSIGN_VERSION = "hm_pkg_hygiene_assign_version"
_ACTION_VERSION = "hm_pkg_hygiene_action_version"

_LIBRARY_CLEANUP = "hm_pkg_hygiene_library_cleanup"
_LIBRARY_FLASH = "hm_pkg_hygiene_library_flash"
_ASSIGN_FLASH = "hm_pkg_hygiene_assign_flash"
_ACTION_FLASH = "hm_pkg_hygiene_action_flash"

_FORM_VERSIONS = (
    ("hm_pkg_library_form_", _LIBRARY_VERSION),
    ("hm_pkg_assign_form_", _ASSIGN_VERSION),
    ("hm_pkg_action_form_", _ACTION_VERSION),
)


def _text(value: object) -> str:
    return str(value or "").strip()


def _version(key: str) -> int:
    return max(int(st.session_state.get(key, 1) or 1), 1)


def _bump(key: str) -> None:
    st.session_state[key] = _version(key) + 1


def _versioned_form_key(key: object) -> str:
    value = _text(key)
    for prefix, version_key in _FORM_VERSIONS:
        if value.startswith(prefix):
            return f"{value}_v{_version(version_key)}"
    return value


def _set_flash(key: str, message: str) -> None:
    st.session_state[key] = _text(message)


def _render_flash(key: str) -> None:
    message = _text(st.session_state.pop(key, ""))
    if message:
        st.success(message)


def _consume_library_cleanup() -> None:
    prefix = _text(st.session_state.pop(_LIBRARY_CLEANUP, ""))
    if prefix:
        clear_prefixed_widget_state((prefix,))


@contextmanager
def _versioned_package_forms():
    """Give completed Package transactions a new Streamlit form identity.

    The patch is active only while one Package renderer executes. It does not
    alter forms elsewhere in the application.
    """

    original_form = st.form

    def form_with_version(key, *args, **kwargs):
        return original_form(_versioned_form_key(key), *args, **kwargs)

    st.form = form_with_version
    try:
        yield
    finally:
        st.form = original_form


def _write_succeeded(result: Any) -> bool:
    return isinstance(result, dict) and not bool(result.get("error"))


def install_package_form_hygiene(package_ui) -> None:
    """Install success-only reset behaviour for the Admin Package workspace.

    Member, package/subscription and active-section selectors remain stable.
    Only transaction widgets receive a fresh identity after confirmed writes.
    Exceptions and unsuccessful results schedule no reset, preserving user input.
    """

    global _INSTALLED
    if _INSTALLED or getattr(package_ui, "_hm_package_form_hygiene_installed", False):
        return

    original_save_package = package_ui.save_package
    original_assign = package_ui.assign_or_replace_member_package
    original_update_subscription = package_ui.update_subscription
    original_adjust_sessions = package_ui.adjust_subscription_sessions

    def save_package_with_hygiene(*args, **kwargs):
        result = original_save_package(*args, **kwargs)
        if _write_succeeded(result):
            package_id = _text(kwargs.get("package_id"))
            suffix = package_id or "new"
            st.session_state[_LIBRARY_CLEANUP] = (
                f"hm_pkg_library_inclusion_{suffix}_"
            )
            _bump(_LIBRARY_VERSION)
            package_name = _text(result.get("package_name")) or _text(
                kwargs.get("package_name")
            )
            _set_flash(
                _LIBRARY_FLASH,
                f"Package saved: {package_name or 'Package'}",
            )
        return result

    def assign_with_hygiene(*args, **kwargs):
        result = original_assign(*args, **kwargs)
        if isinstance(result, dict) and bool(result.get("assigned")):
            _bump(_ASSIGN_VERSION)
            _set_flash(
                _ASSIGN_FLASH,
                "Package assignment saved with commercial snapshot and audit history.",
            )
        return result

    def update_subscription_with_hygiene(*args, **kwargs):
        result = original_update_subscription(*args, **kwargs)
        if _write_succeeded(result):
            _bump(_ACTION_VERSION)
            _set_flash(
                _ACTION_FLASH,
                "Subscription action saved with audit history.",
            )
        return result

    def adjust_sessions_with_hygiene(*args, **kwargs):
        result = original_adjust_sessions(*args, **kwargs)
        if _write_succeeded(result):
            _bump(_ACTION_VERSION)
            _set_flash(
                _ACTION_FLASH,
                "Subscription action saved with audit history.",
            )
        return result

    package_ui.save_package = save_package_with_hygiene
    package_ui.assign_or_replace_member_package = assign_with_hygiene
    package_ui.update_subscription = update_subscription_with_hygiene
    package_ui.adjust_subscription_sessions = adjust_sessions_with_hygiene

    original_library = package_ui._render_package_library
    original_assign_render = package_ui._render_assign_replace
    original_management = package_ui._render_subscription_management

    def render_library_with_hygiene(packages, actor_id) -> None:
        _consume_library_cleanup()
        _render_flash(_LIBRARY_FLASH)
        with _versioned_package_forms():
            original_library(packages, actor_id)

    def render_assign_with_hygiene(packages, actor_id) -> None:
        _render_flash(_ASSIGN_FLASH)
        with _versioned_package_forms():
            original_assign_render(packages, actor_id)

    def render_management_with_hygiene(subscriptions, actor_id) -> None:
        _render_flash(_ACTION_FLASH)
        with _versioned_package_forms():
            original_management(subscriptions, actor_id)

    package_ui._render_package_library = render_library_with_hygiene
    package_ui._render_assign_replace = render_assign_with_hygiene
    package_ui._render_subscription_management = render_management_with_hygiene
    package_ui._hm_package_form_hygiene_installed = True
    _INSTALLED = True
