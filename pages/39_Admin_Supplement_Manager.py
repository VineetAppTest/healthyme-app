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
from components.ui_common import (
    apply_luxe_theme,
    inject_global_styles,
    render_back_to_top,
    render_page_nav,
    topbar,
    utility_logout_bar,
)


st.set_page_config(
    page_title="Supplement Management",
    page_icon="💚",
    layout="wide",
    initial_sidebar_state="collapsed",
)

inject_global_styles()
apply_luxe_theme()
require_admin()
utility_logout_bar()
topbar(
    "Supplement Management",
    "Create and maintain the master supplement repository used by Recommendation Profile Builder.",
    "Admin supplements",
)


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


def _esc(value):
    return html.escape(str(value or ""))


def _actor_id():
    return st.session_state.get("user_id") or st.session_state.get("oidc_email") or "admin"


def _custom_timing_parts(extra):
    raw = str(extra or "").strip()
    if not raw:
        return []
    return [part.strip() for part in re.split(r"[,;|\n]+", raw) if part.strip()]


def _timing_from_choices(choices, extra):
    parts = [str(value).strip() for value in (choices or []) if str(value).strip()]
    parts.extend(_custom_timing_parts(extra))
    return ", ".join(dict.fromkeys(parts))


def _split_timing(text):
    parts = [part.strip() for part in str(text or "").replace("|", ",").split(",") if part.strip()]
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


def _repository_details(row):
    metadata = []
    if row.get("dosage"):
        metadata.append(f"<span><b>Dosage:</b> {_esc(row.get('dosage'))}</span>")
    if row.get("frequency"):
        metadata.append(f"<span><b>Frequency:</b> {_esc(row.get('frequency'))}</span>")
    if row.get("timing"):
        metadata.append(f"<span><b>Timing:</b> {_esc(row.get('timing'))}</span>")
    if row.get("instructions"):
        metadata.append(f"<span><b>Instructions:</b> {_esc(row.get('instructions'))}</span>")
    meta_html = "".join(metadata) or "<span>No reusable defaults recorded.</span>"
    return f"""
    <div class='hm-sup-list-details'>
      <div class='hm-sup-list-name'>{_esc(row.get('supplement_name'))}</div>
      <div class='hm-sup-list-meta'>{meta_html}</div>
    </div>
    """


def _status_pill(status):
    inactive_class = " inactive" if str(status or "").lower() != "active" else ""
    return f"<span class='hm-sup-status{inactive_class}'>{_esc(status)}</span>"


st.markdown(
    """
<style>
.hm-sup-page{max-width:1180px;margin:0 auto;}
.hm-sup-panel{border:1px solid #E3C98E;background:linear-gradient(180deg,#FFFDF8 0%,#FFF9EC 100%);border-radius:20px;padding:1rem;box-shadow:0 10px 24px rgba(15,23,42,.05);}
.hm-sup-title-row{display:flex;align-items:center;justify-content:space-between;margin-bottom:.72rem;gap:.75rem;}
.hm-sup-title{color:#064E3B;font-size:1.02rem;font-weight:950;}
.hm-sup-badge{background:#DDF7F3;color:#006D6F;border-radius:999px;padding:.22rem .58rem;font-size:.72rem;font-weight:900;white-space:nowrap;}
.hm-sup-list-head{color:#64748B;font-size:.67rem;font-weight:900;letter-spacing:.04em;text-transform:uppercase;padding:.10rem 0 .34rem;}
.hm-sup-list-details{padding:.20rem 0 .16rem;min-height:44px;}
.hm-sup-list-name{color:#1F2937;font-size:.88rem;font-weight:930;line-height:1.25;margin-bottom:.18rem;}
.hm-sup-list-meta{display:flex;flex-wrap:wrap;gap:.12rem .68rem;color:#64748B;font-size:.72rem;font-weight:720;line-height:1.35;}
.hm-sup-list-meta span{display:inline-block;}
.hm-sup-list-divider{height:1px;background:#EADDBE;margin:.34rem 0 .38rem;}
.hm-sup-status{display:inline-flex;font-size:.69rem;font-weight:900;color:#006D6F;border:1px solid #BEEBE4;background:#F0FDFA;border-radius:999px;padding:.20rem .46rem;white-space:nowrap;margin-top:.28rem;}
.hm-sup-status.inactive{color:#64748B;border-color:#D7DCE3;background:#F4F5F7;}
.hm-sup-empty{border:1px dashed #D9C28F;background:#FFFDF8;border-radius:14px;padding:.78rem;color:#64748B;font-size:.82rem;font-weight:760;margin:.55rem 0;}
.hm-sup-edit-label{font-size:.80rem;font-weight:900;color:#064E3B;margin:.20rem 0 .10rem;}
div[data-testid="stButton"] button p{white-space:nowrap;}
@media(max-width:850px){.hm-sup-list-meta{display:block}.hm-sup-list-meta span{display:block;margin:.08rem 0}}
</style>
""",
    unsafe_allow_html=True,
)

st.markdown("<div class='hm-sup-page'>", unsafe_allow_html=True)

counts = supplement_repository_counts()
all_rows = list_supplement_repository(active_only=False)
active_rows = [row for row in all_rows if row.get("status") == "Active"]
inactive_rows = [row for row in all_rows if row.get("status") != "Active"]

# Creation remains first, repository second.
add_column, repository_column = st.columns([0.78, 1.22], gap="large")

with add_column:
    st.markdown("<div class='hm-sup-panel'>", unsafe_allow_html=True)
    st.markdown("<div class='hm-sup-title'>Add Supplement</div>", unsafe_allow_html=True)
    with st.form("hm_v1023a_add_supplement_form", clear_on_submit=True):
        name = st.text_input("Supplement Name", placeholder="e.g. Magnesium Glycinate")
        dose_col, frequency_col = st.columns(2, gap="small")
        with dose_col:
            dosage = st.text_input("Default Dosage", placeholder="e.g. 400 mg")
        with frequency_col:
            frequency = st.selectbox(
                "Default Frequency",
                FREQUENCY_OPTIONS,
                index=0,
                key="hm_v1023a_add_frequency",
            )
        timing_options = st.multiselect("Default Timing", TIMING_OPTIONS, default=[])
        custom_timing = st.text_input(
            "Additional Timing",
            placeholder="Optional custom timing; separate multiple values with commas.",
        )
        instructions = st.text_area(
            "Default Instructions",
            placeholder="Reusable guidance that can be adjusted inside Profile Builder.",
        )
        submitted = st.form_submit_button("Add to Repository", use_container_width=True)

        if submitted:
            try:
                add_supplement_repository_item(
                    {
                        "supplement_name": name,
                        "dosage": dosage,
                        "frequency": frequency,
                        "timing": _timing_from_choices(timing_options, custom_timing),
                        "instructions": instructions,
                    },
                    actor_id=_actor_id(),
                )
                st.success("Supplement added to repository.")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))
    st.markdown("</div>", unsafe_allow_html=True)

with repository_column:
    st.markdown("<div class='hm-sup-panel'>", unsafe_allow_html=True)
    st.markdown(
        f"<div class='hm-sup-title-row'><div class='hm-sup-title'>Current Repository</div>"
        f"<div class='hm-sup-badge'>{counts['active']} Active</div></div>",
        unsafe_allow_html=True,
    )

    if not active_rows:
        st.markdown(
            "<div class='hm-sup-empty'>No active supplements are available. Add the first repository item.</div>",
            unsafe_allow_html=True,
        )
    else:
        head_details, head_status, head_edit, head_deactivate = st.columns(
            [4.2, 0.9, 0.8, 1.35],
            gap="small",
        )
        with head_details:
            st.markdown(
                "<div class='hm-sup-list-head'>Supplement and reusable defaults</div>",
                unsafe_allow_html=True,
            )
        with head_status:
            st.markdown("<div class='hm-sup-list-head'>Status</div>", unsafe_allow_html=True)
        with head_edit:
            st.markdown("<div class='hm-sup-list-head'>Edit</div>", unsafe_allow_html=True)
        with head_deactivate:
            st.markdown("<div class='hm-sup-list-head'>Availability</div>", unsafe_allow_html=True)

    for row in active_rows:
        details_col, status_col, edit_col, deactivate_col = st.columns(
            [4.2, 0.9, 0.8, 1.35],
            gap="small",
        )
        with details_col:
            st.markdown(_repository_details(row), unsafe_allow_html=True)
        with status_col:
            st.markdown(_status_pill(row.get("status")), unsafe_allow_html=True)
        with edit_col:
            if st.button("Edit", key=f"hm_supp_repo_edit_{row['id']}", use_container_width=True):
                st.session_state["hm_supp_repo_edit_id"] = row["id"]
                st.rerun()
        with deactivate_col:
            if st.button(
                "Deactivate",
                key=f"hm_supp_repo_deactivate_{row['id']}",
                use_container_width=True,
            ):
                try:
                    set_supplement_repository_status(row["id"], False, actor_id=_actor_id())
                    st.success(
                        "Supplement deactivated in the repository. Existing member plans remain unchanged."
                    )
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))

        if st.session_state.get("hm_supp_repo_edit_id") == row["id"]:
            selected_timing, custom_timing = _split_timing(row.get("timing"))
            with st.form(f"hm_supp_repo_edit_form_{row['id']}"):
                st.markdown(
                    "<div class='hm-sup-edit-label'>Edit repository item</div>",
                    unsafe_allow_html=True,
                )
                edit_name = st.text_input(
                    "Supplement Name",
                    value=row.get("supplement_name", ""),
                    key=f"hm_supp_repo_edit_name_{row['id']}",
                )
                dose_col, frequency_col = st.columns(2)
                with dose_col:
                    edit_dosage = st.text_input(
                        "Default Dosage",
                        value=row.get("dosage", ""),
                        key=f"hm_supp_repo_edit_dosage_{row['id']}",
                    )
                with frequency_col:
                    frequency_value = (
                        row.get("frequency")
                        if row.get("frequency") in FREQUENCY_OPTIONS
                        else FREQUENCY_OPTIONS[0]
                    )
                    edit_frequency = st.selectbox(
                        "Default Frequency",
                        FREQUENCY_OPTIONS,
                        index=FREQUENCY_OPTIONS.index(frequency_value),
                        key=f"hm_supp_repo_edit_frequency_{row['id']}",
                    )
                edit_timing = st.multiselect(
                    "Default Timing",
                    TIMING_OPTIONS,
                    default=selected_timing,
                    key=f"hm_supp_repo_edit_timing_{row['id']}",
                )
                edit_custom_timing = st.text_input(
                    "Additional Timing",
                    value=custom_timing,
                    key=f"hm_supp_repo_edit_custom_timing_{row['id']}",
                )
                edit_instructions = st.text_area(
                    "Default Instructions",
                    value=row.get("instructions", ""),
                    key=f"hm_supp_repo_edit_instructions_{row['id']}",
                )
                save_col, cancel_col = st.columns(2)
                with save_col:
                    save_edit = st.form_submit_button("Save Changes", use_container_width=True)
                with cancel_col:
                    cancel_edit = st.form_submit_button("Cancel", use_container_width=True)

                if save_edit:
                    try:
                        update_supplement_repository_item(
                            row["id"],
                            {
                                "supplement_name": edit_name,
                                "dosage": edit_dosage,
                                "frequency": edit_frequency,
                                "timing": _timing_from_choices(edit_timing, edit_custom_timing),
                                "instructions": edit_instructions,
                            },
                            actor_id=_actor_id(),
                        )
                        st.session_state.pop("hm_supp_repo_edit_id", None)
                        st.success("Supplement repository item updated.")
                        st.rerun()
                    except Exception as exc:
                        st.error(str(exc))
                if cancel_edit:
                    st.session_state.pop("hm_supp_repo_edit_id", None)
                    st.rerun()

        st.markdown("<div class='hm-sup-list-divider'></div>", unsafe_allow_html=True)

    inactive_open_key = "hm_supp_repo_inactive_open"
    inactive_open = bool(st.session_state.get(inactive_open_key, False))
    inactive_toggle_label = (
        f"- Inactive Repository Items ({counts['inactive']})"
        if inactive_open
        else f"+ Inactive Repository Items ({counts['inactive']})"
    )
    if st.button(
        inactive_toggle_label,
        key="hm_supp_repo_inactive_toggle",
        use_container_width=True,
    ):
        st.session_state[inactive_open_key] = not inactive_open
        st.rerun()

    if inactive_open:
        if not inactive_rows:
            st.caption("No inactive repository items.")
        for row in inactive_rows:
            details_col, status_col, reactivate_col = st.columns([4.8, 0.9, 1.55], gap="small")
            with details_col:
                st.markdown(_repository_details(row), unsafe_allow_html=True)
            with status_col:
                st.markdown(_status_pill(row.get("status")), unsafe_allow_html=True)
            with reactivate_col:
                if st.button(
                    "Reactivate",
                    key=f"hm_supp_repo_reactivate_{row['id']}",
                    use_container_width=True,
                ):
                    try:
                        set_supplement_repository_status(row["id"], True, actor_id=_actor_id())
                        st.success("Supplement reactivated in the repository.")
                        st.rerun()
                    except Exception as exc:
                        st.error(str(exc))
            st.markdown("<div class='hm-sup-list-divider'></div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

render_page_nav(
    "Supplement Management",
    back_page="pages/10_Admin_Dashboard.py",
    dashboard_page="pages/10_Admin_Dashboard.py",
    show_evaluation=False,
    show_dashboard=True,
    location="bottom",
)
render_back_to_top()

# Repository-only boundary:
# - no member selection;
# - no direct member allocation/publishing;
# - member plans remain managed through Recommendation Profile Builder;
# - legacy member supplement records remain unchanged and readable by their existing consumers.
