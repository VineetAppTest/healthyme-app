from __future__ import annotations

import pathlib

import pandas as pd
import streamlit as st

from components.guards import require_admin
from components.storage_assets import upload_content_image
from components.ui_common import (
    apply_luxe_theme,
    inject_global_styles,
    render_back_to_top,
    render_page_nav,
    topbar,
    utility_logout_bar,
)


st.set_page_config(
    page_title="Recipe Repository",
    page_icon="💚",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_global_styles()
apply_luxe_theme()
require_admin()
utility_logout_bar()


PATH = pathlib.Path(__file__).resolve().parents[1] / "data" / "recipes.csv"
RECIPE_COLUMNS = [
    "title",
    "description",
    "meal_type",
    "diet_type",
    "goal_tags",
    "condition_tags",
    "prep_time",
    "calories",
    "protein",
    "fat",
    "carbohydrates",
    "additional_nutrition",
    "servings",
    "portion_size",
    "image_url",
    "image_bucket",
    "image_path",
    "image_access_type",
    "ingredients",
    "steps",
    "nutrition",
    "status",
]


def ensure_columns(df: pd.DataFrame) -> pd.DataFrame:
    output = df.copy()
    for column in RECIPE_COLUMNS:
        if column not in output.columns:
            output[column] = ""
    return output[RECIPE_COLUMNS]


def load() -> pd.DataFrame:
    if not PATH.exists():
        return pd.DataFrame(columns=RECIPE_COLUMNS)
    return ensure_columns(pd.read_csv(PATH))


def save(df: pd.DataFrame) -> None:
    ensure_columns(df).to_csv(PATH, index=False)


def _clean(value) -> str:
    text = str(value or "").strip()
    return "" if text.lower() in {"nan", "none", "null"} else text


def _status(value) -> str:
    return "inactive" if _clean(value).lower() == "inactive" else "active"


def _flash(message: str, level: str = "success") -> None:
    st.session_state["hm_recipe_repository_flash"] = (level, message)


def _show_flash() -> None:
    payload = st.session_state.pop("hm_recipe_repository_flash", None)
    if not payload:
        return
    level, message = payload
    getattr(st, level if level in {"success", "warning", "error", "info"} else "info")(
        message
    )


def is_valid_image_url(value) -> bool:
    value = _clean(value)
    return value.startswith("http://") or value.startswith("https://")


def clean_image_value(value) -> str:
    return _clean(value)


def recipe_form(prefix: str, row=None) -> dict:
    row = row or {}
    st.markdown("#### Core display fields")
    left, right = st.columns(2)
    with left:
        title = st.text_input(
            "Title", value=_clean(row.get("title")), key=f"{prefix}_title"
        )
        meal_type = st.text_input(
            "Meal type",
            value=_clean(row.get("meal_type")),
            key=f"{prefix}_meal_type",
        )
        prep_time = st.text_input(
            "Timing / prep time in minutes",
            value=_clean(row.get("prep_time")),
            key=f"{prefix}_prep_time",
        )
        calories = st.text_input(
            "Calories", value=_clean(row.get("calories")), key=f"{prefix}_calories"
        )
        protein = st.text_input(
            "Protein", value=_clean(row.get("protein")), key=f"{prefix}_protein"
        )
        fat = st.text_input(
            "Fat", value=_clean(row.get("fat")), key=f"{prefix}_fat"
        )
        carbohydrates = st.text_input(
            "Carbohydrates",
            value=_clean(row.get("carbohydrates")),
            key=f"{prefix}_carbohydrates",
        )
    with right:
        image_url = st.text_input(
            "Manual Image URL / fallback",
            value=clean_image_value(row.get("image_url")),
            key=f"{prefix}_image_url",
            help="Optional fallback. Uploaded Supabase image takes priority.",
        )
        image_access_type = st.selectbox(
            "Uploaded image visibility",
            ["public", "private"],
            index=1 if _clean(row.get("image_access_type")).lower() == "private" else 0,
            key=f"{prefix}_image_access_type",
        )
        uploaded_image = st.file_uploader(
            "Upload recipe image",
            type=["jpg", "jpeg", "png", "webp"],
            key=f"{prefix}_image_upload",
        )
        image_bucket = _clean(row.get("image_bucket"))
        image_path = _clean(row.get("image_path"))
        if uploaded_image is not None and st.button(
            "Upload image to Supabase",
            key=f"{prefix}_upload_btn",
            use_container_width=True,
        ):
            try:
                uploaded_meta = upload_content_image(
                    uploaded_image,
                    "recipes",
                    title or "recipe",
                    image_access_type,
                )
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
        diet_type = st.text_input(
            "Diet type", value=_clean(row.get("diet_type")), key=f"{prefix}_diet_type"
        )
        servings = st.text_input(
            "Servings", value=_clean(row.get("servings")), key=f"{prefix}_servings"
        )
        portion_size = st.text_input(
            "Portion size",
            value=_clean(row.get("portion_size")),
            key=f"{prefix}_portion_size",
        )

    description = st.text_area(
        "Short description",
        value=_clean(row.get("description")),
        key=f"{prefix}_description",
    )
    st.markdown("#### Details shown on second page")
    ingredients = st.text_area(
        "Ingredients",
        value=_clean(row.get("ingredients")),
        key=f"{prefix}_ingredients",
        help="Use one line per ingredient or separate with semicolons.",
    )
    steps = st.text_area(
        "Instructions / steps",
        value=_clean(row.get("steps")),
        key=f"{prefix}_steps",
        help="Use one line per instruction or separate with semicolons.",
    )
    nutrition = st.text_area(
        "Nutrition details",
        value=_clean(row.get("nutrition")),
        key=f"{prefix}_nutrition",
    )
    additional_nutrition = st.text_area(
        "Additional nutrition metrics",
        value=_clean(row.get("additional_nutrition")),
        key=f"{prefix}_additional_nutrition",
        placeholder="Example: Fibre: 8g; Sodium: 120mg",
    )
    goal_col, condition_col = st.columns(2)
    with goal_col:
        goal_tags = st.text_input(
            "Goal tags", value=_clean(row.get("goal_tags")), key=f"{prefix}_goal_tags"
        )
    with condition_col:
        condition_tags = st.text_input(
            "Condition tags",
            value=_clean(row.get("condition_tags")),
            key=f"{prefix}_condition_tags",
        )
    status = st.selectbox(
        "Status",
        ["active", "inactive"],
        index=1 if _status(row.get("status")) == "inactive" else 0,
        key=f"{prefix}_status",
    )
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


def _recipe_summary(row) -> str:
    details = [
        _clean(row.get("meal_type")),
        f"{_clean(row.get('prep_time'))} min" if _clean(row.get("prep_time")) else "",
        _clean(row.get("diet_type")),
    ]
    return " · ".join(part for part in details if part) or "No summary details recorded."


def _safe_delete_recipe(df: pd.DataFrame, index: int) -> None:
    # Phase 1 deliberately uses reversible safe deletion. The Recipe Repository still
    # uses CSV row positions as legacy identifiers, so physical deletion or index reset
    # could break existing references. Phase 2 will migrate these rows to durable IDs.
    df.at[index, "status"] = "inactive"
    save(df)


st.markdown(
    """
<style>
.block-container{padding-top:.45rem!important;max-width:1120px!important;}
.hero-shell{margin:.45rem 0 .75rem!important;padding:1rem 1.15rem!important;}
.hm-repo-row{border:1px solid #E3C98E;background:#FFFDF8;border-radius:14px;padding:.72rem .82rem;margin:.42rem 0;}
.hm-repo-title{font-weight:900;color:#064E3B;font-size:.95rem;}
.hm-repo-meta{color:#64748B;font-size:.78rem;margin-top:.12rem;}
</style>
""",
    unsafe_allow_html=True,
)

topbar(
    "Recipe Repository",
    "Create and maintain reusable recipe definitions. Member allocation is managed separately.",
    "Admin content repository",
)
_show_flash()

repository_tab, add_tab = st.tabs(["Current Repository", "Add Recipe"])

with repository_tab:
    df = load()
    if df.empty:
        st.info("No recipes are available. Add the first recipe.")
    else:
        active_df = df[df["status"].map(_status).eq("active")]
        inactive_df = df[df["status"].map(_status).eq("inactive")]

        if active_df.empty:
            st.info("No active recipes are available.")
        for index, row in active_df.iterrows():
            st.markdown(
                f"<div class='hm-repo-row'><div class='hm-repo-title'>{_clean(row.get('title')) or 'Untitled Recipe'}</div>"
                f"<div class='hm-repo-meta'>{_recipe_summary(row)}</div></div>",
                unsafe_allow_html=True,
            )
            edit_col, delete_col = st.columns([1, 1])
            with edit_col:
                if st.button(
                    "Edit",
                    key=f"recipe_repo_edit_{index}",
                    use_container_width=True,
                ):
                    st.session_state["hm_recipe_repository_edit_index"] = int(index)
                    st.session_state.pop("hm_recipe_repository_delete_index", None)
                    st.rerun()
            with delete_col:
                if st.button(
                    "Delete",
                    key=f"recipe_repo_delete_{index}",
                    use_container_width=True,
                ):
                    st.session_state["hm_recipe_repository_delete_index"] = int(index)
                    st.session_state.pop("hm_recipe_repository_edit_index", None)
                    st.rerun()

            if st.session_state.get("hm_recipe_repository_edit_index") == int(index):
                with st.expander("Edit recipe", expanded=True):
                    edited = recipe_form(f"recipe_repo_edit_form_{index}", row.to_dict())
                    save_col, cancel_col = st.columns(2)
                    with save_col:
                        if st.button(
                            "Save Changes",
                            key=f"recipe_repo_save_{index}",
                            type="primary",
                            use_container_width=True,
                        ):
                            if not _clean(edited.get("title")):
                                st.error("Recipe title is required.")
                            else:
                                for column in RECIPE_COLUMNS:
                                    df.at[index, column] = edited.get(column, "")
                                save(df)
                                st.session_state.pop(
                                    "hm_recipe_repository_edit_index", None
                                )
                                _flash("Recipe updated.")
                                st.rerun()
                    with cancel_col:
                        if st.button(
                            "Cancel",
                            key=f"recipe_repo_cancel_{index}",
                            use_container_width=True,
                        ):
                            st.session_state.pop(
                                "hm_recipe_repository_edit_index", None
                            )
                            st.rerun()

            if st.session_state.get("hm_recipe_repository_delete_index") == int(index):
                st.warning(
                    "Delete removes this recipe from future selection. Existing and historical member plans remain protected."
                )
                confirm_col, cancel_col = st.columns(2)
                with confirm_col:
                    if st.button(
                        "Confirm Delete",
                        key=f"recipe_repo_confirm_delete_{index}",
                        type="primary",
                        use_container_width=True,
                    ):
                        _safe_delete_recipe(df, int(index))
                        st.session_state.pop(
                            "hm_recipe_repository_delete_index", None
                        )
                        _flash(
                            "Recipe removed from the active repository. Historical references were retained."
                        )
                        st.rerun()
                with cancel_col:
                    if st.button(
                        "Cancel",
                        key=f"recipe_repo_cancel_delete_{index}",
                        use_container_width=True,
                    ):
                        st.session_state.pop(
                            "hm_recipe_repository_delete_index", None
                        )
                        st.rerun()

        with st.expander(f"Inactive Repository Items ({len(inactive_df)})"):
            if inactive_df.empty:
                st.caption("No inactive repository items.")
            for index, row in inactive_df.iterrows():
                label_col, action_col = st.columns([4, 1])
                with label_col:
                    st.markdown(
                        f"**{_clean(row.get('title')) or 'Untitled Recipe'}**  \n{_recipe_summary(row)}"
                    )
                with action_col:
                    if st.button(
                        "Reactivate",
                        key=f"recipe_repo_reactivate_{index}",
                        use_container_width=True,
                    ):
                        df.at[index, "status"] = "active"
                        save(df)
                        _flash("Recipe reactivated.")
                        st.rerun()

with add_tab:
    st.subheader("Add Recipe")
    values = recipe_form("new_recipe_repository")
    if st.button("Save Recipe", type="primary", use_container_width=True):
        if not _clean(values.get("title")):
            st.error("Recipe title is required.")
        else:
            df = load()
            df.loc[len(df)] = [values.get(column, "") for column in RECIPE_COLUMNS]
            save(df)
            _flash("Recipe saved.")
            st.rerun()

render_page_nav(
    "Recipe Repository",
    back_page="pages/10_Admin_Dashboard.py",
    dashboard_page="pages/10_Admin_Dashboard.py",
    show_evaluation=False,
    show_dashboard=True,
    location="bottom",
)
render_back_to_top()

# Hidden for Phase 1: Import CSV and Member Feedback.
# Removed from this repository page: direct member allocation and the separate Edit/Delete workspace.
