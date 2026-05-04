
import streamlit as st, pandas as pd, pathlib
from components.guards import require_member
from components.ui_common import inject_global_styles, apply_luxe_theme, topbar, card_start, card_end, utility_logout_bar
from components.db import get_workflow
st.set_page_config(page_title="Recipes", page_icon="💚", layout="wide")
inject_global_styles(); apply_luxe_theme(); require_member(); utility_logout_bar()
wf=get_workflow(st.session_state["user_id"]); topbar("Recipe Repository","Search and browse personalized recipes.","Personalized content")
if not wf.get("admin_completed"): st.warning("Your personalized plan will unlock after expert evaluation is completed."); st.stop()
df=pd.read_csv(pathlib.Path(__file__).resolve().parents[1]/"data"/"recipes.csv"); df=df[df["status"].fillna("active").eq("active")].copy()
st.markdown("<div class='repo-search-card'><b>Search recipes</b><br><span style='color:var(--hm-muted);font-size:.9rem;'>Search by recipe name, meal type, diet type, ingredients, tags, or description.</span></div>", unsafe_allow_html=True)
search=st.text_input("Search recipes", placeholder="Example: breakfast, paneer, vegetarian", label_visibility="collapsed")
if search.strip():
    q=search.strip().lower(); cols=["title","description","meal_type","diet_type","goal_tags","condition_tags","ingredients","steps"]; mask=pd.Series(False,index=df.index)
    for c in cols:
        if c in df.columns: mask=mask | df[c].fillna("").astype(str).str.lower().str.contains(q, regex=False)
    results=df[mask]
else: results=df
st.markdown(f"<div class='repo-result-count'>{len(results)} recipe(s) found</div>", unsafe_allow_html=True)
if results.empty: st.info("No matching recipes found.")
else:
    for i in range(0,len(results),2):
        cs=st.columns(2)
        for j,(_,row) in enumerate(results.iloc[i:i+2].iterrows()):
            with cs[j]:
                card_start(); st.markdown(f"### {row.get('title','Untitled Recipe')}"); st.caption(f"{row.get('meal_type','')} · {row.get('diet_type','')} · Prep {row.get('prep_time','')} min"); st.write(row.get("description",""))
                with st.expander("Ingredients"): st.write(row.get("ingredients",""))
                with st.expander("Steps"): st.write(row.get("steps",""))
                card_end()
if st.button("Back to Home"): st.switch_page("pages/02_Member_Home.py")
