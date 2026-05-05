import streamlit as st, json, pathlib
from components.guards import require_member
from components.ui_common import inject_global_styles, apply_luxe_theme, topbar, card_start, card_end, stat_grid, utility_logout_bar
from components.db import get_form_response, save_form_response, save_nsp_score
from components.assessment_instances import get_current_assessment_instance, get_instance_response, save_instance_page_response
from components.scoring import completion, unanswered_questions, score_answers
from components.flash import set_system_message, render_system_message

st.set_page_config(page_title="NSP Client Assessment - Page 2", page_icon="💚", layout="wide", initial_sidebar_state="collapsed")
inject_global_styles(); apply_luxe_theme(); require_member(); utility_logout_bar()

user_id = st.session_state["user_id"]
current_instance = get_current_assessment_instance(user_id)
instance_id = current_instance["instance_id"]
requested_pages = current_instance.get("requested_pages", ["nsp1", "nsp2"])

if "nsp2" not in requested_pages:
    st.warning("NSP Page 2 is not part of the current requested assessment.")
    if st.button("Back to Home"):
        st.switch_page("pages/02_Member_Home.py")
    st.stop()

questions = json.loads((pathlib.Path(__file__).resolve().parents[1] / "config" / "nsp_page2_questions.json").read_text())
questions = [q for q in questions if not q.get("deleted")]
existing = get_instance_response(instance_id, "nsp2") or get_form_response("nsp2_responses", user_id)
laf = get_form_response("laf_responses", user_id)

gender = str(laf.get("gender", "")).strip().lower()
is_male = gender == "male"
female_only_codes = {"nsp2_q49", "nsp2_q50", "nsp2_q60"}

def mapped_libido_default():
    libido = str(laf.get("libido_decline", "")).strip().lower()
    if libido == "yes":
        return "2"
    if libido == "no":
        return "NA"
    return "Select"

topbar(
    "NSP Client Assessment - Page 2",
    f"{current_instance.get('instance_type')} — Instance {current_instance.get('instance_number')}",
    "Assessment"
)
render_system_message()

card_start()
st.info("1 = mild/rare, 2 = moderate/regular, 3 = severe/often, NA = not applicable. This page auto-saves.")
st.caption(f"Requested pages: {', '.join(['NSP Page 1' if p=='nsp1' else 'NSP Page 2' for p in requested_pages])}")

if is_male:
    st.caption("Female-specific NSP questions are automatically marked NA because Gender is selected as Male in LAF Basic Profile.")

answers = {}
opts = ["Select", "NA", "1", "2", "3"]

for q in questions:
    code = q["code"]

    if code in female_only_codes and is_male:
        st.caption(f"{q['number']}. {q['text']} — Not applicable because Gender is Male.")
        answers[code] = st.selectbox(
            f"{q['number']}. {q['text']}",
            ["NA"],
            index=0,
            key=f"{instance_id}_{code}",
            disabled=True,
        )
        continue

    if code == "nsp2_q65":
        default = existing.get(code, "")
        if default in ["", "Select", None]:
            default = mapped_libido_default()
        st.caption("Mapped from LAF: libido decline. Yes → 2, No → NA. You may override if needed.")
    else:
        default = existing.get(code, "Select")

    answers[code] = st.selectbox(
        f"{q['number']}. {q['text']}",
        opts,
        index=opts.index(default) if default in opts else 0,
        key=f"{instance_id}_{code}",
    )

save_instance_page_response(user_id, "nsp2", answers)
save_form_response("nsp2_responses", user_id, answers)

missing = unanswered_questions(questions, answers)
answered, prog = completion(answers, len(questions))
all_na = len(questions) > 0 and all(v == "NA" for v in answers.values())

stat_grid([
    {"label": "Instance", "value": current_instance.get("instance_number"), "note": current_instance.get("instance_type")},
    {"label": "Completed", "value": answered, "note": "Questions answered"},
    {"label": "Remaining", "value": len(missing), "note": "Questions still unanswered"},
    {"label": "Progress", "value": f"{int(prog*100)}%", "note": "Completion"},
])
st.progress(prog)
st.markdown("<div class='autosave-note'>Auto-saved. Submit from the consent page.</div>", unsafe_allow_html=True)

if missing:
    st.warning(f"{len(missing)} questions remain unanswered.")
    with st.expander("Show unanswered questions"):
        for q in missing:
            st.write(f"{q['number']}. {q['text']}")
if all_na:
    st.warning("All responses are marked as NA. If accurate, you may submit.")

c1, c2 = st.columns(2)
with c1:
    if st.button("Previous Page", use_container_width=True):
        if "nsp1" in requested_pages:
            st.switch_page("pages/04_NSP_Page1.py")
        else:
            st.switch_page("pages/02_Member_Home.py")
with c2:
    if st.button("Proceed to Consent & Submit", type="primary", use_container_width=True):
        if missing:
            set_system_message("Please answer all applicable questions before continuing.", "error")
            st.rerun()
        else:
            save_instance_page_response(user_id, "nsp2", answers)
            save_nsp_score(user_id, score_answers(answers))
            st.switch_page("pages/24_NSP_Consent_Submit.py")
card_end()