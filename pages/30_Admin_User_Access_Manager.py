import pandas as pd
import streamlit as st

from components.auth0_management import (
    auth0_config_status,
    check_auth0_user_status,
    provision_auth0_user,
    send_password_setup_email,
    set_auth0_user_blocked,
    update_auth0_user_profile,
)
from components.db import (
    link_user_auth0_record_v1024b14g,
    list_all_users_for_access_manager,
    update_user_access_record,
)
from components.flash import render_system_message, set_system_message
from components.guards import require_admin
from components.ui_common import (
    apply_luxe_theme,
    card_end,
    card_start,
    inject_global_styles,
    render_back_to_top,
    render_page_nav,
    stat_grid,
    topbar,
    utility_logout_bar,
)


SELECTED_USER_KEY = "hm_access_selected_user_id"
FORM_VERSION_PREFIX = "hm_access_form_version_"
CLEANUP_KEY = "hm_access_cleanup_keys"


def _form_version(user_id: str) -> int:
    key = f"{FORM_VERSION_PREFIX}{user_id}"
    return max(int(st.session_state.get(key, 1) or 1), 1)


def _bump_form_version(user_id: str) -> None:
    key = f"{FORM_VERSION_PREFIX}{user_id}"
    st.session_state[key] = _form_version(user_id) + 1


def _consume_form_cleanup() -> None:
    keys = st.session_state.pop(CLEANUP_KEY, ())
    for key in keys or ():
        st.session_state.pop(str(key), None)


def _user_label(user: dict) -> str:
    return (
        f"{user.get('id', '')} — {user.get('name', '')} — "
        f"{user.get('email', '')} — {user.get('role', '')} — "
        f"{'Active' if user.get('is_active') else 'Inactive'}"
    )


st.set_page_config(
    page_title="User Access Manager",
    page_icon="💚",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_global_styles()
apply_luxe_theme()
require_admin()
utility_logout_bar()
_consume_form_cleanup()

topbar(
    "User Access Manager",
    "Edit roles, deactivate/reactivate users, resend setup email, and check Auth0 status.",
    "Admin access control",
)
render_system_message()

users = list_all_users_for_access_manager()
active_count = len([u for u in users if u.get("is_active")])
inactive_count = len([u for u in users if not u.get("is_active")])
admin_count = len(
    [u for u in users if u.get("role") == "admin" and u.get("is_active")]
)
member_count = len(
    [u for u in users if u.get("role") == "member" and u.get("is_active")]
)

stat_grid(
    [
        {
            "label": "Active Members",
            "value": member_count,
            "note": "Can access member flow",
        },
        {
            "label": "Active Admins",
            "value": admin_count,
            "note": "Can access admin flow",
        },
        {
            "label": "Inactive Users",
            "value": inactive_count,
            "note": "Blocked/deactivated",
        },
        {
            "label": "Total Records",
            "value": len(users),
            "note": "HealthyMe users",
        },
    ]
)

auth0_status = auth0_config_status()
if not all(
    [
        auth0_status.get("AUTH0_DOMAIN"),
        auth0_status.get("AUTH0_M2M_CLIENT_ID"),
        auth0_status.get("AUTH0_M2M_CLIENT_SECRET"),
        auth0_status.get("AUTH0_CONNECTION"),
    ]
):
    st.warning(
        "Auth0 Management API provisioning is not fully configured. Edit in HealthyMe may work, but Auth0 sync actions may fail."
    )

card_start()
st.subheader("All users")
if users:
    df = pd.DataFrame(users)
    st.dataframe(
        df[["name", "email", "role", "is_active", "auth_provider"]],
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info("No users found.")
card_end()

if not users:
    st.stop()

card_start()
st.subheader("Edit / deactivate / reactivate")
user_map = {str(user.get("id", "")): user for user in users if user.get("id")}
user_ids = list(user_map.keys())
selected_user_id = st.selectbox(
    "Select user",
    user_ids,
    format_func=lambda user_id: _user_label(user_map[user_id]),
    key=SELECTED_USER_KEY,
)
user = user_map[selected_user_id]
uid = str(user["id"])
version = _form_version(uid)

st.markdown(f"**Selected:** {user['name']} — `{user['email']}`")

name_key = f"hm_access_name_{uid}_v{version}"
role_key = f"hm_access_role_{uid}_v{version}"
active_key = f"hm_access_active_{uid}_v{version}"

with st.form(f"edit_user_form_{uid}_v{version}", clear_on_submit=False):
    new_name = st.text_input("Name", value=user["name"], key=name_key)
    new_role = st.selectbox(
        "Role",
        ["member", "admin"],
        index=0 if user["role"] == "member" else 1,
        key=role_key,
    )
    new_active = st.checkbox(
        "Active",
        value=bool(user["is_active"]),
        key=active_key,
    )
    st.caption(
        "Email editing is intentionally disabled in this MVP to avoid identity mismatch between Auth0 and HealthyMe history."
    )
    submitted = st.form_submit_button(
        "Save Changes",
        type="primary",
        use_container_width=True,
    )

if submitted:
    old_email = user["email"]
    ok, msg = update_user_access_record(
        uid,
        name=new_name,
        role=new_role,
        is_active=new_active,
        actor=st.session_state.get("user_id", "admin"),
    )
    auth0_msgs = []
    if ok:
        profile_result = update_auth0_user_profile(old_email, name=new_name)
        auth0_msgs.append(profile_result.get("message", ""))

        block_result = set_auth0_user_blocked(old_email, blocked=not new_active)
        auth0_msgs.append(block_result.get("message", ""))

        set_system_message(
            msg + " Auth0 sync: " + " ".join([m for m in auth0_msgs if m]),
            "success",
            celebrate=True,
        )
        st.session_state[CLEANUP_KEY] = (name_key, role_key, active_key)
        _bump_form_version(uid)
    else:
        set_system_message(msg, "error")
    st.rerun()

st.divider()
c1, c2, c3, c4 = st.columns(4)
with c1:
    if st.button("Check Auth0 Status", use_container_width=True):
        status = check_auth0_user_status(user["email"])
        if status.get("ok"):
            st.info(
                f"{status.get('message')} Exists: {status.get('exists')}, Blocked: {status.get('blocked')}, Email verified: {status.get('email_verified')}"
            )
        else:
            st.error(status.get("message"))
with c2:
    if st.button("Create / Repair Auth0 User", use_container_width=True):
        prov = provision_auth0_user(
            user["email"],
            user.get("name", ""),
            send_setup_email=True,
        )
        if prov.get("ok"):
            link_user_auth0_record_v1024b14g(
                user["id"],
                auth0_user_id=prov.get("auth0_user_id", ""),
                auth0_email_verified=prov.get("auth0_email_verified", False),
                actor=st.session_state.get("user_id", "admin"),
            )
            set_system_message(
                "Auth0 user is now linked to the HealthyMe user record. "
                + str(prov.get("message", "")),
                "success",
            )
        else:
            set_system_message(
                "Auth0 repair failed: " + str(prov.get("message", "")),
                "error",
            )
        st.rerun()
with c3:
    if st.button("Resend Password Setup Email", use_container_width=True):
        ok, msg = send_password_setup_email(user["email"])
        set_system_message(msg, "success" if ok else "error")
        st.rerun()
with c4:
    st.button("Hard Delete - Disabled", disabled=True, use_container_width=True)
    st.caption("Hard delete is intentionally disabled. Use deactivate for now.")

card_end()

card_start()
st.subheader("Recommended operating rule")
st.markdown(
    """
    <div class='info-banner'>
      <b>Use Deactivate instead of hard delete.</b><br>
      Deactivation keeps historical LAF/NSP/reports intact and blocks login by setting the user inactive in HealthyMe and blocked in Auth0.
    </div>
    """,
    unsafe_allow_html=True,
)
card_end()

render_page_nav(
    "Access Manager",
    back_page="pages/10_Admin_Dashboard.py",
    dashboard_page="pages/10_Admin_Dashboard.py",
    show_evaluation=False,
    show_dashboard=True,
    location="bottom",
)
render_back_to_top()
