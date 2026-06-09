
from pathlib import Path
import streamlit.components.v1 as components

_component_path = Path(__file__).parent / "frontend"
_mobile_time_input = components.declare_component("healthyme_mobile_time_input", path=str(_component_path))

def mobile_time_input(label, value="08:00", key=None):
    """
    Returns time in HH:MM 24-hour format, e.g. "08:30".
    Browser renders a native mobile time input where supported.
    """
    return _mobile_time_input(label=label, value=value, key=key, default=value)
