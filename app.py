from __future__ import annotations

import runpy
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import streamlit as st

from components import guards as _member_guards
from components.member_timezone import member_local_today


def _unwrap_navigation_callable(candidate: Any) -> Any:
    """Recover Streamlit's native navigation callable from stale runtime wrappers.

    Streamlit reruns reuse one Python process. If a previous run stops while the
    dynamic full-app adapter is installed, a cached navigation primitive can point
    at `_patched_navigation` rather than Streamlit's native function. Reusing that
    wrapper causes the Member/Admin route list to be appended twice, producing
    duplicate URL paths such as `My_Profile`.
    """
    seen: set[int] = set()
    current = candidate

    while callable(current) and id(current) not in seen:
        seen.add(id(current))
        name = str(getattr(current, "__name__", "") or "")
        namespace = getattr(current, "__globals__", {})
        next_callable = None

        if name == "_patched_navigation":
            next_callable = namespace.get("_ORIGINAL_NAVIGATION")
        elif name.startswith("_navigation_with_"):
            next_callable = namespace.get("_BASE_NAVIGATION")

        if not callable(next_callable) or next_callable is current:
            break
        current = next_callable

    return current


# Streamlit reruns reuse the same Python process. Always restore the process-level
# routing primitives before installing the current production wrapper. Navigation
# receives an additional unwrapping pass so a stale full-app adapter cannot become
# the cached base and register the same URL path twice.
_ROUTING_PRIMITIVES = {
    "Page": "_hm_h13r2_base_page",
    "navigation": "_hm_h13r2_base_navigation",
    "switch_page": "_hm_h13r2_base_switch_page",
}
for public_name, cache_name in _ROUTING_PRIMITIVES.items():
    current_callable = getattr(st, public_name)
    base_callable = getattr(st, cache_name, None)
    resolved_callable = base_callable if callable(base_callable) else current_callable
    if public_name == "navigation":
        resolved_callable = _unwrap_navigation_callable(resolved_callable)
    setattr(st, cache_name, resolved_callable)
    setattr(st, public_name, resolved_callable)

_BASE_NAVIGATION = getattr(st, "_hm_h13r2_base_navigation")
_BASE_SWITCH_PAGE = getattr(st, "_hm_h13r2_base_switch_page")


def _install_member_local_daily_log_defaults() -> None:
    """Use the member's LAF/profile timezone for Daily Log default dates.

    The accepted Daily Log guard already owns page-entry defaults. Replace only its
    Daily Log branch, preserving all other guard, authentication and routing logic.
    Streamlit process reuse is handled by caching the original callable once.
    """
    cache_name = "_hm_original_apply_member_page_defaults_before_timezone"
    original = getattr(_member_guards, cache_name, None)
    if original is None:
        original = _member_guards._apply_member_page_defaults
        setattr(_member_guards, cache_name, original)
    else:
        _member_guards._apply_member_page_defaults = original

    def _apply_member_page_defaults_with_local_date(current_page: str) -> None:
        if current_page != "18_Daily_Log.py":
            original(current_page)
            return

        previous_page = st.session_state.get("_hm_previous_member_page")
        if previous_page != current_page:
            today = member_local_today(st.session_state.get("user_id", ""))
            st.session_state["hm_h9a4c_saved_from"] = today
            st.session_state["hm_h9a4c_saved_to"] = today
            # Preserve a member-selected or historically loaded journal date during
            # ordinary reruns. Only a new Daily Log session receives today's date.
            st.session_state.setdefault("hm_food_journal_date", today)
        st.session_state["_hm_previous_member_page"] = current_page

    _member_guards._apply_member_page_defaults = (
        _apply_member_page_defaults_with_local_date
    )


def _install_daily_log_tab_emphasis() -> None:
    """Make the two Daily Log journals read as primary section headers."""
    cache_name = "_hm_original_daily_log_ui_before_tab_emphasis"
    original = getattr(_member_guards, cache_name, None)
    if original is None:
        original = _member_guards._apply_daily_log_ui_and_autosave
        setattr(_member_guards, cache_name, original)
    else:
        _member_guards._apply_daily_log_ui_and_autosave = original

    def _apply_daily_log_ui_with_prominent_tabs(current_page: str) -> None:
        original(current_page)
        if current_page != "18_Daily_Log.py":
            return
        st.markdown(
            """
            <style id="hm-daily-log-primary-tabs-v1">
            html body [data-testid="stAppViewContainer"] div[data-testid="stTabs"] [role="tablist"],
            html body [data-testid="stAppViewContainer"] div[data-testid="stTabs"] [data-baseweb="tab-list"]{
              display:grid!important;
              grid-template-columns:repeat(2,minmax(0,1fr))!important;
              gap:.75rem!important;
              width:100%!important;
              margin:.35rem 0 1.15rem 0!important;
              padding:.42rem!important;
              border:1px solid #E3D4BA!important;
              border-radius:16px!important;
              background:#FFF9EE!important;
              box-sizing:border-box!important;
            }
            html body [data-testid="stAppViewContainer"] div[data-testid="stTabs"] button[role="tab"],
            html body [data-testid="stAppViewContainer"] div[data-testid="stTabs"] [data-baseweb="tab"]{
              width:100%!important;
              min-width:0!important;
              min-height:3.15rem!important;
              display:flex!important;
              align-items:center!important;
              justify-content:center!important;
              border:1.5px solid #D8A84E!important;
              border-radius:13px!important;
              background:#FFFFFF!important;
              color:#064E3B!important;
              font-size:1rem!important;
              font-weight:950!important;
              letter-spacing:.01em!important;
              padding:.70rem 1rem!important;
              box-shadow:0 6px 14px rgba(6,78,59,.07)!important;
            }
            html body [data-testid="stAppViewContainer"] div[data-testid="stTabs"] button[role="tab"] *,
            html body [data-testid="stAppViewContainer"] div[data-testid="stTabs"] [data-baseweb="tab"] *{
              color:inherit!important;
              font-size:inherit!important;
              font-weight:inherit!important;
            }
            html body [data-testid="stAppViewContainer"] div[data-testid="stTabs"] button[role="tab"][aria-selected="true"],
            html body [data-testid="stAppViewContainer"] div[data-testid="stTabs"] [data-baseweb="tab"][aria-selected="true"]{
              background:linear-gradient(135deg,#064E3B 0%,#0F766E 100%)!important;
              color:#FFFFFF!important;
              border-color:#064E3B!important;
              box-shadow:0 10px 20px rgba(6,78,59,.18)!important;
            }
            @media(max-width:640px){
              html body [data-testid="stAppViewContainer"] div[data-testid="stTabs"] [role="tablist"],
              html body [data-testid="stAppViewContainer"] div[data-testid="stTabs"] [data-baseweb="tab-list"]{
                gap:.42rem!important;
                padding:.32rem!important;
              }
              html body [data-testid="stAppViewContainer"] div[data-testid="stTabs"] button[role="tab"],
              html body [data-testid="stAppViewContainer"] div[data-testid="stTabs"] [data-baseweb="tab"]{
                min-height:2.85rem!important;
                font-size:.90rem!important;
                padding:.58rem .40rem!important;
              }
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

    _member_guards._apply_daily_log_ui_and_autosave = (
        _apply_daily_log_ui_with_prominent_tabs
    )


_install_member_local_daily_log_defaults()
_install_daily_log_tab_emphasis()


from native_bridge import root_authorization_ui as _router_authorization_ui  # noqa: E402
from native_bridge import root_authorization_ui_h13r7e as _root_authorization_ui  # noqa: E402


BUILD = "H13R9C-profile-dropdown-daily-log-tabs-v1"
ROLLBACK_BUILD = "H13R9B-member-local-daily-log-date-v1"


def _native_identity_present() -> bool:
    try:
        return bool(st.user and st.user.is_logged_in)
    except Exception:
        return False


def _browser_path() -> str:
    try:
        raw_url = str(st.context.url or "").strip()
        path = urlsplit(raw_url).path or "/"
        return path.rstrip("/") or "/"
    except Exception:
        return ""


def _iter_pages(pages: Any) -> Iterable[Any]:
    if isinstance(pages, Mapping):
        for section_pages in pages.values():
            yield from _iter_pages(section_pages)
        return
    if isinstance(pages, (list, tuple)):
        for page in pages:
            yield page
        return
    yield pages


def _install_one_time_post_oauth_reload() -> None:
    """Restore the PR #205 browser refresh after OAuth identity is created.

    Streamlit Cloud can expose a clean server-side route while the top-level browser
    still shows the consumed ``authorization_id`` callback. PR #205 proved that one
    guarded full browser reload reconciles those states and then lets the registered
    role router land on the canonical Member/Admin route.
    """
    if not _native_identity_present():
        return

    st.html(
        r"""
        <script>
        (() => {
          let topWindow;
          try {
            topWindow = window.top || window.parent || window;
          } catch (_error) {
            topWindow = window;
          }

          let currentUrl;
          try {
            currentUrl = new URL(topWindow.location.href);
          } catch (_error) {
            return;
          }

          const authorizationId = currentUrl.searchParams.get("authorization_id");
          if (!authorizationId) {
            return;
          }

          const key = `hm_h13r2_oauth_reload:${authorizationId}`;
          let shouldReload = true;

          try {
            const storage = topWindow.sessionStorage;
            if (storage.getItem(key) === "done") {
              storage.removeItem(key);
              shouldReload = false;
            } else {
              storage.setItem(key, "done");
            }
          } catch (_storageError) {
            const marker = `|${key}|`;
            const currentName = String(topWindow.name || "");
            if (currentName.includes(marker)) {
              topWindow.name = currentName.replace(marker, "");
              shouldReload = false;
            } else {
              topWindow.name = `${currentName}${marker}`;
            }
          }

          if (!shouldReload) {
            return;
          }

          try {
            const doc = topWindow.document;
            if (doc && doc.body && !doc.getElementById("hm-h13r2-login-finalising")) {
              const overlay = doc.createElement("div");
              overlay.id = "hm-h13r2-login-finalising";
              overlay.textContent = "Finalising secure login…";
              overlay.style.cssText = [
                "position:fixed",
                "inset:0",
                "z-index:2147483647",
                "display:flex",
                "align-items:center",
                "justify-content:center",
                "background:#fffaf2",
                "color:#073b2c",
                "font:600 16px system-ui,sans-serif"
              ].join(";");
              doc.body.appendChild(overlay);
            }
          } catch (_overlayError) {}

          topWindow.setTimeout(() => topWindow.location.reload(), 40);
        })();
        </script>
        """,
        unsafe_allow_javascript=True,
    )


# Keep the accepted H13R7E HealthyMe-branded authorizer. Once native identity exists,
# leave the consumed request for the PR #205 refresh and registered role router.
_BASE_AUTHORIZER = getattr(
    _root_authorization_ui,
    "_hm_h13r9_base_render_root_authorization_ui",
    None,
)
if _BASE_AUTHORIZER is None:
    _BASE_AUTHORIZER = _root_authorization_ui.render_root_authorization_ui
    _root_authorization_ui._hm_h13r9_base_render_root_authorization_ui = (
        _BASE_AUTHORIZER
    )
else:
    _root_authorization_ui.render_root_authorization_ui = _BASE_AUTHORIZER


def _render_root_authorization_ui_for_native_router(authorization_id: str) -> None:
    if _native_identity_present():
        return
    _BASE_AUTHORIZER(authorization_id)


_root_authorization_ui.render_root_authorization_ui = (
    _render_root_authorization_ui_for_native_router
)

# The compiled full Member/Admin runtime imports the legacy authorizer module.
# Point it to the accepted H13R7E wrapper without altering the login-page UX.
_router_authorization_ui.render_root_authorization_ui = (
    _render_root_authorization_ui_for_native_router
)


def _navigation_with_authenticated_root_canonicalization(
    pages: Any,
    *args: Any,
    **kwargs: Any,
) -> Any:
    selected_page = _BASE_NAVIGATION(pages, *args, **kwargs)

    # After the guarded browser refresh, an authenticated callback can re-enter at
    # the app root. Move through the registered Login page with an empty query set;
    # the existing role router then selects Member_Home or the correct Admin route.
    if _native_identity_present() and _browser_path() == "/":
        login_page = next(
            (
                page
                for page in _iter_pages(pages)
                if str(getattr(page, "url_path", "") or "") == "Login"
            ),
            None,
        )
        if login_page is None:
            raise RuntimeError(
                "H13R9C could not locate the registered Login page for OAuth canonicalization."
            )
        _BASE_SWITCH_PAGE(login_page, query_params={})
        st.stop()

    return selected_page


st.navigation = _navigation_with_authenticated_root_canonicalization
_install_one_time_post_oauth_reload()


CUTOVER_ENTRY = (
    Path(__file__).resolve().parent
    / "production_cutover"
    / "production_live_cutover_app.py"
)

runpy.run_path(
    str(CUTOVER_ENTRY),
    run_name="__hm_h13r9c_profile_dropdown_daily_log_tabs__",
)
