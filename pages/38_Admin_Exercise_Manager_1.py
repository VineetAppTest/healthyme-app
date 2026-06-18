
# v102.2B: parallel page shell
st.markdown("""<style>.hm-v1022b-shell{border:1px solid #E3C98E;background:linear-gradient(180deg,#FFFDF8 0%,#FFF9EC 100%);border-radius:20px;padding:1rem;margin:.75rem 0 1rem 0;box-shadow:0 10px 24px rgba(15,23,42,.05)}.hm-v1022b-title{color:#064E3B;font-size:1.08rem;font-weight:950;margin:0 0 .35rem 0}.hm-v1022b-note{color:#475569;font-size:.86rem;font-weight:720;margin:0}.hm-v1022b-chip{display:inline-flex;padding:.22rem .58rem;border:1px solid #E3C98E;border-radius:999px;background:#FFF7E6;color:#7A5A16;font-size:.76rem;font-weight:850;margin:.45rem .2rem 0 0}</style>
<div class="hm-v1022b-shell">
  <div class="hm-v1022b-title">Admin Exercise-1 parallel UX shell</div>
  <div class="hm-v1022b-note">Admin exercise-library workspace inspired by the new mockup. Existing Exercise Manager remains available as fallback.</div>
  <span class="hm-v1022b-chip">Parallel UX</span><span class="hm-v1022b-chip">Existing data logic retained</span><span class="hm-v1022b-chip">Test safely</span>
</div>
""", unsafe_allow_html=True)
from components.ui_common import render_page_nav, render_back_to_top, inject_recipe_exercise_v1022a_styles

import pathlib
import pandas as pd
import streamlit as st

from components.guards import require_admin
from components.ui_common import inject_global_styles, apply_luxe_theme, topbar, utility_logout_bar, render_back_to_top, render_page_nav
from components.storage_assets import upload_content_image, PUBLIC_BUCKET, PRIVATE_BUCKET
from components.db import list_members, get_resource_assignments, save_resource_assignments, list_resource_feedback

st.set_page_config(page_title="Manage & Allocate Exercises-1", page_icon="💚", layout="wide", initial_sidebar_state="collapsed")
inject_global_styles(); apply_luxe_theme(); require_admin(); utility_logout_bar()
inject_recipe_exercise_v1022a_styles()
st.markdown("""<div class='hm-v1022a-admin-note'>v102.2A restores the v93 allocation-first Recipe/Exercise manager layout while retaining latest image upload, feedback and allocation functionality.</div>""", unsafe_allow_html=True)

PATH = pathlib.Path(__file__).resolve().parents[1] / "data" / "exercises.csv"
EXERCISE_COLUMNS = ['title', 'description', 'category', 'difficulty', 'goal_tags', 'condition_tags', 'duration_or_reps', 'hidden_calories_v96', 'equipment', 'image_url', 'image_bucket', 'image_path', 'image_access_type', 'instructions', 'benefits', 'status']


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

def exercise_form(prefix, row=None):
    row = row or {}
    st.markdown("#### Core display fields")
    c1, c2 = st.columns(2)
    with c1:
        title = st.text_input("Title", value=str(row.get("title", "")), key=f"{prefix}_title")
        category = st.text_input("Category", value=str(row.get("category", "")), key=f"{prefix}_category")
        duration_or_reps = st.text_input("Timing / duration / reps", value=str(row.get("duration_or_reps", "")), key=f"{prefix}_duration")
        hidden_calories_v96 = st.text_input("", value=str(row.get("hidden_calories_v96", "")), key=f"{prefix}_hidden_calories_v96")
    with c2:
        image_url = st.text_input("Manual Image URL / fallback", value=clean_image_value(row.get("image_url", "")), key=f"{prefix}_image_url", help="Optional fallback. Uploaded Supabase image takes priority.")
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
        if is_valid_image_url(uploaded_meta.get("image_url")):
            image_url = uploaded_meta.get("image_url")
            st.image(image_url, caption="Uploaded image preview", use_container_width=True)
        elif is_valid_image_url(image_url):
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
        "hidden_calories_v96": hidden_calories_v96,
        "equipment": equipment,
        "image_url": image_url,
        "image_bucket": image_bucket,
        "image_path": image_path,
        "image_access_type": image_access_type,
        "instructions": instructions,
        "benefits": benefits,
        "status": status,
    }


# v101.6: top page navigation removed; bottom nav remains standard


topbar("Manage & Allocate Exercises-1", "Manage image, title, timing, exercise details and member allocation.", "Admin content manager")

tabs = st.tabs(["Allocate to Member", "Current Repository", "Add Exercise", "Import CSV", "Edit / Delete", "Member Feedback"])

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
            checked = st.checkbox(f"{row.get('title', 'Untitled Exercise')} · {row.get('duration_or_reps','')} · {row.get('hidden_calories_v96','')} cal", key=key)
            if checked:
                selected.append(eid)

        if st.button("Save Allocation", type="primary", use_container_width=True):
            save_resource_assignments(member_id, "exercises", selected)
            st.session_state[state_key] = set(selected)
            st.success("Exercise allocation saved. Member notification/email has been queued.")

with tabs[1]:
    st.subheader("Current Manage & Allocate Exercises-1-1")
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
    st.caption("CSV can include exercise details and image reference fields. For local images, fill image_file_name_to_upload in the CSV and upload matching image files below.")
    csv_file = st.file_uploader("Choose exercise CSV file", type=["csv"], key="exercise_csv_upload_v96_12")
    uploaded_images = st.file_uploader("Upload exercise images referenced in CSV", type=["jpg", "jpeg", "png", "webp"], accept_multiple_files=True, key="exercise_csv_images_v96_12")
    c_download, c_import = st.columns(2, gap="large")
    with c_download:
        st.download_button("Download CSV Format", data='title,description,category,difficulty,duration_or_reps,equipment,image_url,image_file_name_to_upload,image_access_type,instructions,benefits,goal_tags,condition_tags,status\r\nBrisk Walking,Easy cardio starter,Cardio,Beginner,20 min,None,https://example.com/brisk-walking.jpg,brisk_walking.jpg,public,Warm up; Walk briskly; Cool down,Improves stamina; Supports metabolism,cardio;weight management,general wellness,active\r\n', file_name="healthyme_exercise_upload_format.csv", mime="text/csv", use_container_width=True)
    with c_import:
        if st.button("Import CSV", type="primary", disabled=csv_file is None, use_container_width=True):
            imported = pd.read_csv(csv_file)
            try:
                imported, upload_count = attach_uploaded_images_to_import(imported, uploaded_images, "exercises")
            except Exception as exc:
                st.error(f"Image upload failed: {exc}")
                st.stop()
            df = pd.concat([load(), ensure_columns(imported)], ignore_index=True)
            save(df)
            st.success(f"CSV imported. {upload_count} image(s) uploaded and linked.")
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


with tabs[5]:
    st.subheader("Member Exercise Feedback")
    members = list_members()
    if not members:
        st.info("No members available.")
    else:
        member_options = {f"{m['name']} — {m['email']}": m["id"] for m in members}
        label = st.selectbox("Select member for exercise feedback", list(member_options.keys()), key="exercise_feedback_member_v1003")
        member_id = member_options[label]
        feedback_rows_v1003 = list_resource_feedback(member_id=member_id, resource_type="exercises")
        if feedback_rows_v1003:
            feedback_df_v1003 = pd.DataFrame(feedback_rows_v1003)
            show_cols_v1003 = [c for c in ["title", "status", "rating", "notes", "updated_at"] if c in feedback_df_v1003.columns]
            st.dataframe(feedback_df_v1003[show_cols_v1003], use_container_width=True, hide_index=True)
        else:
            st.caption("No exercise feedback submitted by this member yet.")



# v96: Allocation success message required: st.success("Exercise allocated successfully.") after allocation save.

# v96_back_route_note: Edit Back button should return to Manage & Allocate Exercise page.

# v101.8: standard bottom navigation

# v102.0: canonical global footer navigation

# v102.1: single canonical footer navigation only
render_page_nav("Manage & Allocate Exercises-1", back_page="pages/10_Admin_Dashboard.py", dashboard_page="pages/10_Admin_Dashboard.py", show_evaluation=False, show_dashboard=True, location="bottom")
render_back_to_top()

# v102.2A reconciliation marker: v93 UX restored, latest functionality retained.

# v102.2B: single canonical admin footer
render_page_nav("Manage & Allocate Exercises-1-1", back_page="pages/10_Admin_Dashboard.py", dashboard_page="pages/10_Admin_Dashboard.py", show_evaluation=False, show_dashboard=True, location="bottom")
render_back_to_top()
