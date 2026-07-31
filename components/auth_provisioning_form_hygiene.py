from __future__ import annotations

import functools
import inspect
from typing import Any

import streamlit as st

import components.supabase_auth_lifecycle_h10 as auth_lifecycle
import components.supabase_provisioning_h6 as provisioning


_MARKER = "_hm_auth_provisioning_form_hygiene_v1"
_PAGE = "pages/34_Admin_Supabase_Auth_Provisioning_Workbench.py"
_PENDING_RESULT = "_hm_auth_provisioning_pending_result"
_FORM_KEYS = {
    "reset": "hm_h10_password_reset_form",
    "single": "hm_h6_single_supabase_provisioning_form",
    "batch": "hm_h6_batch_supabase_provisioning_form",
}
_EXPLICIT_DRY_RUN_KEYS = {
    "h10_reset_dry_run": "reset",
    "h6_batch_dry_run": "batch",
}


def _on_workbench_page() -> bool:
    frame = inspect.currentframe()
    frame = frame.f_back if frame is not None else None
    while frame is not None:
        path = str((frame.f_globals or {}).get("__file__") or "").replace("\\", "/")
        if path.endswith(_PAGE):
            return True
        frame = frame.f_back
    return False


def _version_key(scope: str) -> str:
    return f"_hm_auth_provisioning_{scope}_version"


def _version(scope: str) -> int:
    try:
        return max(int(st.session_state.get(_version_key(scope), 1) or 1), 1)
    except Exception:
        return 1


def _advance(scope: str) -> None:
    st.session_state[_version_key(scope)] = _version(scope) + 1


def _replace_form_key(args: tuple[Any, ...], kwargs: dict[str, Any], new_key: str):
    updated_kwargs = dict(kwargs)
    if "key" in updated_kwargs:
        updated_kwargs["key"] = new_key
        return args, updated_kwargs
    if not args:
        return (new_key,), updated_kwargs
    return (new_key, *args[1:]), updated_kwargs


def _rows(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict):
        return [dict(payload)]
    if isinstance(payload, (list, tuple)):
        return [dict(row) for row in payload if isinstance(row, dict)]
    return []


def _single_completed(result: Any, *, dry_run: bool) -> bool:
    if dry_run or not isinstance(result, dict):
        return False
    status = str(result.get("status") or "").strip().lower()
    reset_status = str(result.get("password_reset_status") or "").strip().lower()
    return status == "ok" and reset_status != "failed"


def _batch_completed(payload: Any, *, dry_run: bool) -> bool:
    if dry_run:
        return False
    rows = _rows(payload)
    if not rows:
        return False
    statuses = [str(row.get("status") or "").strip().lower() for row in rows]
    if "ok" not in statuses:
        return False
    if any(status in {"failed", "partial", "review", "stopped"} for status in statuses):
        return False
    if any(str(row.get("password_reset_status") or "").strip().lower() == "failed" for row in rows):
        return False
    return True


def _stage_completed(scope: str, payload: Any, message: str) -> None:
    st.session_state[_PENDING_RESULT] = {
        "scope": scope,
        "rows": _rows(payload),
        "message": str(message or "Action completed successfully."),
    }
    _advance(scope)
    st.rerun()


def _render_pending(scope: str) -> None:
    pending = st.session_state.get(_PENDING_RESULT)
    if not isinstance(pending, dict) or str(pending.get("scope") or "") != scope:
        return
    pending = st.session_state.pop(_PENDING_RESULT)
    message = str(pending.get("message") or "Action completed successfully.")
    rows = _rows(pending.get("rows"))
    st.success(message)
    if rows:
        st.dataframe(rows, use_container_width=True, hide_index=True)


def install_auth_provisioning_form_hygiene() -> None:
    current_form = st.form
    if getattr(current_form, _MARKER, False):
        return

    current_checkbox = st.checkbox
    current_reset = auth_lifecycle.send_password_reset_for_member
    current_single = provisioning.provision_single_member
    current_batch = provisioning.provision_batch_members

    @functools.wraps(current_form)
    def form_with_success_version(*args, **kwargs):
        form_key = str(kwargs.get("key") if "key" in kwargs else (args[0] if args else ""))
        scope = next((name for name, key in _FORM_KEYS.items() if key == form_key), "")
        if scope and _on_workbench_page():
            _render_pending(scope)
            new_key = f"{form_key}_{_version(scope)}"
            args, kwargs = _replace_form_key(args, kwargs, new_key)
        return current_form(*args, **kwargs)

    @functools.wraps(current_checkbox)
    def checkbox_with_success_version(*args, **kwargs):
        key = str(kwargs.get("key") or "")
        scope = _EXPLICIT_DRY_RUN_KEYS.get(key, "")
        if scope and _on_workbench_page():
            kwargs = dict(kwargs)
            kwargs["key"] = f"{key}_{_version(scope)}"
        return current_checkbox(*args, **kwargs)

    @functools.wraps(current_reset)
    def reset_with_success_hygiene(*args, **kwargs):
        result = current_reset(*args, **kwargs)
        dry_run = bool(kwargs.get("dry_run", True))
        if (
            _on_workbench_page()
            and not dry_run
            and isinstance(result, dict)
            and str(result.get("status") or "").strip().lower() == "sent"
        ):
            _stage_completed(
                "reset",
                result,
                str(result.get("message") or "Password reset email sent."),
            )
        return result

    @functools.wraps(current_single)
    def single_with_success_hygiene(*args, **kwargs):
        result = current_single(*args, **kwargs)
        dry_run = bool(kwargs.get("dry_run", True))
        if _on_workbench_page() and _single_completed(result, dry_run=dry_run):
            _stage_completed(
                "single",
                result,
                str((result or {}).get("message") or "Single-member provisioning completed."),
            )
        return result

    @functools.wraps(current_batch)
    def batch_with_success_hygiene(*args, **kwargs):
        result = current_batch(*args, **kwargs)
        dry_run = bool(kwargs.get("dry_run", True))
        if _on_workbench_page() and _batch_completed(result, dry_run=dry_run):
            _stage_completed(
                "batch",
                result,
                "Batch execution completed successfully. Review the result table and audit log.",
            )
        return result

    for wrapped in (
        form_with_success_version,
        checkbox_with_success_version,
        reset_with_success_hygiene,
        single_with_success_hygiene,
        batch_with_success_hygiene,
    ):
        setattr(wrapped, _MARKER, True)

    st.form = form_with_success_version
    st.checkbox = checkbox_with_success_version
    auth_lifecycle.send_password_reset_for_member = reset_with_success_hygiene
    provisioning.provision_single_member = single_with_success_hygiene
    provisioning.provision_batch_members = batch_with_success_hygiene
