from __future__ import annotations

import ast
import pathlib
import types
import unittest
from collections.abc import Iterable, Mapping
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parents[1]
APP_PATH = ROOT / "app.py"
PENDING_KEY = "_hm_h13r9e_pending_rerun_path"


class _StopSignal(Exception):
    pass


class _FakeStreamlit:
    def __init__(self):
        self.session_state = {}

    def stop(self):
        raise _StopSignal()


class _Page:
    def __init__(self, url_path: str):
        self.url_path = url_path


def _load_router_functions():
    source = APP_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(APP_PATH))
    wanted_functions = {
        "_registered_path_from_browser",
        "_rerun_with_route_preservation",
        "_iter_pages",
        "_navigation_with_authenticated_root_canonicalization",
    }
    selected_nodes = []
    for node in tree.body:
        if isinstance(node, ast.Assign):
            names = {
                target.id
                for target in node.targets
                if isinstance(target, ast.Name)
            }
            if "_PENDING_RERUN_PATH_KEY" in names:
                selected_nodes.append(node)
        elif isinstance(node, ast.FunctionDef) and node.name in wanted_functions:
            selected_nodes.append(node)

    module = ast.Module(body=selected_nodes, type_ignores=[])
    ast.fix_missing_locations(module)
    namespace = {
        "Any": Any,
        "Iterable": Iterable,
        "Mapping": Mapping,
    }
    exec(compile(module, str(APP_PATH), "exec"), namespace)
    return source, namespace


class NativeRouterRerunRetentionTests(unittest.TestCase):
    def test_app_caches_and_installs_native_rerun_wrapper(self):
        source, _namespace = _load_router_functions()
        self.assertIn('"rerun": "_hm_h13r2_base_rerun"', source)
        self.assertIn("_BASE_RERUN = getattr(st, \"_hm_h13r2_base_rerun\")", source)
        self.assertIn("st.rerun = _rerun_with_route_preservation", source)

    def test_explicit_app_rerun_records_current_registered_route(self):
        _source, namespace = _load_router_functions()
        fake_st = _FakeStreamlit()
        calls = []

        namespace.update(
            {
                "st": fake_st,
                "_native_identity_present": lambda: True,
                "_registered_path_from_browser": lambda: "Daily_Log",
                "_BASE_RERUN": lambda *args, **kwargs: calls.append(
                    (args, kwargs)
                )
                or "rerun-called",
            }
        )

        result = namespace["_rerun_with_route_preservation"]()
        self.assertEqual(result, "rerun-called")
        self.assertEqual(fake_st.session_state[PENDING_KEY], "Daily_Log")
        self.assertEqual(calls, [((), {})])

    def test_fragment_rerun_does_not_create_route_restore_marker(self):
        _source, namespace = _load_router_functions()
        fake_st = _FakeStreamlit()
        namespace.update(
            {
                "st": fake_st,
                "_native_identity_present": lambda: True,
                "_registered_path_from_browser": lambda: "Daily_Log",
                "_BASE_RERUN": lambda *args, **kwargs: None,
            }
        )

        namespace["_rerun_with_route_preservation"](scope="fragment")
        self.assertNotIn(PENDING_KEY, fake_st.session_state)

    def test_pending_daily_log_route_is_restored_before_root_login_fallback(self):
        _source, namespace = _load_router_functions()
        fake_st = _FakeStreamlit()
        fake_st.session_state[PENDING_KEY] = "Daily_Log"
        pages = [_Page("Login"), _Page("Member_Home"), _Page("Daily_Log")]
        switches = []

        namespace.update(
            {
                "st": fake_st,
                "_BASE_NAVIGATION": lambda *args, **kwargs: pages[1],
                "_BASE_SWITCH_PAGE": lambda page, *args, **kwargs: switches.append(
                    page.url_path
                ),
                "_native_identity_present": lambda: True,
                "_browser_path": lambda: "/",
            }
        )

        with self.assertRaises(_StopSignal):
            namespace[
                "_navigation_with_authenticated_root_canonicalization"
            ](pages)

        self.assertEqual(switches, ["Daily_Log"])
        self.assertNotIn(PENDING_KEY, fake_st.session_state)

    def test_existing_root_login_canonicalization_remains_when_no_route_is_pending(self):
        _source, namespace = _load_router_functions()
        fake_st = _FakeStreamlit()
        pages = [_Page("Login"), _Page("Member_Home"), _Page("Daily_Log")]
        switches = []

        namespace.update(
            {
                "st": fake_st,
                "_BASE_NAVIGATION": lambda *args, **kwargs: pages[1],
                "_BASE_SWITCH_PAGE": lambda page, *args, **kwargs: switches.append(
                    page.url_path
                ),
                "_native_identity_present": lambda: True,
                "_browser_path": lambda: "/",
            }
        )

        with self.assertRaises(_StopSignal):
            namespace[
                "_navigation_with_authenticated_root_canonicalization"
            ](pages)

        self.assertEqual(switches, ["Login"])


if __name__ == "__main__":
    unittest.main()
