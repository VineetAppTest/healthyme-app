from __future__ import annotations

import functools
import json
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


def _render_member_measurement_export(diagnostics: Any, summary: dict[str, Any]) -> None:
    history = _member_measurement_history(diagnostics.measurement_history())
    if not history:
        return

    run_id = str(summary.get("run_id") or "current")
    with st.container(border=True):
        st.markdown("### Performance measurement active")
        st.caption(
            "This panel appears only when Member measurement is enabled with `?perf=1`. "
            "Download the accumulated Member measurements before logging out. "
            "The file contains timing, operation names and aggregate counts only."
        )
        st.download_button(
            f"Download Member measurement JSON ({len(history)} runs)",
            data=json.dumps(history, indent=2, sort_keys=True),
            file_name="healthyme_member_performance_measurements.json",
            mime="application/json",
            use_container_width=True,
            key=f"hm_member_perf_download_{run_id}",
        )


def install_performance_measurement_gate() -> None:
    """Gate measurements and expose a direct, session-local Member JSON download."""

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
            if (
                isinstance(summary, dict)
                and diagnostics.measurement_enabled()
                and resolved_page.startswith(_MEMBER_PAGE_PREFIX)
            ):
                _render_member_measurement_export(diagnostics, summary)
            return summary

        setattr(finish_with_member_export, _MEMBER_EXPORT_MARKER, True)
        finish_with_member_export._hm_perf_original = current_finish
        diagnostics.finish_and_render_page_diagnostics = finish_with_member_export
