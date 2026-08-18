from __future__ import annotations

from typing import Any


def unwrap_stale_full_app_navigation(candidate: Any) -> Any:
    """Remove only stale full-app `_patched_navigation` wrappers.

    Streamlit reruns may reuse one Python process. If a prior dynamic HealthyMe
    full-app run exits while its navigation adapter is installed, the next run can
    start with `_patched_navigation` still assigned to `st.navigation`. Letting the
    production cutover capture that wrapper as its base causes the member/admin
    route set to be appended twice (for example `My_Profile` twice).

    Do not unwrap the current app-level canonicalization wrapper here; it owns
    login/rerun route preservation. This helper only strips dynamic full-app
    adapters until the first non-`_patched_navigation` callable is reached.
    """

    seen: set[int] = set()
    current = candidate
    while callable(current) and id(current) not in seen:
        seen.add(id(current))
        if str(getattr(current, "__name__", "") or "") != "_patched_navigation":
            break
        namespace = getattr(current, "__globals__", {})
        previous = namespace.get("_ORIGINAL_NAVIGATION") if isinstance(namespace, dict) else None
        if not callable(previous) or previous is current:
            break
        current = previous
    return current
