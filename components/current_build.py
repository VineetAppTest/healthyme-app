"""HealthyMe current build override helpers.

Small, low-risk helper used by authentication and migration pages to show the
current build label without rewriting the large shared ui_common history file.
"""

from __future__ import annotations

from typing import Any

APP_BUILD_VERSION = "v102.4B15S3H13O1"
APP_BUILD_LABEL = "Same-App Supabase OIDC PoC"
FULL_BUILD_LABEL = f"{APP_BUILD_VERSION} · {APP_BUILD_LABEL}"


def apply_current_build(ui_common_module: Any | None = None) -> None:
    """Patch ui_common build globals at runtime for pages that import topbar."""
    if ui_common_module is None:
        import components.ui_common as ui_common_module
    try:
        ui_common_module.APP_BUILD_VERSION = APP_BUILD_VERSION
        ui_common_module.APP_BUILD_LABEL = APP_BUILD_LABEL
    except Exception:
        pass
