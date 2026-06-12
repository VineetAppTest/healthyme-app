
import html
import pathlib
import pandas as pd
import streamlit as st

from components.guards import require_member
from components.ui_common import (
    inject_global_styles,
    apply_luxe_theme,
    utility_logout_bar,
    render_back_to_top,
    render_page_nav,
)
from components.storage_assets import resolve_content_image_url
from components.db import get_workflow, get_resource_assignments


st.set_page_config(page_title="Exercises", page_icon="💚", layout="wide", initial_sidebar_state="collapsed")
inject_global_styles(); apply_luxe_theme(); require_member(); utility_logout_bar(); render_back_to_top()

DATA_PATH = pathlib.Path(__file__).resolve().parents[1] / "data" / "exercises.csv"

EXERCISE_COLUMNS = ['title', 'description', 'category', 'difficulty', 'goal_tags', 'condition_tags', 'duration_or_reps', 'calories', 'equipment', 'image_url', 'image_bucket', 'image_path', 'image_access_type', 'instructions', 'benefits', 'status']

FALLBACK_IMAGES = [
    "https://images.unsplash.com/photo-1518611012118-696072aa579a?auto=format&fit=crop&w=900&q=80",
    "https://images.unsplash.com/photo-1599058917212-d750089bc07e?auto=format&fit=crop&w=900&q=80",
    "https://images.unsplash.com/photo-1544367567-0f2fcb009e0b?auto=format&fit=crop&w=900&q=80",
    "https://images.unsplash.com/photo-1517836357463-d25dfeac3438?auto=format&fit=crop&w=900&q=80",
]


def load_exercises():
    if not DATA_PATH.exists():
        return pd.DataFrame(columns=EXERCISE_COLUMNS)
    df = pd.read_csv(DATA_PATH)
    for c in EXERCISE_COLUMNS:
        if c not in df.columns:
            df[c] = ""
    return df[EXERCISE_COLUMNS]


def esc(value):
    return html.escape(str(value or ""))


def first_value(row, keys, default=""):
    for k in keys:
        value = row.get(k, "")
        if pd.notna(value) and str(value).strip():
            return str(value).strip()
    return default


def image_for(row, idx):
    return resolve_content_image_url(row, FALLBACK_IMAGES[int(idx) % len(FALLBACK_IMAGES)])


def split_lines(value):
    raw = str(value or "").replace("\r", "\n")
    if "\n" in raw:
        return [x.strip(" •-") for x in raw.split("\n") if x.strip(" •-")]
    if ";" in raw:
        return [x.strip(" •-") for x in raw.split(";") if x.strip(" •-")]
    return [raw.strip()] if raw.strip() else []


def inject_exercise_css():
    st.markdown("""
<style>
.hm-module-shell{max-width:1120px;margin:0 auto;padding:.3rem 0 1.5rem 0;}
.hm-module-brand{text-align:center;margin:.25rem 0 .45rem 0;}
.hm-module-brand .hm-logo-text{font-family:Georgia,serif;color:#064E3B;font-size:2.1rem;font-weight:800;letter-spacing:-.04rem;}
.hm-module-tabs{display:grid;grid-template-columns:1fr 1fr;gap:.35rem;background:#FFFDF8;border:1px solid #E5D2A9;border-radius:999px;padding:.3rem;margin:.6rem 0 1rem 0;}
.hm-module-tab-active,.hm-module-tab{border-radius:999px;padding:.75rem 1rem;text-align:center;font-weight:900;}
.hm-module-tab-active{background:#064E3B;color:#fff;box-shadow:0 8px 20px rgba(6,78,59,.18);}
.hm-module-tab{color:#064E3B;background:transparent;}
.hm-module-tools{display:grid;grid-template-columns:1fr auto auto;gap:.65rem;align-items:center;margin:.75rem 0 .7rem 0;}
.hm-tool-circle{width:3.1rem;height:3.1rem;border-radius:999px;background:#F2F4E9;border:1px solid #E5D2A9;display:flex;align-items:center;justify-content:center;color:#064E3B;font-size:1.35rem;font-weight:900;}
.hm-displaying{color:#102A43;font-size:1.05rem;margin:.35rem 0 .8rem 0;}
.hm-content-card{background:#fff;border:1px solid #E5D2A9;border-radius:18px;overflow:hidden;box-shadow:0 8px 22px rgba(15,23,42,.06);margin-bottom:.7rem;}
.hm-content-card img{width:100%;height:220px;object-fit:cover;display:block;}
.hm-content-card-body{padding:1rem 1rem .9rem 1rem;}
.hm-content-title{font-family:Georgia,serif;color:#064E3B;font-size:1.35rem;line-height:1.1;font-weight:900;margin:0 0 .7rem 0;}
.hm-content-meta{display:flex;gap:.55rem;align-items:center;color:#365A45;font-weight:700;font-size:.92rem;}
.hm-detail-hero{border-radius:22px;overflow:hidden;border:1px solid #E5D2A9;box-shadow:0 10px 26px rgba(15,23,42,.07);margin:.7rem 0 1rem 0;}
.hm-detail-hero img{width:100%;height:340px;object-fit:cover;display:block;}
.hm-detail-title{font-family:Georgia,serif;color:#064E3B;font-size:2.35rem;line-height:1.02;font-weight:900;margin:.8rem 0 1rem 0;}
.hm-detail-grid{display:grid;grid-template-columns:1fr 1fr;gap:.8rem;margin:.7rem 0 1.15rem 0;}
.hm-detail-pill{background:#FFFDF8;border:1px solid #E5D2A9;border-radius:18px;padding:.9rem 1rem;color:#064E3B;box-shadow:0 6px 18px rgba(15,23,42,.045);}
.hm-detail-pill b{font-size:1.1rem;}
.hm-detail-pill span{display:block;color:#64705F;font-size:.82rem;margin-top:.15rem;}
.hm-detail-section-card{background:#fff;border:1px solid #E5D2A9;border-radius:22px;padding:1rem 1.1rem;margin-top:.8rem;}
.hm-check-row{display:flex;gap:.75rem;align-items:flex-start;padding:.72rem 0;border-bottom:1px solid #EEE3CC;color:#064E3B;font-size:1.04rem;}
.hm-check-box{width:1.05rem;height:1.05rem;border:2px solid #6D9C6C;border-radius:4px;flex:0 0 auto;margin-top:.15rem;}
@media(max-width:768px){
  .hm-module-shell{padding:.1rem .1rem 1rem .1rem;}
  .hm-module-brand .hm-logo-text{font-size:1.9rem;}
  .hm-module-tools{grid-template-columns:1fr 2.55rem 2.55rem;gap:.45rem;}
  .hm-tool-circle{width:2.55rem;height:2.55rem;font-size:1rem;}
  .hm-content-card img{height:165px;}
  .hm-content-title{font-size:1.15rem;}
  .hm-detail-hero img{height:250px;}
  .hm-detail-title{font-size:2rem;}
  .hm-detail-grid{grid-template-columns:1fr 1fr;gap:.55rem;}
  .hm-detail-pill{padding:.72rem .72rem;}
}
</style>
""", unsafe_allow_html=True)


def render_landing(df):
    st.markdown("<div class='hm-module-shell'>", unsafe_allow_html=True)
    st.markdown("<div class='hm-module-brand'><div class='hm-logo-text'>HealthyMe</div></div>", unsafe_allow_html=True)
    st.markdown("""
<div class='hm-module-tabs'>
  <div class='hm-module-tab'>🍲 RECIPES</div>
  <div class='hm-module-tab-active'>🏃 EXERCISES</div>
</div>
""", unsafe_allow_html=True)

    st.markdown("<div class='hm-module-tools'>", unsafe_allow_html=True)
    search = st.text_input("Search exercises", placeholder="Search exercises...", label_visibility="collapsed", key="exercise_search_v93")
    st.markdown("<div class='hm-tool-circle'>☷</div>", unsafe_allow_html=True)
    st.markdown("<div class='hm-tool-circle'>♡</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    if st.button("Open Recipes", use_container_width=True, help="Switch to Recipe module"):
        st.switch_page("pages/08_Recipe_Repository.py")

    results = df
    if search.strip():
        q = search.strip().lower()
        cols = ["title","description","category","difficulty","goal_tags","condition_tags","instructions","benefits","equipment"]
        mask = pd.Series(False, index=df.index)
        for c in cols:
            if c in df.columns:
                mask = mask | df[c].fillna("").astype(str).str.lower().str.contains(q, regex=False)
        results = df[mask]

    st.markdown(f"<div class='hm-displaying'>Displaying - {'All' if not search.strip() else esc(search.strip())}</div>", unsafe_allow_html=True)

    if results.empty:
        st.info("No matching exercises found.")
    else:
        for row_start in range(0, len(results), 2):
            cols = st.columns(2)
            for col_i, (idx, row) in enumerate(results.iloc[row_start:row_start+2].iterrows()):
                with cols[col_i]:
                    img = image_for(row, idx)
                    title = esc(row.get("title", "Untitled Exercise"))
                    duration = esc(first_value(row, ["duration_or_reps"], ""))
                    cal = esc(first_value(row, ["calories"], ""))
                    st.markdown(f"""
<div class='hm-content-card'>
  <img src='{esc(img)}'>
  <div class='hm-content-card-body'>
    <div class='hm-content-title'>{title}</div>
    <div class='hm-content-meta'>
      <span>◷ {duration or "-"}</span>
      <span>•</span>
      <span>🔥 {cal or "-"} cal</span>
      <span style='margin-left:auto;'>♡</span>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)
                    if st.button("View exercise", key=f"view_exercise_{idx}", use_container_width=True):
                        st.session_state["hm_exercise_selected_id"] = str(idx)
                        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


def render_detail(row, idx):
    img = image_for(row, idx)
    title = str(row.get("title", "Untitled Exercise") or "Untitled Exercise")
    if st.button("← Back to exercises"):
        st.session_state.pop("hm_exercise_selected_id", None)
        st.rerun()

    st.markdown("<div class='hm-module-shell'>", unsafe_allow_html=True)
    st.markdown(f"<div class='hm-detail-hero'><img src='{esc(img)}'></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='hm-detail-title'>{esc(title)}</div>", unsafe_allow_html=True)

    duration = first_value(row, ["duration_or_reps"], "-")
    calories = first_value(row, ["calories"], "-")
    difficulty = first_value(row, ["difficulty"], "-")
    equipment = first_value(row, ["equipment"], "-")

    st.markdown(f"""
<div class='hm-detail-grid'>
  <div class='hm-detail-pill'><b>◷ {esc(duration)}</b><span>Duration / reps</span></div>
  <div class='hm-detail-pill'><b>🔥 {esc(calories)} Calories</b><span>Estimate</span></div>
  <div class='hm-detail-pill'><b>📈 {esc(difficulty)}</b><span>Difficulty</span></div>
  <div class='hm-detail-pill'><b>⚙ {esc(equipment)}</b><span>Equipment</span></div>
</div>
""", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["OVERVIEW", "INSTRUCTIONS", "BENEFITS"])
    with tab1:
        st.markdown("<div class='hm-detail-section-card'>", unsafe_allow_html=True)
        st.write(str(row.get("description", "") or "No overview added yet."))
        st.markdown("</div>", unsafe_allow_html=True)
    with tab2:
        st.markdown("<div class='hm-detail-section-card'>", unsafe_allow_html=True)
        instructions = split_lines(row.get("instructions", ""))
        if not instructions:
            st.info("No instructions added yet.")
        for n, item in enumerate(instructions, start=1):
            st.markdown(f"<div class='hm-check-row'><b>{n}.</b><div>{esc(item)}</div></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with tab3:
        st.markdown("<div class='hm-detail-section-card'>", unsafe_allow_html=True)
        benefits = split_lines(row.get("benefits", ""))
        if not benefits:
            st.info("No benefits added yet.")
        for item in benefits:
            st.markdown(f"<div class='hm-check-row'><div class='hm-check-box'></div><div>{esc(item)}</div></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.button("Submit feedback on exercise 🌿", type="primary", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)


inject_exercise_css()
wf = get_workflow(st.session_state["user_id"])
if not wf.get("admin_completed"):
    st.warning("Your personalized plan will unlock after expert evaluation is completed.")
    st.stop()

df = load_exercises()
df = df[df["status"].fillna("active").astype(str).str.lower().eq("active")].copy()
assigned_ids = set(get_resource_assignments(st.session_state["user_id"], "exercises"))
if assigned_ids:
    df = df[df.index.astype(str).isin(assigned_ids)].copy()

selected_id = st.session_state.get("hm_exercise_selected_id")
if selected_id is not None and selected_id.isdigit() and int(selected_id) in df.index:
    render_detail(df.loc[int(selected_id)], int(selected_id))
else:
    render_landing(df)

render_page_nav("Exercises", back_page="pages/02_Member_Home.py", show_evaluation=False, location="bottom")
