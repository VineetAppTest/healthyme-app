
import streamlit as st, pathlib, pandas as pd
from components.guards import require_admin
from components.ui_common import inject_global_styles, apply_luxe_theme, topbar, utility_logout_bar, render_build_text_v14, render_back_to_top, render_page_nav, card_start, card_end
from components.db import list_members, get_resource_assignments, save_resource_assignments

st.set_page_config(page_title="Manage & Allocate Recipes", page_icon="💚", layout="wide", initial_sidebar_state="collapsed")
inject_global_styles(); apply_luxe_theme(); require_admin(); utility_logout_bar(); render_back_to_top()

path = pathlib.Path(__file__).resolve().parents[1] / "data" / "recipes.csv"

def load():
    if not path.exists():
        return pd.DataFrame(columns=["title","description","meal_type","diet_type","goal_tags","condition_tags","prep_time","ingredients","steps","status"])
    return pd.read_csv(path)

def save(df):
    df.to_csv(path, index=False)

render_build_text_v15()
render_page_nav("Recipes", back_page="pages/10_Admin_Dashboard.py", show_evaluation=False, location="top")
topbar("Manage & Allocate Recipes", "Allocate existing recipes first. Add/import/edit only when the repository needs changes.", "Admin content manager")

tabs = st.tabs(["Allocate to Member", "Current Repository", "Add Recipe", "Import CSV", "Edit / Delete"])

with tabs[0]:
    st.subheader("Allocate Recipes to Member")
    st.markdown("<div class='hm-v15-compact-note'>Use the checkboxes below to assign recipes.</div>", unsafe_allow_html=True)
    members = list_members()
    df = load()
    if not df.empty and "status" in df.columns:
        df = df[df["status"].fillna("active").eq("active")].copy()
    if not members:
        st.info("No members available.")
    elif df.empty:
        st.info("No active recipes available. Add or import recipes first.")
    else:
        member_options = {f"{m['name']} — {m['email']}": m["id"] for m in members}
        card_start()
        st.markdown("### 👤 Allocation Context")
        st.caption("This member selection controls which recipe allocation is visible and saved below.")
        label = st.selectbox("👤 Member", list(member_options.keys()), key="recipe_alloc_member_v7")
        member_id = member_options[label]
        st.markdown(f"<div class='hm-date-emphasis'>👤 Allocating recipes for: {label}</div>", unsafe_allow_html=True)
        card_end()
        all_ids = [str(i) for i in df.index.tolist()]
        current = set(get_resource_assignments(member_id, "recipes"))
        state_key = f"recipe_alloc_state_{member_id}"
        if state_key not in st.session_state:
            st.session_state[state_key] = set(current)

        c1, c2 = st.columns(2)
        with c1:
            if st.button("Select All Recipes", use_container_width=True):
                st.session_state[state_key] = set(all_ids)
                for rid in all_ids:
                    st.session_state[f"recipe_alloc_{member_id}_{rid}"] = True
                st.rerun()
        with c2:
            if st.button("Deselect All Recipes", use_container_width=True):
                st.session_state[state_key] = set()
                for rid in all_ids:
                    st.session_state[f"recipe_alloc_{member_id}_{rid}"] = False
                st.rerun()

        selected = []
        st.markdown("#### Available recipes")
        for idx, row in df.iterrows():
            rid = str(idx)
            key = f"recipe_alloc_{member_id}_{rid}"
            if key not in st.session_state:
                st.session_state[key] = rid in st.session_state[state_key]
            checked = st.checkbox(str(row.get("title", "Untitled Recipe")), key=key)
            if checked:
                selected.append(rid)

        if st.button("Save Allocation", type="primary", use_container_width=True, help="Saves selected recipes for the member and queues notification/email flag."):
            save_resource_assignments(member_id, "recipes", selected)
            st.session_state[state_key] = set(selected)
            st.success("Recipe allocation saved. Member notification/email has been queued.")

with tabs[1]:
    st.subheader("Current Recipe Repository")
    st.dataframe(load(), use_container_width=True, hide_index=True)

with tabs[2]:
    st.subheader("Add New Recipe")
    cols = ["title","description","meal_type","diet_type","goal_tags","condition_tags","prep_time","ingredients","steps"]
    values = {}
    for c in cols:
        label = c.replace("_"," ").title()
        if c in ["description","ingredients","steps"]:
            values[c] = st.text_area(label, key=f"new_recipe_{c}")
        else:
            values[c] = st.text_input(label, key=f"new_recipe_{c}")
    if st.button("Save Recipe", type="primary", use_container_width=True):
        if not values["title"].strip():
            st.error("Recipe title is required.")
        else:
            df = load()
            df.loc[len(df)] = [values.get(c,"") for c in cols] + ["active"]
            save(df)
            st.success("Recipe saved.")
            st.rerun()

with tabs[3]:
    st.subheader("Import Recipe CSV")
    st.markdown("<div class='hm-v7-small-note'>CSV should match the repository columns as closely as possible.</div>", unsafe_allow_html=True)
    csv_file = st.file_uploader("Choose recipe CSV file", type=["csv"], key="recipe_csv_upload_v7")
    if st.button("Import CSV", type="primary", disabled=csv_file is None, use_container_width=True):
        df = pd.concat([load(), pd.read_csv(csv_file)], ignore_index=True)
        save(df)
        st.success("CSV imported.")
        st.rerun()

with tabs[4]:
    st.subheader("Edit or Delete Recipe")
    df = load()
    if df.empty:
        st.info("No recipes available.")
    else:
        options = [f"{idx} — {str(row.get('title','Untitled'))[:45]}" for idx,row in df.iterrows()]
        selected = st.selectbox("Select recipe", options)
        idx = int(selected.split(" — ")[0])
        row = df.loc[idx]
        cols = ["title","description","meal_type","diet_type","goal_tags","condition_tags","prep_time","ingredients","steps"]
        edited = {}
        for c in cols:
            label = c.replace("_"," ").title()
            if c in ["description","ingredients","steps"]:
                edited[c] = st.text_area(label, value=str(row.get(c,"")), key=f"edit_recipe_{c}_{idx}")
            else:
                edited[c] = st.text_input(label, value=str(row.get(c,"")), key=f"edit_recipe_{c}_{idx}")
        status_options = ["active","inactive"]
        current_status = str(row.get("status","active"))
        edited["status"] = st.selectbox("Status", status_options, index=status_options.index(current_status) if current_status in status_options else 0)
        b1, b2 = st.columns(2)
        with b1:
            if st.button("Update Recipe", type="primary", use_container_width=True):
                df.loc[idx, cols + ["status"]] = [edited[c] for c in cols + ["status"]]
                save(df)
                st.success("Recipe updated.")
                st.rerun()
        with b2:
            confirm = st.checkbox("Confirm delete selected recipe")
            if st.button("Delete Recipe", disabled=not confirm, use_container_width=True):
                df = df.drop(index=idx).reset_index(drop=True)
                save(df)
                st.success("Recipe deleted.")
                st.rerun()

render_page_nav("Recipes", back_page="pages/10_Admin_Dashboard.py", show_evaluation=False, location="bottom")
