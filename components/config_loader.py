from pathlib import Path
import json
import streamlit as st

BASE = Path(__file__).resolve().parents[1]

@st.cache_data(show_spinner=False)
def load_config_json_cached(relative_path: str):
    """Cached static JSON loader for config files.

    Use for LAF, Body-Mind, NSP, recipes/exercises and admin dietary configs.
    Business logic remains unchanged; this only avoids repeated disk reads.
    """
    path = BASE / relative_path
    return json.loads(path.read_text(encoding="utf-8"))

def load_laf_questions_cached():
    return load_config_json_cached("config/laf_questions.json")

def load_body_mind_questions_cached():
    return load_config_json_cached("config/body_mind_questions.json")

def load_admin_dietary_habits_questions_cached():
    return load_config_json_cached("config/admin_dietary_habits_questions.json")
