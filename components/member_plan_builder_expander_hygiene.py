from __future__ import annotations

from streamlit.delta_generator import DeltaGenerator


_INSTALLED = False


def install_member_plan_builder_expander_hygiene() -> None:
    global _INSTALLED
    if _INSTALLED:
        return

    original_expander = DeltaGenerator.expander

    def compact_expander(self, label, *args, **kwargs):
        text = str(label or "").strip()
        if text == "More setup details" or text.startswith("More details —"):
            label = "More details"
        return original_expander(self, label, *args, **kwargs)

    compact_expander._hm_member_plan_builder_expander = True
    DeltaGenerator.expander = compact_expander
    _INSTALLED = True
