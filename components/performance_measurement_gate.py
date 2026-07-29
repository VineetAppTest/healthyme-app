from __future__ import annotations

import functools
import json
import re
from typing import Any

import streamlit as st


_MEMBER_EXPORT_MARKER = "_hm_member_performance_export"
_MEMBER_PAGE_PREFIX = "Member "


def _member_measurement_history(history: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return only sanitized Member-page measurement summaries."""

    return [
        dict(item)
        for item in history
        if isinstance(item, dict)
        and str(item.get("page") or "").startswith(_MEMBER_PAGE_PREFIX)
    ]


def _key_part(value: object) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "_", str(value or "member")).strip("_").lower()


def _set_perf_query(value: str) -> None:
    try:
        st.query_params["perf"] = value
    except Exception:
        pass


def _render_member_measurement_panel(
    diagnostics: Any,
    summary: dict[str, Any] | None,
    page_name: str,
) -> None:
    """Always expose a visible, session-local Member diagnostics control."""

    history = _member_measurement_history(diagnostics.measurement_history())
    enabled = diagnostics.measurement_enabled()
    run_id = str((summary or {}).get("run_id") or _key_part(page_name) or "current")

    with st.container(border=True):
        st.markdown("### Member Performance Diagnostics")
        if not enabled:
            st.caption(
                "Start temporary measurement, use Member Home, Daily Log and My Schedule, "
                "then download the accumulated JSON before logging out. Only timing, "
                "operation names and aggregate counts are captured."
            )
            if st.button(
                "Start Member performance measurement",
                key=f"hm_member_perf_start_{run_id}",
                use_container_width=True,
            ):
                diagnostics.clear_measurement_history()
                diagnostics.set_measurement_enabled(True)
                _set_perf_query("1")
                st.rerun()
            return

        st.caption(
            "Measurement is active for this browser session. Navigate through the Member "
            "journey and download the JSON before logging out."
        )
        if history:
            st.download_button(
                f"Download Member measurement JSON ({len(history)} runs)",
                data=json.dumps(history, indent=2, sort_keys=True),
                file_name="healthyme_member_performance_measurements.json",
                mime="application/json",
                use_container_width=True,
                key=f"hm_member_perf_download_{run_id}",
            )
        else:
            st.caption(
                "Measurement has started. Open or interact with a Member page to create "
                "the first recorded run."
            )

        stop_col, clear_col = st.columns(2)
        with stop_col:
            if st.button(
                "Stop measurement",
                key=f"hm_member_perf_stop_{run_id}",
                use_container_width=True,
            ):
                diagnostics.set_measurement_enabled(False)
                _set_perf_query("0")
                st.rerun()
        with clear_col:
            if st.button(
                "Clear recorded runs",
                key=f"hm_member_perf_clear_{run_id}",
                use_container_width=True,
                disabled=not bool(history),
            ):
                diagnostics.clear_measurement_history()
                st.rerun()


def install_performance_measurement_gate() -> None:
    """Gate measurements and expose a direct, visible Member JSON control."""

    from components import performance_diagnostics as diagnostics

    current_begin = diagnostics.begin_page_measurement
    if not getattr(current_begin, "_hm_perf_enable_gate", False):

        @functools.wraps(current_begin)
        def gated_begin_page_measurement(page_name: str) -> None:
            if not diagnostics.measurement_enabled():
                return
            current_begin(page_name)

        gated_begin_page_measurement._hm_perf_enable_gate = True
        gated_begin_page_measurement._hm_perf_original = current_begin
        diagnostics.begin_page_measurement = gated_begin_page_measurement

    current_finish = diagnostics.finish_and_render_page_diagnostics
    if not getattr(current_finish, _MEMBER_EXPORT_MARKER, False):

        @functools.wraps(current_finish)
        def finish_with_member_export(page_name: str):
            summary = current_finish(page_name)
            resolved_page = str(
                (summary or {}).get("page") or page_name or ""
            ).strip()
            if resolved_page.startswith(_MEMBER_PAGE_PREFIX):
                _render_member_measurement_panel(
                    diagnostics,
                    summary if isinstance(summary, dict) else None,
                    resolved_page,
                )
            return summary

        setattr(finish_with_member_export, _MEMBER_EXPORT_MARKER, True)
        finish_with_member_export._hm_perf_original = current_finish
        diagnostics.finish_and_render_page_diagnostics = finish_with_member_export
