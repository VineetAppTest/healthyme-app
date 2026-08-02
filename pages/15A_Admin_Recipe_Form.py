from __future__ import annotations

import runpy
from pathlib import Path

import streamlit as st


st.session_state["_hm_recipe_workspace_embedded"] = True
try:
    runpy.run_path(
        str(Path(__file__).resolve().with_name("15_Admin_Recipe_Manager.py")),
        run_name="__hm_recipe_workspace__",
    )
finally:
    st.session_state.pop("_hm_recipe_workspace_embedded", None)
