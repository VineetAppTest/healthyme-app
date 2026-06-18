from components.ui_common import render_page_nav, render_back_to_top

import pathlib
import pandas as pd
import streamlit as st

from components.guards import require_admin
from components.ui_common import inject_global_styles, apply_luxe_theme, topbar, utility_logout_bar, render_back_to_top, render_page_nav
from components.storage_assets import upload_content_image, PUBLIC_BUCKET, PRIVATE_BUCKET
from components.db import list_members, get_resource_assignments, save_resource_assignments, list_resource_feedback

st.set_page_config(page_title="Manage & Allocate Recipes", page_icon="💚", layout="wide", initial_sidebar_state="collapsed")

# v102.2C: parallel page shell placed after Streamlit setup
st.markdown("""
<style>
.hm-v1022c-shell{border:1px solid #E3C98E;background:linear-gradient(180deg,#FFFDF8 0%,#FFF9EC 100%);border-radius:20px;padding:1rem;margin:.75rem 0 1rem 0;box-shadow:0 10px 24px rgba(15,23,42,.05)}
.hm-v1022c-title{color:#064E3B;font-size:1.08rem;font-weight:950;margin:0 0 .35rem 0}
.hm-v1022c-note{color:#475569;font-size:.86rem;font-weight:720;margin:0}
.hm-v1022c-chip{display:inline-flex;padding:.22rem .58rem;border:1px solid #E3C98E;border-radius:999px;background:#FFF7E6;color:#7A5A16;font-size:.76rem;font-weight:850;margin:.45rem .2rem 0 0}
</style>
<div class="hm-v1022c-shell">
  <div class="hm-v1022c-title">Manage & Allocate Recipes-1</div>
  <div class="hm-v1022c-note">Admin meal-library workspace inspired by the new mockup. Existing Recipe Manager remains available as fallback.</div>
  <span class="hm-v1022c-chip">Parallel UX</span><span class="hm-v1022c-chip">Existing data logic retained</span><span class="hm-v1022c-chip">Test safely</span>
</div>
""", unsafe_allow_html=True)
inject_global_styles(); apply_luxe_theme(); require_admin(); utility_logout_bar()

st.markdown("""
<style>
/* v96.10 Recipe Manager compact layout */
.block-container{padding-top:.45rem!important;max-width:1120px!important;}
.hero-shell{margin:.45rem 0 .75rem 0!important;padding:1rem 1.15rem!important;}
[data-testid="stTabs"]{margin-top:.25rem!important;}
[data-testid="stTabs"] button p{font-size:.82rem!important;}
div[data-testid="stTextInput"], div[data-testid="stSelectbox"], div[data-testid="stFileUploader"]{margin-bottom:.35rem!important;}
textarea{min-height:92px!important;}
</style>
""", unsafe_allow_html=True)


PATH = pathlib.Path(__file__).resolve().parents[1] / "data" / "recipes.csv"
RECIPE_COLUMNS = ['title', 'description', 'meal_type', 'diet_type', 'goal_tags', 'condition_tags', 'prep_time', 'calories', 'protein', 'fat', 'carbohydrates', 'additional_nutrition', 'servings', 'portion_size', 'image_url', 'image_bucket', 'image_path', 'image_access_type', 'ingredients', 'steps', 'nutrition', 'status']


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


def attach_uploaded_images_to_import(imported, uploaded_images, module_name):
    uploaded_images = uploaded_images or []
    image_map = {getattr(f, "name", ""): f for f in uploaded_images}
    upload_count = 0
    if "image_file_name_to_upload" not in imported.columns:
        return imported, upload_count
    for idx, row in imported.iterrows():
        file_name = str(row.get("image_file_name_to_upload", "") or "").strip()
        if not file_name or file_name not in image_map:
            continue
        access_type = str(row.get("image_access_type", "public") or "public").strip().lower()
        title = str(row.get("title", module_name) or module_name)
        meta = upload_content_image(image_map[file_name], module_name, title, access_type)
        for key in ["image_url", "image_bucket", "image_path", "image_access_type"]:
            imported.at[idx, key] = meta.get(key, "")
        upload_count += 1
    return imported, upload_count

def recipe_form(prefix, row=None):
    row = row or {}
    st.markdown("#### Core display fields")
    c1, c2 = st.columns(2)
    with c1:
        title = st.text_input("Title", value=str(row.get("title", "")), key=f"{prefix}_title")
        meal_type = st.text_input("Meal type", value=str(row.get("meal_type", "")), key=f"{prefix}_meal_type")
        prep_time = st.text_input("Timing / prep time in minutes", value=str(row.get("prep_time", "")), key=f"{prefix}_prep_time")
        calories = st.text_input("Calories", value=str(row.get("calories", "")), key=f"{prefix}_calories")
        protein = st.text_input("Protein", value=str(row.get("protein", "")), key=f"{prefix}_protein")
        fat = st.text_input("Fat", value=str(row.get("fat", "")), key=f"{prefix}_fat")
        carbohydrates = st.text_input("Carbohydrates", value=str(row.get("carbohydrates", "")), key=f"{prefix}_carbohydrates")
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
    additional_nutrition = st.text_area("Additional nutrition metrics", value=str(row.get("additional_nutrition", "")), key=f"{prefix}_additional_nutrition", placeholder="Example: Fibre: 8g; Sodium: 120mg")
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
        "protein": protein,
        "fat": fat,
        "carbohydrates": carbohydrates,
        "additional_nutrition": additional_nutrition,
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


# v101.6: top page navigation removed; bottom nav remains standard


topbar("Manage & Allocate Recipes", "Manage image, title, timing, calories, macros, recipe details and member allocation.", "Admin content manager")

tabs = st.tabs(["Current Repository", "Add Recipe", "Import CSV", "Edit / Delete", "Member Feedback", "Allocate to Member"])

with tabs[5]:
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
            checked = st.checkbox(f"{row.get('title', 'Untitled Recipe')} · {row.get('prep_time','')} mins", key=key)
            if checked:
                selected.append(rid)

        if st.button("Save Allocation", type="primary", use_container_width=True):
            save_resource_assignments(member_id, "recipes", selected)
            st.session_state[state_key] = set(selected)
            st.success("Recipe allocation saved. Member notification/email has been queued.")

with tabs[0]:
    st.subheader("Current Recipe Repository")
    st.dataframe(load(), use_container_width=True, hide_index=False)

with tabs[1]:
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

with tabs[2]:
    st.subheader("Import Recipe CSV")
    st.caption("CSV can include recipe details and image reference fields. For local images, fill image_file_name_to_upload in the CSV and upload matching image files below.")
    csv_file = st.file_uploader("Choose recipe CSV file", type=["csv"], key="recipe_csv_upload_v96_12")
    uploaded_images = st.file_uploader("Upload recipe images referenced in CSV", type=["jpg", "jpeg", "png", "webp"], accept_multiple_files=True, key="recipe_csv_images_v96_12")
    c_download, c_import = st.columns(2, gap="large")
    with c_download:
        st.download_button("Download CSV Format", data='title,description,meal_type,diet_type,goal_tags,condition_tags,prep_time,calories,protein,fat,carbohydrates,additional_nutrition,servings,portion_size,image_url,image_file_name_to_upload,image_access_type,ingredients,steps,nutrition,status\r\nMoong Dal Chilla,Light protein-rich breakfast option,Breakfast,Vegetarian,weight management;energy,general wellness,15,180,10g,5g,24g,Fibre: 4g; Sodium: 120mg,1,2 chillas,https://example.com/moong-dal-chilla.jpg,moong_dal_chilla.jpg,public,Moong dal; Ginger; Green chilli; Salt,Soak dal; Blend batter; Cook on pan,Balanced breakfast with protein and fibre,active\r\n', file_name="healthyme_recipe_upload_format.csv", mime="text/csv", use_container_width=True)
    with c_import:
        if st.button("Import CSV", type="primary", disabled=csv_file is None, use_container_width=True):
            imported = pd.read_csv(csv_file)
            try:
                imported, upload_count = attach_uploaded_images_to_import(imported, uploaded_images, "recipes")
            except Exception as exc:
                st.error(f"Image upload failed: {exc}")
                st.stop()
            df = pd.concat([load(), ensure_columns(imported)], ignore_index=True)
            save(df)
            st.success(f"CSV imported. {upload_count} image(s) uploaded and linked.")
            st.rerun()

with tabs[3]:
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


with tabs[4]:
    st.subheader("Member Recipe Feedback")
    members = list_members()
    if not members:
        st.info("No members available.")
    else:
        member_options = {f"{m['name']} — {m['email']}": m["id"] for m in members}
        label = st.selectbox("Select member for recipe feedback", list(member_options.keys()), key="recipe_feedback_member_v1003")
        member_id = member_options[label]
        feedback_rows_v1003 = list_resource_feedback(member_id=member_id, resource_type="recipes")
        if feedback_rows_v1003:
            feedback_df_v1003 = pd.DataFrame(feedback_rows_v1003)
            show_cols_v1003 = [c for c in ["title", "status", "rating", "notes", "updated_at"] if c in feedback_df_v1003.columns]
            st.dataframe(feedback_df_v1003[show_cols_v1003], use_container_width=True, hide_index=True)
        else:
            st.caption("No recipe feedback submitted by this member yet.")



# v96_recipe_macros: Protein, Fat, Carbohydrates, Additional nutrition metrics

# v101.8: standard bottom navigation

# v102.0: canonical global footer navigation

# v102.2C: single canonical admin footer
render_page_nav("Manage & Allocate Recipes-1", back_page="pages/10_Admin_Dashboard.py", dashboard_page="pages/10_Admin_Dashboard.py", show_evaluation=False, show_dashboard=True, location="bottom")
render_back_to_top()
