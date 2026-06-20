import streamlit as st

from components.guards import require_admin
from components.ui_common import inject_global_styles, apply_luxe_theme, utility_logout_bar, topbar, render_page_nav, render_back_to_top
from components.db import (
    list_members,
    create_package_v1024b14,
    update_package_v1024b14,
    list_packages_v1024b14,
    assign_member_package_v1024b14,
    list_member_packages_v1024b14,
)

st.set_page_config(page_title="Packages", page_icon="💚", layout="wide", initial_sidebar_state="collapsed")
inject_global_styles()
apply_luxe_theme()
require_admin()
utility_logout_bar()
topbar("Packages", "Create, edit and assign predefined wellness packages.", "Admin workflow")

st.markdown("""
<style>
section.main > div.block-container,.main .block-container,[data-testid="stAppViewBlockContainer"],.stMainBlockContainer,.block-container{max-width:1120px!important;padding-top:.72rem!important;}
.hm-b14-package-card{border:1.25px solid #E3C98E;background:linear-gradient(180deg,#FFFDF8 0%,#FFF9EC 100%);border-radius:20px;padding:1rem 1.05rem;margin:.35rem 0 .95rem 0;box-shadow:0 10px 24px rgba(15,23,42,.05);}
.hm-b14-title{color:#064E3B;font-size:1.04rem;font-weight:760;margin:0 0 .22rem 0;}
.hm-b14-sub{color:#72551A;font-size:.82rem;font-weight:520;margin:0 0 .82rem 0;}
.hm-b14-row{border:1px solid #E3C98E;border-radius:16px;background:#FFFDF8;padding:.78rem .88rem;margin:.52rem 0;}
.hm-b14-row-title{color:#064E3B;font-size:.94rem;font-weight:640;margin-bottom:.18rem;}
.hm-b14-line{color:#334155;font-size:.82rem;font-weight:500;margin:.06rem 0;}
.hm-b14-mini{display:inline-block;padding:.22rem .55rem;border-radius:999px;border:1px solid #E3C98E;background:#FFF8E8;color:#72551A;font-size:.74rem;margin:.14rem .2rem .14rem 0;}
div[data-testid="stTabs"] button p{font-weight:520!important;color:#064E3B!important;}
div[data-testid="stButton"] > button{min-height:2.72rem!important;border-radius:14px!important;border:1.25px solid #D9C28F!important;background:#FFFDF8!important;color:#064E3B!important;font-weight:500!important;box-shadow:none!important;}
div[data-testid="stButton"] > button:hover{border-color:#B89345!important;background:#FFF7E6!important;}
</style>
""", unsafe_allow_html=True)

CURRENCIES = ["INR", "USD", "AED", "GBP", "EUR"]
INCLUSION_KEYS = ["Evaluation", "Meal plan", "Exercise plan", "Supplement plan", "Review sessions"]

def _inclusion_payload(prefix, defaults=None):
    defaults = defaults or {}
    c1, c2 = st.columns(2, gap="medium")
    values = {}
    with c1:
        values["Evaluation"] = st.checkbox("Evaluation", value=bool(defaults.get("Evaluation", True)), key=f"{prefix}_inc_eval")
        values["Meal plan"] = st.checkbox("Meal plan", value=bool(defaults.get("Meal plan", True)), key=f"{prefix}_inc_meal")
        values["Exercise plan"] = st.checkbox("Exercise plan", value=bool(defaults.get("Exercise plan", True)), key=f"{prefix}_inc_ex")
    with c2:
        values["Supplement plan"] = st.checkbox("Supplement plan", value=bool(defaults.get("Supplement plan", True)), key=f"{prefix}_inc_supp")
        values["Review sessions"] = st.checkbox("Review sessions", value=bool(defaults.get("Review sessions", True)), key=f"{prefix}_inc_review")
    return values

def _currency_index(value):
    try:
        return CURRENCIES.index(str(value or "INR"))
    except ValueError:
        return 0

def _status_index(value):
    statuses = ["active", "inactive"]
    try:
        return statuses.index(str(value or "active").lower())
    except ValueError:
        return 0

packages_all = list_packages_v1024b14(active_only=False)
packages_active = [p for p in packages_all if str(p.get("status", "active")).lower() == "active"]
member_packages = list_member_packages_v1024b14()

tab_create, tab_list, tab_subs = st.tabs([
    "Create Package",
    f"List of Packages ({len(packages_all)})",
    f"Member Subscriptions ({len(member_packages)})",
])

with tab_create:
    st.markdown("<div class='hm-b14-package-card'>", unsafe_allow_html=True)
    st.markdown("<div class='hm-b14-title'>Create Package</div>", unsafe_allow_html=True)
    st.markdown("<div class='hm-b14-sub'>Create reusable package options for admin selection and member subscription.</div>", unsafe_allow_html=True)

    package_name = st.text_input("Package name", placeholder="Example: 4-session Wellness Package", key="pkg_create_name")
    c1, c2, c3, c4 = st.columns(4, gap="medium")
    with c1:
        session_count = st.number_input("Count of sessions", min_value=1, value=1, step=1, key="pkg_create_sessions")
    with c2:
        cost_per_session = st.number_input("Cost of each session", min_value=0.0, value=0.0, step=100.0, format="%.2f", key="pkg_create_cost")
    with c3:
        currency = st.selectbox("Currency", CURRENCIES, index=0, key="pkg_create_currency")
    with c4:
        number_of_people = st.number_input("Number of people", min_value=1, value=1, step=1, key="pkg_create_people")

    st.markdown("<div class='hm-b14-sub'>Inclusions</div>", unsafe_allow_html=True)
    inclusions = _inclusion_payload("pkg_create")

    if st.button("Create Package", use_container_width=True, key="pkg_create_btn"):
        pkg = create_package_v1024b14(
            package_name=package_name,
            session_count=session_count,
            cost_per_session=cost_per_session,
            currency=currency,
            number_of_people=number_of_people,
            inclusions=inclusions,
            actor_id=st.session_state.get("user_id", "admin"),
        )
        st.success(f"Package created: {pkg.get('package_name')}")
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

with tab_list:
    st.markdown("<div class='hm-b14-package-card'>", unsafe_allow_html=True)
    st.markdown("<div class='hm-b14-title'>List of Packages</div>", unsafe_allow_html=True)
    st.markdown("<div class='hm-b14-sub'>View and edit predefined packages. Inactive packages remain visible here but are not offered for new subscriptions.</div>", unsafe_allow_html=True)

    if not packages_all:
        st.info("No packages have been created yet.")
    else:
        package_options = {
            f"{p.get('package_name','Package')} · {p.get('session_count',0)} sessions · {p.get('currency','INR')} {float(p.get('cost_per_session',0) or 0):,.2f}/session · {str(p.get('status','active')).title()}": p.get("id")
            for p in packages_all
        }
        selected_label = st.selectbox("Select package to edit", list(package_options.keys()), key="pkg_edit_select")
        selected_id = package_options[selected_label]
        selected_pkg = next((p for p in packages_all if p.get("id") == selected_id), None)

        if selected_pkg:
            with st.form("pkg_edit_form", clear_on_submit=False):
                st.markdown("<div class='hm-b14-title'>Edit Package</div>", unsafe_allow_html=True)
                edit_name = st.text_input("Package name", value=selected_pkg.get("package_name", ""), key="pkg_edit_name")
                e1, e2, e3, e4, e5 = st.columns(5, gap="medium")
                with e1:
                    edit_sessions = st.number_input("Count of sessions", min_value=1, value=int(selected_pkg.get("session_count", 1) or 1), step=1, key="pkg_edit_sessions")
                with e2:
                    edit_cost = st.number_input("Cost of each session", min_value=0.0, value=float(selected_pkg.get("cost_per_session", 0) or 0), step=100.0, format="%.2f", key="pkg_edit_cost")
                with e3:
                    edit_currency = st.selectbox("Currency", CURRENCIES, index=_currency_index(selected_pkg.get("currency")), key="pkg_edit_currency")
                with e4:
                    edit_people = st.number_input("Number of people", min_value=1, value=int(selected_pkg.get("number_of_people", 1) or 1), step=1, key="pkg_edit_people")
                with e5:
                    edit_status = st.selectbox("Status", ["active", "inactive"], index=_status_index(selected_pkg.get("status")), key="pkg_edit_status")
                st.markdown("<div class='hm-b14-sub'>Inclusions</div>", unsafe_allow_html=True)
                edit_inclusions = _inclusion_payload("pkg_edit", selected_pkg.get("inclusions", {}) or {})
                submitted = st.form_submit_button("Update Package", use_container_width=True)
                if submitted:
                    result = update_package_v1024b14(
                        package_id=selected_id,
                        package_name=edit_name,
                        session_count=edit_sessions,
                        cost_per_session=edit_cost,
                        currency=edit_currency,
                        number_of_people=edit_people,
                        inclusions=edit_inclusions,
                        status=edit_status,
                        actor_id=st.session_state.get("user_id", "admin"),
                    )
                    if result and result.get("error"):
                        st.error(result.get("error"))
                    else:
                        st.success("Package updated successfully.")
                        st.rerun()

        st.markdown("<div class='hm-b14-title'>Package Library</div>", unsafe_allow_html=True)
        for p in packages_all:
            inc = ", ".join([k for k, v in (p.get("inclusions", {}) or {}).items() if v]) or "No inclusions selected"
            st.markdown(
                f"<div class='hm-b14-row'><div class='hm-b14-row-title'>{p.get('package_name','Package')} <span class='hm-b14-mini'>{str(p.get('status','active')).title()}</span></div>"
                f"<div class='hm-b14-line'>{p.get('session_count',0)} sessions · {p.get('currency','INR')} {float(p.get('cost_per_session',0) or 0):,.2f} per session · {p.get('number_of_people',1)} people</div>"
                f"<div class='hm-b14-line'>Inclusions: {inc}</div></div>",
                unsafe_allow_html=True,
            )
    st.markdown("</div>", unsafe_allow_html=True)

with tab_subs:
    st.markdown("<div class='hm-b14-package-card'>", unsafe_allow_html=True)
    st.markdown("<div class='hm-b14-title'>Member Subscriptions</div>", unsafe_allow_html=True)
    st.markdown("<div class='hm-b14-sub'>Assign an active package to a member and review subscription history.</div>", unsafe_allow_html=True)

    members = list_members()
    if not packages_active:
        st.info("Create and activate at least one package before subscribing a member.")
    elif not members:
        st.info("No members are available for package subscription.")
    else:
        c1, c2 = st.columns(2, gap="large")
        with c1:
            package_options = {f"{p.get('package_name','Package')} · {p.get('session_count',0)} sessions · {p.get('currency','INR')} {float(p.get('cost_per_session',0) or 0):,.2f}/session": p.get("id") for p in packages_active}
            selected_pkg_label = st.selectbox("Select active package", list(package_options.keys()), key="pkg_sub_package")
        with c2:
            member_options = {f"{m.get('name','')} — {m.get('email','')}": m.get("id") for m in members}
            selected_member_label = st.selectbox("Assign to member", list(member_options.keys()), key="pkg_sub_member")
        if st.button("Subscribe Member to Package", use_container_width=True, key="pkg_sub_btn", disabled=not selected_member_label):
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

    st.markdown("<div class='hm-b14-title'>Subscription History</div>", unsafe_allow_html=True)
    member_packages = list_member_packages_v1024b14()
    if not member_packages:
        st.info("No member package subscription has been recorded yet.")
    else:
        for sub in member_packages[:50]:
            inc = ", ".join([k for k, v in (sub.get("inclusions", {}) or {}).items() if v]) or "No inclusions selected"
            st.markdown(
                f"<div class='hm-b14-row'><div class='hm-b14-row-title'>{sub.get('member_name') or sub.get('member_email','Member')} · {sub.get('package_name','Package')} <span class='hm-b14-mini'>{str(sub.get('status','active')).title()}</span></div>"
                f"<div class='hm-b14-line'>{sub.get('session_count',0)} sessions · {sub.get('currency','INR')} {float(sub.get('cost_per_session',0) or 0):,.2f} per session · {sub.get('number_of_people',1)} people</div>"
                f"<div class='hm-b14-line'>Inclusions: {inc}</div></div>",
                unsafe_allow_html=True,
            )
    st.markdown("</div>", unsafe_allow_html=True)

render_page_nav("Packages", back_page="pages/10_Admin_Dashboard.py", dashboard_page="pages/10_Admin_Dashboard.py", show_evaluation=False, show_dashboard=True, location="bottom")
render_back_to_top()
