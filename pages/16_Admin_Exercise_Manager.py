
import pathlib
import pandas as pd
import streamlit as st

from components.guards import require_admin
from components.ui_common import inject_global_styles, apply_luxe_theme, topbar, utility_logout_bar, render_back_to_top, render_page_nav
from components.storage_assets import upload_content_image, PUBLIC_BUCKET, PRIVATE_BUCKET
from components.db import list_members, get_resource_assignments, save_resource_assignments

st.set_page_config(page_title="Manage & Allocate Exercises", page_icon="💚", layout="wide", initial_sidebar_state="collapsed")
inject_global_styles(); apply_luxe_theme(); require_admin(); utility_logout_bar(); render_back_to_top()

PATH = pathlib.Path(__file__).resolve().parents[1] / "data" / "exercises.csv"
EXERCISE_COLUMNS = ['title', 'description', 'category', 'difficulty', 'goal_tags', 'condition_tags', 'duration_or_reps', 'calories', 'equipment', 'image_url', 'image_bucket', 'image_path', 'image_access_type', 'instructions', 'benefits', 'status']


def ensure_columns(df):
    for c in EXERCISE_COLUMNS:
        if c not in df.columns:
            df[c] = ""
    return df[EXERCISE_COLUMNS]


def load():
    if not PATH.exists():
        return pd.DataFrame(columns=EXERCISE_COLUMNS)
    return ensure_columns(pd.read_csv(PATH))


def save(df):
    ensure_columns(df).to_csv(PATH, index=False)


def exercise_form(prefix, row=None):
    row = row or {}
    st.markdown("#### Core display fields")
    c1, c2 = st.columns(2)
    with c1:
        title = st.text_input("Title", value=str(row.get("title", "")), key=f"{prefix}_title")
        category = st.text_input("Category", value=str(row.get("category", "")), key=f"{prefix}_category")
        duration_or_reps = st.text_input("Timing / duration / reps", value=str(row.get("duration_or_reps", "")), key=f"{prefix}_duration")
        calories = st.text_input("Calories", value=str(row.get("calories", "")), key=f"{prefix}_calories")
    with c2:
        image_url = st.text_input("Manual Image URL / fallback", value=str(row.get("image_url", "")), key=f"{prefix}_image_url", help="Optional fallback. Uploaded Supabase image takes priority.")
        image_access_type = st.selectbox(
            "Uploaded image visibility",
            ["public", "private"],
            index=1 if str(row.get("image_access_type", "public")).lower() == "private" else 0,
            key=f"{prefix}_image_access_type",
            help="Exercise images usually remain public, but private is available if required.",
        )
        uploaded_image = st.file_uploader("Upload exercise image", type=["jpg", "jpeg", "png", "webp"], key=f"{prefix}_image_upload")
        image_bucket = str(row.get("image_bucket", ""))
        image_path = str(row.get("image_path", ""))
        if uploaded_image is not None:
            if st.button("Upload image to Supabase", key=f"{prefix}_upload_btn", use_container_width=True):
                try:
                    uploaded_meta = upload_content_image(uploaded_image, "exercises", title or "exercise", image_access_type)
                    st.session_state[f"{prefix}_uploaded_image_meta"] = uploaded_meta
                    st.success("Image uploaded and ready to save with this exercise.")
                except Exception as exc:
                    st.error(f"Image upload failed: {exc}")
        uploaded_meta = st.session_state.get(f"{prefix}_uploaded_image_meta", {})
        image_bucket = uploaded_meta.get("image_bucket", image_bucket)
        image_path = uploaded_meta.get("image_path", image_path)
        if uploaded_meta.get("image_url"):
            image_url = uploaded_meta.get("image_url")
            st.image(image_url, caption="Uploaded image preview", use_container_width=True)
        elif image_url:
            st.image(image_url, caption="Current image preview", use_container_width=True)
        difficulty = st.text_input("Difficulty", value=str(row.get("difficulty", "")), key=f"{prefix}_difficulty")
        equipment = st.text_input("Equipment", value=str(row.get("equipment", "")), key=f"{prefix}_equipment")
        status = st.selectbox("Status", ["active", "inactive"], index=0 if str(row.get("status", "active")) != "inactive" else 1, key=f"{prefix}_status")

    description = st.text_area("Short description", value=str(row.get("description", "")), key=f"{prefix}_description")
    st.markdown("#### Details shown on second page")
    instructions = st.text_area("Instructions", value=str(row.get("instructions", "")), key=f"{prefix}_instructions", help="Use one line per instruction or separate with semicolons.")
    benefits = st.text_area("Benefits", value=str(row.get("benefits", "")), key=f"{prefix}_benefits")
    c3, c4 = st.columns(2)
    with c3:
        goal_tags = st.text_input("Goal tags", value=str(row.get("goal_tags", "")), key=f"{prefix}_goal_tags")
    with c4:
        condition_tags = st.text_input("Condition tags", value=str(row.get("condition_tags", "")), key=f"{prefix}_condition_tags")
    return {
        "title": title,
        "description": description,
        "category": category,
        "difficulty": difficulty,
        "goal_tags": goal_tags,
        "condition_tags": condition_tags,
        "duration_or_reps": duration_or_reps,
        "calories": calories,
        "equipment": equipment,
        "image_url": image_url,
        "image_bucket": image_bucket,
        "image_path": image_path,
        "image_access_type": image_access_type,
        "instructions": instructions,
        "benefits": benefits,
        "status": status,
    }


render_page_nav("Exercises", back_page="pages/10_Admin_Dashboard.py", show_evaluation=False, location="top")
topbar("Manage & Allocate Exercises", "Manage image, title, timing, calories, exercise details and member allocation.", "Admin content manager")

tabs = st.tabs(["Allocate to Member", "Current Repository", "Add Exercise", "Import CSV", "Edit / Delete"])

with tabs[0]:
    st.subheader("Allocate Exercises to Member")
    members = list_members()
    df = load()
    active_df = df[df["status"].fillna("active").astype(str).str.lower().eq("active")].copy()
    if not members:
        st.info("No members available.")
    elif active_df.empty:
        st.info("No active exercises available. Add or import exercises first.")
    else:
        member_options = {f"{m['name']} — {m['email']}": m["id"] for m in members}
        label = st.selectbox("Select member", list(member_options.keys()), key="exercise_alloc_member_v93")
        member_id = member_options[label]
        all_ids = [str(i) for i in active_df.index.tolist()]
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
        for idx, row in active_df.iterrows():
            eid = str(idx)
            key = f"exercise_alloc_{member_id}_{eid}"
            if key not in st.session_state:
                st.session_state[key] = eid in st.session_state[state_key]
            checked = st.checkbox(f"{row.get('title', 'Untitled Exercise')} · {row.get('duration_or_reps','')} · {row.get('calories','')} cal", key=key)
            if checked:
                selected.append(eid)

        if st.button("Save Allocation", type="primary", use_container_width=True):
            save_resource_assignments(member_id, "exercises", selected)
            st.session_state[state_key] = set(selected)
            st.success("Exercise allocation saved. Member notification/email has been queued.")

with tabs[1]:
    st.subheader("Current Exercise Repository")
    st.dataframe(load(), use_container_width=True, hide_index=False)

with tabs[2]:
    st.subheader("Add New Exercise")
    values = exercise_form("new_exercise_v93")
    if st.button("Save Exercise", type="primary", use_container_width=True):
        if not values["title"].strip():
            st.error("Exercise title is required.")
        else:
            df = load()
            df.loc[len(df)] = [values.get(c, "") for c in EXERCISE_COLUMNS]
            save(df)
            st.success("Exercise saved.")
            st.rerun()

with tabs[3]:
    st.subheader("Import Exercise CSV")
    st.markdown("CSV can include image_url, image_bucket, image_path, image_access_type, title, duration_or_reps, calories, equipment, instructions and benefits. Missing columns will be added.")
    csv_file = st.file_uploader("Choose exercise CSV file", type=["csv"], key="exercise_csv_upload_v93")
    if st.button("Import CSV", type="primary", disabled=csv_file is None, use_container_width=True):
        imported = pd.read_csv(csv_file)
        df = pd.concat([load(), ensure_columns(imported)], ignore_index=True)
        save(df)
        st.success("CSV imported.")
        st.rerun()

with tabs[4]:
    st.subheader("Edit or Delete Exercise")
    df = load()
    if df.empty:
        st.info("No exercises available.")
    else:
        options = [f"{idx} — {str(row.get('title','Untitled'))[:55]}" for idx, row in df.iterrows()]
        selected = st.selectbox("Select exercise", options)
        idx = int(selected.split(" — ")[0])
        row = df.loc[idx].to_dict()
        edited = exercise_form(f"edit_exercise_v93_{idx}", row)
        b1, b2 = st.columns(2)
        with b1:
            if st.button("Update Exercise", type="primary", use_container_width=True):
                for c in EXERCISE_COLUMNS:
                    df.at[idx, c] = edited.get(c, "")
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
