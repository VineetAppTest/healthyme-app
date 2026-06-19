import html
import pathlib
import re
from datetime import date, timedelta

import pandas as pd
import streamlit as st

from components.guards import require_admin
from components.db import (
    get_latest_recommendation_share,
    list_active_member_supplements,
    list_members,
    save_recommendation_share,
)
from components.ui_common import (
    inject_global_styles,
    apply_luxe_theme,
    utility_logout_bar,
    topbar,
    render_page_nav,
    render_back_to_top,
)

st.set_page_config(page_title="Recommendations Share", page_icon="💚", layout="wide", initial_sidebar_state="collapsed")
inject_global_styles()
apply_luxe_theme()
require_admin()
utility_logout_bar()
topbar(
    "Recommendations Share",
    "Create and publish one 7-day member recommendation window.",
    "Admin recommendations",
)

BASE = pathlib.Path(__file__).resolve().parents[1]
RECIPES_PATH = BASE / "data" / "recipes.csv"
EXERCISES_PATH = BASE / "data" / "exercises.csv"
MEAL_SLOTS = ["Breakfast", "Lunch", "Snacks", "Dinner", "Bedtime"]
TIMING_OPTIONS = ["Morning", "Midday", "Evening", "Before Bed", "With Food", "Empty Stomach", "After Meals"]
FREQUENCY_OPTIONS = ["Once", "Twice", "Thrice", "Four times", "Five times", "Six times", "Seven times", "Eight times", "Nine times", "Ten times"]
FREQUENCY_WORD_COUNTS = {
    "once": 1,
    "one": 1,
    "twice": 2,
    "two": 2,
    "thrice": 3,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
}


def _esc(value):
    return html.escape(str(value or ""))


def _actor_id():
    return st.session_state.get("user_id") or st.session_state.get("oidc_email") or "admin"


def _load_csv(path, expected_cols):
    if not path.exists():
        return pd.DataFrame(columns=expected_cols)
    df = pd.read_csv(path)
    for col in expected_cols:
        if col not in df.columns:
            df[col] = ""
    return df


def _active(df):
    if df.empty:
        return df
    if "status" not in df.columns:
        df["status"] = "active"
    return df[df["status"].fillna("active").astype(str).str.lower().eq("active")].copy()


def _date_from_iso(value):
    raw = str(value or "").strip()
    try:
        return date.fromisoformat(raw[:10])
    except Exception:
        return date.today()


def _date_or_default(value, default_date=None):
    raw = str(value or "").strip()
    if not raw:
        return default_date or date.today()
    try:
        return date.fromisoformat(raw[:10])
    except Exception:
        return default_date or date.today()


def _day_label(day_date, idx):
    return f"Day {idx} · {day_date.strftime('%a, %d %b %Y')}"


def _fold_label(day_date, idx):
    return _day_label(day_date, idx)


def _recipe_options(df):
    options = {"— No recipe —": ""}
    for idx, row in df.iterrows():
        title = str(row.get("title") or "Untitled Recipe").strip()
        meal = str(row.get("meal_type") or "").strip()
        options[f"{idx} — {title}{' · ' + meal if meal else ''}"] = str(idx)
    return options


def _exercise_options(df):
    options = {"— No exercise —": ""}
    for idx, row in df.iterrows():
        title = str(row.get("title") or "Untitled Exercise").strip()
        meta = str(row.get("duration_or_reps") or row.get("category") or "").strip()
        options[f"{idx} — {title}{' · ' + meta if meta else ''}"] = str(idx)
    return options


def _clean_date_label(value):
    raw = str(value or "").strip()
    return raw[:10] if raw else "NA"


def _supp_options(supps):
    options = {}
    for row in supps:
        title = str(row.get("supplement_name") or "Supplement").strip()
        dosage = str(row.get("dosage") or "Dosage NA").strip()
        frequency = str(row.get("frequency") or "Frequency NA").strip()
        timing = str(row.get("timing") or "Timing NA").strip()
        start_date = _clean_date_label(row.get("start_date"))
        end_date = _clean_date_label(row.get("end_date"))
        label = f"{title} · {dosage} · {frequency} · {timing} · Start {start_date} · End {end_date}"
        options[label] = str(row.get("id"))
    return options


def _supp_by_id(supps):
    return {str(row.get("id")): row for row in supps}


def _select_label_for_id(options, item_id):
    for label, value in options.items():
        if str(value) == str(item_id):
            return label
    return list(options.keys())[0] if options else ""


def _multi_labels_for_ids(options, ids):
    ids = {str(x) for x in (ids or [])}
    return [label for label, value in options.items() if str(value) in ids]


def _get_meal_existing(share, day_iso, slot):
    for item in (share or {}).get("meal_plan", []) or []:
        if str(item.get("date")) == day_iso and str(item.get("meal_slot")) == slot:
            return item
    return {}


def _get_exercise_existing(share, day_iso):
    for item in (share or {}).get("exercise_plan", []) or []:
        if str(item.get("date")) == day_iso:
            return item
    return {}


def _get_supp_existing(share, day_iso):
    for item in (share or {}).get("supplement_plan", []) or []:
        if str(item.get("date")) == day_iso:
            return item
    return {}


def _eligible_supp_ids_for_date(supps, day_iso):
    eligible = []
    for row in supps:
        start_raw = str(row.get("start_date") or "").strip()
        end_raw = str(row.get("end_date") or "").strip()
        if start_raw and start_raw[:10] > day_iso:
            continue
        if end_raw and end_raw[:10] < day_iso:
            continue
        eligible.append(str(row.get("id")))
    return eligible


def _custom_timing_parts(extra):
    raw = str(extra or "").strip()
    if not raw:
        return []
    return [part.strip() for part in re.split(r"[,;|\n]+", raw) if part.strip()]


def _timing_from_choices(choices, extra):
    parts = [str(x).strip() for x in (choices or []) if str(x).strip()]
    parts.extend(_custom_timing_parts(extra))
    return ", ".join(parts)


def _timing_count(choices, extra):
    return len([x for x in (choices or []) if str(x).strip()]) + len(_custom_timing_parts(extra))


def _frequency_expected_count(frequency):
    raw = str(frequency or "").strip().lower()
    if not raw:
        return None
    number_match = re.search(r"\b(\d{1,2})\s*(?:x|time|times)\b", raw)
    if number_match:
        try:
            return int(number_match.group(1))
        except Exception:
            return None
    x_match = re.search(r"\b(\d{1,2})\s*x\b", raw)
    if x_match:
        try:
            return int(x_match.group(1))
        except Exception:
            return None
    for word, count in FREQUENCY_WORD_COUNTS.items():
        if re.search(rf"\b{re.escape(word)}\b", raw):
            return count
    return None


def _frequency_default_option(value):
    expected = _frequency_expected_count(value)
    if expected and 1 <= expected <= len(FREQUENCY_OPTIONS):
        return FREQUENCY_OPTIONS[expected - 1]
    raw = str(value or "").strip().lower()
    for option in FREQUENCY_OPTIONS:
        if option.lower() == raw:
            return option
    return FREQUENCY_OPTIONS[0]


def _frequency_timing_error(frequency, choices, extra):
    expected = _frequency_expected_count(frequency)
    if expected is None:
        return ""
    actual = _timing_count(choices, extra)
    if actual != expected:
        return f"Frequency indicates {expected} timing(s), but {actual} timing(s) were selected/entered."
    return ""


def _split_timing_for_edit(text):
    parts = [p.strip() for p in str(text or "").replace("|", ",").split(",") if p.strip()]
    option_lookup = {opt.lower(): opt for opt in TIMING_OPTIONS}
    selected = []
    extra_parts = []
    for part in parts:
        matched = option_lookup.get(part.lower())
        if matched:
            if matched not in selected:
                selected.append(matched)
        else:
            extra_parts.append(part)
    return selected, ", ".join(extra_parts)


def _existing_supp_detail(existing_item, sid, source_row):
    base = {
        "supplement_id": str(sid or ""),
        "supplement_name": source_row.get("supplement_name") or "Supplement",
        "dosage": source_row.get("dosage") or "",
        "frequency": source_row.get("frequency") or FREQUENCY_OPTIONS[0],
        "timing": source_row.get("timing") or "",
        "start_date": source_row.get("start_date") or "",
        "end_date": source_row.get("end_date") or "",
        "instructions": source_row.get("instructions") or "",
        "admin_notes": source_row.get("admin_notes") or "",
    }
    for detail in existing_item.get("supplement_details", []) or []:
        if not isinstance(detail, dict):
            continue
        detail_sid = str(detail.get("supplement_id") or detail.get("source_supplement_id") or detail.get("id") or "")
        if detail_sid == str(sid):
            merged = dict(base)
            for key in ["supplement_name", "dosage", "frequency", "timing", "start_date", "end_date", "instructions", "admin_notes"]:
                if detail.get(key) not in [None]:
                    merged[key] = detail.get(key)
            return merged
    return base


st.markdown("""
<style>
.hm-rec-page{max-width:1180px;margin:0 auto;}
.hero-shell{padding:.72rem .95rem!important;margin-bottom:.45rem!important;border-radius:20px!important;}
.hero-kicker{padding:.28rem .62rem!important;margin-bottom:.28rem!important;font-size:.70rem!important;}
.hero-title{font-size:1.55rem!important;line-height:1.08!important;}
.hero-subtitle{margin-top:.16rem!important;font-size:.84rem!important;}
.meta-pill{display:none!important;}
.hm-rec-note{border:1px solid #E3C98E;background:#FFFDF8;border-radius:14px;padding:.55rem .8rem;color:#475569;font-size:.78rem;font-weight:720;line-height:1.35;margin:.25rem 0 .7rem;}
.hm-rec-alert{border:2px solid #F59E0B;background:#FFFBEB;border-radius:18px;padding:1rem 1.05rem;color:#78350F;font-size:.92rem;font-weight:850;line-height:1.45;margin:.75rem 0 1rem;box-shadow:0 10px 24px rgba(245,158,11,.12);}
.hm-member-control-title{color:#064E3B;font-size:1.02rem;font-weight:950;margin-bottom:.16rem;}
.hm-member-control-sub{color:#8A5F10;font-size:.78rem;font-weight:830;margin-bottom:.35rem;}
.hm-rec-title{color:#064E3B;font-size:1.03rem;font-weight:950;margin:.65rem 0 .35rem;}
.hm-rec-sub{color:#64748B;font-size:.80rem;font-weight:720;line-height:1.4;margin-bottom:.75rem;}
.hm-rec-empty{border:1px dashed #D9C28F;background:#FFF9EC;border-radius:14px;padding:.65rem .75rem;color:#64748B;font-size:.78rem;font-weight:760;line-height:1.4;margin:.35rem 0 .65rem;}
.hm-rec-supp-editor-title{color:#064E3B;font-size:.90rem;font-weight:950;margin:.15rem 0 .45rem;}
.hm-rec-supp-source{color:#64748B;font-size:.72rem;font-weight:760;margin:-.15rem 0 .55rem;}
.hm-rec-na{font-size:.78rem;font-weight:820;color:#64748B;background:#FFFDF8;border:1px dashed #D9C28F;border-radius:12px;padding:.52rem .58rem;margin-top:1.72rem;min-height:38px;display:flex;align-items:center;}
/* Remove visual dividers and convert expanders into clean +/- controls. */
div[data-testid="stTabs"] [role="tablist"]{border-bottom:0!important;box-shadow:none!important;margin-bottom:.4rem!important;}
div[data-testid="stTabs"] [role="tab"]{border:1px solid #E3C98E!important;border-radius:999px!important;margin-right:.35rem!important;background:#FFFDF8!important;padding:.35rem .75rem!important;}
div[data-testid="stTabs"] [aria-selected="true"]{background:#064E3B!important;color:#fff!important;border-color:#064E3B!important;}
div[data-testid="stTabs"] [aria-selected="true"] p{color:#fff!important;}
div[data-testid="stExpander"] details{border:0!important;background:transparent!important;box-shadow:none!important;margin:.55rem 0!important;}
div[data-testid="stExpander"] details summary{list-style:none!important;border:1.5px solid #D8A84E!important;background:linear-gradient(135deg,#FFFDF8 0%,#FFF4DE 100%)!important;border-radius:999px!important;padding:.48rem .85rem!important;box-shadow:0 8px 20px rgba(138,95,16,.08)!important;}
div[data-testid="stExpander"] details summary::-webkit-details-marker{display:none!important;}
div[data-testid="stExpander"] details summary::marker{font-size:0!important;content:""!important;}
div[data-testid="stExpander"] details summary svg{display:none!important;}
div[data-testid="stExpander"] details summary::before{content:"+";display:inline-flex;align-items:center;justify-content:center;width:1.35rem;height:1.35rem;margin-right:.45rem;border-radius:999px;background:#064E3B;color:#FFFDF8;font-weight:950;font-size:.86rem;line-height:1;}
div[data-testid="stExpander"] details[open] summary::before{content:"−";}
div[data-testid="stExpander"] details summary p{display:inline!important;font-weight:950!important;color:#064E3B!important;font-size:.84rem!important;}
div[data-testid="stExpander"] details summary:hover{border-color:#064E3B!important;box-shadow:0 10px 24px rgba(6,78,59,.10)!important;}
hr{display:none!important;}
@media(max-width:850px){.hero-title{font-size:1.28rem!important}}
</style>
""", unsafe_allow_html=True)

members = list_members()
if not members:
    st.warning("No active members found. Create or activate a member before creating recommendations.")
    render_page_nav("Recommendations Share", back_page="pages/10_Admin_Dashboard.py", dashboard_page="pages/10_Admin_Dashboard.py", show_evaluation=False, show_dashboard=True, location="bottom")
    render_back_to_top()
    st.stop()

recipe_df = _active(_load_csv(RECIPES_PATH, ["title", "meal_type", "status"]))
exercise_df = _active(_load_csv(EXERCISES_PATH, ["title", "category", "duration_or_reps", "status"]))
recipe_opts = _recipe_options(recipe_df)
exercise_opts = _exercise_options(exercise_df)

st.markdown("<div class='hm-rec-note'><b>Source of truth:</b> this 7-day share feeds Today’s Journey, Nutritionist Report, Meal Plan, Exercise Plan and Supplements.</div>", unsafe_allow_html=True)
validation_slot = st.empty()

member_options = {f"{m.get('name') or 'Member'} — {m.get('email') or m.get('id')}": m for m in members}
with st.container(border=True):
    st.markdown("<div class='hm-member-control-title'>Member Control</div><div class='hm-member-control-sub'>Select the member first. Every field below is controlled by this selection.</div>", unsafe_allow_html=True)
    selected_label = st.selectbox("🔎 Select Member — controls this full Recommendations Share", list(member_options.keys()), key="hm_v1024_rec_member")
member = member_options[selected_label]
member_id = member["id"]
existing = get_latest_recommendation_share(member_id, include_draft=True) or {}
active_supps = list_active_member_supplements(member_id)
supp_opts = _supp_options(active_supps)
supp_lookup = _supp_by_id(active_supps)

start_default = _date_from_iso(existing.get("start_date"))
existing_status = existing.get("status") or "New"

st.markdown("<div class='hm-rec-title'>Recommendation Window</div>", unsafe_allow_html=True)
c1, c2, c3 = st.columns([.34, .33, .33], gap="small")
with c1:
    start_date = st.date_input("Start Date", value=start_default, key="hm_v1024_rec_start")
end_date = start_date + timedelta(days=6)
with c2:
    st.text_input("End Date", value=end_date.isoformat(), disabled=True)
with c3:
    st.text_input("Status", value=existing_status, disabled=True)
nutritionist_report = st.text_area(
    "Nutritionist Report / Member Note",
    value=existing.get("nutritionist_report", ""),
    placeholder="Write the member-facing recommendation note here. This appears on the member side as the Nutritionist Report.",
    height=140,
    key="hm_v1024_nutritionist_report",
)

days = [start_date + timedelta(days=i) for i in range(7)]
recipe_tab, exercise_tab, supplement_tab = st.tabs(["Recipe", "Exercise", "Supplement"])

with recipe_tab:
    st.markdown("<div class='hm-rec-title'>7-Day Meal Plan</div><div class='hm-rec-sub'>Select recipes from the repository for each day and meal slot. These selections also keep the member Recipe page connected to the same plan.</div>", unsafe_allow_html=True)
    meal_plan = []
    for idx, day in enumerate(days, start=1):
        day_iso = day.isoformat()
        with st.expander(_fold_label(day, idx), expanded=(idx == 1)):
            for slot in MEAL_SLOTS:
                existing_item = _get_meal_existing(existing, day_iso, slot)
                default_label = _select_label_for_id(recipe_opts, existing_item.get("recipe_id", ""))
                c_recipe, c_note = st.columns([.58, .42], gap="small")
                with c_recipe:
                    chosen_label = st.selectbox(
                        f"{slot} Recipe",
                        list(recipe_opts.keys()),
                        index=list(recipe_opts.keys()).index(default_label),
                        key=f"hm_v1024_meal_{idx}_{slot}",
                    )
                with c_note:
                    note = st.text_input(f"{slot} Note", value=existing_item.get("notes", ""), key=f"hm_v1024_meal_note_{idx}_{slot}")
                meal_plan.append({"day_number": idx, "date": day_iso, "meal_slot": slot, "recipe_id": recipe_opts.get(chosen_label, ""), "notes": note})

with exercise_tab:
    st.markdown("<div class='hm-rec-title'>7-Day Exercise Plan</div><div class='hm-rec-sub'>Select one primary exercise recommendation per day. Use the notes field for additional instruction or rest-day guidance.</div>", unsafe_allow_html=True)
    exercise_plan = []
    for idx, day in enumerate(days, start=1):
        day_iso = day.isoformat()
        existing_item = _get_exercise_existing(existing, day_iso)
        default_label = _select_label_for_id(exercise_opts, existing_item.get("exercise_id", ""))
        with st.expander(_fold_label(day, idx), expanded=(idx == 1)):
            ex_label = st.selectbox("Exercise", list(exercise_opts.keys()), index=list(exercise_opts.keys()).index(default_label), key=f"hm_v1024_ex_{idx}")
            ex_col1, ex_col2 = st.columns(2, gap="small")
            with ex_col1:
                ex_timing = st.text_input("Timing", value=existing_item.get("timing", ""), key=f"hm_v1024_ex_time_{idx}", placeholder="e.g. Morning / Evening")
            with ex_col2:
                ex_notes = st.text_input("Instruction", value=existing_item.get("notes", ""), key=f"hm_v1024_ex_note_{idx}")
            exercise_plan.append({"day_number": idx, "date": day_iso, "exercise_id": exercise_opts.get(ex_label, ""), "timing": ex_timing, "notes": ex_notes})

with supplement_tab:
    st.markdown("<div class='hm-rec-title'>7-Day Supplement Schedule</div><div class='hm-rec-sub'>Supplements are pulled from the member’s active regimen, then can be edited inside this 7-day share without changing the master regimen.</div>", unsafe_allow_html=True)
    supplement_plan = []
    supplement_validation_errors = []
    if not supp_opts:
        st.info("No active supplements are assigned to this member yet. Add supplements first if needed.")
    for idx, day in enumerate(days, start=1):
        day_iso = day.isoformat()
        existing_item = _get_supp_existing(existing, day_iso)
        if existing:
            default_ids = existing_item.get("supplement_ids", [])
        else:
            default_ids = _eligible_supp_ids_for_date(active_supps, day_iso)
        default_labels = _multi_labels_for_ids(supp_opts, default_ids)
        with st.expander(_fold_label(day, idx), expanded=(idx == 1)):
            labels = st.multiselect("Supplements", list(supp_opts.keys()), default=default_labels, key=f"hm_v1024_supp_{idx}") if supp_opts else []
            selected_ids = [supp_opts[x] for x in labels]
            editable_details = []
            for order, sid in enumerate(selected_ids, start=1):
                source_row = supp_lookup.get(str(sid), {})
                detail = _existing_supp_detail(existing_item, sid, source_row)
                st.markdown(f"<div class='hm-rec-supp-editor-title'>{order}. {_esc(detail.get('supplement_name') or 'Supplement')}</div><div class='hm-rec-supp-source'>Pulled from active regimen. Edits below apply to this Recommendations Share only.</div>", unsafe_allow_html=True)
                name = st.text_input("Supplement Name", value=detail.get("supplement_name", ""), key=f"hm_v1024_supp_name_{idx}_{sid}")
                d_col, f_col = st.columns(2, gap="small")
                with d_col:
                    dosage = st.text_input("Dosage", value=detail.get("dosage", ""), key=f"hm_v1024_supp_dose_{idx}_{sid}")
                with f_col:
                    frequency_default = _frequency_default_option(detail.get("frequency", ""))
                    frequency = st.selectbox("Frequency", FREQUENCY_OPTIONS, index=FREQUENCY_OPTIONS.index(frequency_default), key=f"hm_v1024_supp_freq_{idx}_{sid}")
                timing_default, custom_default = _split_timing_for_edit(detail.get("timing", ""))
                t_col, a_col = st.columns(2, gap="small")
                with t_col:
                    timing_choices = st.multiselect("Timing", TIMING_OPTIONS, default=timing_default, key=f"hm_v1024_supp_timing_{idx}_{sid}")
                with a_col:
                    custom_timing = st.text_input("Additional Timing", value=custom_default, key=f"hm_v1024_supp_custom_timing_{idx}_{sid}")
                start_existing = _date_or_default(detail.get("start_date"), day)
                e_existing = str(detail.get("end_date") or "").strip()
                s_col, e_col = st.columns(2, gap="small")
                with s_col:
                    supp_start = st.date_input("Start Date", value=start_existing, key=f"hm_v1024_supp_start_{idx}_{sid}")
                with e_col:
                    set_end = st.checkbox("Set End Date", value=bool(e_existing), key=f"hm_v1024_supp_end_enabled_{idx}_{sid}")
                    if set_end:
                        supp_end = st.date_input("End Date", value=_date_or_default(e_existing, supp_start), key=f"hm_v1024_supp_end_{idx}_{sid}")
                    else:
                        st.markdown("<div class='hm-rec-na'>End Date: NA</div>", unsafe_allow_html=True)
                        supp_end = None
                i_col, n_col = st.columns(2, gap="small")
                with i_col:
                    instructions = st.text_area("Member Instructions", value=detail.get("instructions", ""), key=f"hm_v1024_supp_instr_{idx}_{sid}", height=90)
                with n_col:
                    admin_notes = st.text_area("Admin Notes", value=detail.get("admin_notes", ""), key=f"hm_v1024_supp_admin_{idx}_{sid}", height=90)

                timing_error = _frequency_timing_error(frequency, timing_choices, custom_timing)
                if timing_error:
                    supplement_validation_errors.append(f"Day {idx} · {name or 'Supplement'}: {timing_error}")
                if supp_end and supp_end < supp_start:
                    supplement_validation_errors.append(f"Day {idx} · {name or 'Supplement'}: End Date cannot be earlier than Start Date.")
                editable_details.append({
                    "supplement_id": str(sid),
                    "supplement_name": name,
                    "dosage": dosage,
                    "frequency": frequency,
                    "timing": _timing_from_choices(timing_choices, custom_timing),
                    "start_date": supp_start.isoformat(),
                    "end_date": supp_end.isoformat() if supp_end else "",
                    "instructions": instructions,
                    "admin_notes": admin_notes,
                })
            supp_notes = st.text_input("Supplement Note", value=existing_item.get("notes", ""), key=f"hm_v1024_supp_note_{idx}")
            supplement_plan.append({"day_number": idx, "date": day_iso, "supplement_ids": selected_ids, "supplement_details": editable_details, "notes": supp_notes})

save_col, publish_col = st.columns(2, gap="large")
with save_col:
    save_draft = st.button("Save Draft", use_container_width=True)
with publish_col:
    publish_share = st.button("Publish / Share to Member", type="primary", use_container_width=True)

if save_draft or publish_share:
    try:
        if supplement_validation_errors:
            message = "<br>".join(_esc(x) for x in supplement_validation_errors[:8])
            if len(supplement_validation_errors) > 8:
                message += f"<br>...and {len(supplement_validation_errors) - 8} more validation item(s)."
            validation_slot.markdown(f"<div class='hm-rec-alert'>⚠️ <b>Supplement validation needs attention.</b><br>{message}<br><span style='font-weight:720'>Your filled data has not been cleared. Correct the issue and save again.</span></div>", unsafe_allow_html=True)
            st.stop()
        payload = {
            "id": existing.get("id") or "",
            "start_date": start_date,
            "nutritionist_report": nutritionist_report,
            "meal_plan": meal_plan,
            "exercise_plan": exercise_plan,
            "supplement_plan": supplement_plan,
            "status": "Published" if publish_share else "Draft",
        }
        saved = save_recommendation_share(member_id, payload, actor_id=_actor_id(), publish=publish_share)
        if publish_share:
            st.success("Recommendations shared. Today’s Journey, Nutritionist Report, Meal Plan, Exercise Plan and Supplements are now available to the member from this same 7-day window.")
        else:
            st.success("Draft saved.")
        st.session_state["hm_v1024_last_saved_share_id"] = saved.get("id")
        st.rerun()
    except Exception as exc:
        message = str(exc) or "Could not save Recommendations Share. Please check the highlighted information and try again."
        validation_slot.markdown(f"<div class='hm-rec-alert'>⚠️ <b>Validation check failed.</b><br>{_esc(message)}<br><span style='font-weight:720'>Your filled data has not been cleared. Correct the issue and save again.</span></div>", unsafe_allow_html=True)
        st.error(message)

render_page_nav("Recommendations Share", back_page="pages/10_Admin_Dashboard.py", dashboard_page="pages/10_Admin_Dashboard.py", show_evaluation=False, show_dashboard=True, location="bottom")
render_back_to_top()

# v102.4B2: clean +/- expanders and editable supplement details inside Recommendations Share.
