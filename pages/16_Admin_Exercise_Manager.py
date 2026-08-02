from __future__ import annotations

import streamlit as st

from components.exercise_repository import (
    add_exercise_repository_item,
    list_exercise_repository,
    set_exercise_repository_status,
    update_exercise_repository_item,
)
from components.guards import require_admin
from components.storage_assets import upload_content_image
from components.repository_page_ui import (
    inject_repository_page_ui,
    render_repository_disclosure,
    repository_form_panel,
    repository_inactive_panel,
)
from components.ui_common import (
    apply_luxe_theme,
    inject_global_styles,
    render_back_to_top,
    render_page_nav,
    topbar,
    utility_logout_bar,
)


st.set_page_config(
    page_title="Exercise Repository",
    page_icon="💚",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_global_styles()
apply_luxe_theme()
require_admin()
utility_logout_bar()
inject_repository_page_ui()


def _actor_id() -> str:
    return (
        st.session_state.get("user_id")
        or st.session_state.get("oidc_email")
        or "admin"
    )


def _clean(value) -> str:
    text = str(value or "").strip()
    return "" if text.lower() in {"nan", "none", "null"} else text


def _flash(message: str, level: str = "success") -> None:
    st.session_state["hm_exercise_repository_flash"] = (level, message)


def _show_flash() -> None:
    payload = st.session_state.pop("hm_exercise_repository_flash", None)
    if not payload:
        return
    level, message = payload
    getattr(st, level if level in {"success", "warning", "error", "info"} else "info")(
        message
    )


def is_valid_image_url(value) -> bool:
    value = _clean(value)
    return value.startswith("http://") or value.startswith("https://")


def exercise_form(prefix: str, row=None) -> dict:
    row = row or {}
    st.markdown("#### Core Fields")
    left, right = st.columns(2, gap="small")
    with left:
        title = st.text_input(
            "Title", value=_clean(row.get("title")), key=f"{prefix}_title"
        )
        category = st.text_input(
            "Category", value=_clean(row.get("category")), key=f"{prefix}_category"
        )
        duration_or_reps = st.text_input(
            "Timing / duration / reps",
            value=_clean(row.get("duration_or_reps")),
            key=f"{prefix}_duration",
        )
    with right:
        difficulty = st.text_input(
            "Difficulty",
            value=_clean(row.get("difficulty")),
            key=f"{prefix}_difficulty",
        )
        equipment = st.text_input(
            "Equipment",
            value=_clean(row.get("equipment")),
            key=f"{prefix}_equipment",
        )
        status = st.selectbox(
            "Status",
            ["active", "inactive"],
            index=1 if _clean(row.get("status")).lower() == "inactive" else 0,
            key=f"{prefix}_status",
        )

    st.markdown("#### Guidance / Benefits")
    description = st.text_area(
        "Short description",
        value=_clean(row.get("description")),
        key=f"{prefix}_description",
    )
    detail_left, detail_right = st.columns(2, gap="small")
    with detail_left:
        instructions = st.text_area(
            "Instructions",
            value=_clean(row.get("instructions")),
            key=f"{prefix}_instructions",
            help="Use one line per instruction or separate with semicolons.",
        )
    with detail_right:
        benefits = st.text_area(
            "Benefits", value=_clean(row.get("benefits")), key=f"{prefix}_benefits"
        )

    st.markdown("#### Tags")
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
            value=_clean(row.get("image_url")),
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
            "Upload exercise image",
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
            st.image(image_url, caption="Uploaded image preview", use_container_width=True)
        elif is_valid_image_url(image_url):
            st.image(image_url, caption="Current image preview", use_container_width=True)

    return {
        "title": title,
        "description": description,
        "category": category,
        "difficulty": difficulty,
        "goal_tags": goal_tags,
        "condition_tags": condition_tags,
        "duration_or_reps": duration_or_reps,
        "hidden_calories_v96": _clean(row.get("hidden_calories_v96")),
        "equipment": equipment,
        "image_url": image_url,
        "image_bucket": image_bucket,
        "image_path": image_path,
        "image_access_type": image_access_type,
        "instructions": instructions,
        "benefits": benefits,
        "status": status,
    }


def _exercise_summary(row) -> str:
    details = [
        _clean(row.get("category")),
        _clean(row.get("difficulty")),
        _clean(row.get("duration_or_reps")),
        _clean(row.get("equipment")),
    ]
    return " · ".join(part for part in details if part) or "No summary details recorded."


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
    "Exercise Repository",
    "Create and maintain reusable exercise definitions. Member allocation is managed separately.",
    "Admin content repository",
)
_show_flash()

add_open = bool(st.session_state.get("hm_exercise_repository_add_open", False))
if render_repository_disclosure(
    "Add Exercise",
    is_open=add_open,
    key="exercise_repo_add_disclosure",
):
    st.session_state["hm_exercise_repository_add_open"] = not add_open
    if not add_open:
        st.session_state.pop("hm_exercise_repository_edit_id", None)
        st.session_state.pop("hm_exercise_repository_delete_id", None)
    st.rerun()
if add_open:
    with repository_form_panel():
        values = exercise_form("new_exercise_repository")
        if st.button("Save Exercise", type="primary", use_container_width=True):
            try:
                add_exercise_repository_item(values, actor_id=_actor_id())
                _flash("Exercise saved.")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))

# Do not build repository rows while Add is open. This keeps the run focused
# on one large form and prevents hidden/background form rendering.
if not add_open:
    st.markdown("### Current Repository")
    repository_rows = list_exercise_repository(active_only=False)
    active_rows = [row for row in repository_rows if row.get("status") == "active"]
    inactive_rows = [row for row in repository_rows if row.get("status") != "active"]

    if not active_rows:
        st.info("No active exercises are available.")
    for row in active_rows:
        exercise_id = str(row.get("id"))
        details_col, edit_col, delete_col = st.columns([5.8, 0.72, 0.82], gap="small")
        with details_col:
            st.markdown(
                f"<div class='hm-repo-row'><div class='hm-repo-title'>{_clean(row.get('title')) or 'Untitled Exercise'}</div>"
                f"<div class='hm-repo-meta'>{_exercise_summary(row)}</div></div>",
                unsafe_allow_html=True,
            )
        with edit_col:
            if st.button(
                "Edit",
                key=f"exercise_repo_edit_{exercise_id}",
                use_container_width=True,
            ):
                current = st.session_state.get("hm_exercise_repository_edit_id")
                st.session_state["hm_exercise_repository_edit_id"] = (
                    None if current == exercise_id else exercise_id
                )
                st.session_state.pop("hm_exercise_repository_delete_id", None)
                st.session_state["hm_exercise_repository_add_open"] = False
                st.rerun()
        with delete_col:
            if st.button(
                "Delete",
                key=f"exercise_repo_delete_{exercise_id}",
                use_container_width=True,
            ):
                st.session_state["hm_exercise_repository_delete_id"] = exercise_id
                st.session_state.pop("hm_exercise_repository_edit_id", None)
                st.rerun()

        if st.session_state.get("hm_exercise_repository_edit_id") == exercise_id:
            title = _clean(row.get("title")) or "Untitled Exercise"
            if render_repository_disclosure(
                f"Edit Exercise · {title}",
                is_open=True,
                key=f"exercise_repo_edit_disclosure_{exercise_id}",
            ):
                st.session_state.pop("hm_exercise_repository_edit_id", None)
                st.rerun()
            with repository_form_panel():
                edited = exercise_form(
                    f"exercise_repo_edit_form_{exercise_id}",
                    row,
                )
                save_col, cancel_col, spacer = st.columns([1, 1, 3], gap="small")
                with save_col:
                    if st.button(
                        "Save Changes",
                        key=f"exercise_repo_save_{exercise_id}",
                        type="primary",
                        use_container_width=True,
                    ):
                        try:
                            update_exercise_repository_item(
                                exercise_id,
                                edited,
                                actor_id=_actor_id(),
                            )
                            st.session_state.pop(
                                "hm_exercise_repository_edit_id", None
                            )
                            _flash("Exercise updated.")
                            st.rerun()
                        except Exception as exc:
                            st.error(str(exc))
                with cancel_col:
                    if st.button(
                        "Close",
                        key=f"exercise_repo_cancel_{exercise_id}",
                        use_container_width=True,
                    ):
                        st.session_state.pop(
                            "hm_exercise_repository_edit_id", None
                        )
                        st.rerun()

        if st.session_state.get("hm_exercise_repository_delete_id") == exercise_id:
            st.warning(
                "Delete removes this exercise from future selection. Existing and historical member plans remain protected."
            )
            confirm_col, cancel_col, spacer = st.columns([1.15, 0.8, 3], gap="small")
            with confirm_col:
                if st.button(
                    "Confirm Delete",
                    key=f"exercise_repo_confirm_delete_{exercise_id}",
                    type="primary",
                    use_container_width=True,
                ):
                    try:
                        set_exercise_repository_status(
                            exercise_id,
                            False,
                            actor_id=_actor_id(),
                        )
                        st.session_state.pop(
                            "hm_exercise_repository_delete_id", None
                        )
                        _flash(
                            "Exercise removed from the active repository. Historical references were retained."
                        )
                        st.rerun()
                    except Exception as exc:
                        st.error(str(exc))
            with cancel_col:
                if st.button(
                    "Cancel",
                    key=f"exercise_repo_cancel_delete_{exercise_id}",
                    use_container_width=True,
                ):
                    st.session_state.pop(
                        "hm_exercise_repository_delete_id", None
                    )
                    st.rerun()

    inactive_open = bool(st.session_state.get("hm_exercise_repository_inactive_open", False))
    if render_repository_disclosure(
        f"Inactive Repository Items ({len(inactive_rows)})",
        is_open=inactive_open,
        key="exercise_repo_inactive_disclosure",
    ):
        st.session_state["hm_exercise_repository_inactive_open"] = not inactive_open
        st.rerun()
    if inactive_open:
        with repository_inactive_panel():
            if not inactive_rows:
                st.caption("No inactive repository items.")
            for row in inactive_rows:
                exercise_id = str(row.get("id"))
                label_col, action_col = st.columns([5.5, 1], gap="small")
                with label_col:
                    st.markdown(
                        f"**{_clean(row.get('title')) or 'Untitled Exercise'}**  \n{_exercise_summary(row)}"
                    )
                with action_col:
                    if st.button(
                        "Reactivate",
                        key=f"exercise_repo_reactivate_{exercise_id}",
                        use_container_width=True,
                    ):
                        try:
                            set_exercise_repository_status(
                                exercise_id,
                                True,
                                actor_id=_actor_id(),
                            )
                            _flash("Exercise reactivated.")
                            st.rerun()
                        except Exception as exc:
                            st.error(str(exc))

render_page_nav(
    "Exercise Repository",
    back_page="pages/10_Admin_Dashboard.py",
    dashboard_page="pages/10_Admin_Dashboard.py",
    show_evaluation=False,
    show_dashboard=True,
    location="bottom",
)
render_back_to_top()

# Hidden for Phase 1: Import CSV and Member Feedback.
# Removed from this repository page: direct member allocation and the separate Edit/Delete workspace.
