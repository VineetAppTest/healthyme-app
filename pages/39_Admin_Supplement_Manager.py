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


def _card(row):
    details = []
    if row.get("dosage"):
        details.append(f"Dosage: {_esc(row.get('dosage'))}")
    if row.get("frequency"):
        details.append(f"Frequency: {_esc(row.get('frequency'))}")
    if row.get("timing"):
        details.append(f"Timing: {_esc(row.get('timing'))}")
    detail_html = "".join(f"<div class='hm-sup-dose'>{value}</div>" for value in details)
    instructions = (
        f"<div class='hm-sup-dose'>Instructions: {_esc(row.get('instructions'))}</div>"
        if row.get("instructions")
        else ""
    )
    return f"""
    <div class='hm-sup-card'>
      <div class='hm-sup-icon'>◉</div>
      <div>
        <div class='hm-sup-name'>{_esc(row.get('supplement_name'))}</div>
        {detail_html}
        {instructions}
      </div>
      <div><span class='hm-sup-status'>{_esc(row.get('status'))}</span></div>
    </div>
    """


st.markdown(
    """
<style>
.hm-sup-page{max-width:1180px;margin:0 auto;}
.hm-sup-layout{display:grid;grid-template-columns:1.2fr .8fr;gap:1rem;margin:.8rem 0 1rem;align-items:start;}
.hm-sup-panel{border:1px solid #E3C98E;background:linear-gradient(180deg,#FFFDF8 0%,#FFF9EC 100%);border-radius:20px;padding:1rem;box-shadow:0 10px 24px rgba(15,23,42,.05);}
.hm-sup-title-row{display:flex;align-items:center;justify-content:space-between;margin-bottom:.75rem;gap:.75rem;}
.hm-sup-title{color:#064E3B;font-size:1.02rem;font-weight:950;}
.hm-sup-badge{background:#DDF7F3;color:#006D6F;border-radius:999px;padding:.22rem .58rem;font-size:.72rem;font-weight:900;white-space:nowrap;}
.hm-sup-card{border:1px solid #E6D4A8;background:#FFFDF8;border-radius:16px;padding:.85rem;margin:.72rem 0;display:grid;grid-template-columns:40px 1fr auto;gap:.75rem;align-items:center;}
.hm-sup-card.inactive{background:#F8F5EE;border-style:dashed;opacity:.88;}
.hm-sup-icon{width:34px;height:34px;border-radius:999px;background:#FFF0EA;color:#B35C4D;display:flex;align-items:center;justify-content:center;font-weight:950;}
.hm-sup-name{color:#1F2937;font-size:.92rem;font-weight:920;margin-bottom:.15rem;}
.hm-sup-dose{color:#64748B;font-size:.78rem;font-weight:760;margin:.10rem 0;}
.hm-sup-status{font-size:.72rem;font-weight:900;color:#006D6F;border:1px solid #BEEBE4;background:#F0FDFA;border-radius:999px;padding:.22rem .5rem;}
.hm-sup-empty{border:1px dashed #D9C28F;background:#FFFDF8;border-radius:16px;padding:1rem;color:#64748B;font-size:.85rem;font-weight:760;margin:.8rem 0;}
.hm-sup-boundary{border:1px solid #D8E8E2;background:#F4FBF8;border-radius:14px;padding:.72rem .8rem;color:#285B4D;font-size:.80rem;font-weight:760;margin:.3rem 0 1rem;}
@media(max-width:850px){.hm-sup-layout{grid-template-columns:1fr}.hm-sup-card{grid-template-columns:34px 1fr}.hm-sup-card>div:last-child{grid-column:2}}
</style>
""",
    unsafe_allow_html=True,
)

st.markdown("<div class='hm-sup-page'>", unsafe_allow_html=True)
st.markdown(
    "<div class='hm-sup-boundary'>Member allocation is managed only through Recommendation Profile Builder. "
    "This page creates and maintains reusable supplement definitions and does not publish directly to any member.</div>",
    unsafe_allow_html=True,
)

counts = supplement_repository_counts()
all_rows = list_supplement_repository(active_only=False)
active_rows = [row for row in all_rows if row.get("status") == "Active"]
inactive_rows = [row for row in all_rows if row.get("status") != "Active"]

left, right = st.columns([1.25, .75], gap="large")

with left:
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

    for row in active_rows:
        st.markdown(_card(row), unsafe_allow_html=True)
        edit_col, deactivate_col, spacer = st.columns([.55, .75, 2.2])
        with edit_col:
            if st.button("Edit", key=f"hm_supp_repo_edit_{row['id']}"):
                st.session_state["hm_supp_repo_edit_id"] = row["id"]
                st.rerun()
        with deactivate_col:
            if st.button("Deactivate", key=f"hm_supp_repo_deactivate_{row['id']}"):
                try:
                    set_supplement_repository_status(row["id"], False, actor_id=_actor_id())
                    st.success("Supplement deactivated in the repository. Existing member plans remain unchanged.")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))

        if st.session_state.get("hm_supp_repo_edit_id") == row["id"]:
            selected_timing, custom_timing = _split_timing(row.get("timing"))
            with st.form(f"hm_supp_repo_edit_form_{row['id']}"):
                st.markdown("**Edit repository item**")
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
                    frequency_value = row.get("frequency") if row.get("frequency") in FREQUENCY_OPTIONS else FREQUENCY_OPTIONS[0]
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
                edit_notes = st.text_area(
                    "Admin Notes",
                    value=row.get("admin_notes", ""),
                    key=f"hm_supp_repo_edit_notes_{row['id']}",
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
                                "admin_notes": edit_notes,
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

    with st.expander(f"Inactive Repository Items ({counts['inactive']})", expanded=False):
        if not inactive_rows:
            st.caption("No inactive repository items.")
        for row in inactive_rows:
            st.markdown(_card(row).replace("hm-sup-card", "hm-sup-card inactive", 1), unsafe_allow_html=True)
            if st.button("Reactivate", key=f"hm_supp_repo_reactivate_{row['id']}"):
                try:
                    set_supplement_repository_status(row["id"], True, actor_id=_actor_id())
                    st.success("Supplement reactivated in the repository.")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))

    st.markdown("</div>", unsafe_allow_html=True)

with right:
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
        admin_notes = st.text_area(
            "Admin Notes",
            placeholder="Internal source note; not member allocation guidance.",
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
                        "admin_notes": admin_notes,
                    },
                    actor_id=_actor_id(),
                )
                st.success("Supplement added to repository.")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))
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
