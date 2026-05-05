import streamlit as st, pandas as pd, re
from components.guards import require_admin
from components.ui_common import inject_global_styles, apply_luxe_theme, topbar, card_start, card_end, utility_logout_bar
from components.db import create_user, load_db
from components.auth0_management import provision_auth0_user, auth0_config_status

st.set_page_config(page_title="Admin User Manager", page_icon="💚", layout="wide", initial_sidebar_state="collapsed")
inject_global_styles(); apply_luxe_theme(); require_admin(); utility_logout_bar()

def valid_email(e):
    return re.match(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$", (e or "").strip()) is not None

def valid_name(n):
    n = (n or "").strip()
    return len(n) >= 2 and "@" not in n and re.match(r"^[A-Za-z][A-Za-z .'-]{1,80}$", n) is not None

def email_exists(e):
    return any(u["email"].lower() == (e or "").strip().lower() for u in load_db()["users"])

# Streamlit-safe clearing:
# Widget state cannot be changed after the widget has been rendered in the same run.
# So we clear fields only at the very start of the next rerun.
if st.session_state.pop("clear_member_fields_next_run", False):
    st.session_state["member_name_input"] = ""
    st.session_state["member_email_input"] = ""

if st.session_state.pop("clear_admin_fields_next_run", False):
    st.session_state["admin_name_input"] = ""
    st.session_state["admin_email_input"] = ""

topbar("Create Members / Admins", "Create users once in HealthyMe. Auth0 provisioning runs in the background.", "Admin access manager")

auth0_status = auth0_config_status()
if not all([auth0_status.get("AUTH0_DOMAIN"), auth0_status.get("AUTH0_M2M_CLIENT_ID"), auth0_status.get("AUTH0_M2M_CLIENT_SECRET"), auth0_status.get("AUTH0_CONNECTION")]):
    st.warning("Auth0 provisioning is not fully configured. HealthyMe users can still be created, but Auth0 invite/user creation may not happen.")

# Show success messages after rerun, once the fields have been safely cleared.
if "create_user_success_msg" in st.session_state:
    st.success(st.session_state.pop("create_user_success_msg"))

left, right = st.columns(2)

with left:
    card_start()
    st.subheader("Create Member")
    n = st.text_input("Member name", key="member_name_input")
    e = st.text_input("Member email", key="member_email_input")

    if st.button("Create Member", type="primary", use_container_width=True):
        if not valid_name(n):
            st.error("Please enter a valid member name.")
        elif not valid_email(e):
            st.error("Please enter a valid email address.")
        elif email_exists(e):
            st.error("This email is already registered.")
        else:
            create_user(n.strip(), e.strip().lower(), "member")
            prov = provision_auth0_user(e.strip().lower(), n.strip(), send_setup_email=True)
            if prov.get("ok"):
                st.session_state["create_user_success_msg"] = "Member created in HealthyMe and Auth0 provisioning completed. " + str(prov.get("message", ""))
            else:
                st.session_state["create_user_success_msg"] = "Member created in HealthyMe. Auth0 provisioning needs attention: " + str(prov.get("message", ""))
            st.session_state["clear_member_fields_next_run"] = True
            st.rerun()
    card_end()

with right:
    card_start()
    st.subheader("Create Admin")
    n = st.text_input("Admin name", key="admin_name_input")
    e = st.text_input("Admin email", key="admin_email_input")

    if st.button("Create Admin", type="primary", use_container_width=True):
        if not valid_name(n):
            st.error("Please enter a valid admin name.")
        elif not valid_email(e):
            st.error("Please enter a valid email address.")
        elif email_exists(e):
            st.error("This email is already registered.")
        else:
            create_user(n.strip(), e.strip().lower(), "admin")
            prov = provision_auth0_user(e.strip().lower(), n.strip(), send_setup_email=True)
            if prov.get("ok"):
                st.session_state["create_user_success_msg"] = "Admin created in HealthyMe and Auth0 provisioning completed. " + str(prov.get("message", ""))
            else:
                st.session_state["create_user_success_msg"] = "Admin created in HealthyMe. Auth0 provisioning needs attention: " + str(prov.get("message", ""))
            st.session_state["clear_admin_fields_next_run"] = True
            st.rerun()
    card_end()

card_start()
st.subheader("Existing users")
st.dataframe(
    pd.DataFrame([{k: v for k, v in u.items() if k != "password_hash"} for u in load_db()["users"]]),
    use_container_width=True
)
if st.button("Back to Dashboard"):
    st.switch_page("pages/10_Admin_Dashboard.py")
card_end()