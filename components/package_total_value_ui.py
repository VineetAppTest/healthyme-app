from __future__ import annotations

import streamlit as st


_STATE_KEY = "_hm_package_total_value_inputs"


def install_package_total_value_calculation(package_ui) -> None:
    """Make Package Library total value read-only and derived from allowance × cost."""

    if getattr(st, "_hm_package_total_value_calculation_installed", False):
        return
    st._hm_package_total_value_calculation_installed = True

    base_number_input = st.number_input
    values = {"sessions": 1, "cost": 0.0}
    st.session_state.setdefault(_STATE_KEY, {})

    def calculated_number_input(label, *args, **kwargs):
        label_text = str(label or "")
        if label_text == "Session allowance":
            result = base_number_input(label, *args, **kwargs)
            values["sessions"] = max(int(result or 1), 1)
            st.session_state[_STATE_KEY]["sessions"] = values["sessions"]
            return result

        if label_text == "Cost per session":
            result = base_number_input(label, *args, **kwargs)
            values["cost"] = max(float(result or 0), 0.0)
            st.session_state[_STATE_KEY]["cost"] = values["cost"]
            return result

        if label_text == "Total package value":
            sessions = max(
                int(values.get("sessions") or st.session_state[_STATE_KEY].get("sessions") or 1),
                1,
            )
            cost = max(
                float(values.get("cost") or st.session_state[_STATE_KEY].get("cost") or 0),
                0.0,
            )
            calculated_total = float(sessions) * float(cost)
            adjusted = dict(kwargs)
            adjusted["value"] = calculated_total
            adjusted["disabled"] = True
            adjusted["help"] = (
                "Calculated automatically as Session allowance × Cost per session."
            )
            base_number_input(label, *args, **adjusted)
            return calculated_total

        return base_number_input(label, *args, **kwargs)

    st.number_input = calculated_number_input
    package_ui.st.number_input = calculated_number_input
