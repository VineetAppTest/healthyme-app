from __future__ import annotations

import json
import runpy
import sys
import traceback
from pathlib import Path
from typing import Any

import streamlit as st


BUILD = "H13R1-production-native-full-app-v1"
ROLLBACK_BUILD = "H13R0-production-native-member-auth-only-v1"
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

SOURCE = REPOSITORY_ROOT / "native_bridge" / "native_bridge_full_member_app.py"
GATE4_SOURCE = REPOSITORY_ROOT / "native_bridge" / "native_bridge_gate4_app.py"

st.set_page_config(
    page_title="HealthyMe H13R1 Native Full App",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def _replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise RuntimeError(f"H13R1 source marker missing: {label}")
    return text.replace(old, new, 1)


try:
    from components.native_member_auth import (
        install_native_member_adapters,
        require_native_member,
    )
    from components.native_admin_auth import (
        install_native_admin_adapters,
        logout_native_identity,
        native_role_utility_bar,
        require_native_admin,
    )
    from native_bridge.full_admin_route_registry import (
        AdminRouteSpec,
        discover_admin_page_specs,
    )

    member_adapter_status = install_native_member_adapters()
    admin_adapter_status = install_native_admin_adapters()
except Exception as exc:
    st.error("H13R1 could not install the native role authentication adapters.")
    st.code(
        json.dumps(
            {
                "build": BUILD,
                "rollback_build": ROLLBACK_BUILD,
                "error_type": type(exc).__name__,
                "error_message": str(exc),
            },
            indent=2,
            sort_keys=True,
        ),
        language="json",
    )
    st.code("".join(traceback.format_exception(type(exc), exc, exc.__traceback__)))
    st.stop()

try:
    source_text = SOURCE.read_text(encoding="utf-8")
except Exception as exc:
    st.error("H13R1 could not read the accepted H13R0 Member runtime source.")
    st.exception(exc)
    st.stop()

try:
    source_text = _replace_once(
        source_text,
        'BUILD = "H13Q7-native-full-member-app-v1"',
        f'BUILD = "{BUILD}"',
        "full Member build marker",
    )
    source_text = _replace_once(
        source_text,
        'ROLLBACK_BUILD = "H13Q6-native-gate4-real-todays-plan-v1"',
        f'ROLLBACK_BUILD = "{ROLLBACK_BUILD}"',
        "full Member rollback marker",
    )

    # Keep the accepted Step 3 native Member guard active on every Member page.
    source_text = source_text.replace(
        "guards.require_member = lambda: None",
        "guards.require_member = require_native_member",
    )

    source_text = _replace_once(
        source_text,
        "_ROUTE_SPECS: list[MemberRouteSpec] = []\n"
        "_EXTRA_ROUTE_PATHS: set[str] = set()\n"
        "_SELECTED_PATH = \"\"",
        "_ROUTE_SPECS: list[MemberRouteSpec] = []\n"
        "_EXTRA_ROUTE_PATHS: set[str] = set()\n"
        "_ADMIN_ROUTE_SPECS: list[AdminRouteSpec] = []\n"
        "_ADMIN_ROUTE_PATHS: set[str] = set()\n"
        "_SELECTED_PATH = \"\"",
        "Admin route globals",
    )

    source_text = source_text.replace(
        "This destination is not registered in the consolidated native Member router:",
        "This destination is not registered in the consolidated native HealthyMe router:",
    )

    admin_runtime = r'''
def _render_admin_route(spec: AdminRouteSpec) -> None:
    context = _gate4_context()
    if str(context.get("role_category") or "") != "Admin":
        member_page = _CORE_PAGES.get("Member_Home")
        if member_page is not None:
            _ORIGINAL_SWITCH_PAGE(member_page)
            st.stop()
        st.error("The native router rejected this Admin route.")
        st.stop()

    import components.auth_session as auth_session
    import components.guards as guards
    import components.ui_common as ui_common

    saved = {
        ("guards", "require_admin"): _save_attr(guards, "require_admin"),
        ("auth_session", "logout_current_user"): _save_attr(
            auth_session, "logout_current_user"
        ),
        ("ui_common", "logout_current_user"): _save_attr(
            ui_common, "logout_current_user"
        ),
        ("ui_common", "utility_logout_bar"): _save_attr(
            ui_common, "utility_logout_bar"
        ),
        ("streamlit", "set_page_config"): st.set_page_config,
        ("streamlit", "switch_page"): st.switch_page,
    }
    keepalive_saved: dict[str, Any] = {}
    for name in dir(ui_common):
        if name.startswith("inject_keepalive"):
            keepalive_saved[name] = getattr(ui_common, name)

    guards.require_admin = require_native_admin
    auth_session.logout_current_user = logout_native_identity
    ui_common.logout_current_user = logout_native_identity
    ui_common.utility_logout_bar = native_role_utility_bar
    for name in keepalive_saved:
        setattr(ui_common, name, lambda *args, **kwargs: None)
    st.set_page_config = lambda *args, **kwargs: None
    st.switch_page = lambda target, *args, **kwargs: _embedded_switch_handler(
        _ORIGINAL_SWITCH_PAGE,
        target,
    )

    st.session_state["_hm_native_full_admin_embedded"] = True
    st.session_state["_hm_native_full_admin_route"] = spec.source_path
    context["real_admin_dashboard_loaded"] = spec.filename == "10_Admin_Dashboard.py"
    context["full_admin_page_loaded"] = True
    context["active_admin_source"] = spec.source_path
    context["active_admin_checkpoint"] = spec.checkpoint

    source_file = REPOSITORY_ROOT / spec.source_path
    try:
        runpy.run_path(
            str(source_file),
            run_name=f"__hm_h13r1_{_route_key(spec.filename)}__",
        )
    except Exception as exc:
        if type(exc).__name__ in {"StopException", "RerunException"}:
            raise
        st.error(
            "This HealthyMe Admin page could not complete under the native router. "
            "The native identity remains active so the failing route can be isolated."
        )
        st.code(
            json.dumps(
                {
                    "build": BUILD,
                    "source_page": spec.source_path,
                    "url_path": f"/{spec.url_path}",
                    "checkpoint": spec.checkpoint,
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                    "rollback_build": ROLLBACK_BUILD,
                },
                indent=2,
                sort_keys=True,
            ),
            language="json",
        )
    finally:
        _restore_attr(guards, "require_admin", saved[("guards", "require_admin")])
        _restore_attr(
            auth_session,
            "logout_current_user",
            saved[("auth_session", "logout_current_user")],
        )
        _restore_attr(
            ui_common,
            "logout_current_user",
            saved[("ui_common", "logout_current_user")],
        )
        _restore_attr(
            ui_common,
            "utility_logout_bar",
            saved[("ui_common", "utility_logout_bar")],
        )
        for name, value in keepalive_saved.items():
            setattr(ui_common, name, value)
        st.set_page_config = saved[("streamlit", "set_page_config")]
        st.switch_page = saved[("streamlit", "switch_page")]

    st.caption(
        f"Full Admin integration build: {BUILD} · {spec.checkpoint} · "
        f"{spec.source_path}"
    )


def _make_admin_page(spec: AdminRouteSpec):
    def _page() -> None:
        _render_admin_route(spec)

    _page.__name__ = f"h13r1_{_route_key(spec.url_path)}"
    return _page


def _real_admin_dashboard_page() -> None:
    _render_admin_route(
        AdminRouteSpec(
            filename="10_Admin_Dashboard.py",
            source_path="pages/10_Admin_Dashboard.py",
            title="Admin Dashboard",
            url_path="Admin_Dashboard",
            checkpoint="A-dashboard",
        )
    )


'''
    source_text = _replace_once(
        source_text,
        "def _login_page() -> None:\n",
        admin_runtime + "def _login_page() -> None:\n",
        "Admin runtime insertion",
    )

    source_text = _replace_once(
        source_text,
        '    elif url_path == "Admin_Dashboard":\n        page = _admin_page',
        '    elif url_path == "Admin_Dashboard":\n        page = _real_admin_dashboard_page',
        "real Admin Dashboard page replacement",
    )

    source_text = _replace_once(
        source_text,
        "    global _ROUTE_SPECS\n"
        "    global _EXTRA_ROUTE_PATHS\n"
        "    global _SELECTED_PATH",
        "    global _ROUTE_SPECS\n"
        "    global _EXTRA_ROUTE_PATHS\n"
        "    global _ADMIN_ROUTE_SPECS\n"
        "    global _ADMIN_ROUTE_PATHS\n"
        "    global _SELECTED_PATH",
        "Admin navigation globals",
    )

    member_discovery = '''    specs = discover_member_page_specs(REPOSITORY_ROOT)
    _ROUTE_SPECS = specs
    extra_pages: list[Any] = []
    for spec in specs:
        page_obj = _ORIGINAL_PAGE(
            _make_member_page(spec),
            title=spec.title,
            url_path=spec.url_path,
        )
        extra_pages.append(page_obj)

    _FILE_TO_PAGE = {'''
    full_discovery = '''    specs = discover_member_page_specs(REPOSITORY_ROOT)
    _ROUTE_SPECS = specs
    extra_pages: list[Any] = []
    for spec in specs:
        page_obj = _ORIGINAL_PAGE(
            _make_member_page(spec),
            title=spec.title,
            url_path=spec.url_path,
        )
        extra_pages.append(page_obj)

    admin_specs = discover_admin_page_specs(REPOSITORY_ROOT)
    _ADMIN_ROUTE_SPECS = admin_specs
    admin_pages: list[Any] = []
    for spec in admin_specs:
        page_obj = _ORIGINAL_PAGE(
            _make_admin_page(spec),
            title=spec.title,
            url_path=spec.url_path,
        )
        admin_pages.append(page_obj)

    _FILE_TO_PAGE = {'''
    source_text = _replace_once(
        source_text,
        member_discovery,
        full_discovery,
        "Admin page discovery",
    )

    source_text = _replace_once(
        source_text,
        "    for spec, page_obj in zip(specs, extra_pages):\n"
        "        _FILE_TO_PAGE[spec.source_path] = page_obj\n"
        "        _URL_TO_PAGE[spec.url_path] = page_obj\n"
        "    _FILE_TO_PAGE = {",
        "    for spec, page_obj in zip(specs, extra_pages):\n"
        "        _FILE_TO_PAGE[spec.source_path] = page_obj\n"
        "        _URL_TO_PAGE[spec.url_path] = page_obj\n"
        "    for spec, page_obj in zip(admin_specs, admin_pages):\n"
        "        _FILE_TO_PAGE[spec.source_path] = page_obj\n"
        "        _URL_TO_PAGE[spec.url_path] = page_obj\n"
        "    _FILE_TO_PAGE = {",
        "Admin route mapping",
    )

    source_text = _replace_once(
        source_text,
        "    _EXTRA_ROUTE_PATHS = {spec.url_path for spec in specs}\n",
        "    _EXTRA_ROUTE_PATHS = {spec.url_path for spec in specs}\n"
        "    _ADMIN_ROUTE_PATHS = {spec.url_path for spec in admin_specs}\n",
        "Admin route path set",
    )

    source_text = _replace_once(
        source_text,
        "    context[\"full_member_route_count\"] = len(specs) + 2\n"
        "    context[\"rollback_build\"] = ROLLBACK_BUILD\n",
        "    context[\"full_member_route_count\"] = len(specs) + 2\n"
        "    context[\"full_admin_route_count\"] = len(admin_specs) + 1\n"
        "    context[\"allowed_admin_paths\"] = sorted(\n"
        "        {\"Admin_Dashboard\", *[item.url_path for item in admin_specs]}\n"
        "    )\n"
        "    context[\"rollback_build\"] = ROLLBACK_BUILD\n",
        "Admin context registration",
    )

    source_text = _replace_once(
        source_text,
        "        [*base_pages, *extra_pages],",
        "        [*base_pages, *extra_pages, *admin_pages],",
        "Admin navigation registration",
    )

    source_text = source_text.replace(
        'st.title("HealthyMe native full-member router")',
        'st.title("HealthyMe native full application router")',
    )
    source_text = source_text.replace(
        '"Consolidated Gate 5–7 integration: the accepted Gate 4 identity and role "\n'
        '        "router now registers the current read, write and remaining Member pages."',
        '"Step 4 integration: the accepted native identity and role router now "\n'
        '        "registers the real Member and Admin applications."',
    )
    source_text = source_text.replace(
        '"full_member_route_count": len(_ROUTE_SPECS) + 2,',
        '"full_member_route_count": len(_ROUTE_SPECS) + 2,\n'
        '                "full_admin_route_count": len(_ADMIN_ROUTE_SPECS) + 1,',
    )
    source_text = source_text.replace(
        '"legacy_page_guard_used": False,',
        '"legacy_page_guard_used": False,\n'
        '                "legacy_member_auth_retired": True,\n'
        '                "native_member_guard_installed": True,\n'
        '                "legacy_admin_auth_active": False,\n'
        '                "native_admin_guard_installed": True,\n'
        '                "auth0_restore_used": False,\n'
        '                "nutritionist_role_promoted_to_admin": False,',
    )
    source_text = source_text.replace(
        '"durable_auth_session_used": False,',
        '"durable_auth_session_used": False,\n'
        '                "native_logout_installed": True,',
    )

except Exception as exc:
    st.error("H13R1 source-integrity transformation failed before runtime execution.")
    st.code(
        json.dumps(
            {
                "build": BUILD,
                "rollback_build": ROLLBACK_BUILD,
                "member_adapter_status": member_adapter_status,
                "admin_adapter_status": admin_adapter_status,
                "error_type": type(exc).__name__,
                "error_message": str(exc),
            },
            indent=2,
            sort_keys=True,
        ),
        language="json",
    )
    st.code("".join(traceback.format_exception(type(exc), exc, exc.__traceback__)))
    st.stop()

original_run_path = runpy.run_path


def _run_path_with_native_gate4(
    path_name: str,
    init_globals: dict[str, Any] | None = None,
    run_name: str | None = None,
) -> dict[str, Any]:
    path = Path(path_name)
    try:
        is_gate4 = path.resolve() == GATE4_SOURCE.resolve()
    except Exception:
        is_gate4 = str(path) == str(GATE4_SOURCE)

    if not is_gate4:
        return original_run_path(
            path_name,
            init_globals=init_globals,
            run_name=run_name,
        )

    gate4_text = path.read_text(encoding="utf-8")
    gate4_text = gate4_text.replace(
        "guards.require_member = lambda: None",
        "guards.require_member = require_native_member",
    )

    old_admin_block = '''if role_category == "Admin":
    _clear_derived_application_context()
    ROUTER_CONTEXT["derived_application_context_applied"] = False
    ROUTER_CONTEXT["real_member_home_loaded"] = False
    ROUTER_CONTEXT["real_todays_plan_loaded"] = False
    if selected_path != admin_page.url_path:
        st.switch_page(admin_page)
    selected_page.run()
    st.stop()
'''
    new_admin_block = '''if role_category == "Admin":
    _clear_derived_application_context()
    ROUTER_CONTEXT["derived_application_context_applied"] = False
    ROUTER_CONTEXT["real_member_home_loaded"] = False
    ROUTER_CONTEXT["real_todays_plan_loaded"] = False
    allowed_admin_paths = set(
        ROUTER_CONTEXT.get("allowed_admin_paths") or {admin_page.url_path}
    )
    if selected_path not in allowed_admin_paths:
        st.switch_page(admin_page)
    selected_page.run()
    st.stop()
'''
    if old_admin_block not in gate4_text:
        raise RuntimeError("H13R1 Gate 4 Admin routing marker is missing.")
    gate4_text = gate4_text.replace(old_admin_block, new_admin_block, 1)

    gate4_globals: dict[str, Any] = {
        "__name__": run_name or "__hm_h13r1_native_gate4__",
        "__file__": str(path),
        "__package__": None,
        "__cached__": None,
        "require_native_member": require_native_member,
    }
    if init_globals:
        gate4_globals.update(init_globals)

    exec(
        compile(gate4_text, str(path), "exec"),
        gate4_globals,
    )
    return gate4_globals


original_set_page_config = st.set_page_config
st.set_page_config = lambda *args, **kwargs: None
runpy.run_path = _run_path_with_native_gate4

try:
    exec(
        compile(source_text, str(SOURCE), "exec"),
        {
            "__name__": "__hm_h13r1_native_full_app__",
            "__file__": str(SOURCE),
            "__package__": None,
            "AdminRouteSpec": AdminRouteSpec,
            "discover_admin_page_specs": discover_admin_page_specs,
            "require_native_member": require_native_member,
            "require_native_admin": require_native_admin,
            "logout_native_identity": logout_native_identity,
            "native_role_utility_bar": native_role_utility_bar,
        },
    )
except Exception as exc:
    st.error("H13R1 runtime failed before the requested page completed.")
    st.code(
        json.dumps(
            {
                "build": BUILD,
                "rollback_build": ROLLBACK_BUILD,
                "member_adapter_status": member_adapter_status,
                "admin_adapter_status": admin_adapter_status,
                "error_type": type(exc).__name__,
                "error_message": str(exc),
                "source": str(SOURCE),
            },
            indent=2,
            sort_keys=True,
        ),
        language="json",
    )
    st.code("".join(traceback.format_exception(type(exc), exc, exc.__traceback__)))
    st.stop()
finally:
    runpy.run_path = original_run_path
    st.set_page_config = original_set_page_config
