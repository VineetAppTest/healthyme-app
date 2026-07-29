from __future__ import annotations

import datetime as dt
import functools
import json
import time
import uuid
from collections import Counter
from typing import Any, Callable

import streamlit as st


ENABLED_KEY = "_hm_perf_measurement_enabled"
ACTIVE_RUN_KEY = "_hm_perf_active_run"
HISTORY_KEY = "_hm_perf_history"
MAX_HISTORY = 80
MAX_OPERATIONS_PER_RUN = 250


def _text(value: object) -> str:
    return str(value or "").strip()


def _session_state():
    try:
        return st.session_state
    except Exception:
        return None


def measurement_enabled() -> bool:
    ss = _session_state()
    if ss is None:
        return False
    try:
        query_value = _text(st.query_params.get("perf", ""))
    except Exception:
        query_value = ""
    if query_value == "1":
        ss[ENABLED_KEY] = True
    elif query_value == "0":
        ss[ENABLED_KEY] = False
    return bool(ss.get(ENABLED_KEY, False))


def set_measurement_enabled(enabled: bool) -> None:
    ss = _session_state()
    if ss is not None:
        ss[ENABLED_KEY] = bool(enabled)


def clear_measurement_history() -> None:
    ss = _session_state()
    if ss is None:
        return
    ss.pop(ACTIVE_RUN_KEY, None)
    ss[HISTORY_KEY] = []


def _safe_count(value: object) -> int:
    if isinstance(value, dict):
        return len(value)
    if isinstance(value, (list, tuple, set)):
        return len(value)
    return 0


def _state_shape(db: object) -> dict[str, int]:
    if not isinstance(db, dict):
        return {}
    keys = (
        "users",
        "profiles",
        "workflow",
        "daily_logs",
        "messages",
        "notifications",
        "schedules",
        "reschedule_requests",
        "recommendation_profiles",
        "packages",
        "member_packages",
        "audit_logs",
    )
    return {key: _safe_count(db.get(key)) for key in keys if key in db}


def begin_page_measurement(page_name: str) -> None:
    """Start a temporary, session-local measurement run for one rendered page."""

    install_backend_measurement()
    ss = _session_state()
    if ss is None:
        return
    ss[ACTIVE_RUN_KEY] = {
        "run_id": uuid.uuid4().hex[:10],
        "page": _text(page_name) or "Unknown page",
        "started_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "started_perf": time.perf_counter(),
        "operations": [],
        "state_shape": {},
    }


def record_operation(
    name: str,
    duration_ms: float,
    *,
    details: dict[str, Any] | None = None,
    failed: bool = False,
) -> None:
    ss = _session_state()
    if ss is None:
        return
    run = ss.get(ACTIVE_RUN_KEY)
    if not isinstance(run, dict):
        return
    operations = run.setdefault("operations", [])
    if len(operations) >= MAX_OPERATIONS_PER_RUN:
        return
    safe_details: dict[str, Any] = {}
    for key, value in dict(details or {}).items():
        if isinstance(value, (str, int, float, bool)) or value is None:
            safe_details[str(key)] = value
    operations.append(
        {
            "name": _text(name),
            "duration_ms": round(float(duration_ms), 2),
            "failed": bool(failed),
            "details": safe_details,
        }
    )


def _capture_state_shape_once(db: object) -> None:
    ss = _session_state()
    if ss is None:
        return
    run = ss.get(ACTIVE_RUN_KEY)
    if not isinstance(run, dict) or run.get("state_shape"):
        return
    run["state_shape"] = _state_shape(db)


def finish_page_measurement(page_name: str | None = None) -> dict[str, Any] | None:
    ss = _session_state()
    if ss is None:
        return None
    run = ss.pop(ACTIVE_RUN_KEY, None)
    if not isinstance(run, dict):
        return None

    elapsed_ms = max((time.perf_counter() - float(run.get("started_perf", 0))) * 1000, 0)
    operations = list(run.get("operations") or [])
    operation_counts = Counter(_text(item.get("name")) for item in operations)
    operation_time = Counter()
    for item in operations:
        operation_time[_text(item.get("name"))] += float(item.get("duration_ms") or 0)

    summary = {
        "run_id": run.get("run_id", ""),
        "page": _text(page_name) or _text(run.get("page")) or "Unknown page",
        "started_at": run.get("started_at", ""),
        "total_render_ms": round(elapsed_ms, 2),
        "operation_count": len(operations),
        "operation_counts": dict(operation_counts),
        "operation_time_ms": {key: round(value, 2) for key, value in operation_time.items()},
        "slowest_operations": sorted(
            operations,
            key=lambda item: float(item.get("duration_ms") or 0),
            reverse=True,
        )[:12],
        "state_shape": dict(run.get("state_shape") or {}),
        "session_state_keys": len(ss.keys()),
    }
    history = list(ss.get(HISTORY_KEY) or [])
    history.insert(0, summary)
    ss[HISTORY_KEY] = history[:MAX_HISTORY]
    return summary


def measurement_history() -> list[dict[str, Any]]:
    ss = _session_state()
    if ss is None:
        return []
    return [dict(item) for item in (ss.get(HISTORY_KEY) or []) if isinstance(item, dict)]


def _render_summary(summary: dict[str, Any]) -> None:
    c1, c2, c3, c4 = st.columns(4, gap="small")
    c1.metric("Page render", f"{float(summary.get('total_render_ms', 0)) / 1000:.2f}s")
    c2.metric("Measured operations", int(summary.get("operation_count", 0)))
    counts = dict(summary.get("operation_counts") or {})
    c3.metric("State loads", int(counts.get("db.load_db", 0)))
    c4.metric("State saves", int(counts.get("db.save_db", 0)))

    operation_rows = []
    times = dict(summary.get("operation_time_ms") or {})
    for name, count in sorted(counts.items(), key=lambda item: (-item[1], item[0])):
        operation_rows.append(
            {
                "Operation": name,
                "Calls": count,
                "Total ms": round(float(times.get(name, 0)), 2),
            }
        )
    if operation_rows:
        st.dataframe(operation_rows, use_container_width=True, hide_index=True)

    state_shape = dict(summary.get("state_shape") or {})
    if state_shape:
        st.caption("Application-state record counts loaded during this run")
        st.dataframe(
            [{"Store": key, "Records": value} for key, value in state_shape.items()],
            use_container_width=True,
            hide_index=True,
        )

    slowest = list(summary.get("slowest_operations") or [])
    if slowest:
        st.caption("Slowest measured backend operations")
        st.dataframe(
            [
                {
                    "Operation": row.get("name", ""),
                    "Duration ms": row.get("duration_ms", 0),
                    "Failed": row.get("failed", False),
                    "Details": json.dumps(row.get("details") or {}, sort_keys=True),
                }
                for row in slowest
            ],
            use_container_width=True,
            hide_index=True,
        )


def finish_and_render_page_diagnostics(page_name: str) -> dict[str, Any] | None:
    summary = finish_page_measurement(page_name)
    if summary and measurement_enabled():
        with st.expander("Performance Diagnostics · temporary measurement", expanded=False):
            st.caption(
                "No passwords, message text, health data or member notes are captured. "
                "Measurements remain in this Streamlit session only."
            )
            _render_summary(summary)
    return summary


def render_history_workspace() -> None:
    history = measurement_history()
    if not history:
        st.info(
            "No measurements are available in this browser session. Enable measurement, "
            "open the target pages, interact with them and return here."
        )
        return

    page_options = ["All pages"] + sorted({str(row.get("page") or "Unknown") for row in history})
    selected_page = st.selectbox("Filter page", page_options, key="hm_perf_history_page")
    filtered = history if selected_page == "All pages" else [
        row for row in history if row.get("page") == selected_page
    ]

    rows = []
    for item in filtered:
        counts = dict(item.get("operation_counts") or {})
        rows.append(
            {
                "Started UTC": item.get("started_at", ""),
                "Page": item.get("page", ""),
                "Render seconds": round(float(item.get("total_render_ms", 0)) / 1000, 3),
                "Operations": item.get("operation_count", 0),
                "load_db": counts.get("db.load_db", 0),
                "load_state": counts.get("storage.load_state", 0),
                "Supabase reads": counts.get("storage.supabase_read", 0),
                "Supabase writes": counts.get("storage.supabase_write", 0),
                "Package RPC": counts.get("package.rpc", 0),
                "Session-state keys": item.get("session_state_keys", 0),
            }
        )
    st.dataframe(rows, use_container_width=True, hide_index=True)

    selected_run = st.selectbox(
        "Inspect run",
        [
            f"{row.get('started_at','')} · {row.get('page','')} · {float(row.get('total_render_ms',0))/1000:.2f}s · {row.get('run_id','')}"
            for row in filtered
        ],
        key="hm_perf_history_run",
    )
    selected_index = [
        f"{row.get('started_at','')} · {row.get('page','')} · {float(row.get('total_render_ms',0))/1000:.2f}s · {row.get('run_id','')}"
        for row in filtered
    ].index(selected_run)
    _render_summary(filtered[selected_index])

    export_payload = json.dumps(history, indent=2, sort_keys=True)
    st.download_button(
        "Download measurement JSON",
        data=export_payload,
        file_name="healthyme_performance_measurements.json",
        mime="application/json",
        use_container_width=True,
    )


def _wrap_function(
    module: Any,
    attribute: str,
    operation_name: str,
    *,
    details_before: Callable[[tuple[Any, ...], dict[str, Any]], dict[str, Any]] | None = None,
    details_after: Callable[[Any], dict[str, Any]] | None = None,
    capture_state: bool = False,
) -> None:
    original = getattr(module, attribute, None)
    if not callable(original) or getattr(original, "_hm_perf_wrapped", False):
        return

    @functools.wraps(original)
    def measured(*args, **kwargs):
        started = time.perf_counter()
        failed = False
        result = None
        details: dict[str, Any] = {}
        try:
            if details_before:
                details.update(details_before(args, kwargs) or {})
            result = original(*args, **kwargs)
            if details_after:
                details.update(details_after(result) or {})
            if capture_state:
                _capture_state_shape_once(result)
            return result
        except Exception:
            failed = True
            raise
        finally:
            record_operation(
                operation_name,
                (time.perf_counter() - started) * 1000,
                details=details,
                failed=failed,
            )

    measured._hm_perf_wrapped = True
    measured._hm_perf_original = original
    setattr(module, attribute, measured)


def install_backend_measurement() -> None:
    """Install low-risk timing wrappers without changing application results."""

    try:
        from components import db as db_api
        from components import storage_backend

        _wrap_function(db_api, "load_db", "db.load_db", capture_state=True)
        _wrap_function(db_api, "save_db", "db.save_db")

        def load_details(args, kwargs):
            force_refresh = bool(kwargs.get("force_refresh", args[0] if args else False))
            try:
                cache_hit = (not force_refresh) and storage_backend._get_cache() is not None
            except Exception:
                cache_hit = False
            return {"force_refresh": force_refresh, "cache_hit": cache_hit}

        _wrap_function(
            storage_backend,
            "load_state",
            "storage.load_state",
            details_before=load_details,
            capture_state=True,
        )
        # db.py imported these functions directly, so update its module aliases too.
        db_api.load_state = storage_backend.load_state

        _wrap_function(storage_backend, "save_state", "storage.save_state")
        db_api.save_state = storage_backend.save_state
        _wrap_function(storage_backend, "_load_from_supabase", "storage.supabase_read")
        _wrap_function(storage_backend, "_save_to_supabase", "storage.supabase_write")
    except Exception:
        pass

    try:
        from components import normalized_store
        from components import storage_backend

        _wrap_function(
            normalized_store,
            "load_users_workflow_from_normalized",
            "normalized.users_workflow_read",
        )
        storage_backend.load_users_workflow_from_normalized = (
            normalized_store.load_users_workflow_from_normalized
        )
        _wrap_function(
            normalized_store,
            "sync_users_workflow_to_normalized",
            "normalized.users_workflow_write",
        )
        storage_backend.sync_users_workflow_to_normalized = (
            normalized_store.sync_users_workflow_to_normalized
        )
    except Exception:
        pass

    try:
        from components import package_hardening

        def rpc_details(args, kwargs):
            return {"rpc": _text(args[0] if args else "")}

        _wrap_function(
            package_hardening,
            "_rpc",
            "package.rpc",
            details_before=rpc_details,
        )
    except Exception:
        pass
