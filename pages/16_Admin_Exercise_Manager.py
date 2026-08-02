from components.ui_common import render_page_nav, render_back_to_top

import pandas as pd
import streamlit as st

from components.guards import require_admin
from components.ui_common import (
    inject_global_styles,
    apply_luxe_theme,
    topbar,
    utility_logout_bar,
    render_back_to_top,
    render_page_nav,
)
from components.storage_assets import upload_content_image
from components.db import (
    list_members,
    get_resource_assignments,
    save_resource_assignments,
    list_resource_feedback,
)
from components.exercise_repository import (
    EXERCISE_COLUMNS,
    add_exercise_repository_item,
    delete_exercise_repository_item,
    import_exercise_repository_items,
    list_exercise_repository,
    update_exercise_repository_item,
)


st.set_page_config(
    page_title="Manage & Allocate Exercises",
    page_icon="💚",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_global_styles()
apply_luxe_theme()
require_admin()
utility_logout_bar()


def _actor_id():
    return (
        st.session_state.get("user_id")
        or st.session_state.get("oidc_email")
        or "admin"
    )


def repository_dataframe(rows):
    display_rows = []
    for row in rows or []:
        display_rows.append(
            {
                "id": str(row.get("id", "")),
                **{column: row.get(column, "") for column in EXERCISE_COLUMNS},
            }
        )
    return pd.DataFrame(display_rows, columns=["id"] + EXERCISE_COLUMNS)


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
    image_map = {getattr(file, "name", ""): file for file in uploaded_images}
    upload_count = 0
    if "image_file_name_to_upload" not in imported.columns:
        return imported, upload_count
    for idx, row in imported.iterrows():
        file_name = str(row.get("image_file_name_to_upload", "") or "").strip()
        if not file_name or file_name not in image_map:
            continue
        access_type = str(
            row.get("image_access_type", "public") or "public"
        ).strip().lower()
        title = str(row.get("title", module_name) or module_name)
        meta = upload_content_image(
            image_map[file_name], module_name, title, access_type
        )
        for key in ["image_url", "image_bucket", "image_path", "image_access_type"]:
            imported.at[idx, key] = meta.get(key, "")
        upload_count += 1
    return imported, upload_count


def exercise_form(prefix, row=None):
    row = row or {}
    st.markdown("#### Core display fields")
    c1, c2 = st.columns(2)
    with c1:
        title = st.text_input(
            "Title", value=str(row.get("title", "")), key=f"{prefix}_title"
        )
        category = st.text_input(
            "Category", value=str(row.get("category", "")), key=f"{prefix}_category"
        )
        duration_or_reps = st.text_input(
            "Timing / duration / reps",
            value=str(row.get("duration_or_reps", "")),
            key=f"{prefix}_duration",
        )
        hidden_calories_v96 = st.text_input(
            "",
            value=str(row.get("hidden_calories_v96", "")),
            key=f"{prefix}_hidden_calories_v96",
        )
    with c2:
        image_url = st.text_input(
            "Manual Image URL / fallback",
            value=clean_image_value(row.get("image_url", "")),
            key=f"{prefix}_image_url",
            help="Optional fallback. Uploaded Supabase image takes priority.",
        )
        image_access_type = st.selectbox(
            "Uploaded image visibility",
            ["public", "private"],
            index=(
                1
                if str(row.get("image_access_type", "public")).lower() == "private"
                else 0
            ),
            key=f"{prefix}_image_access_type",
            help="Exercise images usually remain public, but private is available if required.",
        )
        uploaded_image = st.file_uploader(
            "Upload exercise image",
            type=["jpg", "jpeg", "png", "webp"],
            key=f"{prefix}_image_upload",
        )
        image_bucket = str(row.get("image_bucket", ""))
        image_path = str(row.get("image_path", ""))
        if uploaded_image is not None:
            if st.button(
                "Upload image to Supabase",
                key=f"{prefix}_upload_btn",
                use_container_width=True,
            ):
                try:
                    uploaded_meta = upload_content_image(
                        uploaded_image,
                        "exercises",
                        title or "exercise",
                        image_access_type,
                    )
                    st.session_state[f"{prefix}_uploaded_image_meta"] = uploaded_meta
                    st.success("Image uploaded and ready to save with this exercise.")
                except Exception as exc:
                    st.error(f"Image upload failed: {exc}")
        uploaded_meta = st.session_state.get(f"{prefix}_uploaded_image_meta", {})
        image_bucket = uploaded_meta.get("image_bucket", image_bucket)
        image_path = uploaded_meta.get("image_path", image_path)
        if is_valid_image_url(uploaded_meta.get("image_url")):
            image_url = uploaded_meta.get("image_url")
            st.image(
                image_url,
                caption="Uploaded image preview",
                use_container_width=True,
            )
        elif is_valid_image_url(image_url):
            st.image(
                image_url,
                caption="Current image preview",
                use_container_width=True,
            )
        difficulty = st.text_input(
            "Difficulty",
            value=str(row.get("difficulty", "")),
            key=f"{prefix}_difficulty",
        )
        equipment = st.text_input(
            "Equipment",
            value=str(row.get("equipment", "")),
            key=f"{prefix}_equipment",
        )
        status = st.selectbox(
            "Status",
            ["active", "inactive"],
            index=(
                0
                if str(row.get("status", "active")).lower() != "inactive"
                else 1
            ),
            key=f"{prefix}_status",
        )

    description = st.text_area(
        "Short description",
        value=str(row.get("description", "")),
        key=f"{prefix}_description",
    )
    st.markdown("#### Details shown on second page")
    instructions = st.text_area(
        "Instructions",
        value=str(row.get("instructions", "")),
        key=f"{prefix}_instructions",
        help="Use one line per instruction or separate with semicolons.",
    )
    benefits = st.text_area(
        "Benefits",
        value=str(row.get("benefits", "")),
        key=f"{prefix}_benefits",
    )
    c3, c4 = st.columns(2)
    with c3:
        goal_tags = st.text_input(
            "Goal tags",
            value=str(row.get("goal_tags", "")),
            key=f"{prefix}_goal_tags",
        )
    with c4:
        condition_tags = st.text_input(
            "Condition tags",
            value=str(row.get("condition_tags", "")),
            key=f"{prefix}_condition_tags",
        )
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

topbar(
    "Manage & Allocate Exercises",
    "Manage image, title, timing, exercise details and member allocation.",
    "Admin content manager",
)

tabs = st.tabs(
    [
        "Current Repository",
        "Add Exercise",
        "Import CSV",
        "Edit / Delete",
        "Member Feedback",
        "Allocate to Member",
    ]
)

# One fresh Supabase-backed read supplies every visible/hidden section on this rerun.
repository_rows = list_exercise_repository(active_only=False)
active_rows = [row for row in repository_rows if row.get("status") == "active"]

with tabs[5]:
    st.subheader("Allocate Exercises to Member")
    members = list_members()
    if not members:
        st.info("No members available.")
    elif not active_rows:
        st.info("No active exercises available. Add or import exercises first.")
    else:
        member_options = {
            f"{member['name']} — {member['email']}": member["id"]
            for member in members
        }
        label = st.selectbox(
            "Select member",
            list(member_options.keys()),
            key="exercise_alloc_member_v93",
        )
        member_id = member_options[label]
        all_ids = [str(row.get("id")) for row in active_rows]
        current = set(get_resource_assignments(member_id, "exercises"))
        state_key = f"exercise_alloc_state_{member_id}"
        if state_key not in st.session_state:
            st.session_state[state_key] = set(current)

        c1, c2 = st.columns(2)
        with c1:
            if st.button("Select All Exercises", use_container_width=True):
                st.session_state[state_key] = set(all_ids)
                for exercise_id in all_ids:
                    st.session_state[
                        f"exercise_alloc_{member_id}_{exercise_id}"
                    ] = True
                st.rerun()
        with c2:
            if st.button("Deselect All Exercises", use_container_width=True):
                st.session_state[state_key] = set()
                for exercise_id in all_ids:
                    st.session_state[
                        f"exercise_alloc_{member_id}_{exercise_id}"
                    ] = False
                st.rerun()

        selected = []
        st.markdown("#### Available exercises")
        for row in active_rows:
            exercise_id = str(row.get("id"))
            key = f"exercise_alloc_{member_id}_{exercise_id}"
            if key not in st.session_state:
                st.session_state[key] = exercise_id in st.session_state[state_key]
            checked = st.checkbox(
                f"{row.get('title', 'Untitled Exercise')} · "
                f"{row.get('duration_or_reps', '')} · "
                f"{row.get('hidden_calories_v96', '')} cal",
                key=key,
            )
            if checked:
                selected.append(exercise_id)

        if st.button("Save Allocation", type="primary", use_container_width=True):
            save_resource_assignments(member_id, "exercises", selected)
            st.session_state[state_key] = set(selected)
            st.success(
                "Exercise allocation saved. Member notification/email has been queued."
            )

with tabs[0]:
    st.subheader("Current Exercise Repository")
    if repository_rows:
        st.dataframe(
            repository_dataframe(repository_rows),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No exercises available.")

with tabs[1]:
    st.subheader("Add New Exercise")
    values = exercise_form("new_exercise_v93")
    if st.button("Save Exercise", type="primary", use_container_width=True):
        try:
            add_exercise_repository_item(values, actor_id=_actor_id())
            st.success("Exercise saved.")
            st.rerun()
        except Exception as exc:
            st.error(str(exc))

with tabs[2]:
    st.subheader("Import Exercise CSV")
    st.caption(
        "CSV can include exercise details and image reference fields. For local images, "
        "fill image_file_name_to_upload in the CSV and upload matching image files below."
    )
    csv_file = st.file_uploader(
        "Choose exercise CSV file",
        type=["csv"],
        key="exercise_csv_upload_v96_12",
    )
    uploaded_images = st.file_uploader(
        "Upload exercise images referenced in CSV",
        type=["jpg", "jpeg", "png", "webp"],
        accept_multiple_files=True,
        key="exercise_csv_images_v96_12",
    )
    c_download, c_import = st.columns(2, gap="large")
    with c_download:
        st.download_button(
            "Download CSV Format",
            data=(
                "title,description,category,difficulty,duration_or_reps,equipment,"
                "image_url,image_file_name_to_upload,image_access_type,instructions,"
                "benefits,goal_tags,condition_tags,status\r\n"
                "Brisk Walking,Easy cardio starter,Cardio,Beginner,20 min,None,"
                "https://example.com/brisk-walking.jpg,brisk_walking.jpg,public,"
                "Warm up; Walk briskly; Cool down,Improves stamina; Supports metabolism,"
                "cardio;weight management,general wellness,active\r\n"
            ),
            file_name="healthyme_exercise_upload_format.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with c_import:
        if st.button(
            "Import CSV",
            type="primary",
            disabled=csv_file is None,
            use_container_width=True,
        ):
            try:
                imported = pd.read_csv(csv_file)
                imported, upload_count = attach_uploaded_images_to_import(
                    imported, uploaded_images, "exercises"
                )
                result = import_exercise_repository_items(
                    imported.to_dict(orient="records"), actor_id=_actor_id()
                )
                st.success(
                    f"CSV imported. {result['imported']} exercise(s) added, "
                    f"{result['skipped']} duplicate/blank row(s) skipped, and "
                    f"{upload_count} image(s) uploaded and linked."
                )
                st.rerun()
            except Exception as exc:
                st.error(f"CSV import failed: {exc}")

with tabs[3]:
    st.subheader("Edit or Delete Exercise")
    if not repository_rows:
        st.info("No exercises available.")
    else:
        option_map = {
            f"{row.get('id')} — {str(row.get('title', 'Untitled'))[:55]}": row
            for row in repository_rows
        }
        selected_label = st.selectbox("Select exercise", list(option_map.keys()))
        row = dict(option_map[selected_label])
        exercise_id = str(row.get("id"))
        edited = exercise_form(f"edit_exercise_v93_{exercise_id}", row)
        b1, b2 = st.columns(2)
        with b1:
            if st.button("Update Exercise", type="primary", use_container_width=True):
                try:
                    update_exercise_repository_item(
                        exercise_id, edited, actor_id=_actor_id()
                    )
                    st.success("Exercise updated.")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))
        with b2:
            confirm = st.checkbox("Confirm delete selected exercise")
            if st.button(
                "Delete Exercise",
                disabled=not confirm,
                use_container_width=True,
            ):
                try:
                    delete_exercise_repository_item(
                        exercise_id, actor_id=_actor_id()
                    )
                    st.success("Exercise deleted.")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))

with tabs[4]:
    st.subheader("Member Exercise Feedback")
    members = list_members()
    if not members:
        st.info("No members available.")
    else:
        member_options = {
            f"{member['name']} — {member['email']}": member["id"]
            for member in members
        }
        label = st.selectbox(
            "Select member for exercise feedback",
            list(member_options.keys()),
            key="exercise_feedback_member_v1003",
        )
        member_id = member_options[label]
        feedback_rows_v1003 = list_resource_feedback(
            member_id=member_id, resource_type="exercises"
        )
        if feedback_rows_v1003:
            feedback_df_v1003 = pd.DataFrame(feedback_rows_v1003)
            show_cols_v1003 = [
                column
                for column in ["title", "status", "rating", "notes", "updated_at"]
                if column in feedback_df_v1003.columns
            ]
            st.dataframe(
                feedback_df_v1003[show_cols_v1003],
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.caption("No exercise feedback submitted by this member yet.")


# v96: Allocation success message required after allocation save.
# v96_back_route_note: Edit Back button returns to Manage & Allocate Exercise page.
# v101.8: standard bottom navigation
# v102.0: canonical global footer navigation
# v102.1: single canonical footer navigation only
render_page_nav(
    "Manage & Allocate Exercises",
    back_page="pages/10_Admin_Dashboard.py",
    dashboard_page="pages/10_Admin_Dashboard.py",
    show_evaluation=False,
    show_dashboard=True,
    location="bottom",
)
render_back_to_top()
