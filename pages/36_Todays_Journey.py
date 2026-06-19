import html
import pathlib
from datetime import date, timedelta

import pandas as pd
import streamlit as st

from components.guards import require_member
from components.db import get_published_recommendation_for_date, list_active_member_supplements
from components.ui_common import (
    inject_global_styles,
    apply_luxe_theme,
    utility_logout_bar,
    topbar,
    render_page_nav,
    render_back_to_top,
)

st.set_page_config(page_title="Today's Journey", page_icon="💚", layout="wide", initial_sidebar_state="collapsed")
inject_global_styles()
apply_luxe_theme()
require_member()
utility_logout_bar()
topbar(
    "Today's Journey",
    "Your nutritionist-shared daily snapshot from the active seven-day recommendation window.",
    "Member recommendations",
)

BASE = pathlib.Path(__file__).resolve().parents[1]
RECIPES_PATH = BASE / "data" / "recipes.csv"
EXERCISES_PATH = BASE / "data" / "exercises.csv"


def _esc(value):
    return html.escape(str(value or ""))


def _load_csv(path):
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def _row_by_id(df, item_id):
    try:
        idx = int(str(item_id))
        if idx in df.index:
            return df.loc[idx].to_dict()
    except Exception:
        pass
    return {}


def _split_timing(text):
    return [p.strip() for p in str(text or "").replace("|", ",").split(",") if p.strip()]


def _supp_map(member_id):
    rows = list_active_member_supplements(member_id)
    return {str(r.get("id")): r for r in rows}


def _today_iso():
    return date.today().isoformat()


def _date_label(value):
    raw = str(value or "").strip()
    return raw[:10] if raw else "NA"


def _fold_label(label):
    return f"＋ / −  {label}"


def _day_rows(plan, day_iso):
    return [x for x in (plan or []) if str(x.get("date")) == str(day_iso)]


def _render_empty(label):
    st.markdown(f"<div class='hm-tj-empty'>{_esc(label)}</div>", unsafe_allow_html=True)


st.markdown("""
<style>
.hm-tj-page{max-width:1120px;margin:0 auto;}
.hm-tj-hero{border:1px solid #E3C98E;background:linear-gradient(135deg,#FFFDF8 0%,#FFF4DA 100%);border-radius:22px;padding:1rem 1.1rem;box-shadow:0 10px 24px rgba(15,23,42,.05);margin:.55rem 0 .85rem;}
.hm-tj-title{color:#064E3B;font-size:1.3rem;font-weight:950;margin:0 0 .2rem;}
.hm-tj-sub{color:#475569;font-size:.86rem;font-weight:720;line-height:1.45;}
.hm-tj-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:.8rem;margin:.8rem 0;}
.hm-tj-card{border:1px solid #E3C98E;background:#FFFDF8;border-radius:18px;padding:.95rem;box-shadow:0 8px 20px rgba(15,23,42,.045);min-height:180px;}
.hm-tj-card-title{color:#064E3B;font-size:.96rem;font-weight:950;margin-bottom:.55rem;}
.hm-tj-item{border-top:1px solid #F0E4CC;padding:.48rem 0;color:#1F2937;font-size:.82rem;font-weight:760;line-height:1.35;}
.hm-tj-meta{color:#64748B;font-size:.74rem;font-weight:720;margin-top:.08rem;}
.hm-tj-report{border:1px solid #E3C98E;background:linear-gradient(180deg,#FFFDF8 0%,#FFF9EC 100%);border-radius:20px;padding:1rem;box-shadow:0 10px 24px rgba(15,23,42,.05);margin:1rem 0;}
.hm-tj-report-title{color:#064E3B;font-size:1rem;font-weight:950;margin-bottom:.42rem;}
.hm-tj-report-body{color:#334155;font-size:.90rem;font-weight:690;line-height:1.55;white-space:pre-wrap;}
.hm-tj-empty{border:1px dashed #D9C28F;background:#FFF9EC;border-radius:14px;padding:.75rem;color:#64748B;font-size:.80rem;font-weight:740;line-height:1.4;}
.hm-tj-week-card{border:1px solid #E6D4A8;background:#FFFDF8;border-radius:16px;padding:.8rem;margin:.55rem 0;}
.hm-tj-week-title{color:#064E3B;font-size:.90rem;font-weight:940;margin-bottom:.25rem;}
.hm-tj-chip{display:inline-flex;background:#F8F5EE;border:1px solid #E6D4A8;border-radius:999px;padding:.12rem .42rem;font-size:.68rem;font-weight:850;color:#475569;margin:.25rem .16rem 0 0;}
@media(max-width:850px){.hm-tj-grid{grid-template-columns:1fr}}
</style>
""", unsafe_allow_html=True)

user_id = st.session_state.get("user_id", "")
share = get_published_recommendation_for_date(user_id, date.today())
recipes_df = _load_csv(RECIPES_PATH)
exercises_df = _load_csv(EXERCISES_PATH)
supplements_by_id = _supp_map(user_id)
today_iso = _today_iso()

st.markdown("<div class='hm-tj-page'>", unsafe_allow_html=True)

if not share:
    st.markdown("<div class='hm-tj-empty'>No recommendations have been shared yet. Your nutritionist will publish your plan when ready.</div>", unsafe_allow_html=True)
    render_page_nav("Today's Journey", back_page="pages/02_Member_Home.py", dashboard_page="pages/02_Member_Home.py", show_evaluation=False, show_dashboard=True, location="bottom")
    render_back_to_top()
    st.stop()

st.markdown(f"""
<div class='hm-tj-hero'>
  <div class='hm-tj-title'>Today’s Journey · {_esc(today_iso)}</div>
  <div class='hm-tj-sub'>This snapshot is pulled from your published recommendation window: {_esc(share.get('start_date'))} to {_esc(share.get('end_date'))}. It is not a separate plan.</div>
</div>
""", unsafe_allow_html=True)

meal_today = _day_rows(share.get("meal_plan"), today_iso)
exercise_today = _day_rows(share.get("exercise_plan"), today_iso)
supp_today = _day_rows(share.get("supplement_plan"), today_iso)

mcol, ecol, scol = st.columns(3, gap="small")
with mcol:
    st.markdown("<div class='hm-tj-card'><div class='hm-tj-card-title'>Today’s Meal Plan</div>", unsafe_allow_html=True)
    visible_meals = [x for x in meal_today if x.get("recipe_id")]
    if not visible_meals:
        _render_empty("No meal plan item is scheduled for today.")
    for item in visible_meals:
        row = _row_by_id(recipes_df, item.get("recipe_id"))
        st.markdown(f"<div class='hm-tj-item'><b>{_esc(item.get('meal_slot'))}</b>: {_esc(row.get('title') or 'Recipe')}<div class='hm-tj-meta'>{_esc(item.get('notes') or row.get('meal_type') or '')}</div></div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with ecol:
    st.markdown("<div class='hm-tj-card'><div class='hm-tj-card-title'>Today’s Exercise</div>", unsafe_allow_html=True)
    visible_ex = [x for x in exercise_today if x.get("exercise_id")]
    if not visible_ex:
        _render_empty("No exercise item is scheduled for today.")
    for item in visible_ex:
        row = _row_by_id(exercises_df, item.get("exercise_id"))
        st.markdown(f"<div class='hm-tj-item'>{_esc(row.get('title') or 'Exercise')}<div class='hm-tj-meta'>{_esc(item.get('timing') or row.get('duration_or_reps') or '')}</div><div class='hm-tj-meta'>{_esc(item.get('notes') or '')}</div></div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with scol:
    st.markdown("<div class='hm-tj-card'><div class='hm-tj-card-title'>Today’s Supplements</div>", unsafe_allow_html=True)
    visible_supp_ids = []
    for item in supp_today:
        visible_supp_ids.extend(item.get("supplement_ids", []) or [])
    visible_supp_ids = [sid for sid in visible_supp_ids if sid in supplements_by_id]
    if not visible_supp_ids:
        _render_empty("No supplement is scheduled for today.")
    for sid in visible_supp_ids:
        row = supplements_by_id.get(sid, {})
        chips = "".join([f"<span class='hm-tj-chip'>{_esc(x)}</span>" for x in _split_timing(row.get("timing"))])
        st.markdown(f"<div class='hm-tj-item'>{_esc(row.get('supplement_name') or 'Supplement')}<div class='hm-tj-meta'>{_esc(row.get('dosage') or '')} · {_esc(row.get('frequency') or '')}</div><div class='hm-tj-meta'>Start: {_esc(_date_label(row.get('start_date')))} · End: {_esc(_date_label(row.get('end_date')))}</div>{chips}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown(f"""
<div class='hm-tj-report'>
  <div class='hm-tj-report-title'>Nutritionist Report</div>
  <div class='hm-tj-report-body'>{_esc(share.get('nutritionist_report') or 'Your nutritionist report will appear here when shared.')}</div>
</div>
""", unsafe_allow_html=True)

st.markdown("<div class='hm-tj-report-title'>Full 7-Day Plan</div>", unsafe_allow_html=True)
for i in range(7):
    day_iso = str(share.get("start_date"))[:10]
    try:
        day_dt = date.fromisoformat(day_iso) + timedelta(days=i)
        day_iso = day_dt.isoformat()
        label = f"Day {i+1} · " + day_dt.strftime("%a, %d %b %Y")
    except Exception:
        label = f"Day {i+1}"
    with st.expander(_fold_label(label), expanded=(day_iso == today_iso)):
        meals = [x for x in _day_rows(share.get("meal_plan"), day_iso) if x.get("recipe_id")]
        exercises = [x for x in _day_rows(share.get("exercise_plan"), day_iso) if x.get("exercise_id")]
        supps = _day_rows(share.get("supplement_plan"), day_iso)
        st.markdown("**Meals**")
        if meals:
            for item in meals:
                row = _row_by_id(recipes_df, item.get("recipe_id"))
                st.markdown(f"- **{_esc(item.get('meal_slot'))}:** {_esc(row.get('title') or 'Recipe')} {_esc('— ' + item.get('notes') if item.get('notes') else '')}")
        else:
            st.caption("No meals scheduled.")
        st.markdown("**Exercise**")
        if exercises:
            for item in exercises:
                row = _row_by_id(exercises_df, item.get("exercise_id"))
                st.markdown(f"- {_esc(row.get('title') or 'Exercise')} {_esc('— ' + item.get('timing') if item.get('timing') else '')} {_esc('— ' + item.get('notes') if item.get('notes') else '')}")
        else:
            st.caption("No exercise scheduled.")
        st.markdown("**Supplements**")
        ids = []
        for item in supps:
            ids.extend(item.get("supplement_ids", []) or [])
        ids = [sid for sid in ids if sid in supplements_by_id]
        if ids:
            for sid in ids:
                row = supplements_by_id.get(sid, {})
                st.markdown(f"- {_esc(row.get('supplement_name') or 'Supplement')} · {_esc(row.get('dosage') or 'Dosage NA')} · {_esc(row.get('frequency') or 'Frequency NA')} · {_esc(row.get('timing') or 'As advised')} · Start: {_esc(_date_label(row.get('start_date')))} · End: {_esc(_date_label(row.get('end_date')))}")
        else:
            st.caption("No supplements scheduled.")

st.markdown("</div>", unsafe_allow_html=True)
render_page_nav("Today's Journey", back_page="pages/02_Member_Home.py", dashboard_page="pages/02_Member_Home.py", show_evaluation=False, show_dashboard=True, location="bottom")
render_back_to_top()

# v102.4A: Member Today's Journey. Derived from Recommendations Share only, with +/- full-plan folds and richer supplement details.
