from __future__ import annotations

import runpy
from pathlib import Path

import streamlit as st


st.session_state["_hm_supplement_workspace_embedded"] = True
try:
    runpy.run_path(
        str(Path(__file__).resolve().with_name("39_Admin_Supplement_Manager.py")),
        run_name="__hm_supplement_workspace__",
    )
finally:
    st.session_state.pop("_hm_supplement_workspace_embedded", None)
