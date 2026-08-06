import functools

import streamlit as st

from components.admin_dashboard_schedule_reminder import (
    render_admin_upcoming_schedule_reminder,
)
from components.guards import require_admin
from components.performance_diagnostics import (
    begin_page_measurement,
    finish_and_render_page_diagnostics,
)
from components.ui_common import (
    apply_luxe_theme,
    inject_global_styles,
    inject_keepalive_guard_v96_11,
    topbar,
    utility_logout_bar,
)


_HIDDEN_BUILD_LABEL = "Full Admin integration build:"
_BUILD_LABEL_SUPPRESSION_MARKER = "_hm_admin_dashboard_build_label_suppressed"
# Registered routes remain part of the Admin application even though their
# duplicate Dashboard buttons are removed in favour of the Profile Builder hub.
_EXERCISE_ALLOCATION_ROUTE = "pages/42_Admin_Exercise_Member_Allocation.py"
_SUPPLEMENT_ALLOCATION_ROUTE = "pages/43_Admin_Supplement_Member_Allocation.py"


def _install_build_label_suppression() -> None:
    """Suppress the obsolete technical Admin build label wherever it is emitted."""

    def should_hide(value: object) -> bool:
        return _HIDDEN_BUILD_LABEL in str(value or "")

    for attribute in ("caption", "markdown", "write"):
        original = getattr(st, attribute, None)
        if not callable(original) or getattr(original, _BUILD_LABEL_SUPPRESSION_MARKER, False):
            continue

        @functools.wraps(original)
        def without_build_label(*args, __original=original, **kwargs):
            body = args[0] if args else kwargs.get("body", kwargs.get("value", ""))
            if should_hide(body):
                return None
            return __original(*args, **kwargs)

        setattr(without_build_label, _BUILD_LABEL_SUPPRESSION_MARKER, True)
        setattr(st, attribute, without_build_label)


st.set_page_config(
    page_title="Admin Dashboard",
    page_icon="💚",
    layout="wide",
    initial_sidebar_state="collapsed",
)
begin_page_measurement("Admin Dashboard")

_install_build_label_suppression()
inject_global_styles()
apply_luxe_theme()
require_admin()
utility_logout_bar()

render_admin_upcoming_schedule_reminder(
    st.session_state.get("user_id")
    or st.session_state.get("oidc_email")
    or "admin"
)

topbar(
    "Admin Dashboard",
    "Access review workflows, content allocation, reports, communication and scheduling.",
    "Admin workflow",
)

st.markdown(
    """
<style>
/* Final production Admin Dashboard: operational workflows only. */
section.main > div.block-container,
.main .block-container,
[data-testid="stAppViewBlockContainer"],
.stMainBlockContainer,
.block-container{
  max-width:1140px!important;
  padding-top:.58rem!important;
  padding-bottom:1.2rem!important;
}
.hm-admin-title-row{
  margin:.10rem 0 .75rem 0!important;
  padding:.74rem .92rem!important;
  border:1px solid rgba(216,180,98,.46)!important;
  border-radius:20px!important;
  background:linear-gradient(135deg, rgba(255,253,248,.98), rgba(255,247,230,.78))!important;
  box-shadow:0 12px 28px rgba(15,23,42,.055)!important;
}
.hm-admin-title{
  margin:0!important;
  color:#064E3B!important;
  font-size:1.08rem!important;
  font-weight:950!important;
  letter-spacing:.01em!important;
  line-height:1.16!important;
}
.hm-admin-subtitle{
  margin:.18rem 0 0 0!important;
  color:#5D4A1E!important;
  font-size:.82rem!important;
  font-weight:760!important;
  line-height:1.32!important;
}
div[data-testid="stVerticalBlockBorderWrapper"]{
  border:1.25px solid rgba(216,180,98,.62)!important;
  border-radius:22px!important;
  background:linear-gradient(180deg, rgba(255,253,248,.98) 0%, rgba(255,250,239,.94) 100%)!important;
  box-shadow:0 12px 26px rgba(15,23,42,.06)!important;
  padding:.72rem .78rem .68rem .78rem!important;
  margin:0 0 .94rem 0!important;
}
div[data-testid="stVerticalBlockBorderWrapper"]:hover{
  border-color:rgba(184,147,69,.80)!important;
  box-shadow:0 16px 34px rgba(15,23,42,.075)!important;
}
.hm-dash-section-title{
  margin:0 0 .10rem 0!important;
  color:#064E3B!important;
  font-size:.94rem!important;
  line-height:1.10!important;
  font-weight:950!important;
  letter-spacing:.01em!important;
}
.hm-dash-section-caption{
  margin:0 0 .54rem 0!important;
  color:#72551A!important;
  font-size:.76rem!important;
  line-height:1.25!important;
  font-weight:760!important;
}
.hm-dash-card [data-testid="stButton"]{
  margin:0 0 .46rem 0!important;
}
.hm-dash-card [data-testid="stButton"] > button{
  width:100%!important;
  min-height:2.72rem!important;
  height:2.72rem!important;
  padding:0 .84rem!important;
  border:1.25px solid rgba(217,194,143,.92)!important;
  border-radius:15px!important;
  background:linear-gradient(135deg,#FFFFFF 0%,#FFF9ED 100%)!important;
  color:#064E3B!important;
  box-shadow:0 4px 12px rgba(15,23,42,.035)!important;
  font-size:.91rem!important;
  line-height:1.06!important;
  font-weight:880!important;
  display:flex!important;
  align-items:center!important;
  justify-content:center!important;
}
.hm-dash-card [data-testid="stButton"] > button:hover{
  transform:translateY(-1px)!important;
  background:linear-gradient(135deg,#FFF9EA 0%,#FFF3D6 100%)!important;
  border-color:#B89345!important;
  color:#003C36!important;
  box-shadow:0 9px 18px rgba(15,23,42,.075)!important;
}
.hm-dash-card [data-testid="stButton"] > button:active{
  transform:translateY(0)!important;
}
.hm-communication-wrap{max-width:760px;margin:.04rem auto .94rem auto!important;}
@media(max-width:760px){
  div[data-testid="stVerticalBlockBorderWrapper"]{
    border-radius:18px!important;
    padding:.62rem .58rem!important;
    margin-bottom:.74rem!important;
  }
  .hm-admin-title-row{border-radius:18px!important;}
  .hm-communication-wrap{max-width:100%;}
}
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
<div class='hm-admin-title-row'>
  <div class='hm-admin-title'>Main Workflows</div>
  <div class='hm-admin-subtitle'>Premium admin control center with grouped workflow sections.</div>
</div>
""",
    unsafe_allow_html=True,
)


def section_header(title: str, caption: str) -> None:
    st.markdown(
        f"<div class='hm-dash-card'><div class='hm-dash-section-title'>{title}</div>"
        f"<div class='hm-dash-section-caption'>{caption}</div></div>",
        unsafe_allow_html=True,
    )


def nav_cell(label: str, page: str, key: str) -> None:
    if st.button(label, key=key, use_container_width=True):
        st.switch_page(page)


left, right = st.columns(2, gap="large")

with left:
    with st.container(border=True):
        st.markdown("<div class='hm-dash-card'>", unsafe_allow_html=True)
        section_header(
            "Review & Assessment",
            "Track member assessments, reviews and reassessment tasks.",
        )
        nav_cell("Review", "pages/26_Admin_Review_Queue.py", "dash_review_v102_4b4")
        nav_cell(
            "Evaluation Status",
            "pages/11_Evaluation_Status.py",
            "dash_eval_status_v102_4b4",
        )
        nav_cell(
            "Reassessment",
            "pages/25_Admin_Reassessment_Manager.py",
            "dash_reassessment_v102_4b4",
        )
        nav_cell(
            "NSP Compare",
            "pages/27_Comparative_NSP_Report.py",
            "dash_nsp_compare_v102_4b4",
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown("<div class='hm-dash-card'>", unsafe_allow_html=True)
        section_header(
            "Member & Access",
            "Create users and manage member/admin access controls.",
        )
        nav_cell(
            "Create Users",
            "pages/17_Admin_User_Manager.py",
            "dash_create_users_v102_4b4",
        )
        nav_cell(
            "Access Manager",
            "pages/30_Admin_User_Access_Manager.py",
            "dash_access_manager_v102_4b4",
        )
        nav_cell("Packages", "pages/41_Admin_Packages.py", "dash_packages_v102_4b14")
        st.markdown("</div>", unsafe_allow_html=True)

with right:
    with st.container(border=True):
        st.markdown("<div class='hm-dash-card'>", unsafe_allow_html=True)
        section_header(
            "Content & Allocation",
            "Manage recipes, exercises, supplements and recommendation profiles.",
        )
        nav_cell("Recipes", "pages/15_Admin_Recipe_Manager.py", "dash_recipes_v102_4b4")
        nav_cell(
            "Exercises",
            "pages/16_Admin_Exercise_Manager.py",
            "dash_exercises_v102_4b4",
        )
        nav_cell(
            "Supplements",
            "pages/39_Admin_Supplement_Manager.py",
            "dash_supplements_v102_4b4",
        )
        nav_cell(
            "Recommendation Profile Builder",
            "pages/38_Admin_Recommendation_Profile_Builder.py",
            "dash_profile_builder_h9a8b",
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown("<div class='hm-dash-card'>", unsafe_allow_html=True)
        section_header(
            "Reports & Logs",
            "Review logs, questions and response content.",
        )
        nav_cell(
            "Daily Logs",
            "pages/22_Admin_Daily_Log_Report.py",
            "dash_daily_logs_v102_4b4",
        )
        nav_cell(
            "Questions",
            "pages/20_Admin_Question_Manager.py",
            "dash_questions_v102_4b4",
        )
        nav_cell(
            "Responses",
            "pages/21_Admin_Response_Editor.py",
            "dash_responses_v102_4b4",
        )
        st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div class='hm-communication-wrap'>", unsafe_allow_html=True)
with st.container(border=True):
    st.markdown("<div class='hm-dash-card'>", unsafe_allow_html=True)
    section_header(
        "Communication & Scheduling",
        "Send messages and manage member scheduling workflows.",
    )
    message_col, schedule_col = st.columns(2, gap="large")
    with message_col:
        nav_cell(
            "Messages",
            "pages/31_Admin_Member_Communication.py",
            "dash_messages_v102_4b23",
        )
    with schedule_col:
        nav_cell(
            "Scheduling",
            "pages/32_Admin_Scheduling.py",
            "dash_scheduling_v102_4b23",
        )
    st.markdown("</div>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

inject_keepalive_guard_v96_11()
finish_and_render_page_diagnostics("Admin Dashboard")

# Final production Dashboard boundary:
# - operational Admin workflows remain available;
# - System Tools and diagnostic entry points are not exposed on the normal dashboard;
# - Exercise and Supplement member allocation launch from Meal Profile Builder;
# - obsolete technical build labels are suppressed without changing backend utilities;
# - authentication, routing, roles, RLS and business logic remain unchanged.
