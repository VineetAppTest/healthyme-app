import streamlit as st
import pandas as pd

from components.guards import require_admin
from components.ui_common import inject_global_styles, apply_luxe_theme, topbar, card_start, card_end, utility_logout_bar, stat_grid
from components.db import list_all_users_for_access_manager, update_user_access_record
from components.auth0_management import (
    auth0_config_status,
    update_auth0_user_profile,
    set_auth0_user_blocked,
    send_password_setup_email,
    check_auth0_user_status,
)
from components.flash import set_system_message, render_system_message

st.set_page_config(page_title="User Access Manager", page_icon="💚", layout="wide", initial_sidebar_state="collapsed")
inject_global_styles(); apply_luxe_theme(); require_admin(); utility_logout_bar()

topbar("User Access Manager", "Edit roles, deactivate/reactivate users, resend setup email, and check Auth0 status.", "Admin access control")
render_system_message()

users = list_all_users_for_access_manager()
active_count = len([u for u in users if u.get("is_active")])
inactive_count = len([u for u in users if not u.get("is_active")])
admin_count = len([u for u in users if u.get("role") == "admin" and u.get("is_active")])
member_count = len([u for u in users if u.get("role") == "member" and u.get("is_active")])

stat_grid([
    {"label": "Active Members", "value": member_count, "note": "Can access member flow"},
    {"label": "Active Admins", "value": admin_count, "note": "Can access admin flow"},
    {"label": "Inactive Users", "value": inactive_count, "note": "Blocked/deactivated"},
    {"label": "Total Records", "value": len(users), "note": "HealthyMe users"},
])

auth0_status = auth0_config_status()
if not all([auth0_status.get("AUTH0_DOMAIN"), auth0_status.get("AUTH0_M2M_CLIENT_ID"), auth0_status.get("AUTH0_M2M_CLIENT_SECRET"), auth0_status.get("AUTH0_CONNECTION")]):
    st.warning("Auth0 Management API provisioning is not fully configured. Edit in HealthyMe may work, but Auth0 sync actions may fail.")

card_start()
st.subheader("All users")
if users:
    df = pd.DataFrame(users)
    st.dataframe(df[["name", "email", "role", "is_active", "auth_provider"]], use_container_width=True, hide_index=True)
else:
    st.info("No users found.")
card_end()

if not users:
    st.stop()

card_start()
st.subheader("Edit / deactivate / reactivate")
selected_label = st.selectbox(
    "Select user",
    [f"{u['id']} — {u['name']} — {u['email']} — {u['role']} — {'Active' if u['is_active'] else 'Inactive'}" for u in users]
)
uid = selected_label.split(" — ")[0]
user = next(u for u in users if u["id"] == uid)

st.markdown(f"**Selected:** {user['name']} — `{user['email']}`")

with st.form("edit_user_form"):
    new_name = st.text_input("Name", value=user["name"])
    new_role = st.selectbox("Role", ["member", "admin"], index=0 if user["role"] == "member" else 1)
    new_active = st.checkbox("Active", value=bool(user["is_active"]))
    st.caption("Email editing is intentionally disabled in this MVP to avoid identity mismatch between Auth0 and HealthyMe history.")
    submitted = st.form_submit_button("Save Changes", type="primary", use_container_width=True)

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
        # Sync display name
        profile_result = update_auth0_user_profile(old_email, name=new_name)
        auth0_msgs.append(profile_result.get("message", ""))

        # Sync active status as blocked/unblocked
        block_result = set_auth0_user_blocked(old_email, blocked=not new_active)
        auth0_msgs.append(block_result.get("message", ""))

        set_system_message(
            msg + " Auth0 sync: " + " ".join([m for m in auth0_msgs if m]),
            "success",
            celebrate=True,
        )
    else:
        set_system_message(msg, "error")
    st.rerun()

st.divider()
c1, c2, c3 = st.columns(3)
with c1:
    if st.button("Check Auth0 Status", use_container_width=True):
        status = check_auth0_user_status(user["email"])
        if status.get("ok"):
            st.info(f"{status.get('message')} Exists: {status.get('exists')}, Blocked: {status.get('blocked')}, Email verified: {status.get('email_verified')}")
        else:
            st.error(status.get("message"))
with c2:
    if st.button("Resend Password Setup Email", use_container_width=True):
        ok, msg = send_password_setup_email(user["email"])
        set_system_message(msg, "success" if ok else "error")
        st.rerun()
with c3:
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

if st.button("Back to Dashboard"):
    st.switch_page("pages/10_Admin_Dashboard.py")