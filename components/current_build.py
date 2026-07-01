"""HealthyMe current build override helpers.

Small, low-risk helper used by H6 pages to show the current build label without
rewriting the large shared ui_common history file.
"""

from __future__ import annotations

from typing import Any

APP_BUILD_VERSION = "v102.4B15S3H6"
APP_BUILD_LABEL = "Supabase Auth Provisioning Hardening"
FULL_BUILD_LABEL = f"{APP_BUILD_VERSION} · {APP_BUILD_LABEL}"


def apply_current_build(ui_common_module: Any | None = None) -> None:
    """Patch ui_common build globals at runtime for pages that import topbar.

    Streamlit pages import topbar from components.ui_common. topbar reads global
    APP_BUILD_VERSION / APP_BUILD_LABEL from its defining module at call time,
    so updating those globals before topbar() is called is sufficient and keeps
    this build's change small.
    """
    if ui_common_module is None:
        import components.ui_common as ui_common_module
    try:
        ui_common_module.APP_BUILD_VERSION = APP_BUILD_VERSION
        ui_common_module.APP_BUILD_LABEL = APP_BUILD_LABEL
    except Exception:
        pass
