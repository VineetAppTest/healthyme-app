import streamlit as st, json, pathlib, re
import streamlit.components.v1 as components
from collections import OrderedDict
from components.guards import require_member
from components.ui_common import inject_global_styles, apply_luxe_theme, topbar, card_start, card_end, stat_grid, utility_logout_bar
from components.db import get_form_response, save_form_response, update_workflow, sync_profile_from_laf, load_db
from components.flash import set_system_message, render_system_message

st.set_page_config(page_title="LAF", page_icon="💚", layout="wide")
inject_global_styles(); apply_luxe_theme(); require_member(); utility_logout_bar()

questions = json.loads((pathlib.Path(__file__).resolve().parents[1] / "config" / "laf_questions.json").read_text(encoding="utf-8"))
questions = [q for q in questions if not q.get("deleted")]
existing = get_form_response("laf_responses", st.session_state["user_id"])
user_id = st.session_state["user_id"]

should_scroll_top = st.session_state.pop(f"laf_scroll_top_{user_id}", False)

if should_scroll_top:
    components.html(
        """
        <script>
        (function(){
            function scrollAllTheWayTop(){
                try { window.parent.scrollTo(0, 0); } catch(e) {}
                try { window.parent.document.documentElement.scrollTop = 0; } catch(e) {}
                try { window.parent.document.body.scrollTop = 0; } catch(e) {}

                try {
                    const doc = window.parent.document;
                    const selectors = [
                        'html',
                        'body',
                        'main',
                        'section',
                        'div',
                        '[data-testid="stAppViewContainer"]',
                        '[data-testid="stMain"]',
                        '[data-testid="stMainBlockContainer"]',
                        '[data-testid="stVerticalBlock"]',
                        '.main',
                        '.block-container'
                    ];

                    const nodes = new Set();
                    selectors.forEach((selector) => {
                        try { doc.querySelectorAll(selector).forEach((el) => nodes.add(el)); } catch(e) {}
                    });

                    nodes.forEach((el) => {
                        try {
                            if (el && el.scrollHeight && el.scrollHeight > el.clientHeight) {
                                el.scrollTop = 0;
                                el.scrollTo({ top: 0, left: 0, behavior: 'auto' });
                            }
                        } catch(e) {}
                    });
                } catch(e) {}
            }

            scrollAllTheWayTop();
            window.requestAnimationFrame(scrollAllTheWayTop);
            setTimeout(scrollAllTheWayTop, 20);
            setTimeout(scrollAllTheWayTop, 75);
            setTimeout(scrollAllTheWayTop, 150);
            setTimeout(scrollAllTheWayTop, 300);
            setTimeout(scrollAllTheWayTop, 600);
            setTimeout(scrollAllTheWayTop, 1000);
        })();
        </script>
        """,
        height=0,
    )


db = load_db()
current_user = next((u for u in db.get("users", []) if u.get("id") == user_id), {})
login_email = current_user.get("email", "")

DEPENDENCIES = {
    "smoke_tobacco_details": ("smoke_tobacco", ["Yes"]),
    "medicinal_marijuana_details": ("medicinal_marijuana", ["Yes"]),
    "recreational_drugs_details": ("recreational_drugs", ["Yes"]),
    "dependency_type": ("dependency_treatment", ["Yes"]),
    "dependency_how_long_ago": ("dependency_treatment", ["Yes"]),
    "weight_goal_amount": ("weight_goal_type", ["Gain weight", "Lose weight"]),
    "weight_goal_date": ("weight_goal_type", ["Gain weight", "Lose weight"]),
    "weight_goal_motivation": ("weight_goal_type", ["Gain weight", "Lose weight"]),
    "prescription_medication_list": ("prescription_medication", ["Yes"]),
    "otc_medication_list": ("otc_medication", ["Yes"]),
    "antibiotics_details": ("antibiotics_5_years", ["Yes"]),
    "allergies_sensitivities_list": ("allergies_sensitivities", ["Yes"]),
    "diagnosed_illness_details": ("diagnosed_illness", ["Yes"]),
    "hospitalized_reason": ("hospitalized", ["Yes"]),
    "strain_related_food_circumstances": ("strain_bowel_movement", ["Yes", "Occasionally"]),
    "loose_related_food_circumstances": ("loose_bowel_movements", ["Yes", "Occasionally"]),
    "fungal_infections_details": ("fungal_infections", ["Yes"]),
    "libido_decline_details": ("libido_decline", ["Yes"]),
    "kidney_gall_stones_details": ("kidney_gall_stones", ["Yes"]),
    "pregnancy_trimester": ("pregnant_possible", ["Yes"]),
    "menses_changes_details": ("menses_changes", ["Yes"]),
    "menopausal_symptoms_details": ("menopausal_symptoms", ["Yes"]),
    "bone_density_result": ("bone_density_test", ["Yes"]),
    "prostate_problems_details": ("prostate_problems", ["Yes"]),
    "diet_restrictions_explain": ("diet_restrictions_due_to_others", ["Yes"]),
    "avoid_foods_why": ("avoid_foods", ["Yes"]),
    "symptoms_if_meals_missed_explain": ("symptoms_if_meals_missed", ["Yes"]),
    "symptoms_after_meals_explain": ("symptoms_after_meals", ["Yes"]),
}

FEMALE_RELATED_CODES = {
    "pregnant_possible",
    "pregnancy_trimester",
    "miscarriages_history",
    "menses_changes",
    "menses_changes_details",
    "pms_symptoms",
    "peri_menopausal",
    "menopausal",
    "post_menopausal",
    "menopausal_symptoms",
    "menopausal_symptoms_details",
    "bone_density_test",
    "bone_density_result",
    "birth_control",
}

MALE_RELATED_CODES = {
    "prostate_problems",
    "prostate_problems_details",
}

REQUIRED_CODES = {
    "full_name": "Name",
    "age": "Age",
    "gender": "Gender",
    "country": "Country",
    "mobile_number": "Mobile Number",
    "email_id": "Email ID",
}

MOBILE_DIGIT_RULES = {
    "India": (10, 10),
    "United States": (10, 10),
    "Canada": (10, 10),
    "United Kingdom": (10, 10),
    "Australia": (9, 9),
    "United Arab Emirates": (9, 9),
    "Singapore": (8, 8),
    "Other": (7, 15),
}

COUNTRY_PREFIXES = {
    "India": "91",
    "United States": "1",
    "Canada": "1",
    "United Kingdom": "44",
    "Australia": "61",
    "United Arab Emirates": "971",
    "Singapore": "65",
}

MOBILE_DIGIT_RULES = {
    "India": (10, 10),
    "United States": (10, 10),
    "Canada": (10, 10),
    "United Kingdom": (10, 10),
    "Australia": (9, 9),
    "United Arab Emirates": (9, 9),
    "Singapore": (8, 8),
    "Other": (7, 15),
}

def normalize(v):
    if v is None:
        return ""
    return str(v).strip()

def is_blank(v):
    return normalize(v) in ("", "Select", "Not applicable", "None")

def get_current_answers():
    answers = dict(existing)
    # Pull current widget state even when user has moved between guided LAF pages without saving.
    for q in questions:
        widget_key = f"laf_{q['code']}"
        if widget_key in st.session_state:
            val = st.session_state.get(widget_key)
            answers[q["code"]] = "" if val is None else str(val)
    if not answers.get("email_id") and login_email:
        answers["email_id"] = login_email
    return answers

def meaningful_count(vals):
    return sum(1 for v in vals.values() if not is_blank(v))

def page_answer_count(page_questions, vals):
    return sum(1 for q in page_questions if not is_blank(vals.get(q["code"], "")))

def init_laf_state(page_names):
    visited_key = f"laf_visited_pages_{user_id}"
    current_key = f"laf_current_page_{user_id}"
    if visited_key not in st.session_state:
        st.session_state[visited_key] = set()
    if current_key not in st.session_state:
        st.session_state[current_key] = 0
    st.session_state[current_key] = max(0, min(st.session_state[current_key], len(page_names) - 1))
    return visited_key, current_key

def go_to_laf_page(new_idx):
    """Navigate LAF page and trigger best-effort scroll reset."""
    new_idx = max(0, min(new_idx, len(page_names) - 1))
    save_form_response("laf_responses", user_id, get_current_answers())
    sync_profile_from_laf(user_id)
    st.session_state[current_key] = new_idx
    st.session_state[visited_key].add(page_names[new_idx])
    st.session_state[f"laf_scroll_top_{user_id}"] = True
    st.session_state[f"laf_nav_nonce_{user_id}"] = st.session_state.get(f"laf_nav_nonce_{user_id}", 0) + 1
    try:
        st.query_params["laf_page"] = str(new_idx + 1)
        st.query_params["laf_nav"] = str(st.session_state[f"laf_nav_nonce_{user_id}"])
    except Exception:
        pass
    st.rerun()

def identity_mode(answers):
    gender = normalize(answers.get("gender", "")).lower()
    pronoun = normalize(answers.get("pronoun", "")).lower()

    # Gender selected in Basic Profile is the controlling value.
    if gender in ["male", "m"]:
        return "male"
    if gender in ["female", "f"]:
        return "female"

    # Pronoun is secondary only when Gender is non-specific or not selected.
    if pronoun == "he/him":
        return "male"
    if pronoun == "she/her":
        return "female"
    return "open"

def dependency_disabled(q, answers):
    code = q["code"]
    mode = identity_mode(answers)

    if mode == "male" and code in FEMALE_RELATED_CODES:
        return True, "Not applicable because Gender is selected as Male."
    if mode == "female" and code in MALE_RELATED_CODES:
        return True, "Not applicable because Gender is selected as Female."

    if code in DEPENDENCIES:
        parent, valid_values = DEPENDENCIES[code]
        parent_value = normalize(answers.get(parent, existing.get(parent, "")))
        if parent_value not in valid_values:
            return True, f"Enabled only when '{parent.replace('_', ' ').title()}' is answered as: {', '.join(valid_values)}."
    return False, ""

LONG_TEXT_CODES = {
    "purpose_guidance",
    "main_health_concerns",
    "major_trauma_5_years",
    "stress_other",
    "stress_manifest",
    "coping_mechanisms",
    "exercise_details",
    "energy_lulls_highs",
    "prescription_medication_list",
    "otc_medication_list",
    "supplements_list",
    "allergies_sensitivities_list",
    "anaphylaxis",
    "diagnosed_illness_details",
    "hospitalized_reason",
    "fungal_infections_details",
    "libido_decline_details",
    "kidney_gall_stones_details",
    "menses_changes_details",
    "pms_symptoms",
    "menopausal_symptoms_details",
    "prostate_problems_details",
    "diet_restrictions_explain",
    "typical_breakfast",
    "typical_lunch",
    "typical_dinner",
    "typical_snacks",
    "favorite_foods",
    "food_cravings",
    "avoid_foods_why",
    "symptoms_if_meals_missed_explain",
    "symptoms_after_meals_explain",
}

def use_large_text_box(q):
    code = q.get("code", "")
    label = q.get("label", "").lower()
    if code in LONG_TEXT_CODES:
        return True
    large_keywords = [
        "explain", "describe", "please list", "list all", "provide examples",
        "comments", "details", "elaborate", "how does", "what are your main",
        "what is your purpose", "coping", "trauma"
    ]
    return any(word in label for word in large_keywords)

def render_question(q, answers):
    code = q["code"]
    disabled, reason = dependency_disabled(q, answers)
    default = answers.get(code, existing.get(code, ""))
    if code == "email_id" and is_blank(default) and login_email:
        default = login_email
    required_mark = " *" if q.get("required") or code in REQUIRED_CODES else ""
    label = q["label"] + required_mark

    if disabled:
        st.caption(f"Greyed out: {reason}")
        if q.get("type") in ["select", "scale"]:
            answers[code] = st.selectbox(label, ["Not applicable"], index=0, key=f"laf_{code}", disabled=True)
        else:
            answers[code] = st.text_input(label, value="Not applicable", key=f"laf_{code}", disabled=True)
        return

    qtype = q.get("type", "text")

    if qtype == "number":
        min_v = int(q.get("min", 0))
        max_v = int(q.get("max", 999))
        step = int(q.get("step", 1))
        initial = None
        if not is_blank(default):
            try:
                initial = int(float(default))
                initial = max(min_v, min(initial, max_v))
            except Exception:
                initial = None
        try:
            val = st.number_input(label, min_value=min_v, max_value=max_v, step=step, value=initial, key=f"laf_{code}")
        except TypeError:
            val = st.number_input(label, min_value=min_v, max_value=max_v, step=step, value=initial if initial is not None else min_v, key=f"laf_{code}")
        answers[code] = "" if val is None else str(val)

    elif qtype == "phone":
        answers[code] = st.text_input(label, value="" if is_blank(default) else str(default), placeholder="Example: 9876543210 or +91 9876543210", key=f"laf_{code}")

    elif qtype == "email":
        answers[code] = st.text_input(label, value="" if is_blank(default) else str(default), placeholder="name@example.com", key=f"laf_{code}")

    elif qtype == "scale":
        min_v = int(q.get("min", 1))
        max_v = int(q.get("max", 10))
        opts = ["Select"] + [str(i) for i in range(min_v, max_v + 1)]
        idx = opts.index(str(default)) if str(default) in opts else 0
        answers[code] = st.selectbox(label, opts, index=idx, key=f"laf_{code}")

    elif qtype == "select":
        opts = []
        for opt in (["Select"] + q.get("options", [])):
            if opt not in opts:
                opts.append(opt)
        idx = opts.index(default) if default in opts else 0
        answers[code] = st.selectbox(label, opts, index=idx, key=f"laf_{code}")

    else:
        if use_large_text_box(q):
            answers[code] = st.text_area(label, value="" if is_blank(default) else str(default), height=90, key=f"laf_{code}")
        else:
            answers[code] = st.text_input(label, value="" if is_blank(default) else str(default), key=f"laf_{code}")

def validate_mobile_number_by_country(mobile, country):
    mobile = normalize(mobile)
    country = normalize(country)

    if is_blank(mobile):
        return False, "Mobile Number is mandatory."

    if is_blank(country):
        return False, "Country is mandatory."

    digits = re.sub(r"\D", "", mobile)
    if not digits:
        return False, "Mobile Number should contain digits."

    min_digits, max_digits = MOBILE_DIGIT_RULES.get(country, MOBILE_DIGIT_RULES["Other"])
    local_digits = digits

    # Allow country code entry. Example: +91 9876543210 for India.
    prefix = COUNTRY_PREFIXES.get(country)
    if prefix and len(digits) > max_digits and digits.startswith(prefix):
        local_digits = digits[len(prefix):]

    # Basic invalid repeated-number guard.
    if len(set(local_digits)) == 1:
        return False, "Mobile Number cannot be all same digits."

    if not (min_digits <= len(local_digits) <= max_digits):
        if min_digits == max_digits:
            return False, f"Mobile Number for {country} should have {min_digits} digits. Country code is allowed, but the local number must be {min_digits} digits."
        return False, f"Mobile Number for {country} should have {min_digits}-{max_digits} digits."

    return True, ""

def validate_laf(answers):
    errors = []

    for code, label in REQUIRED_CODES.items():
        if is_blank(answers.get(code, "")):
            errors.append(f"{label} is mandatory.")

    if normalize(answers.get("gender", "")) not in ["Female", "Male", "Non-binary", "Prefer not to say", "Other"]:
        errors.append("Gender should be selected from the dropdown.")

    full_name = normalize(answers.get("full_name", ""))
    if full_name and "@" in full_name:
        errors.append("Name should not contain an email address.")

    email = normalize(answers.get("email_id", ""))
    if email and not re.match(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$", email):
        errors.append("Email ID should be a valid email address.")

    mobile = normalize(answers.get("mobile_number", answers.get("phone", "")))
    country = normalize(answers.get("country", ""))
    if mobile and mobile != "Not applicable":
        mobile_ok, mobile_error = validate_mobile_number_by_country(mobile, country)
        if not mobile_ok:
            errors.append(mobile_error)

    for code, label, min_v, max_v in [
        ("age", "Age", 1, 120),
        ("height_cm", "Height", 50, 250),
        ("weight_kg", "Weight", 20, 250),
    ]:
        val = normalize(answers.get(code, ""))
        if val and val != "Not applicable":
            try:
                num = float(val)
                if num < min_v or num > max_v:
                    errors.append(f"{label} should be between {min_v} and {max_v}.")
            except Exception:
                errors.append(f"{label} should be numeric.")

    for child, (parent, valid_values) in DEPENDENCIES.items():
        # Skip disabled due to gender/pronoun
        q = next((x for x in questions if x.get("code") == child), None)
        if q:
            disabled, _ = dependency_disabled(q, answers)
            if disabled:
                continue
        parent_value = normalize(answers.get(parent, ""))
        child_value = normalize(answers.get(child, ""))
        if parent_value in valid_values and is_blank(child_value):
            errors.append(f"Please complete the dependent field: {child.replace('_', ' ').title()}.")

    return errors

topbar(
    "Lifestyle Assessment Form",
    "The full LAF is structured into guided pages with mandatory fields, smart validations and dependent questions.",
    "Assessment step 1"
)
render_system_message()

st.markdown(
    """
    <div class='info-banner'>
      <b>Smart LAF flow.</b><br>
      Name, Age, Gender, Contact Number and Email ID are mandatory. Dependent questions are greyed out when not applicable.
    </div>
    """,
    unsafe_allow_html=True,
)

pages = OrderedDict()
for q in questions:
    page = q.get("page", "Page 1 - Profile, Purpose & Lifestyle")
    section = q.get("section", "General")
    pages.setdefault(page, OrderedDict())
    pages[page].setdefault(section, [])
    pages[page][section].append(q)

page_names = list(pages.keys())
visited_key, current_key = init_laf_state(page_names)

try:
    laf_page_param = st.query_params.get("laf_page", None)
    if laf_page_param:
        desired_idx = int(laf_page_param) - 1
        if 0 <= desired_idx < len(page_names):
            st.session_state[current_key] = desired_idx
except Exception:
    pass

current_idx = st.session_state[current_key]
current_page = page_names[current_idx]
st.session_state[visited_key].add(current_page)

answers = get_current_answers()

visited_count = len(st.session_state[visited_key])
progress = visited_count / len(page_names) if page_names else 0
st.progress(progress)
st.caption(f"LAF page visit progress: {visited_count}/{len(page_names)} pages visited")

nav_cols = st.columns(len(page_names))
for idx, page_name in enumerate(page_names):
    label = f"{'✓' if page_name in st.session_state[visited_key] else '○'} {idx + 1}"
    with nav_cols[idx]:
        if st.button(label, key=f"laf_nav_{idx}", use_container_width=True):
            go_to_laf_page(idx)

st.markdown("### Page navigation")
top_prev, top_page, top_next = st.columns([1, 2, 1])
with top_prev:
    if st.button("⬅ Previous Page", key="laf_top_previous", use_container_width=True, disabled=current_idx == 0):
        go_to_laf_page(current_idx - 1)
with top_page:
    st.markdown(
        f"<div class='info-banner' style='text-align:center; padding:.7rem;'>Currently viewing <b>Page {current_idx + 1} of {len(page_names)}</b><br>{current_page}</div>",
        unsafe_allow_html=True,
    )
with top_next:
    if current_idx < len(page_names) - 1:
        if st.button("Next Page ➡", key="laf_top_next", use_container_width=True):
            go_to_laf_page(current_idx + 1)
    else:
        st.markdown("<div class='autosave-note' style='text-align:center;'>Final LAF page</div>", unsafe_allow_html=True)

st.divider()
st.subheader(current_page)

for section_name, section_questions in pages[current_page].items():
    card_start()
    st.markdown(f"### {section_name}")
    if section_name == "Basic Profile":
        st.caption("Basic Profile is synced with My Profile automatically.")
    if section_name in ["Female or identifying pronouns", "Male or identifying pronouns"]:
        st.caption("Questions in this section are controlled by the Gender selected in Basic Profile. Male-specific or female-specific questions are greyed out when not applicable.")

    if section_name == "Family history":
        st.markdown("<div class='family-history-head'>Family history is captured in a table-style format. Mention relation codes/details such as F, M, S, G, O and relevant type/details.</div>", unsafe_allow_html=True)
        h1, h2 = st.columns([1.1, 2.2])
        with h1:
            st.markdown("**Condition / Disease**")
        with h2:
            st.markdown("**Family relation and details**")
        for q in section_questions:
            default = answers.get(q["code"], existing.get(q["code"], ""))
            condition = q.get("label", q["code"]).replace("Family history:", "").strip()
            c1, c2 = st.columns([1.1, 2.2])
            with c1:
                st.markdown(f"<div class='family-history-row'><b>{condition}</b></div>", unsafe_allow_html=True)
            with c2:
                answers[q["code"]] = st.text_input(
                    "Family relation and details",
                    value="" if is_blank(default) else str(default),
                    key=f"laf_{q['code']}",
                    label_visibility="collapsed",
                    placeholder="Example: F - type/details, M - type/details"
                )
        card_end()
        continue

    for q in section_questions:
        render_question(q, answers)
    card_end()

merged_answers = get_current_answers()
merged_answers.update(answers)
answered = meaningful_count(merged_answers)
missing_pages = [p for p in page_names if p not in st.session_state[visited_key]]
validation_errors = validate_laf(merged_answers)

stat_grid([
    {"label": "Answered", "value": answered, "note": "Fields completed"},
    {"label": "Total Fields", "value": len(questions), "note": "Full LAF fields"},
    {"label": "Visited Pages", "value": f"{visited_count}/{len(page_names)}", "note": "Required before continue"},
    {"label": "Open Validations", "value": len(validation_errors), "note": "Issues to fix"},
])

if validation_errors:
    with st.expander("Validation items to review", expanded=False):
        for err in validation_errors:
            st.write(f"- {err}")


# Auto-save current LAF state on every interaction/rerun.
save_form_response("laf_responses", user_id, merged_answers)
sync_profile_from_laf(user_id)
st.markdown("<div class='autosave-note'>Auto-saved. You can also use the Previous/Next navigation at the top of the page.</div>", unsafe_allow_html=True)

c1, c2, c3 = st.columns(3)
with c1:
    if st.button("Back to Home", use_container_width=True):
        st.switch_page("pages/02_Member_Home.py")
with c2:
    if st.button("Previous Page", use_container_width=True, disabled=current_idx == 0):
        go_to_laf_page(current_idx - 1)
with c3:
    if current_idx < len(page_names) - 1:
        if st.button("Next Page", use_container_width=True):
            go_to_laf_page(current_idx + 1)
    else:
        if st.button("Submit LAF and Continue", type="primary", use_container_width=True):
            if missing_pages:
                set_system_message("Please visit all LAF pages before continuing: " + ", ".join(missing_pages), "error"); st.rerun()
            elif validation_errors:
                set_system_message("Please fix validation items before continuing.", "error"); st.rerun()
            elif meaningful_count(merged_answers) == 0:
                set_system_message("Please provide at least some LAF information before continuing.", "error"); st.rerun()
            else:
                save_form_response("laf_responses", user_id, merged_answers)
                sync_profile_from_laf(user_id)
                update_workflow(user_id, laf_completed=True)
                set_system_message("LAF submitted successfully. Please continue with NSP Page 1.", "success", celebrate=True)
                st.switch_page("pages/04_NSP_Page1.py")
