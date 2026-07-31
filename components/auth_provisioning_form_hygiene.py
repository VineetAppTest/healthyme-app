from __future__ import annotations

import functools
import inspect
from typing import Any

import streamlit as st

from components import supabase_auth_lifecycle_h10 as auth_lifecycle
from components import supabase_provisioning_h6 as provisioning


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
    return f"_hm_auth
            if key == "h10_reset_dry_run":
                kwargs["key"] = f"h10_reset_dry_run_{_version('reset')}"
            elif key == "h6_batch_dry_run":
                kwargs["key"] = f"h6_batch_dry_run_{_version('batch')}"
        return current_checkbox(*args, **kwargs)

    @functools.wraps(current_reset)
    def reset_with_success_hygiene(*args, **kwargs):
        result = current_reset(*args, **kwargs)
        dry_run = bool(kwargs.get("dry_run", True))
        if _on_page() and not dry_run and str((result or {}).get("status") or "") == "sent":
            _stage_completed(
                "reset",
                [dict(result)],
                str((result or {}).get("message") or "Password reset email sent."),
            )
        return result

    @functools.wraps(current_single)
    def single_with_success_hygiene(*args, **kwargs):
        result = current_single(*args, **kwargs)
        dry_run = bool(kwargs.get("dry_run", True))
        status = str((result or {}).get("status") or "").strip().lower()
        reset_status = str((result or {}).get("password_reset_status") or "").strip().lower()
        if _on_page() and not dry_run and status == "ok" and reset_status != "failed":
            _stage_completed(
                "single",
                [dict(result)],
                str((result or {}).get("message") or "Single-member provisioning completed."),
            )
        return result

    @functools.wraps(current_batch)
    def batch_with_success_hygiene(*args, **kwargs):
        rows = current_batch(*args, **kwargs)
        dry_run = bool(kwargs.get("dry_run", True))
        if _on_page() and not dry_run and _batch_completed(rows):
            _stage_completed(
                "batch",
                [dict(row) for row in rows if isinstance(row, dict)],
                "Batch execution completed successfully. Review the result table and audit log.",
            )
        return rows

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
    lifecycle_h10.send_password_reset_for_member = reset_with_success_hygiene
    provisioning_h6.provision_single_member = single_with_success_hygiene
    provisioning_h6.provision_batch_members = batch_with_success_hygiene
