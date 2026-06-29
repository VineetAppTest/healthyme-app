import os
from typing import Any, Dict, List, Optional, Set, Tuple

import pandas as pd
import streamlit as st

from components.guards import require_admin
from components.auth_mode import auth0_enabled, get_auth_mode, supabase_auth_enabled
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
    page_title="Supabase Auth Pilot Readiness",
    page_icon="HM",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_global_styles()
apply_luxe_theme()


require_admin()
utility_logout_bar()
topbar(
    "Supabase Auth Pilot Readiness",
    "Read-only checks for one pilot admin and one pilot member before controlled dual-mode testing.",
    "Admin auth pilot",
)


AUTH_USERS_MANUAL_MESSAGE = (
    "Auth user count requires service-role server-side access and will be checked manually in Supabase."
)


class ReadOnlyCheckError(Exception):
    """Raised only for display-safe read-only readiness check failures."""


def _get_secret(name: str, default: str = "") -> str:
    value = os.environ.get(name)
    if value:
        return value
    try:
        value = st.secrets.get(name, default)
        return str(value) if value is not None else default
    except Exception:
        return default


def _secret_configured(name: str) -> bool:
    return bool((_get_secret(name) or "").strip())


def _config_status() -> Dict[str, bool]:
    return {
        "SUPABASE_URL": _secret_configured("SUPABASE_URL"),
        "SUPABASE_ANON_KEY": _secret_configured("SUPABASE_ANON_KEY"),
        "SUPABASE_SERVICE_ROLE_KEY": _secret_configured("SUPABASE_SERVICE_ROLE_KEY"),
    }


def _create_client_with_key(key_name: str):
    url = (_get_secret("SUPABASE_URL") or "").strip()
    key = (_get_secret(key_name) or "").strip()
    if not url or not key:
        return None
    try:
        from supabase import create_client

        return create_client(url, key)
    except Exception as exc:
        raise ReadOnlyCheckError(f"Could not create Supabase client with {key_name}.") from exc


def _read_client():
    service_client = _create_client_with_key("SUPABASE_SERVICE_ROLE_KEY")
    if service_client is not None:
        return service_client
    return _create_client_with_key("SUPABASE_ANON_KEY")


def _service_role_client():
    return _create_client_with_key("SUPABASE_SERVICE_ROLE_KEY")


def _safe_count(client: Any, table_name: str, active_only: Optional[bool] = None) -> Optional[int]:
    if client is None:
        return None
    try:
        query = client.table(table_name).select("id", count="exact").limit(1)
        if active_only is not None:
            query = query.eq("is_active", active_only)
        result = query.execute()
        count = getattr(result, "count", None)
        if count is not None:
            return int(count)
        return len(getattr(result, "data", None) or [])
    except Exception:
        return None


def _load_active_hm_users(client: Any) -> Optional[List[Dict[str, Any]]]:
    if client is None:
        return None
    try:
        result = client.table("hm_users").select("email,role,is_active").eq("is_active", True).execute()
        return list(getattr(result, "data", None) or [])
    except Exception:
        return None


def _extract_auth_users(response: Any) -> List[Any]:
    if response is None:
        return []
    if isinstance(response, list):
        return response
    if isinstance(response, dict):
        for key in ("users", "data"):
            value = response.get(key)
            if isinstance(value, list):
                return value
            if isinstance(value, dict) and isinstance(value.get("users"), list):
                return value.get("users") or []
    for attr in ("users", "data"):
        value = getattr(response, attr, None)
        if isinstance(value, list):
            return value
        if isinstance(value, dict) and isinstance(value.get("users"), list):
            return value.get("users") or []
    try:
        dumped = response.model_dump()
        return _extract_auth_users(dumped)
    except Exception:
        return []


def _auth_user_email(user: Any) -> str:
    if isinstance(user, dict):
        return str(user.get("email") or "").strip().lower()
    return str(getattr(user, "email", "") or "").strip().lower()


def _load_auth_user_emails(client: Any) -> Tuple[Optional[Set[str]], Optional[int]]:
    if client is None:
        return None, None
    try:
        all_users: List[Any] = []
        try:
            for page in range(1, 11):
                response = client.auth.admin.list_users(page=page, per_page=1000)
                users = _extract_auth_users(response)
                if not users:
                    break
                all_users.extend(users)
                if len(users) < 1000:
                    break
        except TypeError:
            response = client.auth.admin.list_users()
            all_users = _extract_auth_users(response)

        emails = {_auth_user_email(user) for user in all_users if _auth_user_email(user)}
        return emails, len(all_users)
    except Exception:
        return None, None


def _lookup_hm_user(client: Any, email: str) -> Dict[str, Any]:
    clean_email = (email or "").strip().lower()
    if client is None or not clean_email:
        return {"checked": False, "exists": False, "role": "", "active": False}
    try:
        result = (
            client.table("hm_users")
            .select("email,role,is_active")
            .eq("email", clean_email)
            .limit(1)
            .execute()
        )
        rows = list(getattr(result, "data", None) or [])
        if not rows:
            return {"checked": True, "exists": False, "role": "", "active": False}
        row = rows[0]
        return {
            "checked": True,
            "exists": True,
            "role": str(row.get("role") or "other").strip().lower(),
            "active": bool(row.get("is_active", True)),
        }
    except Exception:
        return {"checked": False, "exists": False, "role": "", "active": False}


def _yes_no(value: Optional[bool]) -> str:
    if value is None:
        return "unknown"
    return "yes" if value else "no"


def _count_label(value: Optional[int]) -> str:
    return str(value) if value is not None else "unknown"


def _auth_exists_label(auth_emails: Optional[Set[str]], email: str) -> str:
    if auth_emails is None:
        return "unknown"
    return "yes" if (email or "").strip().lower() in auth_emails else "no"


def _pilot_row(label: str, email: str, expected_role: str, client: Any, auth_emails: Optional[Set[str]]) -> Dict[str, str]:
    clean_email = (email or "").strip().lower()
    user = _lookup_hm_user(client, clean_email)
    hm_exists = user.get("exists") if user.get("checked") else None
    active = user.get("active") if user.get("checked") and user.get("exists") else (False if user.get("checked") else None)
    role = user.get("role") or "other"
    auth_exists = _auth_exists_label(auth_emails, clean_email)

    app_ready = bool(user.get("checked") and user.get("exists") and role == expected_role and active)
    ready = app_ready and auth_exists == "yes"
    if auth_exists == "unknown":
        note = "Manual Supabase Auth confirmation required."
    elif not app_ready:
        note = "HealthyMe hm_users mapping is not ready."
    elif auth_exists == "no":
        note = "Supabase Auth user was not found."
    else:
        note = "Ready for controlled pilot test."

    return {
        "Pilot": label,
        "Exists in hm_users": _yes_no(hm_exists),
        "Role in hm_users": role if user.get("exists") else "other",
        "Active in hm_users": _yes_no(active),
        "Exists in Supabase Auth": auth_exists,
        "Ready for pilot": "yes" if ready else "no",
        "Note": note,
    }


def _collect_readiness_summary() -> Dict[str, Any]:
    try:
        client = _read_client()
    except ReadOnlyCheckError:
        client = None

    try:
        service_client = _service_role_client()
    except ReadOnlyCheckError:
        service_client = None

    active_users = _load_active_hm_users(client)
    auth_emails, auth_count = _load_auth_user_emails(service_client)

    active_emails: Optional[Set[str]] = None
    if active_users is not None:
        active_emails = {
            str(user.get("email") or "").strip().lower()
            for user in active_users
            if str(user.get("email") or "").strip()
        }

    matched = None
    active_without_auth = None
    auth_without_active_hm_user = None
    if active_emails is not None and auth_emails is not None:
        matched = len(active_emails.intersection(auth_emails))
        active_without_auth = len(active_emails.difference(auth_emails))
        auth_without_active_hm_user = len(auth_emails.difference(active_emails))

    return {
        "client": client,
        "auth_emails": auth_emails,
        "hm_total": _safe_count(client, "hm_users"),
        "hm_active": _safe_count(client, "hm_users", active_only=True),
        "auth_count": auth_count,
        "active_matched": matched,
        "active_without_auth": active_without_auth,
        "auth_without_active_hm_user": auth_without_active_hm_user,
    }


st.warning(
    "Stage 4 is pilot readiness only. This page does not migrate users, does not change login mode, and does not execute SQL."
)

card_start()
st.subheader("Current Auth Mode")
mode = get_auth_mode()
auth_mode_rows = [
    {"Item": "Current AUTH_MODE", "Status": mode},
    {"Item": "Auth0 enabled", "Status": _yes_no(auth0_enabled())},
    {"Item": "Supabase pilot login enabled", "Status": _yes_no(supabase_auth_enabled())},
]
st.dataframe(pd.DataFrame(auth_mode_rows), use_container_width=True, hide_index=True)
if mode == "auth0":
    st.success("Default Auth0-only behavior is active.")
elif mode == "dual":
    st.info("Dual mode is enabled for controlled pilot testing.")
else:
    st.warning("Supabase-only mode is active. Confirm this was intentionally enabled for controlled testing.")
card_end()

card_start()
st.subheader("Supabase Config Check")
config = _config_status()
config_rows = [{"Config": key, "Configured": _yes_no(value)} for key, value in config.items()]
st.dataframe(pd.DataFrame(config_rows), use_container_width=True, hide_index=True)
st.caption("Only Yes/No status is shown. Secret values are never displayed on this page.")
card_end()

summary = _collect_readiness_summary()

card_start()
st.subheader("User Mapping Summary")
summary_rows = [
    {"Metric": "hm_users total", "Count": _count_label(summary.get("hm_total"))},
    {"Metric": "active hm_users", "Count": _count_label(summary.get("hm_active"))},
    {"Metric": "Supabase Auth user count", "Count": _count_label(summary.get("auth_count"))},
    {"Metric": "active hm_users matched to auth users by email", "Count": _count_label(summary.get("active_matched"))},
    {"Metric": "active hm_users without auth user", "Count": _count_label(summary.get("active_without_auth"))},
    {"Metric": "auth users without active hm_user", "Count": _count_label(summary.get("auth_without_active_hm_user"))},
]
st.dataframe(pd.DataFrame(summary_rows), use_container_width=True, hide_index=True)
if summary.get("auth_emails") is None:
    st.info(AUTH_USERS_MANUAL_MESSAGE)
st.caption("This section shows counts only and does not list personal data by default.")
card_end()

card_start()
st.subheader("Pilot Email Check")
with st.form("pilot_email_readiness_form"):
    pilot_admin_email = st.text_input("Pilot Admin Email")
    pilot_member_email = st.text_input("Pilot Member Email")
    submitted = st.form_submit_button("Check Pilot Readiness", type="primary", use_container_width=True)

if submitted:
    if not pilot_admin_email.strip() or not pilot_member_email.strip():
        st.warning("Enter both pilot emails before checking readiness.")
    else:
        rows = [
            _pilot_row("Pilot Admin", pilot_admin_email, "admin", summary.get("client"), summary.get("auth_emails")),
            _pilot_row("Pilot Member", pilot_member_email, "member", summary.get("client"), summary.get("auth_emails")),
        ]
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        if any(row["Exists in Supabase Auth"] == "unknown" for row in rows):
            st.info("Supabase Auth existence could not be confirmed server-side. Use the manual dashboard checklist below before enabling pilot testing.")
card_end()

card_start()
st.subheader("Manual Supabase Dashboard Checklist")
st.markdown(
    """
1. Open Supabase Dashboard.
2. Go to Authentication > Users.
3. Confirm pilot admin email exists.
4. Confirm pilot member email exists.
5. Confirm both users can log in through known/password-reset credentials.
6. Do not delete existing users.
7. Do not change Auth settings yet.
8. Do not change redirect URLs yet.
9. Do not run SQL yet.
"""
)
card_end()

card_start()
st.subheader("Pilot Mode Instructions")
st.markdown(
    """
Only after default Auth0 smoke passes, set Streamlit secret:

```text
AUTH_MODE = "dual"
```

Then test:

- Auth0 admin login still works.
- Supabase admin pilot login works.
- Supabase member pilot login works.
- Unauthorized Supabase user is blocked.
- Logout works.
"""
)
card_end()

card_start()
st.subheader("Rollback Instructions")
st.markdown(
    """
Fast rollback:
Remove AUTH_MODE or set:

```text
AUTH_MODE = "auth0"
```

Code rollback branch:

```text
backup/pre-auth-xplat-current-streamlit-20260625-clean
```
"""
)
card_end()

render_page_nav(
    "Supabase Auth Pilot Readiness",
    back_page="pages/10_Admin_Dashboard.py",
    dashboard_page="pages/10_Admin_Dashboard.py",
    show_evaluation=False,
    show_dashboard=True,
    location="bottom",
)
render_back_to_top()
