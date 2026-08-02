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
    st.markdown("#### Core details")
    title_col, meal_col, diet_col = st.columns([1.4, 1, 1], gap="small")
    with title_col:
        title = st.text_input(
            "Title", value=_clean(row.get("title")), key=f"{prefix}_title"
        )
    with meal_col:
        meal_type = st.text_input(
            "Meal type",
            value=_clean(row.get("meal_type")),
            key=f"{prefix}_meal_type",
        )
    with diet_col:
        diet_type = st.text_input(
            "Diet type", value=_clean(row.get("diet_type")), key=f"{prefix}_diet_type"
        )

    prep_col, servings_col, portion_col, status_col = st.columns(4, gap="small")
    with prep_col:
        prep_time = st.text_input(
            "Prep time (minutes)",
            value=_clean(row.get("prep_time")),
            key=f"{prefix}_prep_time",
        )
    with servings_col:
        servings = st.text_input(
            "Servings", value=_clean(row.get("servings")), key=f"{prefix}_servings"
        )
    with portion_col:
        portion_size = st.text_input(
            "Portion size",
            value=_clean(row.get("portion_size")),
            key=f"{prefix}_portion_size",
        )
    with status_col:
        status = st.selectbox(
            "Status",
            ["active", "inactive"],
            index=1 if _status(row.get("status")) == "inactive" else 0,
            key=f"{prefix}_status",
        )

    description = st.text_area(
        "Short description",
        value=_clean(row.get("description")),
        key=f"{prefix}_description",
    )

    st.markdown("#### Nutrition")
    calories_col, protein_col, fat_col, carbs_col = st.columns(4, gap="small")
    with calories_col:
        calories = st.text_input(
            "Calories", value=_clean(row.get("calories")), key=f"{prefix}_calories"
        )
    with protein_col:
        protein = st.text_input(
            "Protein", value=_clean(row.get("protein")), key=f"{prefix}_protein"
        )
    with fat_col:
        fat = st.text_input(
            "Fat", value=_clean(row.get("fat")), key=f"{prefix}_fat"
        )
    with carbs_col:
        carbohydrates = st.text_input(
            "Carbohydrates",
            value=_clean(row.get("carbohydrates")),
            key=f"{prefix}_carbohydrates",
        )
    nutrition_col, additional_col = st.columns(2, gap="small")
    with nutrition_col:
        nutrition = st.text_area(
            "Nutrition details",
            value=_clean(row.get("nutrition")),
            key=f"{prefix}_nutrition",
        )
    with additional_col:
        additional_nutrition = st.text_area(
            "Additional nutrition metrics",
            value=_clean(row.get("additional_nutrition")),
            key=f"{prefix}_additional_nutrition",
            placeholder="Example: Fibre: 8g; Sodium: 120mg",
        )

    st.markdown("#### Preparation")
    ingredients_col, steps_col = st.columns(2, gap="small")
    with ingredients_col:
        ingredients = st.text_area(
            "Ingredients",
            value=_clean(row.get("ingredients")),
            key=f"{prefix}_ingredients",
            help="Use one line per ingredient or separate with semicolons.",
        )
    with steps_col:
        steps = st.text_area(
            "Instructions / steps",
            value=_clean(row.get("steps")),
            key=f"{prefix}_steps",
            help="Use one line per instruction or separate with semicolons.",
        )

    goal_col, condition_col = st.columns(2, gap="small")
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

    st.markdown("#### Image")
    image_left, image_right = st.columns([1.35, 1], gap="small")
    with image_left:
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
    with image_right:
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
.hm-repo-row{border:1px solid #E3C98E;background:#FFFDF8;border-radius:14px;padding:.66rem .78rem;margin:.34rem 0;}
.hm-repo-title{font-weight:900;color:#064E3B;font-size:.92rem;line-height:1.2;}
.hm-repo-meta{color:#64748B;font-size:.75rem;margin-top:.1rem;line-height:1.3;}
div[data-testid="stButton"]>button{min-height:2rem!important;padding:.24rem .58rem!important;border-radius:999px!important;font-size:.76rem!important;font-weight:850!important;white-space:nowrap!important;}
div[data-testid="stExpander"] details{border:1px solid #E3C98E!important;border-radius:14px!important;background:#FFFDF8!important;overflow:hidden!important;}
div[data-testid="stExpander"] summary{padding:.48rem .68rem!important;min-height:2.15rem!important;color:#064E3B!important;font-size:.82rem!important;font-weight:900!important;align-items:center!important;}
div[data-testid="stExpander"] summary svg{display:none!important;}
div[data-testid="stExpander"] summary:before{content:"+";display:inline-flex;align-items:center;justify-content:center;width:1.25rem;height:1.25rem;border-radius:999px;background:#DDF7F3;color:#006D6F;font-weight:950;margin-right:.42rem;flex:0 0 auto;}
div[data-testid="stExpander"] details[open] summary:before{content:"−";}
div[data-testid="stExpander"] summary p{white-space:nowrap!important;overflow:hidden!important;text-overflow:ellipsis!important;}
div[data-testid="stExpander"] details[open]>div{padding:.25rem .7rem .72rem!important;}
div[data-testid="stExpander"] div[data-testid="stVerticalBlock"]{gap:.38rem!important;}
div[data-testid="stExpander"] textarea{min-height:68px!important;}
div[data-testid="stExpander"] h4{font-size:.82rem!important;margin:.2rem 0!important;color:#064E3B!important;}
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
            details_col, edit_col, delete_col = st.columns([5.8, 0.72, 0.82], gap="small")
            with details_col:
                st.markdown(
                    f"<div class='hm-repo-row'><div class='hm-repo-title'>{_clean(row.get('title')) or 'Untitled Recipe'}</div>"
                    f"<div class='hm-repo-meta'>{_recipe_summary(row)}</div></div>",
                    unsafe_allow_html=True,
                )
            with edit_col:
                if st.button(
                    "Edit",
                    key=f"recipe_repo_edit_{index}",
                    use_container_width=True,
                ):
                    current = st.session_state.get("hm_recipe_repository_edit_index")
                    st.session_state["hm_recipe_repository_edit_index"] = (
                        None if current == int(index) else int(index)
                    )
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
                title = _clean(row.get("title")) or "Untitled Recipe"
                with st.expander(f"Edit Recipe · {title}", expanded=True):
                    edited = recipe_form(f"recipe_repo_edit_form_{index}", row.to_dict())
                    save_col, cancel_col, spacer = st.columns([1, 1, 3], gap="small")
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
                            "Close",
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
                confirm_col, cancel_col, spacer = st.columns([1.15, 0.8, 3], gap="small")
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
                label_col, action_col = st.columns([5.5, 1], gap="small")
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
