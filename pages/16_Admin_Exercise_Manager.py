
import streamlit as st, pathlib, pandas as pd
from components.guards import require_admin
from components.ui_common import inject_global_styles, apply_luxe_theme, topbar, card_start, card_end, utility_logout_bar
st.set_page_config(page_title="Manage Exercises", page_icon="💚", layout="wide")
inject_global_styles(); apply_luxe_theme(); require_admin(); utility_logout_bar()
path=pathlib.Path(__file__).resolve().parents[1]/"data"/"exercises.csv"
def load(): return pd.read_csv(path)
def save(df): df.to_csv(path,index=False)
topbar("Manage Exercises","Add, import, edit, delete, and preview exercises.","Admin content manager")
t1,t2,t3,t4=st.tabs(["Add Exercise","Import CSV","Edit / Delete","Current Repository"])
with t1:
    card_start(); st.subheader("Add New Exercise")
    values={}
    values["title"]=st.text_area("Title") if "title" in ["description","ingredients","steps","instructions"] else st.text_input("Title")
    values["description"]=st.text_area("Description") if "description" in ["description","ingredients","steps","instructions"] else st.text_input("Description")
    values["category"]=st.text_area("Category") if "category" in ["description","ingredients","steps","instructions"] else st.text_input("Category")
    values["difficulty"]=st.text_area("Difficulty") if "difficulty" in ["description","ingredients","steps","instructions"] else st.text_input("Difficulty")
    values["goal_tags"]=st.text_area("Goal Tags") if "goal_tags" in ["description","ingredients","steps","instructions"] else st.text_input("Goal Tags")
    values["condition_tags"]=st.text_area("Condition Tags") if "condition_tags" in ["description","ingredients","steps","instructions"] else st.text_input("Condition Tags")
    values["duration_or_reps"]=st.text_area("Duration Or Reps") if "duration_or_reps" in ["description","ingredients","steps","instructions"] else st.text_input("Duration Or Reps")
    values["instructions"]=st.text_area("Instructions") if "instructions" in ["description","ingredients","steps","instructions"] else st.text_input("Instructions")
    if st.button("Save Exercise", type="primary"):
        if not values["title"].strip(): st.error("Exercise title is required.")
        else:
            df=load(); df.loc[len(df)]=["values['title']", "values['description']", "values['category']", "values['difficulty']", "values['goal_tags']", "values['condition_tags']", "values['duration_or_reps']", "values['instructions']", "'active'"]; save(df); st.success("Exercise saved.")
    card_end()
with t2:
    card_start(); st.markdown("<div class='csv-upload-panel'><h4>Upload exercise CSV</h4><p>Choose a CSV file, then click Import CSV.</p></div>", unsafe_allow_html=True)
    csv_file=st.file_uploader("Choose exercise CSV file", type=["csv"], key="exercise_csv_upload", label_visibility="collapsed")
    if st.button("Import CSV", type="primary", disabled=csv_file is None, use_container_width=True):
        df=pd.concat([load(), pd.read_csv(csv_file)], ignore_index=True); save(df); st.success("CSV imported.")
    card_end()
with t3:
    card_start(); st.subheader("Edit or Delete Exercise")
    df=load()
    if df.empty: st.info("No exercises available.")
    else:
        options=[f"{idx} — {str(row.get('title','Untitled'))[:45]}" for idx,row in df.iterrows()]
        selected=st.selectbox("Select exercise", options); idx=int(selected.split(" — ")[0]); row=df.loc[idx]
        edited={}
        edited["title"]=st.text_area("Title", value=str(row.get("title","")), key="exercise_title_edit") if "title" in ["description","ingredients","steps","instructions"] else st.text_input("Title", value=str(row.get("title","")), key="exercise_title_edit")
        edited["description"]=st.text_area("Description", value=str(row.get("description","")), key="exercise_description_edit") if "description" in ["description","ingredients","steps","instructions"] else st.text_input("Description", value=str(row.get("description","")), key="exercise_description_edit")
        edited["category"]=st.text_area("Category", value=str(row.get("category","")), key="exercise_category_edit") if "category" in ["description","ingredients","steps","instructions"] else st.text_input("Category", value=str(row.get("category","")), key="exercise_category_edit")
        edited["difficulty"]=st.text_area("Difficulty", value=str(row.get("difficulty","")), key="exercise_difficulty_edit") if "difficulty" in ["description","ingredients","steps","instructions"] else st.text_input("Difficulty", value=str(row.get("difficulty","")), key="exercise_difficulty_edit")
        edited["goal_tags"]=st.text_area("Goal Tags", value=str(row.get("goal_tags","")), key="exercise_goal_tags_edit") if "goal_tags" in ["description","ingredients","steps","instructions"] else st.text_input("Goal Tags", value=str(row.get("goal_tags","")), key="exercise_goal_tags_edit")
        edited["condition_tags"]=st.text_area("Condition Tags", value=str(row.get("condition_tags","")), key="exercise_condition_tags_edit") if "condition_tags" in ["description","ingredients","steps","instructions"] else st.text_input("Condition Tags", value=str(row.get("condition_tags","")), key="exercise_condition_tags_edit")
        edited["duration_or_reps"]=st.text_area("Duration Or Reps", value=str(row.get("duration_or_reps","")), key="exercise_duration_or_reps_edit") if "duration_or_reps" in ["description","ingredients","steps","instructions"] else st.text_input("Duration Or Reps", value=str(row.get("duration_or_reps","")), key="exercise_duration_or_reps_edit")
        edited["instructions"]=st.text_area("Instructions", value=str(row.get("instructions","")), key="exercise_instructions_edit") if "instructions" in ["description","ingredients","steps","instructions"] else st.text_input("Instructions", value=str(row.get("instructions","")), key="exercise_instructions_edit")
        status_options=["active","inactive"]; edited["status"]=st.selectbox("Status", status_options, index=status_options.index(str(row.get("status","active"))) if str(row.get("status","active")) in status_options else 0)
        b1,b2=st.columns(2)
        with b1:
            if st.button("Update Exercise", type="primary", use_container_width=True):
                df.loc[idx,['title', 'description', 'category', 'difficulty', 'goal_tags', 'condition_tags', 'duration_or_reps', 'instructions', 'status']]=[edited[c] for c in ['title', 'description', 'category', 'difficulty', 'goal_tags', 'condition_tags', 'duration_or_reps', 'instructions', 'status']]; save(df); st.success("Exercise updated."); st.rerun()
        with b2:
            confirm=st.checkbox("Confirm delete selected exercise")
            if st.button("Delete Exercise", disabled=not confirm, use_container_width=True):
                df=df.drop(index=idx).reset_index(drop=True); save(df); st.success("Exercise deleted."); st.rerun()
    card_end()
with t4:
    card_start(); st.dataframe(load(), use_container_width=True); card_end()
if st.button("Back to Dashboard"): st.switch_page("pages/10_Admin_Dashboard.py")
