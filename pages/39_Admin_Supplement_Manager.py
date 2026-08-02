from __future__ import annotations

import html
import re

import streamlit as st

from components.guards import require_admin
from components.supplement_repository import (
    add_supplement_repository_item,
    list_supplement_repository,
    set_supplement_repository_status,
    supplement_repository_counts,
    update_supplement_repository_item,
)
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
    page_title="Supplement Repository",
    page_icon="💚",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_global_styles()
apply_luxe_theme()
require_admin()
utility_logout_bar()
inject_repository_page_ui()


TIMING_OPTIONS = [
    "Morning",
    "Midday",
    "Evening",
    "Before Bed",
    "With Food",
    "Empty Stomach",
    "After Meals",
]
FREQUENCY_OPTIONS = [
    "Once",
    "Twice",
    "Thrice",
    "Four times",
    "Five times",
    "Six times",
    "Seven times",
    "Eight times",
    "Nine times",
    "Ten times",
]


def _esc(value) -> str:
    return html.escape(str(value or ""))


def _actor_id() -> str:
    return (
        st.session_state.get("user_id")
        or st.session_state.get("oidc_email")
        or "admin"
    )


def _flash(message: str, level: str = "success") -> None:
    st.session_state["hm_supplement_repository_flash"] = (level, message)


def _show_flash() -> None:
    payload = st.session_state.pop("hm_supplement_repository_flash", None)
    if not payload:
        return
    level, message = payload
    getattr(st, level if level in {"success", "warning", "error", "info"} else "info")(
        message
    )


def _custom_timing_parts(extra) -> list[str]:
    raw = str(extra or "").strip()
    if not raw:
        return []
    return [part.strip() for part in re.split(r"[,;|\n]+", raw) if part.strip()]


def _timing_from_choices(choices, extra) -> str:
    parts = [str(value).strip() for value in (choices or []) if str(value).strip()]
    parts.extend(_custom_timing_parts(extra))
    return ", ".join(dict.fromkeys(parts))


def _split_timing(text) -> tuple[list[str], str]:
    parts = [
        part.strip()
        for part in str(text or "").replace("|", ",").split(",")
        if part.strip()
    ]
    lookup = {option.lower(): option for option in TIMING_OPTIONS}
    selected = []
    custom = []
    for part in parts:
        option = lookup.get(part.lower())
        if option and option not in selected:
            selected.append(option)
        elif not option:
            custom.append(part)
    return selected, ", ".join(custom)


def _repository_details(row) -> str:
    metadata = []
    if row.get("dosage"):
        metadata.append(f"<span><b>Dosage:</b> {_esc(row.get('dosage'))}</span>")
    if row.get("frequency"):
        metadata.append(
            f"<span><b>Frequency:</b> {_esc(row.get('frequency'))}</span>"
        )
    if row.get("timing"):
        metadata.append(f"<span><b>Timing:</b> {_esc(row.get('timing'))}</span>")
    if row.get("instructions"):
        metadata.append(
            f"<span><b>Instructions:</b> {_esc(row.get('instructions'))}</span>"
        )
    meta_html = "".join(metadata) or "<span>No reusable defaults recorded.</span>"
    return (
        "<div class='hm-sup-row'>"
        f"<div class='hm-sup-name'>{_esc(row.get('supplement_name'))}</div>"
        f"<div class='hm-sup-meta'>{meta_html}</div>"
        "</div>"
    )


st.markdown(
    """
<style>
.block-container{padding-top:.45rem!important;max-width:1120px!important;}
.hero-shell{margin:.45rem 0 .75rem!important;padding:1rem 1.15rem!important;}
.hm-sup-row{border:1px solid #E3C98E;background:#FFFDF8;border-radius:14px;padding:.66rem .78rem;margin:.34rem 0;}
.hm-sup-name{font-weight:900;color:#064E3B;font-size:.92rem;line-height:1.2;}
.hm-sup-meta{display:flex;flex-wrap:wrap;gap:.1rem .65rem;color:#64748B;font-size:.74rem;margin-top:.12rem;line-height:1.3;}
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
</style>
""",
    unsafe_allow_html=True,
)

topbar(
    "Supplement Repository",
    "Create and maintain reusable supplement definitions. Member allocation is managed separately.",
    "Admin content repository",
)
_show_flash()

add_open = bool(st.session_state.get("hm_supplement_repository_add_open", False))
if render_repository_disclosure(
    "Add Supplement",
    is_open=add_open,
    key="supplement_repo_add_disclosure",
):
    st.session_state["hm_supplement_repository_add_open"] = not add_open
    if not add_open:
        st.session_state.pop("hm_supplement_repository_edit_id", None)
        st.session_state.pop("hm_supplement_repository_delete_id", None)
    st.rerun()
if add_open:
    with repository_form_panel():
        with st.form("hm_v1023a_add_supplement_form", clear_on_submit=True):
            st.markdown("#### Basic Details")
            name = st.text_input(
                "Supplement Name", placeholder="e.g. Magnesium Glycinate"
            )
            dose_col, frequency_col = st.columns(2)
            with dose_col:
                dosage = st.text_input("Default Dosage", placeholder="e.g. 400 mg")
            with frequency_col:
                frequency = st.selectbox(
                    "Default Frequency",
                    FREQUENCY_OPTIONS,
                    index=0,
                    key="hm_v1023a_add_frequency",
                )
            st.markdown("#### Timing")
            timing_options = st.multiselect(
                "Default Timing", TIMING_OPTIONS, default=[]
            )
            custom_timing = st.text_input(
                "Additional Timing",
                placeholder="Optional custom timing; separate multiple values with commas.",
            )
            st.markdown("#### Instructions")
            instructions = st.text_area(
                "Default Instructions",
                placeholder="Reusable guidance that can be adjusted during member allocation.",
            )
            submitted = st.form_submit_button(
                "Add to Repository", use_container_width=True
            )
            if submitted:
                try:
                    add_supplement_repository_item(
                        {
                            "supplement_name": name,
                            "dosage": dosage,
                            "frequency": frequency,
                            "timing": _timing_from_choices(
                                timing_options, custom_timing
                            ),
                            "instructions": instructions,
                        },
                        actor_id=_actor_id(),
                    )
                    _flash("Supplement added to repository.")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))

# Do not build repository rows while Add is open. This keeps the run focused
# on one large form and prevents hidden/background form rendering.
if not add_open:
    st.markdown("### Current Repository")
    counts = supplement_repository_counts()
    all_rows = list_supplement_repository(active_only=False)
    active_rows = [row for row in all_rows if row.get("status") == "Active"]
    inactive_rows = [row for row in all_rows if row.get("status") != "Active"]

    st.caption(f"{counts['active']} active supplement(s)")
    if not active_rows:
        st.info("No active supplements are available.")
    for row in active_rows:
        supplement_id = str(row.get("id"))
        details_col, edit_col, delete_col = st.columns([5.8, 0.72, 0.82], gap="small")
        with details_col:
            st.markdown(_repository_details(row), unsafe_allow_html=True)
        with edit_col:
            if st.button(
                "Edit",
                key=f"supplement_repo_edit_{supplement_id}",
                use_container_width=True,
            ):
                current = st.session_state.get("hm_supplement_repository_edit_id")
                st.session_state["hm_supplement_repository_edit_id"] = (
                    None if current == supplement_id else supplement_id
                )
                st.session_state.pop("hm_supplement_repository_delete_id", None)
                st.session_state["hm_supplement_repository_add_open"] = False
                st.rerun()
        with delete_col:
            if st.button(
                "Delete",
                key=f"supplement_repo_delete_{supplement_id}",
                use_container_width=True,
            ):
                st.session_state["hm_supplement_repository_delete_id"] = supplement_id
                st.session_state.pop("hm_supplement_repository_edit_id", None)
                st.rerun()

        if st.session_state.get("hm_supplement_repository_edit_id") == supplement_id:
            selected_timing, custom_timing = _split_timing(row.get("timing"))
            name = row.get("supplement_name") or "Untitled Supplement"
            if render_repository_disclosure(
                f"Edit Supplement · {name}",
                is_open=True,
                key=f"supplement_repo_edit_disclosure_{supplement_id}",
            ):
                st.session_state.pop("hm_supplement_repository_edit_id", None)
                st.rerun()
            with repository_form_panel():
                st.markdown("#### Basic Details")
                basic_name, basic_dose, basic_frequency = st.columns(3, gap="small")
                with basic_name:
                    edit_name = st.text_input(
                        "Supplement Name",
                        value=row.get("supplement_name", ""),
                        key=f"supplement_repo_edit_name_{supplement_id}",
                    )
                with basic_dose:
                    edit_dosage = st.text_input(
                        "Default Dosage",
                        value=row.get("dosage", ""),
                        key=f"supplement_repo_edit_dosage_{supplement_id}",
                    )
                with basic_frequency:
                    frequency_value = (
                        row.get("frequency")
                        if row.get("frequency") in FREQUENCY_OPTIONS
                        else FREQUENCY_OPTIONS[0]
                    )
                    edit_frequency = st.selectbox(
                        "Default Frequency",
                        FREQUENCY_OPTIONS,
                        index=FREQUENCY_OPTIONS.index(frequency_value),
                        key=f"supplement_repo_edit_frequency_{supplement_id}",
                    )
                st.markdown("#### Timing")
                timing_col, custom_col = st.columns([1.35, 1], gap="small")
                with timing_col:
                    edit_timing = st.multiselect(
                        "Default Timing",
                        TIMING_OPTIONS,
                        default=selected_timing,
                        key=f"supplement_repo_edit_timing_{supplement_id}",
                    )
                with custom_col:
                    edit_custom_timing = st.text_input(
                        "Additional Timing",
                        value=custom_timing,
                        key=f"supplement_repo_edit_custom_timing_{supplement_id}",
                    )
                st.markdown("#### Instructions")
                edit_instructions = st.text_area(
                    "Default Instructions",
                    value=row.get("instructions", ""),
                    key=f"supplement_repo_edit_instructions_{supplement_id}",
                )
                save_col, cancel_col, spacer = st.columns([1, 1, 3], gap="small")
                with save_col:
                    if st.button(
                        "Save Changes",
                        key=f"supplement_repo_save_{supplement_id}",
                        type="primary",
                        use_container_width=True,
                    ):
                        try:
                            update_supplement_repository_item(
                                supplement_id,
                                {
                                    "supplement_name": edit_name,
                                    "dosage": edit_dosage,
                                    "frequency": edit_frequency,
                                    "timing": _timing_from_choices(
                                        edit_timing, edit_custom_timing
                                    ),
                                    "instructions": edit_instructions,
                                },
                                actor_id=_actor_id(),
                            )
                            st.session_state.pop(
                                "hm_supplement_repository_edit_id", None
                            )
                            _flash("Supplement updated.")
                            st.rerun()
                        except Exception as exc:
                            st.error(str(exc))
                with cancel_col:
                    if st.button(
                        "Close",
                        key=f"supplement_repo_cancel_{supplement_id}",
                        use_container_width=True,
                    ):
                        st.session_state.pop(
                            "hm_supplement_repository_edit_id", None
                        )
                        st.rerun()

        if st.session_state.get("hm_supplement_repository_delete_id") == supplement_id:
            st.warning(
                "Delete removes this supplement from future selection. Existing and historical member plans remain protected."
            )
            confirm_col, cancel_col, spacer = st.columns([1.15, 0.8, 3], gap="small")
            with confirm_col:
                if st.button(
                    "Confirm Delete",
                    key=f"supplement_repo_confirm_delete_{supplement_id}",
                    type="primary",
                    use_container_width=True,
                ):
                    try:
                        set_supplement_repository_status(
                            supplement_id,
                            False,
                            actor_id=_actor_id(),
                        )
                        st.session_state.pop(
                            "hm_supplement_repository_delete_id", None
                        )
                        _flash(
                            "Supplement removed from the active repository. Historical references were retained."
                        )
                        st.rerun()
                    except Exception as exc:
                        st.error(str(exc))
            with cancel_col:
                if st.button(
                    "Cancel",
                    key=f"supplement_repo_cancel_delete_{supplement_id}",
                    use_container_width=True,
                ):
                    st.session_state.pop(
                        "hm_supplement_repository_delete_id", None
                    )
                    st.rerun()

    inactive_open = bool(st.session_state.get("hm_supplement_repository_inactive_open", False))
    if render_repository_disclosure(
        f"Inactive Repository Items ({len(inactive_rows)})",
        is_open=inactive_open,
        key="supplement_repo_inactive_disclosure",
    ):
        st.session_state["hm_supplement_repository_inactive_open"] = not inactive_open
        st.rerun()
    if inactive_open:
        with repository_inactive_panel():
            if not inactive_rows:
                st.caption("No inactive repository items.")
            for row in inactive_rows:
                supplement_id = str(row.get("id"))
                label_col, action_col = st.columns([5.5, 1], gap="small")
                with label_col:
                    st.markdown(_repository_details(row), unsafe_allow_html=True)
                with action_col:
                    if st.button(
                        "Reactivate",
                        key=f"supplement_repo_reactivate_{supplement_id}",
                        use_container_width=True,
                    ):
                        try:
                            set_supplement_repository_status(
                                supplement_id,
                                True,
                                actor_id=_actor_id(),
                            )
                            _flash("Supplement reactivated.")
                            st.rerun()
                        except Exception as exc:
                            st.error(str(exc))

render_page_nav(
    "Supplement Repository",
    back_page="pages/10_Admin_Dashboard.py",
    dashboard_page="pages/10_Admin_Dashboard.py",
    show_evaluation=False,
    show_dashboard=True,
    location="bottom",
)
render_back_to_top()

# Repository-only boundary: no member selection or direct allocation.
