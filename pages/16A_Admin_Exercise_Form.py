from __future__ import annotations

import runpy
from pathlib import Path

import streamlit as st


st.session_state["_hm_exercise_workspace_embedded"] = True
try:
    runpy.run_path(
        str(Path(__file__).resolve().with_name("16_Admin_Exercise_Manager.py")),
        run_name="__hm_exercise_workspace__",
    )
finally:
    st.session_state.pop("_hm_exercise_workspace_embedded", None)
