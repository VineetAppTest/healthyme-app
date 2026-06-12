
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
from components.storage_assets import resolve_content_image_url
from components.db import get_workflow, get_resource_assignments


st.set_page_config(page_title="Recipes", page_icon="💚", layout="wide", initial_sidebar_state="collapsed")
inject_global_styles(); apply_luxe_theme(); require_member(); utility_logout_bar(); render_back_to_top()
compact_topbar("Recipe Repository", "", "Member content")

DATA_PATH = pathlib.Path(__file__).resolve().parents[1] / "data" / "recipes.csv"

RECIPE_COLUMNS = ['title', 'description', 'meal_type', 'diet_type', 'goal_tags', 'condition_tags', 'prep_time', 'calories', 'servings', 'portion_size', 'image_url', 'image_bucket', 'image_path', 'image_access_type', 'ingredients', 'steps', 'nutrition', 'status']

FALLBACK_IMAGES = [
    "https://images.unsplash.com/photo-1499636136210-6f4ee915583e?auto=format&fit=crop&w=900&q=80",
    "https://images.unsplash.com/photo-1511690656952-34342bb7c2f2?auto=format&fit=crop&w=900&q=80",
    "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?auto=format&fit=crop&w=900&q=80",
    "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?auto=format&fit=crop&w=900&q=80",
]


def load_recipes():
    if not DATA_PATH.exists():
        return pd.DataFrame(columns=RECIPE_COLUMNS)
    df = pd.read_csv(DATA_PATH)
    for c in RECIPE_COLUMNS:
        if c not in df.columns:
            df[c] = ""
    return df[RECIPE_COLUMNS]


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


def inject_recipe_css():
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
.hm-content-meta span{white-space:nowrap;}
.hm-card-action{margin:-.2rem 0 1.1rem 0;}
.hm-detail-hero{border-radius:22px;overflow:hidden;border:1px solid #E5D2A9;box-shadow:0 10px 26px rgba(15,23,42,.07);margin:.7rem 0 1rem 0;}
.hm-detail-hero img{width:100%;height:340px;object-fit:cover;display:block;}
.hm-detail-title{font-family:Georgia,serif;color:#064E3B;font-size:2.45rem;line-height:1.02;font-weight:900;margin:.8rem 0 1rem 0;}
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

/* --- v94.2 Recipe Content UI Alignment --- */
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


/* --- v94.3 Recipe Hard Layout Fix --- */
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


/* --- v94.4 Recipe Functional Toolbar --- */
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


/* --- v94.5 Recipe Card Action Button Proportion Fix --- */
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

</style>
""", unsafe_allow_html=True)



def render_landing(df):
    st.markdown("<div class='hm-module-shell'>", unsafe_allow_html=True)

    if "hm_recipe_filter_open" not in st.session_state:
        st.session_state["hm_recipe_filter_open"] = False
    if "hm_recipe_fav_only" not in st.session_state:
        st.session_state["hm_recipe_fav_only"] = False
    if "hm_recipe_favorites" not in st.session_state:
        st.session_state["hm_recipe_favorites"] = set()

    st.markdown("<div class='hm-content-toolbar-anchor'></div>", unsafe_allow_html=True)
    tool_search_col, tool_filter_col, tool_fav_col = st.columns([12, 1, 1], gap="small")
    with tool_search_col:
        search = st.text_input("Search recipes", placeholder="Search recipes...", label_visibility="collapsed", key="recipe_search_v94_4")
    with tool_filter_col:
        if st.button("☷", key="recipe_filter_toggle_v94_4", help="Filter recipes"):
            st.session_state["hm_recipe_filter_open"] = not st.session_state["hm_recipe_filter_open"]
            st.rerun()
    with tool_fav_col:
        fav_label = "♥" if st.session_state["hm_recipe_fav_only"] else "♡"
        if st.button(fav_label, key="recipe_fav_only_toggle_v94_4", help="Show favourites only"):
            st.session_state["hm_recipe_fav_only"] = not st.session_state["hm_recipe_fav_only"]
            st.rerun()

    meal_filter = "All"
    diet_filter = "All"
    if st.session_state["hm_recipe_filter_open"]:
        st.markdown("<div class='hm-filter-panel'>", unsafe_allow_html=True)
        st.markdown("<div class='hm-filter-note'>Filter recipes by meal type or diet type.</div>", unsafe_allow_html=True)
        fc1, fc2, fc3 = st.columns([1, 1, .7])
        meal_options = ["All"] + sorted([x for x in df.get("meal_type", pd.Series(dtype=str)).fillna("").astype(str).unique().tolist() if x.strip()])
        diet_options = ["All"] + sorted([x for x in df.get("diet_type", pd.Series(dtype=str)).fillna("").astype(str).unique().tolist() if x.strip()])
        with fc1:
            meal_filter = st.selectbox("Meal type", meal_options, key="recipe_meal_filter_v94_4")
        with fc2:
            diet_filter = st.selectbox("Diet type", diet_options, key="recipe_diet_filter_v94_4")
        with fc3:
            if st.button("Clear filters", use_container_width=True, key="recipe_clear_filters_v94_4"):
                st.session_state["recipe_meal_filter_v94_4"] = "All"
                st.session_state["recipe_diet_filter_v94_4"] = "All"
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    results = df.copy()
    if search.strip():
        q = search.strip().lower()
        cols = ["title","description","meal_type","diet_type","goal_tags","condition_tags","ingredients","steps","nutrition"]
        mask = pd.Series(False, index=results.index)
        for c in cols:
            if c in results.columns:
                mask = mask | results[c].fillna("").astype(str).str.lower().str.contains(q, regex=False)
        results = results[mask]

    meal_filter = st.session_state.get("recipe_meal_filter_v94_4", meal_filter)
    diet_filter = st.session_state.get("recipe_diet_filter_v94_4", diet_filter)
    if meal_filter and meal_filter != "All" and "meal_type" in results.columns:
        results = results[results["meal_type"].fillna("").astype(str).eq(meal_filter)]
    if diet_filter and diet_filter != "All" and "diet_type" in results.columns:
        results = results[results["diet_type"].fillna("").astype(str).eq(diet_filter)]

    favs = set(st.session_state.get("hm_recipe_favorites", set()))
    if st.session_state["hm_recipe_fav_only"]:
        results = results[results.index.astype(str).isin(favs)]

    display_label = "Favourites" if st.session_state["hm_recipe_fav_only"] else ("All" if not search.strip() else esc(search.strip()))
    st.markdown(f"<div class='hm-displaying'>Displaying - {display_label}</div>", unsafe_allow_html=True)

    if results.empty:
        st.info("No matching recipes found.")
    else:
        for row_start in range(0, len(results), 2):
            cols = st.columns(2)
            for col_i, (idx, row) in enumerate(results.iloc[row_start:row_start+2].iterrows()):
                with cols[col_i]:
                    img = image_for(row, idx)
                    title = esc(row.get("title", "Untitled Recipe"))
                    prep = esc(first_value(row, ["prep_time"], ""))
                    cal = esc(first_value(row, ["calories"], ""))
                    rid = str(idx)
                    fav_mark = "♥" if rid in favs else "♡"
                    st.markdown(f"""
<div class='hm-content-card'>
  <img src='{esc(img)}'>
  <div class='hm-content-card-body'>
    <div class='hm-content-title'>{title}</div>
    <div class='hm-content-meta'>
      <span>◷ {prep or "-"} mins</span>
      <span>•</span>
      <span>🍃 {cal or "-"} cal</span>
      <span style='margin-left:auto;'>{fav_mark}</span>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)
                    st.markdown("<div class='hm-card-action-row'>", unsafe_allow_html=True)
                    ac1, ac2 = st.columns([5, 1], gap="small")
                    with ac1:
                        if st.button("View recipe", key=f"view_recipe_{idx}", use_container_width=True):
                            st.session_state["hm_recipe_selected_id"] = rid
                            st.rerun()
                    with ac2:
                        if st.button(fav_mark, key=f"fav_recipe_{idx}", help="Add/remove favourite", use_container_width=True):
                            favs = set(st.session_state.get("hm_recipe_favorites", set()))
                            if rid in favs:
                                favs.remove(rid)
                            else:
                                favs.add(rid)
                            st.session_state["hm_recipe_favorites"] = favs
                            st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

def render_detail(row, idx):
    img = image_for(row, idx)
    title = str(row.get("title", "Untitled Recipe") or "Untitled Recipe")
    if st.button("← Back to recipes"):
        st.session_state.pop("hm_recipe_selected_id", None)
        st.rerun()

    st.markdown("<div class='hm-module-shell'>", unsafe_allow_html=True)
    st.markdown(f"<div class='hm-detail-hero'><img src='{esc(img)}'></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='hm-detail-title'>{esc(title)}</div>", unsafe_allow_html=True)

    prep = first_value(row, ["prep_time"], "-")
    calories = first_value(row, ["calories"], "-")
    servings = first_value(row, ["servings"], "-")
    portion = first_value(row, ["portion_size"], "-")

    st.markdown(f"""
<div class='hm-detail-grid'>
  <div class='hm-detail-pill'><b>◷ {esc(prep)} Minutes</b><span>Prep time</span></div>
  <div class='hm-detail-pill'><b>🔥 {esc(calories)} Calories</b><span>Per serving</span></div>
  <div class='hm-detail-pill'><b>👥 {esc(servings)} Servings</b><span>Makes</span></div>
  <div class='hm-detail-pill'><b>↗ {esc(portion)}</b><span>Portion</span></div>
</div>
""", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["INGREDIENTS", "INSTRUCTIONS", "NUTRITION"])
    with tab1:
        st.markdown("<div class='hm-detail-section-card'>", unsafe_allow_html=True)
        ingredients = split_lines(row.get("ingredients", ""))
        if not ingredients:
            st.info("No ingredients added yet.")
        for item in ingredients:
            st.markdown(f"<div class='hm-check-row'><div class='hm-check-box'></div><div>{esc(item)}</div></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with tab2:
        st.markdown("<div class='hm-detail-section-card'>", unsafe_allow_html=True)
        steps = split_lines(row.get("steps", ""))
        if not steps:
            st.info("No instructions added yet.")
        for n, item in enumerate(steps, start=1):
            st.markdown(f"<div class='hm-check-row'><b>{n}.</b><div>{esc(item)}</div></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with tab3:
        nutrition = str(row.get("nutrition", "") or "").strip()
        st.markdown("<div class='hm-detail-section-card'>", unsafe_allow_html=True)
        st.write(nutrition or "No nutrition details added yet.")
        st.markdown("</div>", unsafe_allow_html=True)

    st.button("Submit feedback on recipe 🌿", type="primary", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)


inject_recipe_css()
wf = get_workflow(st.session_state["user_id"])
if not wf.get("admin_completed"):
    st.warning("Your personalized plan will unlock after expert evaluation is completed.")
    st.stop()

df = load_recipes()
df = df[df["status"].fillna("active").astype(str).str.lower().eq("active")].copy()
assigned_ids = set(get_resource_assignments(st.session_state["user_id"], "recipes"))
if assigned_ids:
    df = df[df.index.astype(str).isin(assigned_ids)].copy()

selected_id = st.session_state.get("hm_recipe_selected_id")
if selected_id is not None and selected_id.isdigit() and int(selected_id) in df.index:
    render_detail(df.loc[int(selected_id)], int(selected_id))
else:
    render_landing(df)

render_page_nav("Recipes", back_page="pages/02_Member_Home.py", show_evaluation=False, location="bottom")
