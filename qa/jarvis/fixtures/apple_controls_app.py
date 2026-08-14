from __future__ import annotations

from datetime import date, time
import importlib.util
from pathlib import Path
import sys

import streamlit as st


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


COMPAT_PATH = ROOT / "components" / "apple_appearance_compat.py"
compat_spec = importlib.util.spec_from_file_location(
    "healthyme_apple_appearance_compat",
    COMPAT_PATH,
)
if compat_spec is None or compat_spec.loader is None:
    raise RuntimeError("Unable to load the HealthyMe Apple compatibility layer.")
compat_module = importlib.util.module_from_spec(compat_spec)
compat_spec.loader.exec_module(compat_module)


st.set_page_config(
    page_title="HealthyMe Apple contrast fixture",
    layout="wide",
    initial_sidebar_state="collapsed",
)
compat_module.render_apple_appearance_compat()

st.title("HealthyMe Apple contrast fixture")
st.caption("Synthetic controls only. No authentication, database or user data.")

left, right = st.columns(2)
with left:
    st.text_input("Text input", placeholder="Readable placeholder")
    st.text_input("Password input", type="password", value="Synthetic value")
    st.text_input("Disabled input", value="Disabled but readable", disabled=True)
    st.text_area("Text area", value="Readable Apple text", height=90)
    st.number_input("Number input", value=12)
    st.date_input("Date input", value=date(2026, 8, 14))
    st.time_input("Time input", value=time(10, 30))

with right:
    st.selectbox("Select input", ["First option", "Second option"])
    st.multiselect("Multiselect input", ["Alpha", "Beta"], default=["Alpha"])
    st.checkbox("Checkbox input", value=True)
    st.radio("Radio input", ["One", "Two"], horizontal=True)
    st.toggle("Toggle input", value=True)
    st.slider("Slider input", 0, 10, 5)
    st.file_uploader("File uploader")

st.data_editor(
    {"Field": ["Synthetic"], "Value": ["Readable"]},
    disabled=True,
    hide_index=True,
    use_container_width=True,
)
