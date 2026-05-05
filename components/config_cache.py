import json
import pathlib
import streamlit as st

BASE_DIR = pathlib.Path(__file__).resolve().parents[1]

@st.cache_data(show_spinner=False)
def load_config_json(rel_path: str):
    """Cached loader for static app config JSON files.

    Helps avoid repeated disk reads/parsing of large questionnaire templates
    across reruns. Question Manager writes still update files; use refresh_config_cache()
    after edits.
    """
    return json.loads((BASE_DIR / rel_path).read_text(encoding="utf-8"))

def refresh_config_cache():
    load_config_json.clear()