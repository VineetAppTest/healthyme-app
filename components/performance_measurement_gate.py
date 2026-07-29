from __future__ import annotations


def install_performance_measurement_gate() -> None:
    """Ensure explicit page measurements honor the temporary enable/pause control."""

    from components import performance_diagnostics as diagnostics

    current = diagnostics.begin_page_measurement
    if getattr(current, "_hm_perf_enable_gate", False):
        return

    def gated_begin_page_measurement(page_name: str) -> None:
        if not diagnostics.measurement_enabled():
            return
        current(page_name)

    gated_begin_page_measurement._hm_perf_enable_gate = True
    gated_begin_page_measurement._hm_perf_original = current
    diagnostics.begin_page_measurement = gated_begin_page_measurement
