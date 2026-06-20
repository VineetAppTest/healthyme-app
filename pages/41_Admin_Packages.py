import streamlit as st

from components.guards import require_admin
from components.ui_common import inject_global_styles, apply_luxe_theme, utility_logout_bar, topbar, render_page_nav, render_back_to_top
from components.db import (
    list_members,
    create_package_v1024b14,
    list_packages_v1024b14,
    assign_member_package_v1024b14,
    list_member_packages_v1024b14,
)

st.set_page_config(page_title="Packages", page_icon="💚", layout="wide", initial_sidebar_state="collapsed")
inject_global_styles()
apply_luxe_theme()
require_admin()
utility_logout_bar()
topbar("Packages", "Create predefined service packages and subscribe members to them.", "Admin workflow")

st.markdown("""
<style>
section.main > div.block-container,.main .block-container,[data-testid="stAppViewBlockContainer"],.stMainBlockContainer,.block-container{max-width:1120px!important;padding-top:.72rem!important;}
.hm-b14-package-card{border:1.25px solid #E3C98E;background:linear-gradient(180deg,#FFFDF8 0%,#FFF9EC 100%);border-radius:20px;padding:1rem 1.05rem;margin:.35rem 0 .95rem 0;box-shadow:0 10px 24px rgba(15,23,42,.05);}
.hm-b14-title{color:#064E3B;font-size:1.04rem;font-weight:850;margin:0 0 .22rem 0;}
.hm-b14-sub{color:#72551A;font-size:.82rem;font-weight:560;margin:0 0 .82rem 0;}
.hm-b14-row{border:1px solid #E3C98E;border-radius:16px;background:#FFFDF8;padding:.78rem .88rem;margin:.52rem 0;}
.hm-b14-row-title{color:#064E3B;font-size:.94rem;font-weight:760;margin-bottom:.18rem;}
.hm-b14-line{color:#334155;font-size:.82rem;font-weight:520;margin:.06rem 0;}
div[data-testid="stButton"] > button{min-height:2.72rem!important;border-radius:14px!important;border:1.25px solid #D9C28F!important;background:#FFFDF8!important;color:#064E3B!important;font-weight:500!important;box-shadow:none!important;}
div[data-testid="stButton"] > button:hover{border-color:#B89345!important;background:#FFF7E6!important;}
</style>
""", unsafe_allow_html=True)

left, right = st.columns(2, gap="large")

with left:
    st.markdown("<div class='hm-b14-package-card'>", unsafe_allow_html=True)
    st.markdown("<div class='hm-b14-title'>Create Package</div>", unsafe_allow_html=True)
    st.markdown("<div class='hm-b14-sub'>Define reusable package options for admin selection.</div>", unsafe_allow_html=True)
    package_name = st.text_input("Package name", placeholder="Example: 4-session Wellness Package")
    c1, c2 = st.columns(2, gap="medium")
    with c1:
        session_count = st.number_input("Count of sessions", min_value=1, value=1, step=1)
        currency = st.selectbox("Currency", ["INR", "USD", "AED", "GBP", "EUR"], index=0)
    with c2:
        cost_per_session = st.number_input("Cost of each session", min_value=0.0, value=0.0, step=100.0, format="%.2f")
        number_of_people = st.number_input("Number of people", min_value=1, value=1, step=1)
    st.markdown("<div class='hm-b14-sub'>Inclusions</div>", unsafe_allow_html=True)
    inc1, inc2 = st.columns(2, gap="medium")
    with inc1:
        inc_eval = st.checkbox("Evaluation", value=True)
        inc_meal = st.checkbox("Meal plan", value=True)
        inc_ex = st.checkbox("Exercise plan", value=True)
    with inc2:
        inc_supp = st.checkbox("Supplement plan", value=True)
        inc_review = st.checkbox("Review sessions", value=True)
    if st.button("Create Package", use_container_width=True):
        pkg = create_package_v1024b14(
            package_name=package_name,
            session_count=session_count,
            cost_per_session=cost_per_session,
            currency=currency,
            number_of_people=number_of_people,
            inclusions={
                "Evaluation": inc_eval,
                "Meal plan": inc_meal,
                "Exercise plan": inc_ex,
                "Supplement plan": inc_supp,
                "Review sessions": inc_review,
            },
            actor_id=st.session_state.get("user_id", "admin"),
        )
        st.success(f"Package created: {pkg.get('package_name')}")
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

with right:
    st.markdown("<div class='hm-b14-package-card'>", unsafe_allow_html=True)
    st.markdown("<div class='hm-b14-title'>List of Packages</div>", unsafe_allow_html=True)
    st.markdown("<div class='hm-b14-sub'>Internal admin list. Select a predefined plan and assign it to a member.</div>", unsafe_allow_html=True)
    packages = list_packages_v1024b14(active_only=True)
    members = list_members()
    if not packages:
        st.info("No packages have been created yet.")
    else:
        package_options = {f"{p.get('package_name','Package')} · {p.get('session_count',0)} sessions · {p.get('currency','INR')} {float(p.get('cost_per_session',0) or 0):,.2f}/session": p.get("id") for p in packages}
        selected_pkg_label = st.selectbox("Select package", list(package_options.keys()))
        member_options = {f"{m.get('name','')} — {m.get('email','')}": m.get("id") for m in members}
        selected_member_label = st.selectbox("Assign to member", list(member_options.keys())) if member_options else None
        if st.button("Subscribe Member to Package", use_container_width=True, disabled=not selected_member_label):
            result = assign_member_package_v1024b14(
                member_id=member_options[selected_member_label],
                package_id=package_options[selected_pkg_label],
                actor_id=st.session_state.get("user_id", "admin"),
            )
            if result and result.get("error"):
                st.error(result.get("error"))
            else:
                st.success("Package subscribed for selected member.")
                st.rerun()
        for p in packages:
            inc = ", ".join([k for k, v in (p.get("inclusions", {}) or {}).items() if v]) or "No inclusions selected"
            st.markdown(
                f"<div class='hm-b14-row'><div class='hm-b14-row-title'>{p.get('package_name','Package')}</div>"
                f"<div class='hm-b14-line'>{p.get('session_count',0)} sessions · {p.get('currency','INR')} {float(p.get('cost_per_session',0) or 0):,.2f} per session · {p.get('number_of_people',1)} people</div>"
                f"<div class='hm-b14-line'>Inclusions: {inc}</div></div>",
                unsafe_allow_html=True,
            )
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div class='hm-b14-package-card'>", unsafe_allow_html=True)
st.markdown("<div class='hm-b14-title'>Member Subscriptions</div>", unsafe_allow_html=True)
member_packages = list_member_packages_v1024b14()
if not member_packages:
    st.info("No member package subscription has been recorded yet.")
else:
    for sub in member_packages[:30]:
        inc = ", ".join([k for k, v in (sub.get("inclusions", {}) or {}).items() if v]) or "No inclusions selected"
        st.markdown(
            f"<div class='hm-b14-row'><div class='hm-b14-row-title'>{sub.get('member_name') or sub.get('member_email','Member')} · {sub.get('package_name','Package')}</div>"
            f"<div class='hm-b14-line'>{sub.get('session_count',0)} sessions · {sub.get('currency','INR')} {float(sub.get('cost_per_session',0) or 0):,.2f} per session · Status: {sub.get('status','active').title()}</div>"
            f"<div class='hm-b14-line'>Inclusions: {inc}</div></div>",
            unsafe_allow_html=True,
        )
st.markdown("</div>", unsafe_allow_html=True)

render_page_nav("Packages", back_page="pages/10_Admin_Dashboard.py", dashboard_page="pages/10_Admin_Dashboard.py", show_evaluation=False, show_dashboard=True, location="bottom")
render_back_to_top()
