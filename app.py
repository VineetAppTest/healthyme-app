
import streamlit as st
from components.ui_common import inject_global_styles
st.set_page_config(page_title="HealthyMe", page_icon="🌿", layout="wide", initial_sidebar_state="collapsed")
inject_global_styles()
st.switch_page("pages/01_Login.py")
