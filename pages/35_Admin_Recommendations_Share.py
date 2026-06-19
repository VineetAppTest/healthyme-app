import html
import pathlib
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
    "Create one 7-day recommendation window that feeds Today’s Journey, member report, meal plan, exercise plan and supplements.",
    "Admin recommendations",
)

BASE = pathlib.Path(__file__).resolve().parents[1]
RECIPES_PATH = BASE / "data" / "recipes.csv"
EXERCISES_PATH = BASE / "data" / "exercises.csv"
MEAL_SLOTS = ["Breakfast", "Lunch", "Snacks", "Dinner", "Bedtime"]


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


def _day_label(day_date, idx):
    return f"Day {idx} · {day_date.strftime('%a, %d %b %Y')}"


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


def _supp_options(supps):
    options = {}
    for row in supps:
        title = str(row.get("supplement_name") or "Supplement").strip()
        timing = str(row.get("timing") or "As advised").strip()
        dosage = str(row.get("dosage") or "").strip()
        label = f"{title}{' · ' + dosage if dosage else ''} · {timing}"
        options[label] = str(row.get("id"))
    return options


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


st.markdown("""
<style>
.hm-rec-page{max-width:1180px;margin:0 auto;}
.hm-rec-note{border:1px solid #E3C98E;background:#FFFDF8;border-radius:16px;padding:.85rem 1rem;color:#475569;font-size:.86rem;font-weight:720;line-height:1.45;margin:.6rem 0 1rem;}
.hm-rec-section{border:1px solid #E3C98E;background:linear-gradient(180deg,#FFFDF8 0%,#FFF9EC 100%);border-radius:20px;padding:1rem;box-shadow:0 10px 24px rgba(15,23,42,.05);margin:.9rem 0;}
.hm-rec-title{color:#064E3B;font-size:1.03rem;font-weight:950;margin-bottom:.35rem;}
.hm-rec-sub{color:#64748B;font-size:.80rem;font-weight:720;line-height:1.4;margin-bottom:.75rem;}
.hm-rec-day{border:1px solid #E6D4A8;background:#FFFDF8;border-radius:16px;padding:.85rem;margin:.75rem 0;}
.hm-rec-day-title{color:#064E3B;font-size:.92rem;font-weight:940;margin-bottom:.48rem;}
.hm-rec-grid2{display:grid;grid-template-columns:1fr 1fr;gap:1rem;}
@media(max-width:850px){.hm-rec-grid2{grid-template-columns:1fr}}
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

st.markdown("<div class='hm-rec-page'>", unsafe_allow_html=True)
st.markdown("<div class='hm-rec-note'><b>Source of truth:</b> this 7-day Recommendations Share feeds Today’s Journey, Nutritionist Report, Meal Plan, Exercise Plan and Supplements. Today’s Journey is only a date-filtered snapshot of this share.</div>", unsafe_allow_html=True)

member_options = {f"{m.get('name') or 'Member'} — {m.get('email') or m.get('id')}": m for m in members}
selected_label = st.selectbox("Select Member", list(member_options.keys()), key="hm_v1024_rec_member")
member = member_options[selected_label]
member_id = member["id"]
existing = get_latest_recommendation_share(member_id, include_draft=True) or {}
active_supps = list_active_member_supplements(member_id)
supp_opts = _supp_options(active_supps)

start_default = _date_from_iso(existing.get("start_date"))
existing_status = existing.get("status") or "New"

with st.form("hm_v1024_recommendations_form"):
    st.markdown("<div class='hm-rec-section'>", unsafe_allow_html=True)
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
    )
    st.markdown("</div>", unsafe_allow_html=True)

    days = [start_date + timedelta(days=i) for i in range(7)]

    st.markdown("<div class='hm-rec-section'>", unsafe_allow_html=True)
    st.markdown("<div class='hm-rec-title'>7-Day Meal Plan</div><div class='hm-rec-sub'>Select recipes from the repository for each day and meal slot. These selections also keep the member Recipe page connected to the same plan.</div>", unsafe_allow_html=True)
    meal_plan = []
    for idx, day in enumerate(days, start=1):
        day_iso = day.isoformat()
        with st.expander(_day_label(day, idx), expanded=(idx == 1)):
            for slot in MEAL_SLOTS:
                existing_item = _get_meal_existing(existing, day_iso, slot)
                default_label = _select_label_for_id(recipe_opts, existing_item.get("recipe_id", ""))
                c_recipe, c_note = st.columns([.58, .42], gap="small")
                with c_recipe:
                    chosen_label = st.selectbox(f"{slot} Recipe", list(recipe_opts.keys()), index=list(recipe_opts.keys()).index(default_label), key=f"hm_v1024_meal_{idx}_{slot}")
                with c_note:
                    note = st.text_input(f"{slot} Note", value=existing_item.get("notes", ""), key=f"hm_v1024_meal_note_{idx}_{slot}")
                meal_plan.append({"day_number": idx, "date": day_iso, "meal_slot": slot, "recipe_id": recipe_opts.get(chosen_label, ""), "notes": note})
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='hm-rec-grid2'>", unsafe_allow_html=True)
    st.markdown("<div class='hm-rec-section'>", unsafe_allow_html=True)
    st.markdown("<div class='hm-rec-title'>7-Day Exercise Plan</div><div class='hm-rec-sub'>Select one primary exercise recommendation per day. Use the notes field for additional instruction or rest-day guidance.</div>", unsafe_allow_html=True)
    exercise_plan = []
    for idx, day in enumerate(days, start=1):
        day_iso = day.isoformat()
        existing_item = _get_exercise_existing(existing, day_iso)
        default_label = _select_label_for_id(exercise_opts, existing_item.get("exercise_id", ""))
        st.markdown(f"<div class='hm-rec-day-title'>{_esc(_day_label(day, idx))}</div>", unsafe_allow_html=True)
        ex_label = st.selectbox("Exercise", list(exercise_opts.keys()), index=list(exercise_opts.keys()).index(default_label), key=f"hm_v1024_ex_{idx}")
        ex_timing = st.text_input("Timing", value=existing_item.get("timing", ""), key=f"hm_v1024_ex_time_{idx}", placeholder="e.g. Morning / Evening")
        ex_notes = st.text_input("Instruction", value=existing_item.get("notes", ""), key=f"hm_v1024_ex_note_{idx}")
        exercise_plan.append({"day_number": idx, "date": day_iso, "exercise_id": exercise_opts.get(ex_label, ""), "timing": ex_timing, "notes": ex_notes})
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='hm-rec-section'>", unsafe_allow_html=True)
    st.markdown("<div class='hm-rec-title'>7-Day Supplement Schedule</div><div class='hm-rec-sub'>Supplements come from the member’s active regimen. By default, eligible active supplements are included for each day in the window.</div>", unsafe_allow_html=True)
    supplement_plan = []
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
        st.markdown(f"<div class='hm-rec-day-title'>{_esc(_day_label(day, idx))}</div>", unsafe_allow_html=True)
        labels = st.multiselect("Supplements", list(supp_opts.keys()), default=default_labels, key=f"hm_v1024_supp_{idx}") if supp_opts else []
        supp_notes = st.text_input("Supplement Note", value=existing_item.get("notes", ""), key=f"hm_v1024_supp_note_{idx}")
        supplement_plan.append({"day_number": idx, "date": day_iso, "supplement_ids": [supp_opts[x] for x in labels], "notes": supp_notes})
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    save_col, publish_col = st.columns(2, gap="large")
    with save_col:
        save_draft = st.form_submit_button("Save Draft", use_container_width=True)
    with publish_col:
        publish_share = st.form_submit_button("Publish / Share to Member", type="primary", use_container_width=True)

    if save_draft or publish_share:
        try:
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
            st.error(str(exc))

st.markdown("</div>", unsafe_allow_html=True)
render_page_nav("Recommendations Share", back_page="pages/10_Admin_Dashboard.py", dashboard_page="pages/10_Admin_Dashboard.py", show_evaluation=False, show_dashboard=True, location="bottom")
render_back_to_top()

# v102.4: Admin Recommendations Share shell/foundation. One seven-day source feeds Today's Journey and member recommendations.
