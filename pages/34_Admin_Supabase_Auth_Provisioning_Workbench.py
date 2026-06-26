import os
from typing import Any, Dict, List, Optional, Set, Tuple

import pandas as pd
import streamlit as st

from components.auth_mode import supabase_auth_enabled
from components.auth_session import restore_login_from_token
from components.normalized_store import find_user_by_email_fast
from components.supabase_auth_session import restore_supabase_login_from_session
from components.ui_common import (
    apply_luxe_theme,
    card_end,
    card_start,
    inject_global_styles,
    render_back_to_top,
    render_page_nav,
    topbar,
    utility_logout_bar,
)


st.set_page_config(
    page_title="Supabase Auth Provisioning Workbench",
    page_icon="HM",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_global_styles()
apply_luxe_theme()


if not st.session_state.get("logged_in"):
    try:
        if supabase_auth_enabled():
            restore_supabase_login_from_session()
    except Exception:
        pass

if not st.session_state.get("logged_in"):
    try:
        restore_login_from_token()
    except Exception:
        pass

if not st.session_state.get("logged_in"):
    st.info("Please sign in as an admin to view the Supabase Auth provisioning workbench.")
    st.stop()

if st.session_state.get("user_role") != "admin":
    st.warning("Admin access required")
    st.stop()

utility_logout_bar()
topbar(
    "Supabase Auth Provisioning Workbench",
    "One-email-at-a-time supervised provisioning for controlled Supabase Auth pilot operations.",
    "Admin auth provisioning",
)


SECRET_SECTIONS = ("auth", "auth0", "authentication", "healthyme", "supabase")
ACTION_NONE = "No email action"
ACTION_INVITE = "Send Supabase invite for missing user"
ACTION_RECOVERY = "Send Supabase recovery/reset email for existing user"
ACTION_OPTIONS = (ACTION_NONE, ACTION_INVITE, ACTION_RECOVERY)
SERVICE_ROLE_REQUIRED = "Service-role server-side access is required for provisioning actions."
CONFIRMATION_TEXT = "PROVISION"
VALID_ROLES = {"admin", "member"}
READINESS_STATE_KEY = "supabase_auth_provisioning_readiness_result"


def _clean_value(value: object, default: str = "") -> str:
    if value is None:
        return default
    return str(value).strip()


def _get_secret(name: str, default: str = "") -> str:
    value = os.environ.get(name)
    if value:
        return _clean_value(value, default)

    try:
        value = st.secrets.get(name)
        if value is not None:
            return _clean_value(value, default)

        lower_name = name.lower()
        value = st.secrets.get(lower_name)
        if value is not None:
            return _clean_value(value, default)

        for section in SECRET_SECTIONS:
            section_values = st.secrets.get(section)
            if not section_values:
                continue
            try:
                value = section_values.get(name)
                if value is None:
                    value = section_values.get(lower_name)
                if value is not None:
                    return _clean_value(value, default)
            except Exception:
                continue
    except Exception:
        pass

    return default


def _normalize_email(email: str) -> str:
    return (email or "").strip().lower()


def _yes_no_unknown(value: Optional[bool]) -> str:
    if value is None:
        return "unknown"
    return "yes" if value else "no"


def _config_status() -> Dict[str, bool]:
    return {
        "SUPABASE_URL": bool(_get_secret("SUPABASE_URL")),
        "SUPABASE_SERVICE_ROLE_KEY": bool(_get_secret("SUPABASE_SERVICE_ROLE_KEY")),
    }


def _service_role_client():
    url = _get_secret("SUPABASE_URL")
    key = _get_secret("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        return None
    try:
        from supabase import create_client

        return create_client(url, key)
    except Exception:
        return None


def _hm_user_unknown(source: str = "unknown") -> Dict[str, Any]:
    return {
        "exists": None,
        "role": "other",
        "active": None,
        "source": source,
    }


def _lookup_hm_user(email: str, service_client: Any) -> Dict[str, Any]:
    if not email:
        return _hm_user_unknown("missing email")

    if service_client is not None:
        try:
            result = (
                service_client.table("hm_users")
                .select("email,role,is_active")
                .eq("email", email)
                .limit(1)
                .execute()
            )
            rows = list(getattr(result, "data", None) or [])
            if not rows:
                return {"exists": False, "role": "other", "active": False, "source": "hm_users via service role"}
            row = rows[0]
            return {
                "exists": True,
                "role": str(row.get("role") or "other").strip().lower(),
                "active": bool(row.get("is_active", True)),
                "source": "hm_users via service role",
            }
        except Exception:
            pass

    try:
        ok, user, _ = find_user_by_email_fast(email)
        if ok and user:
            return {
                "exists": True,
                "role": str(user.get("role") or "other").strip().lower(),
                "active": bool(user.get("is_active", True)),
                "source": "active app lookup",
            }
        if ok:
            return {"exists": False, "role": "other", "active": False, "source": "active app lookup"}
    except Exception:
        pass

    return _hm_user_unknown("hm_users lookup unavailable")


def _extract_auth_users(response: Any) -> List[Any]:
    if response is None:
        return []
    if isinstance(response, list):
        return response
    if isinstance(response, dict):
        for key in ("users", "data", "items"):
            value = response.get(key)
            if isinstance(value, list):
                return value
            if isinstance(value, dict) and isinstance(value.get("users"), list):
                return value.get("users") or []
    for attr in ("users", "data", "items"):
        value = getattr(response, attr, None)
        if isinstance(value, list):
            return value
        if isinstance(value, dict) and isinstance(value.get("users"), list):
            return value.get("users") or []
    try:
        return _extract_auth_users(response.model_dump())
    except Exception:
        return []


def _auth_user_email(user: Any) -> str:
    if isinstance(user, dict):
        return str(user.get("email") or "").strip().lower()
    return str(getattr(user, "email", "") or "").strip().lower()


def _load_auth_user_emails(service_client: Any) -> Tuple[Optional[Set[str]], str]:
    if service_client is None:
        return None, "Service-role server-side access is missing."

    admin = getattr(getattr(service_client, "auth", None), "admin", None)
    if admin is None or not hasattr(admin, "list_users"):
        return None, "Supabase Auth user listing is not available in the installed client."

    try:
        users: List[Any] = []
        try:
            for page in range(1, 21):
                response = admin.list_users(page=page, per_page=1000)
                page_users = _extract_auth_users(response)
                if not page_users:
                    break
                users.extend(page_users)
                if len(page_users) < 1000:
                    break
        except TypeError:
            response = admin.list_users()
            users = _extract_auth_users(response)
        emails = {_auth_user_email(user) for user in users if _auth_user_email(user)}
        return emails, "Supabase Auth users checked server-side."
    except Exception as exc:
        return None, f"Supabase Auth user listing failed: {exc}"


def _auth_exists_for_email(email: str, service_client: Any) -> Tuple[Optional[bool], str]:
    emails, message = _load_auth_user_emails(service_client)
    if emails is None:
        return None, message
    return email in emails, message


def _is_active_hm_mapping(hm_user: Dict[str, Any]) -> bool:
    return bool(hm_user.get("exists") is True and hm_user.get("active") is True and hm_user.get("role") in VALID_ROLES)


def _recommended_action(hm_user: Dict[str, Any], auth_exists: Optional[bool]) -> str:
    if hm_user.get("exists") is False or hm_user.get("active") is False:
        return "Do not provision. HealthyMe user mapping missing or inactive."
    if hm_user.get("exists") is None or hm_user.get("active") is None:
        return "Manual HealthyMe user mapping check required before action."
    if auth_exists is None:
        return "Manual Supabase Dashboard check required before action."
    if auth_exists is True:
        return "Already provisioned. Use recovery/reset email only if login help is needed."
    return "Eligible for one-user Supabase Auth invite."


def _readiness_row(email: str, hm_user: Dict[str, Any], auth_exists: Optional[bool], recommended_action: str) -> Dict[str, str]:
    return {
        "email checked": email,
        "exists in hm_users": _yes_no_unknown(hm_user.get("exists")),
        "role in hm_users": str(hm_user.get("role") or "other"),
        "active in hm_users": _yes_no_unknown(hm_user.get("active")),
        "exists in Supabase Auth": _yes_no_unknown(auth_exists),
        "recommended action": recommended_action,
    }


def _readiness_status_rows(result: Dict[str, Any]) -> List[Dict[str, str]]:
    hm_user = result["hm_user"]
    return [
        {"Status item": "HealthyMe mapping", "Result": _yes_no_unknown(hm_user.get("exists"))},
        {"Status item": "HealthyMe role", "Result": str(hm_user.get("role") or "other")},
        {"Status item": "HealthyMe active status", "Result": _yes_no_unknown(hm_user.get("active"))},
        {"Status item": "Supabase Auth user", "Result": _yes_no_unknown(result.get("auth_exists"))},
        {"Status item": "Recommended next step", "Result": result.get("recommended", "Manual review required.")},
    ]


def _render_readiness_result(result: Dict[str, Any]) -> None:
    email = result["email"]
    hm_user = result["hm_user"]
    auth_exists = result["auth_exists"]
    recommended = result["recommended"]
    auth_message = result.get("auth_message", "")

    st.markdown(f"**Readiness result for:** `{email}`")
    st.dataframe(
        pd.DataFrame(_readiness_status_rows(result)),
        use_container_width=True,
        hide_index=True,
    )
    with st.expander("Compact detail row", expanded=False):
        st.dataframe(
            pd.DataFrame([_readiness_row(email, hm_user, auth_exists, recommended)]),
            use_container_width=True,
            hide_index=True,
        )
    st.caption(f"hm_users source: {hm_user.get('source', 'unknown')}")
    if auth_exists is None:
        st.info(auth_message or "Manual Supabase Dashboard check required before action.")
    st.info(recommended)


def _confirmation_ok(confirmed: bool, confirm_text: str) -> bool:
    return bool(confirmed and (confirm_text or "").strip() == CONFIRMATION_TEXT)


def _send_invite(service_client: Any, email: str) -> Tuple[bool, str]:
    admin = getattr(getattr(service_client, "auth", None), "admin", None)
    method = getattr(admin, "invite_user_by_email", None) if admin is not None else None
    if not callable(method):
        return False, "Invite method is not available in the installed Supabase client. Use Supabase Dashboard manual invite."
    try:
        method(email)
        return True, "Supabase email request submitted for this one user."
    except Exception as exc:
        return False, f"Supabase invite failed: {exc}"


def _send_recovery(service_client: Any, email: str) -> Tuple[bool, str]:
    auth = getattr(service_client, "auth", None)
    method = getattr(auth, "reset_password_for_email", None) if auth is not None else None
    if not callable(method):
        return False, "Recovery method is not available in the installed Supabase client. Use Supabase Dashboard manual reset."
    try:
        method(email)
        return True, "Supabase email request submitted for this one user."
    except Exception as exc:
        return False, f"Supabase recovery/reset failed: {exc}"


def _action_button_label(action: str) -> str:
    if action == ACTION_INVITE:
        return "Send one Supabase invite email"
    if action == ACTION_RECOVERY:
        return "Send one Supabase recovery/reset email"
    return "No email action"


def _handle_selected_action(
    action: str,
    email: str,
    hm_user: Dict[str, Any],
    auth_exists: Optional[bool],
    service_client: Any,
    confirmed: bool,
    confirm_text: str,
) -> None:
    if action == ACTION_NONE:
        st.info("No email action selected. No Supabase email request was submitted.")
        return

    if auth_exists is None:
        st.error("Run readiness check and confirm Supabase Auth status before sending any email.")
        return

    if service_client is None:
        st.error(SERVICE_ROLE_REQUIRED)
        return

    if not _confirmation_ok(confirmed, confirm_text):
        st.error("Action not executed. Confirm the checkbox and type PROVISION exactly.")
        return

    if not _is_active_hm_mapping(hm_user):
        st.error("Action not executed. A valid active admin/member hm_users mapping is required.")
        return

    if action == ACTION_INVITE:
        if auth_exists is not False:
            st.error("Invite not executed. Supabase Auth user must be confirmed missing first.")
            return
        ok, message = _send_invite(service_client, email)
        (st.success if ok else st.error)(message)
        return

    if action == ACTION_RECOVERY:
        if auth_exists is not True:
            st.error("Recovery/reset not executed. Supabase Auth user must already exist.")
            return
        ok, message = _send_recovery(service_client, email)
        (st.success if ok else st.error)(message)
        return

    st.error("Unknown action. No Supabase Auth action was performed.")


st.warning(
    "AUTH-XPLAT-5C is a supervised one-user provisioning workbench only. It does not run SQL, does not update hm_users, and does not perform batch migration."
)
st.info("Dry-run/readiness does not send emails. Email actions are separated below.")

config = _config_status()
service_client = _service_role_client()

card_start()
st.subheader("Server-side configuration check")
st.dataframe(
    pd.DataFrame(
        [
            {"Config": "SUPABASE_URL", "Configured": _yes_no_unknown(config["SUPABASE_URL"])},
            {"Config": "SUPABASE_SERVICE_ROLE_KEY", "Configured": _yes_no_unknown(config["SUPABASE_SERVICE_ROLE_KEY"])},
        ]
    ),
    use_container_width=True,
    hide_index=True,
)
st.caption("Secret values are never displayed. Service-role access is required for invite/recovery actions.")
if service_client is None:
    st.info(SERVICE_ROLE_REQUIRED)
card_end()

card_start()
st.subheader("Stage 1: Readiness Check Only")
st.caption("This stage normalizes one email, checks HealthyMe mapping, checks Supabase Auth existence where available, and stores the readiness result.")
with st.form("supabase_auth_provisioning_readiness_form"):
    email_input = st.text_input("Email")
    readiness_submitted = st.form_submit_button(
        "Run readiness check — no email will be sent",
        type="primary",
        use_container_width=True,
    )

if readiness_submitted:
    email = _normalize_email(email_input)
    if not email:
        st.session_state.pop(READINESS_STATE_KEY, None)
        st.warning("Enter one email before running the readiness check.")
    else:
        hm_user = _lookup_hm_user(email, service_client)
        auth_exists, auth_message = _auth_exists_for_email(email, service_client)
        recommended = _recommended_action(hm_user, auth_exists)
        st.session_state[READINESS_STATE_KEY] = {
            "email": email,
            "hm_user": hm_user,
            "auth_exists": auth_exists,
            "auth_message": auth_message,
            "recommended": recommended,
        }

readiness_result = st.session_state.get(READINESS_STATE_KEY)
if readiness_result:
    _render_readiness_result(readiness_result)
card_end()

if readiness_result:
    card_start()
    st.subheader("Optional email action")
    st.warning(
        "This action can send a real Supabase email. Use only for one supervised user after confirming the readiness result."
    )
    st.info(
        "Email delivery is requested through Supabase. Actual receipt depends on Supabase/email provider delivery, spam filtering, and rate limits."
    )

    selected_action = st.selectbox("Email action", ACTION_OPTIONS, index=0)
    if selected_action == ACTION_NONE:
        st.info("No email action selected. No Supabase email will be requested.")
    elif readiness_result.get("auth_exists") is None:
        st.error("Run readiness check and confirm Supabase Auth status before sending any email.")
    else:
        button_label = _action_button_label(selected_action)
        with st.form("supabase_auth_provisioning_email_action_form"):
            confirmed = st.checkbox("I understand this is a one-user supervised Supabase Auth email action.")
            confirm_text = st.text_input("Type PROVISION to confirm invite/recovery action")
            action_submitted = st.form_submit_button(button_label, type="primary", use_container_width=True)

        if action_submitted:
            _handle_selected_action(
                selected_action,
                readiness_result["email"],
                readiness_result["hm_user"],
                readiness_result["auth_exists"],
                service_client,
                confirmed,
                confirm_text,
            )
    card_end()

card_start()
st.subheader("Manual rollback and safety notes")
st.markdown(
    """
- This page processes one email at a time.
- No CSV upload, batch loop, SQL migration, schema change, hm_users update, role change, or password edit is included.
- If an invite or recovery/reset email is requested by mistake, use the Supabase Dashboard > Authentication > Users view for manual review.
- A successful API call means the email request was submitted to Supabase; it does not guarantee inbox delivery.
- Fast auth-mode rollback remains: remove `AUTH_MODE` or set `AUTH_MODE = "auth0"`.
- Code rollback branch remains: `backup/pre-auth-xplat-current-streamlit-20260625-clean`.
"""
)
card_end()

render_page_nav(
    "Supabase Auth Provisioning Workbench",
    back_page="pages/10_Admin_Dashboard.py",
    dashboard_page="pages/10_Admin_Dashboard.py",
    show_evaluation=False,
    show_dashboard=True,
    location="bottom",
)
render_back_to_top()
