import streamlit as st, json, pathlib, datetime
from collections import OrderedDict
from components.guards import require_member
from components.ui_common import inject_global_styles, apply_luxe_theme, topbar, card_start, card_end, utility_logout_bar
from components.db import get_workflow, get_body_mind_response, save_body_mind_response, get_profile_with_laf_fallback
from components.flash import set_system_message, render_system_message

st.set_page_config(page_title="Body-Mind Connection", page_icon="💚", layout="wide", initial_sidebar_state="collapsed")
inject_global_styles(); apply_luxe_theme(); require_member(); utility_logout_bar()

user_id = st.session_state["user_id"]
wf = get_workflow(user_id)
if not wf.get("body_mind_unlocked"):
    st.warning("This page will be available after your evaluator enables it.")
    st.stop()

BASE = pathlib.Path(__file__).resolve().parents[1]
questions = json.loads((BASE / "config" / "body_mind_questions.json").read_text(encoding="utf-8"))
questions = [q for q in questions if not q.get("deleted") and q.get("section") != "Client Statement"]
existing = get_body_mind_response(user_id)
profile = get_profile_with_laf_fallback(user_id)

topbar("Body-Mind Connection", "This section is enabled by the admin after assessment review.", "Member reflection")
render_system_message()

st.markdown("""
<div class='info-banner'>
<b>Auto-save enabled.</b><br>
Your Body-Mind responses are saved as you work. The client consent statement is now captured in the NSP submission flow.
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