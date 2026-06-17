# v100.5 direct topbar import hotfix

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
    compact_topbar,
)
from components.ui_common import topbar
from components.storage_assets import resolve_content_image_url
from components.db import get_workflow, get_resource_assignments, save_resource_feedback, get_resource_feedback


st.set_page_config(page_title="Exercises", page_icon="💚", layout="wide", initial_sidebar_state="collapsed")
require_member(); utility_logout_bar()





topbar("Exercise Repository", "", "Member content")

DATA_PATH = pathlib.Path(__file__).resolve().parents[1] / "data" / "exercises.csv"

EXERCISE_COLUMNS = ['title', 'description', 'category', 'difficulty', 'goal_tags', 'condition_tags', 'duration_or_reps', 'hidden_calories_v96', 'equipment', 'image_url', 'image_bucket', 'image_path', 'image_access_type', 'instructions', 'benefits', 'status']

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

/* --- v94.2 Exercise Content UI Alignment --- */
.hm-module-brand{
  text-align:left!important;
  margin:.15rem 0 .6rem 0!important;
}
.hm-module-brand .hm-logo-text{
  font-family:inherit!important;
  color:#064E3B!important;
  font-size:1.55rem!important;
  font-weight:900!important;
  letter-spacing:0!important;
}
.hm-module-tabs{
  display:none!important;
}
.hm-module-tools{
  display:grid!important;
  grid-template-columns:minmax(0,1fr) 3.1rem 3.1rem!important;
  gap:.55rem!important;
  align-items:center!important;
  margin:.55rem 0 .7rem 0!important;
}
.hm-module-tools .stTextInput,
.hm-module-tools [data-testid="stTextInput"]{
  margin:0!important;
}
.hm-module-tools input{
  background:#EEF2F7!important;
  border-radius:10px!important;
  min-height:44px!important;
}
.hm-tool-circle{
  width:3.1rem!important;
  height:3.1rem!important;
  border-radius:999px!important;
  background:#FFFDF8!important;
  border:1px solid #E5D2A9!important;
  display:flex!important;
  align-items:center!important;
  justify-content:center!important;
  color:#064E3B!important;
  font-size:1.15rem!important;
  font-weight:900!important;
  margin:0!important;
}
@media(max-width:768px){
  .hm-module-brand .hm-logo-text{font-size:1.35rem!important;}
  .hm-module-tools{grid-template-columns:minmax(0,1fr) 2.6rem 2.6rem!important;gap:.4rem!important;}
  .hm-tool-circle{width:2.6rem!important;height:2.6rem!important;font-size:1rem!important;}
}


/* --- v94.3 Exercise Hard Layout Fix --- */
.hm-module-shell{
  max-width:1120px;
  margin:0 auto;
  padding:.25rem 0 1.5rem 0;
}
.hm-module-brand,.hm-module-tabs{
  display:none!important;
}
.hm-tool-circle{
  width:44px!important;
  height:44px!important;
  border-radius:999px!important;
  background:#FFFDF8!important;
  border:1px solid #E5D2A9!important;
  display:flex!important;
  align-items:center!important;
  justify-content:center!important;
  color:#064E3B!important;
  font-size:1.05rem!important;
  font-weight:900!important;
  margin:0 auto!important;
}
[data-testid="column"] [data-testid="stTextInput"]{
  margin-bottom:0!important;
}
[data-testid="column"] input{
  min-height:44px!important;
  background:#EEF2F7!important;
  border-radius:10px!important;
}
@media(max-width:768px){
  .hm-tool-circle{width:40px!important;height:40px!important;font-size:.95rem!important;}
}


/* --- v94.4 Exercise Functional Toolbar --- */
.hm-module-shell{
  max-width:1120px;
  margin:0 auto;
  padding:.2rem 0 1.5rem 0;
}
.hm-module-brand,.hm-module-tabs{
  display:none!important;
}
.hm-content-toolbar-anchor + div [data-testid="stHorizontalBlock"]{
  display:flex!important;
  flex-direction:row!important;
  flex-wrap:nowrap!important;
  gap:.45rem!important;
  align-items:flex-start!important;
}
.hm-content-toolbar-anchor + div [data-testid="stHorizontalBlock"] > div[data-testid="column"]:first-child{
  flex:1 1 auto!important;
  min-width:0!important;
  width:auto!important;
}
.hm-content-toolbar-anchor + div [data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(2),
.hm-content-toolbar-anchor + div [data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(3){
  flex:0 0 48px!important;
  min-width:48px!important;
  width:48px!important;
}
.hm-content-toolbar-anchor + div [data-testid="stHorizontalBlock"] [data-testid="stTextInput"]{
  margin-bottom:0!important;
}
.hm-content-toolbar-anchor + div [data-testid="stHorizontalBlock"] input{
  min-height:44px!important;
  background:#EEF2F7!important;
  border-radius:10px!important;
}
.hm-content-toolbar-anchor + div [data-testid="stHorizontalBlock"] .stButton > button,
.hm-content-toolbar-anchor + div [data-testid="stHorizontalBlock"] button{
  min-height:44px!important;
  height:44px!important;
  width:44px!important;
  padding:0!important;
  border-radius:999px!important;
  background:#FFFDF8!important;
  border:1px solid #E5D2A9!important;
  color:#064E3B!important;
  box-shadow:none!important;
  font-size:1.05rem!important;
}
.hm-content-toolbar-anchor + div [data-testid="stHorizontalBlock"] .stButton > button *,
.hm-content-toolbar-anchor + div [data-testid="stHorizontalBlock"] button *{
  color:#064E3B!important;
}
.hm-filter-panel{
  background:#FFFDF8;
  border:1px solid #E5D2A9;
  border-radius:16px;
  padding:.8rem .9rem;
  margin:.5rem 0 .8rem 0;
}
.hm-filter-note{
  color:#64705F;
  font-size:.86rem;
  margin:.2rem 0 .4rem 0;
}
.hm-card-action-row{
  margin:-.35rem 0 1rem 0;
}
@media(max-width:768px){
  .hm-content-toolbar-anchor + div [data-testid="stHorizontalBlock"]{flex-wrap:nowrap!important;}
  .hm-content-toolbar-anchor + div [data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(2),
  .hm-content-toolbar-anchor + div [data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(3){
    flex-basis:42px!important;
    min-width:42px!important;
    width:42px!important;
  }
  .hm-content-toolbar-anchor + div [data-testid="stHorizontalBlock"] .stButton > button,
  .hm-content-toolbar-anchor + div [data-testid="stHorizontalBlock"] button{
    width:40px!important;
    height:40px!important;
    min-height:40px!important;
  }
}


/* --- v94.5 Exercise Card Action Button Proportion Fix --- */
.hm-card-action-row{
  margin:-.35rem 0 1rem 0!important;
}
.hm-card-action-row + div [data-testid="stHorizontalBlock"]{
  display:flex!important;
  flex-direction:row!important;
  flex-wrap:nowrap!important;
  gap:.55rem!important;
  align-items:stretch!important;
}
.hm-card-action-row + div [data-testid="stHorizontalBlock"] > div[data-testid="column"]:first-child{
  flex:1 1 auto!important;
  min-width:0!important;
}
.hm-card-action-row + div [data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(2){
  flex:0 0 72px!important;
  min-width:72px!important;
  max-width:72px!important;
}
.hm-card-action-row + div [data-testid="stHorizontalBlock"] .stButton{
  height:44px!important;
  margin:0!important;
}
.hm-card-action-row + div [data-testid="stHorizontalBlock"] .stButton > button{
  height:44px!important;
  min-height:44px!important;
  max-height:44px!important;
  padding:0 .9rem!important;
  border-radius:14px!important;
  border:1.3px solid #CDBB8F!important;
  background:#FFFFFF!important;
  color:#064E3B!important;
  box-shadow:0 3px 10px rgba(25,36,31,.045)!important;
  display:flex!important;
  align-items:center!important;
  justify-content:center!important;
  line-height:1!important;
  font-weight:500!important;
}
.hm-card-action-row + div [data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(2) .stButton > button{
  width:72px!important;
  min-width:72px!important;
  max-width:72px!important;
  padding:0!important;
  font-size:1rem!important;
}
.hm-card-action-row + div [data-testid="stHorizontalBlock"] .stButton > button *,
.hm-card-action-row + div [data-testid="stHorizontalBlock"] button *{
  color:#064E3B!important;
}
@media(max-width:768px){
  .hm-card-action-row + div [data-testid="stHorizontalBlock"]{
    gap:.45rem!important;
  }
  .hm-card-action-row + div [data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(2){
    flex-basis:52px!important;
    min-width:52px!important;
    max-width:52px!important;
  }
  .hm-card-action-row + div [data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(2) .stButton > button{
    width:52px!important;
    min-width:52px!important;
    max-width:52px!important;
  }
  .hm-card-action-row + div [data-testid="stHorizontalBlock"] .stButton,
  .hm-card-action-row + div [data-testid="stHorizontalBlock"] .stButton > button{
    height:42px!important;
    min-height:42px!important;
    max-height:42px!important;
  }
}


/* --- v94.6 Exercise Page-Level Button Normalization --- */

/* Normalise all module buttons first; this is intentionally page-level because
   Streamlit wraps buttons unpredictably inside column containers. */
div[data-testid="stButton"] > button{
  min-height:44px!important;
  height:44px!important;
  max-height:44px!important;
  border-radius:14px!important;
  border:1.3px solid #CDBB8F!important;
  background:#FFFFFF!important;
  color:#064E3B!important;
  box-shadow:0 3px 10px rgba(25,36,31,.045)!important;
  display:flex!important;
  align-items:center!important;
  justify-content:center!important;
  line-height:1!important;
  padding:0 .9rem!important;
  font-weight:500!important;
  white-space:nowrap!important;
}
div[data-testid="stButton"] > button *{
  color:#064E3B!important;
  line-height:1!important;
}

/* Card action rows: the code gives View button a 5-column width and heart a
   1-column width; this locks both to the same height while keeping the heart compact. */
.hm-card-action-row + div div[data-testid="stHorizontalBlock"]{
  display:flex!important;
  flex-wrap:nowrap!important;
  align-items:stretch!important;
  gap:.55rem!important;
}
.hm-card-action-row + div div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:first-child{
  flex:1 1 auto!important;
  min-width:0!important;
}
.hm-card-action-row + div div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(2){
  flex:0 0 64px!important;
  width:64px!important;
  min-width:64px!important;
  max-width:64px!important;
}
.hm-card-action-row + div div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(2) div[data-testid="stButton"] > button{
  width:64px!important;
  min-width:64px!important;
  max-width:64px!important;
  padding:0!important;
}

/* Toolbar buttons remain compact circular despite page-level button normalisation. */
.hm-content-toolbar-anchor + div div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(2) div[data-testid="stButton"] > button,
.hm-content-toolbar-anchor + div div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(3) div[data-testid="stButton"] > button{
  width:44px!important;
  min-width:44px!important;
  max-width:44px!important;
  border-radius:999px!important;
  padding:0!important;
}

/* Mobile proportion */
@media(max-width:768px){
  div[data-testid="stButton"] > button{
    min-height:42px!important;
    height:42px!important;
    max-height:42px!important;
    border-radius:13px!important;
  }
  .hm-card-action-row + div div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(2){
    flex-basis:52px!important;
    width:52px!important;
    min-width:52px!important;
    max-width:52px!important;
  }
  .hm-card-action-row + div div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(2) div[data-testid="stButton"] > button{
    width:52px!important;
    min-width:52px!important;
    max-width:52px!important;
  }
}

</style>
""", unsafe_allow_html=True)



def render_landing(df):
    st.markdown("<div class='hm-module-shell'>", unsafe_allow_html=True)

    if "hm_exercise_filter_open" not in st.session_state:
        st.session_state["hm_exercise_filter_open"] = False
    if "hm_exercise_fav_only" not in st.session_state:
        st.session_state["hm_exercise_fav_only"] = False
    if "hm_exercise_favorites" not in st.session_state:
        st.session_state["hm_exercise_favorites"] = set()

    st.markdown("<div class='hm-content-toolbar-anchor'></div>", unsafe_allow_html=True)
    tool_search_col, tool_filter_col, tool_fav_col = st.columns([12, 1, 1], gap="small")
    with tool_search_col:
        search = st.text_input("Search exercises", placeholder="Search exercises...", label_visibility="collapsed", key="exercise_search_v94_4")
    with tool_filter_col:
        if st.button("☷", key="exercise_filter_toggle_v94_4", help="Filter exercises"):
            st.session_state["hm_exercise_filter_open"] = not st.session_state["hm_exercise_filter_open"]
            st.rerun()
    with tool_fav_col:
        fav_label = "♥" if st.session_state["hm_exercise_fav_only"] else "♡"
        if st.button(fav_label, key="exercise_fav_only_toggle_v94_4", help="Show favourites only"):
            st.session_state["hm_exercise_fav_only"] = not st.session_state["hm_exercise_fav_only"]
            st.rerun()

    category_filter = "All"
    difficulty_filter = "All"
    if st.session_state["hm_exercise_filter_open"]:
        st.markdown("<div class='hm-filter-panel'>", unsafe_allow_html=True)
        st.markdown("<div class='hm-filter-note'>Filter exercises by category or difficulty.</div>", unsafe_allow_html=True)
        fc1, fc2, fc3 = st.columns([1, 1, .7])
        category_options = ["All"] + sorted([x for x in df.get("category", pd.Series(dtype=str)).fillna("").astype(str).unique().tolist() if x.strip()])
        difficulty_options = ["All"] + sorted([x for x in df.get("difficulty", pd.Series(dtype=str)).fillna("").astype(str).unique().tolist() if x.strip()])
        with fc1:
            category_filter = st.selectbox("Category", category_options, key="exercise_category_filter_v94_4")
        with fc2:
            difficulty_filter = st.selectbox("Difficulty", difficulty_options, key="exercise_difficulty_filter_v94_4")
        with fc3:
            if st.button("Clear filters", use_container_width=True, key="exercise_clear_filters_v94_4"):
                st.session_state["exercise_category_filter_v94_4"] = "All"
                st.session_state["exercise_difficulty_filter_v94_4"] = "All"
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    results = df.copy()
    if search.strip():
        q = search.strip().lower()
        cols = ["title","description","category","difficulty","goal_tags","condition_tags","instructions","benefits","equipment"]
        mask = pd.Series(False, index=results.index)
        for c in cols:
            if c in results.columns:
                mask = mask | results[c].fillna("").astype(str).str.lower().str.contains(q, regex=False)
        results = results[mask]

    category_filter = st.session_state.get("exercise_category_filter_v94_4", category_filter)
    difficulty_filter = st.session_state.get("exercise_difficulty_filter_v94_4", difficulty_filter)
    if category_filter and category_filter != "All" and "category" in results.columns:
        results = results[results["category"].fillna("").astype(str).eq(category_filter)]
    if difficulty_filter and difficulty_filter != "All" and "difficulty" in results.columns:
        results = results[results["difficulty"].fillna("").astype(str).eq(difficulty_filter)]

    favs = set(st.session_state.get("hm_exercise_favorites", set()))
    if st.session_state["hm_exercise_fav_only"]:
        results = results[results.index.astype(str).isin(favs)]

    display_label = "Favourites" if st.session_state["hm_exercise_fav_only"] else ("All" if not search.strip() else esc(search.strip()))
    st.markdown(f"<div class='hm-displaying'>Displaying - {display_label}</div>", unsafe_allow_html=True)

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
                    eid = str(idx)
                    fav_mark = "♥" if eid in favs else "♡"
                    st.markdown(f"""
<div class='hm-content-card'>
  <img src='{esc(img)}'>
  <div class='hm-content-card-body'>
    <div class='hm-content-title'>{title}</div>
    <div class='hm-content-meta'>
      <span>◷ {duration or "-"}</span>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)
                    st.markdown("<div class='hm-card-action-row'>", unsafe_allow_html=True)
                    ac1, ac2 = st.columns([5, 1], gap="small")
                    with ac1:
                        if st.button("View exercise", key=f"view_exercise_{idx}", type="secondary", use_container_width=True):
                            st.session_state["hm_exercise_selected_id"] = eid
                            st.rerun()
                    with ac2:
                        if st.button(fav_mark, key=f"fav_exercise_{idx}", help="Add/remove favourite", type="secondary", use_container_width=True):
                            favs = set(st.session_state.get("hm_exercise_favorites", set()))
                            if eid in favs:
                                favs.remove(eid)
                            else:
                                favs.add(eid)
                            st.session_state["hm_exercise_favorites"] = favs
                            st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

def render_detail(row, idx):
    img = image_for(row, idx)
    title = str(row.get("title", "Untitled Exercise") or "Untitled Exercise")

    st.markdown("<div class='hm-module-shell'>", unsafe_allow_html=True)
    st.markdown(f"<div class='hm-detail-hero'><img src='{esc(img)}'></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='hm-detail-title'>{esc(title)}</div>", unsafe_allow_html=True)

    duration = first_value(row, ["duration_or_reps"], "-")
    difficulty = first_value(row, ["difficulty"], "-")
    equipment = first_value(row, ["equipment"], "-")

    st.markdown(f"""
<div class='hm-detail-grid'>
  <div class='hm-detail-pill'><b>◷ {esc(duration)}</b><span>Duration / reps</span></div>
  <div class='hm-detail-pill'><b>📈 {esc(difficulty)}</b><span>Difficulty</span></div>
  <div class='hm-detail-pill'><b>⚙ {esc(equipment)}</b><span>Equipment</span></div>
</div>
""", unsafe_allow_html=True)

    section_key_v1008 = f"exercise_detail_section_{idx}"
    if section_key_v1008 not in st.session_state:
        st.session_state[section_key_v1008] = "overview"
    sec_col1, sec_col2, sec_col3 = st.columns(3)
    with sec_col1:
        if st.button("Overview", use_container_width=True, key=f"exercise_tab_overview_{idx}"):
            st.session_state[section_key_v1008] = "overview"
    with sec_col2:
        if st.button("Instructions", use_container_width=True, key=f"exercise_tab_instructions_{idx}"):
            st.session_state[section_key_v1008] = "instructions"
    with sec_col3:
        if st.button("Benefits", use_container_width=True, key=f"exercise_tab_benefits_{idx}"):
            st.session_state[section_key_v1008] = "benefits"

    active_exercise_section_v1008 = st.session_state.get(section_key_v1008, "overview")
    if active_exercise_section_v1008 == "overview":
        section_title_v1013 = "Overview"
        section_items_v1013 = split_lines(row.get("description", ""))
    elif active_exercise_section_v1008 == "instructions":
        section_title_v1013 = "Instructions"
        section_items_v1013 = split_lines(row.get("instructions", ""))
    else:
        section_title_v1013 = "Benefits"
        section_items_v1013 = split_lines(row.get("benefits", ""))

    if section_items_v1013:
        rows_v1013 = "".join([
            f"<div class='hm-v1013-premium-row'><span class='hm-v1013-check'>✓</span><div>{esc(item)}</div></div>"
            for item in section_items_v1013
        ])
    else:
        rows_v1013 = "<div class='hm-v1013-empty'>No details added yet.</div>"
    st.markdown(
        f"""
        <div class='hm-v1013-premium-card'>
          <div class='hm-v1013-section-title'>{section_title_v1013}</div>
          {rows_v1013}
        </div>
        """,
        unsafe_allow_html=True,
    )

    existing_feedback_v100 = get_resource_feedback(st.session_state["user_id"], "exercises", str(idx))
    exercise_reset_token_v1006 = st.session_state.get(f"exercise_feedback_reset_{idx}", 0)
    if st.session_state.pop(f"exercise_feedback_submitted_{idx}", False):
        st.balloons()
        st.success("Exercise feedback submitted for admin review. The feedback form has been cleared.")
    with st.expander("Exercise feedback", expanded=False):
        st.markdown("<div class='hm-v1008-feedback-note'>Mark completion and share feedback for admin review.</div>", unsafe_allow_html=True)
        status_options_v100 = ["Not started", "Completed", "Partially completed", "Need help / not suitable"]
        exercise_status_v100 = st.selectbox("Exercise status", status_options_v100, index=0, key=f"exercise_feedback_status_{idx}_{exercise_reset_token_v1006}")
        rating_options_v100 = ["", "1", "2", "3", "4", "5"]
        exercise_rating_v100 = st.selectbox("Rating", rating_options_v100, index=0, key=f"exercise_feedback_rating_{idx}_{exercise_reset_token_v1006}")
        exercise_notes_v100 = st.text_area("Member feedback", value="", key=f"exercise_feedback_notes_{idx}_{exercise_reset_token_v1006}")
        if st.button("Submit feedback on exercise 🌿", type="primary", use_container_width=True, key=f"exercise_feedback_submit_{idx}_{exercise_reset_token_v1006}"):
            save_resource_feedback(
                st.session_state["user_id"],
                "exercises",
                str(idx),
                title=title,
                status=exercise_status_v100,
                rating=exercise_rating_v100,
                notes=exercise_notes_v100,
            )
            st.session_state[f"exercise_feedback_reset_{idx}"] = exercise_reset_token_v1006 + 1
            st.session_state[f"exercise_feedback_submitted_{idx}"] = True
            st.rerun()
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
is_detail_view = selected_id is not None and selected_id.isdigit() and int(selected_id) in df.index

if is_detail_view:
    render_detail(df.loc[int(selected_id)], int(selected_id))
else:
    render_landing(df)

if is_detail_view:
    nav_back, nav_dashboard = st.columns(2)
    with nav_back:
        if st.button("← Back", key="exercise_detail_bottom_back", use_container_width=True):
            st.session_state.pop("hm_exercise_selected_id", None)
            st.rerun()
    with nav_dashboard:
        if st.button("Dashboard", key="exercise_detail_bottom_dashboard", use_container_width=True):
            st.session_state.pop("hm_exercise_selected_id", None)
            st.switch_page("pages/02_Member_Home.py")
else:
    render_page_nav("Exercises", back_page="pages/02_Member_Home.py", dashboard_page="pages/02_Member_Home.py", show_evaluation=False, location="bottom")


# v100.8: Deferred Exercise CSS after visible content to avoid invisible top spacing.
st.markdown("""
<style>
/* v100.8 Exercise structural polish */
section.main > div.block-container,
.main .block-container,
[data-testid="stAppViewBlockContainer"],
.stMainBlockContainer,
.block-container{
  padding-top:.16rem!important;
}
.hero-shell,
.hm-hero,
[class*="hero"]{
  margin-top:.02rem!important;
  margin-bottom:.20rem!important;
  padding-top:.72rem!important;
  padding-bottom:.72rem!important;
}

/* Hide any residual tab divider if a cached Streamlit tab structure exists */
div[data-testid="stTabs"], div[data-testid="stTabs"] *{
  border-bottom:0!important;
  box-shadow:none!important;
}
div[data-testid="stTabs"] [data-baseweb="tab-highlight"],
div[data-testid="stTabs"] [data-baseweb="tab-border"],
div[data-testid="stTabs"] hr,
div[data-testid="stTabs"] button[role="tab"]::before,
div[data-testid="stTabs"] button[role="tab"]::after{
  display:none!important;
  height:0!important;
  border:0!important;
  background:transparent!important;
}

/* Button-driven pseudo tabs */
div[data-testid="stButton"] > button{
  min-height:2.45rem!important;
  border-radius:999px!important;
  border:1.25px solid #D9C28F!important;
  background:#FFFDF8!important;
  color:#064E3B!important;
  font-weight:850!important;
}

/* Premium detail card */
.hm-v1008-section-shell{
  border:1px solid #E3C98E;
  background:linear-gradient(180deg,#FFFDF8 0%,#FFF9EC 100%);
  border-radius:18px;
  padding:.88rem 1.02rem;
  margin:.34rem 0 .58rem 0;
  box-shadow:0 8px 20px rgba(15,23,42,.045);
}
.hm-v1008-section-title{
  color:#064E3B;
  font-weight:950;
  font-size:.96rem;
  margin:0 0 .42rem 0;
}
.hm-v1008-row{
  display:flex;
  gap:.76rem;
  align-items:flex-start;
  padding:.58rem 0;
  border-bottom:1px solid #F0E4CC;
  color:#064E3B;
  font-size:1.01rem;
  line-height:1.38;
}
.hm-v1008-row:last-child{border-bottom:0;}
.hm-v1008-check{
  width:1.34rem;
  height:1.34rem;
  min-width:1.34rem;
  border-radius:999px;
  background:#ECFDF5;
  border:1.5px solid #6D9C6C;
  color:#065F46;
  display:inline-flex;
  align-items:center;
  justify-content:center;
  font-size:.75rem;
  font-weight:950;
  margin-top:.04rem;
}
.hm-v1008-num{
  width:1.44rem;
  height:1.44rem;
  min-width:1.44rem;
  border-radius:999px;
  background:#FFF7E6;
  border:1.5px solid #D9C28F;
  color:#7A5A16;
  display:inline-flex;
  align-items:center;
  justify-content:center;
  font-size:.76rem;
  font-weight:950;
  margin-top:.03rem;
}

/* Premium feedback expander */
div[data-testid="stExpander"] details{
  border:1.4px solid #D9C28F!important;
  border-radius:18px!important;
  background:linear-gradient(180deg,#FFFDF8 0%,#FFF9EC 100%)!important;
  box-shadow:0 9px 22px rgba(15,23,42,.05)!important;
  overflow:hidden!important;
}
div[data-testid="stExpander"] summary{
  min-height:2.78rem!important;
  padding:.64rem .92rem!important;
  background:#FFFDF8!important;
}
div[data-testid="stExpander"] summary p{
  color:#064E3B!important;
  font-size:.96rem!important;
  font-weight:940!important;
  white-space:nowrap!important;
}
.hm-v1008-feedback-note{
  color:#64748B!important;
  font-size:.80rem!important;
  font-weight:740!important;
  margin:.08rem 0 .48rem 0!important;
}
</style>
""", unsafe_allow_html=True)


# v100.9: Deferred compact hero + premium detail CSS for Exercise Repository.
inject_global_styles()
apply_luxe_theme()
render_back_to_top()


st.markdown("""
<style>
/* v100.13 standard hero + premium detail closure */
.hero-shell{
  margin-bottom:.14rem!important;
  padding-top:1.05rem!important;
  padding-bottom:1.02rem!important;
}
.hm-content-toolbar-anchor{
  height:0!important;
  min-height:0!important;
  margin:0!important;
  padding:0!important;
}
.hm-content-toolbar-anchor + div{
  margin-top:.02rem!important;
}
div[data-testid="stTextInput"] input{
  min-height:2.08rem!important;
  height:2.08rem!important;
  border-radius:12px!important;
}
.hm-v1013-premium-card{
  border:1.45px solid #D9C28F;
  background:linear-gradient(180deg,#FFFDF8 0%,#FFF7E6 100%);
  border-radius:20px;
  padding:1.02rem 1.14rem;
  margin:.34rem 0 .70rem 0;
  box-shadow:0 12px 28px rgba(15,23,42,.065);
}
.hm-v1013-section-title{
  color:#003C36;
  font-size:1.04rem;
  font-weight:980;
  margin:0 0 .46rem 0;
}
.hm-v1013-premium-row{
  display:flex;
  gap:.82rem;
  align-items:flex-start;
  padding:.68rem 0;
  border-bottom:1px solid #F0E4CC;
  color:#064E3B;
  font-size:1.04rem;
  line-height:1.42;
}
.hm-v1013-premium-row:last-child{
  border-bottom:0;
}
.hm-v1013-check{
  width:1.46rem;
  height:1.46rem;
  min-width:1.46rem;
  border-radius:999px;
  background:#ECFDF5;
  border:1.5px solid #6D9C6C;
  color:#065F46;
  display:inline-flex;
  align-items:center;
  justify-content:center;
  font-size:.80rem;
  font-weight:950;
}
.hm-v1013-empty{
  color:#64748B;
  font-size:.90rem;
  font-weight:720;
  padding:.35rem 0;
}
div[data-testid="stExpander"] details{
  border:1.6px solid #D9C28F!important;
  border-radius:20px!important;
  background:linear-gradient(180deg,#FFFDF8 0%,#FFF7E6 100%)!important;
  box-shadow:0 12px 30px rgba(15,23,42,.07)!important;
}
div[data-testid="stExpander"] summary{
  min-height:3.02rem!important;
  padding:.74rem 1.04rem!important;
}
div[data-testid="stExpander"] summary p{
  color:#064E3B!important;
  font-size:1.00rem!important;
  font-weight:970!important;
}
</style>
""", unsafe_allow_html=True)

