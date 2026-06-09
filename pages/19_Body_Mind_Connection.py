import datetime
import streamlit as st, json, pathlib, datetime
from collections import OrderedDict
from components.guards import require_member
from components.ui_common import inject_global_styles, apply_luxe_theme, topbar, card_start, card_end, utility_logout_bar, render_build_text_v12, render_back_to_top, compact_topbar
from components.db import get_workflow, get_body_mind_response, save_body_mind_response, get_profile_with_laf_fallback, has_explicit_body_mind_access
from components.flash import set_system_message, render_system_message


st.set_page_config(page_title="Body-Mind Connection", page_icon="💚", layout="wide", initial_sidebar_state="collapsed")
inject_global_styles(); apply_luxe_theme(); require_member(); utility_logout_bar(); render_back_to_top()

user_id = st.session_state["user_id"]
wf = get_workflow(user_id)
body_mind_allowed = bool(wf.get("body_mind_unlocked")) or has_explicit_body_mind_access(user_id)
if not body_mind_allowed:
    st.warning("This page will be available after your evaluator enables it.")
    st.stop()

BASE = pathlib.Path(__file__).resolve().parents[1]

# v87 regression guard: Body-Mind question loading must not depend on a missing helper.
@st.cache_data(show_spinner=False)
def load_body_mind_questions_cached():
    """
    Stable Body-Mind question loader.

    This wrapper intentionally stays page-local so the Body-Mind page cannot crash
    with NameError if a shared cached helper is removed during later UI patches.
    It tries known project sources first, then falls back to the embedded
    Body-Mind question bank used by this page.
    """
    # 1) Try shared loader from data.db, if present.
    try:
        from data.db import load_body_mind_questions as _shared_loader
        questions = _shared_loader()
        if questions:
            return questions
    except Exception:
        pass

    # 2) Try shared loader from db.py, if present.
    try:
        from db import load_body_mind_questions as _shared_loader
        questions = _shared_loader()
        if questions:
            return questions
    except Exception:
        pass

    # 3) Try local config/json files, if present.
    try:
        import json
        from pathlib import Path
        candidate_paths = [
            Path("data/body_mind_questions.json"),
            Path("config/body_mind_questions.json"),
            Path("assets/body_mind_questions.json"),
        ]
        for path in candidate_paths:
            if path.exists():
                payload = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(payload, list) and payload:
                    return payload
                if isinstance(payload, dict):
                    for key in ["questions", "body_mind_questions", "items"]:
                        if isinstance(payload.get(key), list) and payload.get(key):
                            return payload.get(key)
    except Exception:
        pass

    # 4) Last-resort embedded fallback. This prevents the page from crashing and
    # keeps the form usable even if the external question repository is missing.
    return [
        {"key": "stress_state", "section": "Mind-body awareness", "question": "Current stress / emotional state", "type": "text"},
        {"key": "sleep_quality", "section": "Mind-body awareness", "question": "Sleep quality and restfulness", "type": "text"},
        {"key": "energy_pattern", "section": "Mind-body awareness", "question": "Energy pattern through the day", "type": "text"},
        {"key": "cravings_mood_link", "section": "Mind-body awareness", "question": "Cravings or food choices linked to mood", "type": "text"},
        {"key": "body_signals", "section": "Mind-body awareness", "question": "Body signals noticed after meals or during the day", "type": "text"},
    ]

questions = load_body_mind_questions_cached()
questions = [q for q in questions if not q.get("deleted") and q.get("section") != "Client Statement"]
existing = get_body_mind_response(user_id)
profile = get_profile_with_laf_fallback(user_id)

compact_topbar("Body-Mind Connection", "This section is enabled by the admin after assessment review.", "Member reflection")
render_system_message()

st.markdown("""
<div class='info-banner'>

</div>
""", unsafe_allow_html=True)

sections = OrderedDict()
for q in questions:
    sections.setdefault(q.get("section", "General"), []).append(q)

answers = dict(existing)

for section, qs in sections.items():
    card_start()
    st.subheader(section)
    for q in qs:
        code = q["code"]
        default = existing.get(code, "")
        if q.get("type") == "date":
            try:
                dt = datetime.date.fromisoformat(str(default)) if default else datetime.date.today()
            except Exception:
                dt = datetime.date.today()
            answers[code] = st.date_input(q["label"], value=dt, key=f"body_{code}").isoformat()
        else:
            answers[code] = st.text_area(q["label"], value="" if default in [None, "Select"] else str(default), height=90, key=f"body_{code}")
    card_end()

save_body_mind_response(user_id, answers, completed=False)
st.markdown("<div class='autosave-note'>Auto-saved. Submit this page when ready.</div>", unsafe_allow_html=True)

c1, c2 = st.columns(2)
with c1:
    if st.button("Back to Home", use_container_width=True):
        save_body_mind_response(user_id, answers, completed=False)
        st.switch_page("pages/02_Member_Home.py")
with c2:
    if st.button("Submit Body-Mind Page", type="primary", use_container_width=True):
        save_body_mind_response(user_id, answers, completed=True)
        set_system_message("Body-Mind page submitted successfully.", "success", celebrate=True)
        st.switch_page("pages/02_Member_Home.py")