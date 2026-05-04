
import streamlit as st, pathlib, pandas as pd
from components.guards import require_admin
from components.ui_common import inject_global_styles, apply_luxe_theme, topbar, card_start, card_end, utility_logout_bar
st.set_page_config(page_title="Manage Recipes", page_icon="💚", layout="wide")
inject_global_styles(); apply_luxe_theme(); require_admin(); utility_logout_bar()
path=pathlib.Path(__file__).resolve().parents[1]/"data"/"recipes.csv"
def load(): return pd.read_csv(path)
def save(df): df.to_csv(path,index=False)
topbar("Manage Recipes","Add, import, edit, delete, and preview recipes.","Admin content manager")
t1,t2,t3,t4=st.tabs(["Add Recipe","Import CSV","Edit / Delete","Current Repository"])
with t1:
    card_start(); st.subheader("Add New Recipe")
    values={}
    values["title"]=st.text_area("Title") if "title" in ["description","ingredients","steps","instructions"] else st.text_input("Title")
    values["description"]=st.text_area("Description") if "description" in ["description","ingredients","steps","instructions"] else st.text_input("Description")
    values["meal_type"]=st.text_area("Meal Type") if "meal_type" in ["description","ingredients","steps","instructions"] else st.text_input("Meal Type")
    values["diet_type"]=st.text_area("Diet Type") if "diet_type" in ["description","ingredients","steps","instructions"] else st.text_input("Diet Type")
    values["goal_tags"]=st.text_area("Goal Tags") if "goal_tags" in ["description","ingredients","steps","instructions"] else st.text_input("Goal Tags")
    values["condition_tags"]=st.text_area("Condition Tags") if "condition_tags" in ["description","ingredients","steps","instructions"] else st.text_input("Condition Tags")
    values["prep_time"]=st.text_area("Prep Time") if "prep_time" in ["description","ingredients","steps","instructions"] else st.text_input("Prep Time")
    values["ingredients"]=st.text_area("Ingredients") if "ingredients" in ["description","ingredients","steps","instructions"] else st.text_input("Ingredients")
    values["steps"]=st.text_area("Steps") if "steps" in ["description","ingredients","steps","instructions"] else st.text_input("Steps")
    if st.button("Save Recipe", type="primary"):
        if not values["title"].strip(): st.error("Recipe title is required.")
        else:
            df=load(); df.loc[len(df)]=["values['title']", "values['description']", "values['meal_type']", "values['diet_type']", "values['goal_tags']", "values['condition_tags']", "values['prep_time']", "values['ingredients']", "values['steps']", "'active'"]; save(df); st.success("Recipe saved.")
    card_end()
with t2:
    card_start(); st.markdown("<div class='csv-upload-panel'><h4>Upload recipe CSV</h4><p>Choose a CSV file, then click Import CSV.</p></div>", unsafe_allow_html=True)
    csv_file=st.file_uploader("Choose recipe CSV file", type=["csv"], key="recipe_csv_upload", label_visibility="collapsed")
    if st.button("Import CSV", type="primary", disabled=csv_file is None, use_container_width=True):
        df=pd.concat([load(), pd.read_csv(csv_file)], ignore_index=True); save(df); st.success("CSV imported.")
    card_end()
with t3:
    card_start(); st.subheader("Edit or Delete Recipe")
    df=load()
    if df.empty: st.info("No recipes available.")
    else:
        options=[f"{idx} — {str(row.get('title','Untitled'))[:45]}" for idx,row in df.iterrows()]
        selected=st.selectbox("Select recipe", options); idx=int(selected.split(" — ")[0]); row=df.loc[idx]
        edited={}
        edited["title"]=st.text_area("Title", value=str(row.get("title","")), key="recipe_title_edit") if "title" in ["description","ingredients","steps","instructions"] else st.text_input("Title", value=str(row.get("title","")), key="recipe_title_edit")
        edited["description"]=st.text_area("Description", value=str(row.get("description","")), key="recipe_description_edit") if "description" in ["description","ingredients","steps","instructions"] else st.text_input("Description", value=str(row.get("description","")), key="recipe_description_edit")
        edited["meal_type"]=st.text_area("Meal Type", value=str(row.get("meal_type","")), key="recipe_meal_type_edit") if "meal_type" in ["description","ingredients","steps","instructions"] else st.text_input("Meal Type", value=str(row.get("meal_type","")), key="recipe_meal_type_edit")
        edited["diet_type"]=st.text_area("Diet Type", value=str(row.get("diet_type","")), key="recipe_diet_type_edit") if "diet_type" in ["description","ingredients","steps","instructions"] else st.text_input("Diet Type", value=str(row.get("diet_type","")), key="recipe_diet_type_edit")
        edited["goal_tags"]=st.text_area("Goal Tags", value=str(row.get("goal_tags","")), key="recipe_goal_tags_edit") if "goal_tags" in ["description","ingredients","steps","instructions"] else st.text_input("Goal Tags", value=str(row.get("goal_tags","")), key="recipe_goal_tags_edit")
        edited["condition_tags"]=st.text_area("Condition Tags", value=str(row.get("condition_tags","")), key="recipe_condition_tags_edit") if "condition_tags" in ["description","ingredients","steps","instructions"] else st.text_input("Condition Tags", value=str(row.get("condition_tags","")), key="recipe_condition_tags_edit")
        edited["prep_time"]=st.text_area("Prep Time", value=str(row.get("prep_time","")), key="recipe_prep_time_edit") if "prep_time" in ["description","ingredients","steps","instructions"] else st.text_input("Prep Time", value=str(row.get("prep_time","")), key="recipe_prep_time_edit")
        edited["ingredients"]=st.text_area("Ingredients", value=str(row.get("ingredients","")), key="recipe_ingredients_edit") if "ingredients" in ["description","ingredients","steps","instructions"] else st.text_input("Ingredients", value=str(row.get("ingredients","")), key="recipe_ingredients_edit")
        edited["steps"]=st.text_area("Steps", value=str(row.get("steps","")), key="recipe_steps_edit") if "steps" in ["description","ingredients","steps","instructions"] else st.text_input("Steps", value=str(row.get("steps","")), key="recipe_steps_edit")
        status_options=["active","inactive"]; edited["status"]=st.selectbox("Status", status_options, index=status_options.index(str(row.get("status","active"))) if str(row.get("status","active")) in status_options else 0)
        b1,b2=st.columns(2)
        with b1:
            if st.button("Update Recipe", type="primary", use_container_width=True):
                df.loc[idx,['title', 'description', 'meal_type', 'diet_type', 'goal_tags', 'condition_tags', 'prep_time', 'ingredients', 'steps', 'status']]=[edited[c] for c in ['title', 'description', 'meal_type', 'diet_type', 'goal_tags', 'condition_tags', 'prep_time', 'ingredients', 'steps', 'status']]; save(df); st.success("Recipe updated."); st.rerun()
        with b2:
            confirm=st.checkbox("Confirm delete selected recipe")
            if st.button("Delete Recipe", disabled=not confirm, use_container_width=True):
                df=df.drop(index=idx).reset_index(drop=True); save(df); st.success("Recipe deleted."); st.rerun()
    card_end()
with t4:
    card_start(); st.dataframe(load(), use_container_width=True); card_end()
if st.button("Back to Dashboard"): st.switch_page("pages/10_Admin_Dashboard.py")
