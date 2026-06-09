
import streamlit as st, pathlib, pandas as pd
from components.guards import require_admin
from components.ui_common import inject_global_styles, apply_luxe_theme, topbar, utility_logout_bar, render_build_text_v14, render_back_to_top, render_page_nav
from components.db import list_members, get_resource_assignments, save_resource_assignments

st.set_page_config(page_title="Manage & Allocate Exercises", page_icon="💚", layout="wide", initial_sidebar_state="collapsed")
inject_global_styles(); apply_luxe_theme(); require_admin(); utility_logout_bar(); render_back_to_top()

path = pathlib.Path(__file__).resolve().parents[1] / "data" / "exercises.csv"

def load():
    if not path.exists():
        return pd.DataFrame(columns=["title","description","category","difficulty","goal_tags","condition_tags","duration_or_reps","instructions","status"])
    return pd.read_csv(path)

def save(df):
    df.to_csv(path, index=False)

render_build_text_v15()
render_page_nav("Exercises", back_page="pages/10_Admin_Dashboard.py", show_evaluation=False, location="top")
topbar("Manage & Allocate Exercises", "Allocate existing exercises first. Add/import/edit only when the repository needs changes.", "Admin content manager")

tabs = st.tabs(["Allocate to Member", "Current Repository", "Add Exercise", "Import CSV", "Edit / Delete"])

with tabs[0]:
    st.subheader("Allocate Exercises to Member")
    st.markdown("<div class='hm-v15-compact-note'>Use the checkboxes below to assign exercises.</div>", unsafe_allow_html=True)
    members = list_members()
    df = load()
    if not df.empty and "status" in df.columns:
        df = df[df["status"].fillna("active").eq("active")].copy()
    if not members:
        st.info("No members available.")
    elif df.empty:
        st.info("No active exercises available. Add or import exercises first.")
    else:
        member_options = {f"{m['name']} — {m['email']}": m["id"] for m in members}
        label = st.selectbox("Select member", list(member_options.keys()), key="exercise_alloc_member_v7")
        member_id = member_options[label]
        all_ids = [str(i) for i in df.index.tolist()]
        current = set(get_resource_assignments(member_id, "exercises"))
        state_key = f"exercise_alloc_state_{member_id}"
        if state_key not in st.session_state:
            st.session_state[state_key] = set(current)

        c1, c2 = st.columns(2)
        with c1:
            if st.button("Select All Exercises", use_container_width=True):
                st.session_state[state_key] = set(all_ids)
                for eid in all_ids:
                    st.session_state[f"exercise_alloc_{member_id}_{eid}"] = True
                st.rerun()
        with c2:
            if st.button("Deselect All Exercises", use_container_width=True):
                st.session_state[state_key] = set()
                for eid in all_ids:
                    st.session_state[f"exercise_alloc_{member_id}_{eid}"] = False
                st.rerun()

        selected = []
        st.markdown("#### Available exercises")
        for idx, row in df.iterrows():
            eid = str(idx)
            key = f"exercise_alloc_{member_id}_{eid}"
            if key not in st.session_state:
                st.session_state[key] = eid in st.session_state[state_key]
            checked = st.checkbox(str(row.get("title", "Untitled Exercise")), key=key)
            if checked:
                selected.append(eid)

        if st.button("Save Allocation", type="primary", use_container_width=True, help="Saves selected exercises for the member and queues notification/email flag."):
            save_resource_assignments(member_id, "exercises", selected)
            st.session_state[state_key] = set(selected)
            st.success("Exercise allocation saved. Member notification/email has been queued.")

with tabs[1]:
    st.subheader("Current Exercise Repository")
    st.dataframe(load(), use_container_width=True, hide_index=True)

with tabs[2]:
    st.subheader("Add New Exercise")
    cols = ["title","description","category","difficulty","goal_tags","condition_tags","duration_or_reps","instructions"]
    values = {}
    for c in cols:
        label = c.replace("_"," ").title()
        if c in ["description","instructions"]:
            values[c] = st.text_area(label, key=f"new_exercise_{c}")
        else:
            values[c] = st.text_input(label, key=f"new_exercise_{c}")
    if st.button("Save Exercise", type="primary", use_container_width=True):
        if not values["title"].strip():
            st.error("Exercise title is required.")
        else:
            df = load()
            df.loc[len(df)] = [values.get(c,"") for c in cols] + ["active"]
            save(df)
            st.success("Exercise saved.")
            st.rerun()

with tabs[3]:
    st.subheader("Import Exercise CSV")
    st.markdown("<div class='hm-v7-small-note'>CSV should match the repository columns as closely as possible.</div>", unsafe_allow_html=True)
    csv_file = st.file_uploader("Choose exercise CSV file", type=["csv"], key="exercise_csv_upload_v7")
    if st.button("Import CSV", type="primary", disabled=csv_file is None, use_container_width=True):
        df = pd.concat([load(), pd.read_csv(csv_file)], ignore_index=True)
        save(df)
        st.success("CSV imported.")
        st.rerun()

with tabs[4]:
    st.subheader("Edit or Delete Exercise")
    df = load()
    if df.empty:
        st.info("No exercises available.")
    else:
        options = [f"{idx} — {str(row.get('title','Untitled'))[:45]}" for idx,row in df.iterrows()]
        selected = st.selectbox("Select exercise", options)
        idx = int(selected.split(" — ")[0])
        row = df.loc[idx]
        cols = ["title","description","category","difficulty","goal_tags","condition_tags","duration_or_reps","instructions"]
        edited = {}
        for c in cols:
            label = c.replace("_"," ").title()
            if c in ["description","instructions"]:
                edited[c] = st.text_area(label, value=str(row.get(c,"")), key=f"edit_exercise_{c}_{idx}")
            else:
                edited[c] = st.text_input(label, value=str(row.get(c,"")), key=f"edit_exercise_{c}_{idx}")
        status_options = ["active","inactive"]
        current_status = str(row.get("status","active"))
        edited["status"] = st.selectbox("Status", status_options, index=status_options.index(current_status) if current_status in status_options else 0)
        b1, b2 = st.columns(2)
        with b1:
            if st.button("Update Exercise", type="primary", use_container_width=True):
                df.loc[idx, cols + ["status"]] = [edited[c] for c in cols + ["status"]]
                save(df)
                st.success("Exercise updated.")
                st.rerun()
        with b2:
            confirm = st.checkbox("Confirm delete selected exercise")
            if st.button("Delete Exercise", disabled=not confirm, use_container_width=True):
                df = df.drop(index=idx).reset_index(drop=True)
                save(df)
                st.success("Exercise deleted.")
                st.rerun()

render_page_nav("Exercises", back_page="pages/10_Admin_Dashboard.py", show_evaluation=False, location="bottom")
