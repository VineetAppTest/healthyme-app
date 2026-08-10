from __future__ import annotations

import ast
from pathlib import Path
import unittest
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]
ROUTER = ROOT / "native_bridge/native_bridge_full_member_app.py"
PENDING_KEY = "_hm_h13r9e_pending_rerun_path"


class _StopSignal(Exception):
    pass


class _FakeStreamlit:
    def __init__(self):
        self.session_state = {}
        self.warnings = []

    def stop(self):
        raise _StopSignal()

    def warning(self, message):
        self.warnings.append(str(message))


class _Page:
    def __init__(self, url_path: str):
        self.url_path = url_path


def _load_embedded_switch_handler():
    source = ROUTER.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(ROUTER))
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
        elif isinstance(node, ast.FunctionDef) and node.name == "_embedded_switch_handler":
            selected_nodes.append(node)

    module = ast.Module(body=selected_nodes, type_ignores=[])
    ast.fix_missing_locations(module)
    namespace = {"Any": Any, "Callable": Callable}
    exec(compile(module, str(ROUTER), "exec"), namespace)
    return namespace


class NativeEmbeddedSwitchRouteIntentTests(unittest.TestCase):
    def test_resolved_daily_log_route_is_staged_before_native_switch(self):
        namespace = _load_embedded_switch_handler()
        fake_st = _FakeStreamlit()
        daily_log = _Page("Daily_Log")
        switches = []

        def switch_page(page):
            switches.append(
                (page.url_path, fake_st.session_state.get(PENDING_KEY))
            )

        namespace.update(
            {
                "st": fake_st,
                "_resolve_page": lambda target: daily_log,
                "_ORIGINAL_SWITCH_PAGE": switch_page,
                "_normalise_target": lambda target: str(target or ""),
            }
        )

        with self.assertRaises(_StopSignal):
            namespace["_embedded_switch_handler"](
                switch_page,
                "pages/18_Daily_Log.py",
            )

        self.assertEqual(switches, [("Daily_Log", "Daily_Log")])

    def test_unknown_target_stays_on_current_page_without_route_marker(self):
        namespace = _load_embedded_switch_handler()
        fake_st = _FakeStreamlit()
        switches = []
        namespace.update(
            {
                "st": fake_st,
                "_resolve_page": lambda target: None,
                "_ORIGINAL_SWITCH_PAGE": lambda page: switches.append(page),
                "_normalise_target": lambda target: str(target or ""),
            }
        )

        namespace["_embedded_switch_handler"](
            lambda page: switches.append(page),
            "pages/Unknown.py",
        )

        self.assertEqual(switches, [])
        self.assertNotIn(PENDING_KEY, fake_st.session_state)
        self.assertEqual(len(fake_st.warnings), 1)


if __name__ == "__main__":
    unittest.main()
