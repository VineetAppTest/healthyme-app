
import pathlib
import pandas as pd
import streamlit as st

from components.guards import require_admin
from components.ui_common import inject_global_styles, apply_luxe_theme, topbar, utility_logout_bar, render_back_to_top, render_page_nav
from components.storage_assets import upload_content_image, PUBLIC_BUCKET, PRIVATE_BUCKET
from components.db import list_members, get_resource_assignments, save_resource_assignments

st.set_page_config(page_title="Manage & Allocate Recipes", page_icon="💚", layout="wide", initial_sidebar_state="collapsed")
inject_global_styles(); apply_luxe_theme(); require_admin(); utility_logout_bar(); render_back_to_top()

PATH = pathlib.Path(__file__).resolve().parents[1] / "data" / "recipes.csv"
RECIPE_COLUMNS = ['title', 'description', 'meal_type', 'diet_type', 'goal_tags', 'condition_tags', 'prep_time', 'calories', 'servings', 'portion_size', 'image_url', 'image_bucket', 'image_path', 'image_access_type', 'ingredients', 'steps', 'nutrition', 'status']


def ensure_columns(df):
    for c in RECIPE_COLUMNS:
        if c not in df.columns:
            df[c] = ""
    return df[RECIPE_COLUMNS]


def load():
    if not PATH.exists():
        return pd.DataFrame(columns=RECIPE_COLUMNS)
    return ensure_columns(pd.read_csv(PATH))


def save(df):
    ensure_columns(df).to_csv(PATH, index=False)



def is_valid_image_url(value):
    value = str(value or "").strip()
    if value.lower() in {"nan", "none", "null"}:
        return False
    return value.startswith("http://") or value.startswith("https://")


def clean_image_value(value):
    value = str(value or "").strip()
    if value.lower() in {"nan", "none", "null"}:
        return ""
    return value


def recipe_form(prefix, row=None):
    row = row or {}
    st.markdown("#### Core display fields")
    c1, c2 = st.columns(2)
    with c1:
        title = st.text_input("Title", value=str(row.get("title", "")), key=f"{prefix}_title")
        meal_type = st.text_input("Meal type", value=str(row.get("meal_type", "")), key=f"{prefix}_meal_type")
        prep_time = st.text_input("Timing / prep time in minutes", value=str(row.get("prep_time", "")), key=f"{prefix}_prep_time")
        calories = st.text_input("Calories", value=str(row.get("calories", "")), key=f"{prefix}_calories")
    with c2:
        image_url = st.text_input("Manual Image URL / fallback", value=clean_image_value(row.get("image_url", "")), key=f"{prefix}_image_url", help="Optional fallback. Uploaded Supabase image takes priority.")
        image_access_type = st.selectbox(
            "Uploaded image visibility",
            ["public", "private"],
            index=1 if str(row.get("image_access_type", "public")).lower() == "private" else 0,
            key=f"{prefix}_image_access_type",
            help="Use private for nutritionist-created/premium recipe assets.",
        )
        uploaded_image = st.file_uploader("Upload recipe image", type=["jpg", "jpeg", "png", "webp"], key=f"{prefix}_image_upload")
        image_bucket = str(row.get("image_bucket", ""))
        image_path = str(row.get("image_path", ""))
        if uploaded_image is not None:
            if st.button("Upload image to Supabase", key=f"{prefix}_upload_btn", use_container_width=True):
                try:
                    uploaded_meta = upload_content_image(uploaded_image, "recipes", title or "recipe", image_access_type)
                    st.session_state[f"{prefix}_uploaded_image_meta"] = uploaded_meta
                    st.success("Image uploaded and ready to save with this recipe.")
                except Exception as exc:
                    st.error(f"Image upload failed: {exc}")
        uploaded_meta = st.session_state.get(f"{prefix}_uploaded_image_meta", {})
        image_bucket = uploaded_meta.get("image_bucket", image_bucket)
        image_path = uploaded_meta.get("image_path", image_path)
        if is_valid_image_url(uploaded_meta.get("image_url")):
            image_url = uploaded_meta.get("image_url")
            st.image(image_url, caption="Uploaded image preview", use_container_width=True)
        elif is_valid_image_url(image_url):
            st.image(image_url, caption="Current image preview", use_container_width=True)
        diet_type = st.text_input("Diet type", value=str(row.get("diet_type", "")), key=f"{prefix}_diet_type")
        servings = st.text_input("Servings", value=str(row.get("servings", "")), key=f"{prefix}_servings")
        portion_size = st.text_input("Portion size", value=str(row.get("portion_size", "")), key=f"{prefix}_portion_size")

    description = st.text_area("Short description", value=str(row.get("description", "")), key=f"{prefix}_description")
    st.markdown("#### Details shown on second page")
    ingredients = st.text_area("Ingredients", value=str(row.get("ingredients", "")), key=f"{prefix}_ingredients", help="Use one line per ingredient or separate with semicolons.")
    steps = st.text_area("Instructions / steps", value=str(row.get("steps", "")), key=f"{prefix}_steps", help="Use one line per instruction or separate with semicolons.")
    nutrition = st.text_area("Nutrition details", value=str(row.get("nutrition", "")), key=f"{prefix}_nutrition")
    c3, c4 = st.columns(2)
    with c3:
        goal_tags = st.text_input("Goal tags", value=str(row.get("goal_tags", "")), key=f"{prefix}_goal_tags")
    with c4:
        condition_tags = st.text_input("Condition tags", value=str(row.get("condition_tags", "")), key=f"{prefix}_condition_tags")
    status = st.selectbox("Status", ["active", "inactive"], index=0 if str(row.get("status", "active")) != "inactive" else 1, key=f"{prefix}_status")
    return {
        "title": title,
        "description": description,
        "meal_type": meal_type,
        "diet_type": diet_type,
        "goal_tags": goal_tags,
        "condition_tags": condition_tags,
        "prep_time": prep_time,
        "calories": calories,
        "servings": servings,
        "portion_size": portion_size,
        "image_url": image_url,
        "image_bucket": image_bucket,
        "image_path": image_path,
        "image_access_type": image_access_type,
        "ingredients": ingredients,
        "steps": steps,
        "nutrition": nutrition,
        "status": status,
    }


render_page_nav("Recipes", back_page="pages/10_Admin_Dashboard.py", show_evaluation=False, location="top")
topbar("Manage & Allocate Recipes", "Manage image, title, timing, calories, recipe details and member allocation.", "Admin content manager")

tabs = st.tabs(["Allocate to Member", "Current Repository", "Add Recipe", "Import CSV", "Edit / Delete"])

with tabs[0]:
    st.subheader("Allocate Recipes to Member")
    members = list_members()
    df = load()
    active_df = df[df["status"].fillna("active").astype(str).str.lower().eq("active")].copy()
    if not members:
        st.info("No members available.")
    elif active_df.empty:
        st.info("No active recipes available. Add or import recipes first.")
    else:
        member_options = {f"{m['name']} — {m['email']}": m["id"] for m in members}
        label = st.selectbox("Select member", list(member_options.keys()), key="recipe_alloc_member_v93")
        member_id = member_options[label]
        all_ids = [str(i) for i in active_df.index.tolist()]
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
        for idx, row in active_df.iterrows():
            rid = str(idx)
            key = f"recipe_alloc_{member_id}_{rid}"
            if key not in st.session_state:
                st.session_state[key] = rid in st.session_state[state_key]
            checked = st.checkbox(f"{row.get('title', 'Untitled Recipe')} · {row.get('prep_time','')} mins · {row.get('calories','')} cal", key=key)
            if checked:
                selected.append(rid)

        if st.button("Save Allocation", type="primary", use_container_width=True):
            save_resource_assignments(member_id, "recipes", selected)
            st.session_state[state_key] = set(selected)
            st.success("Recipe allocation saved. Member notification/email has been queued.")

with tabs[1]:
    st.subheader("Current Recipe Repository")
    st.dataframe(load(), use_container_width=True, hide_index=False)

with tabs[2]:
    st.subheader("Add New Recipe")
    values = recipe_form("new_recipe_v93")
    if st.button("Save Recipe", type="primary", use_container_width=True):
        if not values["title"].strip():
            st.error("Recipe title is required.")
        else:
            df = load()
            df.loc[len(df)] = [values.get(c, "") for c in RECIPE_COLUMNS]
            save(df)
            st.success("Recipe saved.")
            st.rerun()

with tabs[3]:
    st.subheader("Import Recipe CSV")
    st.markdown("CSV can include image_url, image_bucket, image_path, image_access_type, title, prep_time, calories, ingredients, steps and nutrition. Missing columns will be added.")
    csv_file = st.file_uploader("Choose recipe CSV file", type=["csv"], key="recipe_csv_upload_v93")
    if st.button("Import CSV", type="primary", disabled=csv_file is None, use_container_width=True):
        imported = pd.read_csv(csv_file)
        df = pd.concat([load(), ensure_columns(imported)], ignore_index=True)
        save(df)
        st.success("CSV imported.")
        st.rerun()

with tabs[4]:
    st.subheader("Edit or Delete Recipe")
    df = load()
    if df.empty:
        st.info("No recipes available.")
    else:
        options = [f"{idx} — {str(row.get('title','Untitled'))[:55]}" for idx, row in df.iterrows()]
        selected = st.selectbox("Select recipe", options)
        idx = int(selected.split(" — ")[0])
        row = df.loc[idx].to_dict()
        edited = recipe_form(f"edit_recipe_v93_{idx}", row)
        b1, b2 = st.columns(2)
        with b1:
            if st.button("Update Recipe", type="primary", use_container_width=True):
                for c in RECIPE_COLUMNS:
                    df.at[idx, c] = edited.get(c, "")
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
