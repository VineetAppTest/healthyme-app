import os
import secrets
import string
from typing import Dict, Tuple, Optional

import requests

def _get_secret(name: str, default: str = "") -> str:
    value = os.environ.get(name)
    if value:
        return value
    try:
        import streamlit as st
        value = st.secrets.get(name, default)
        return str(value) if value is not None else default
    except Exception:
        return default

def _get_nested_secret(section: str, key: str, default: str = "") -> str:
    try:
        import streamlit as st
        value = st.secrets.get(section, {}).get(key, default)
        return str(value) if value is not None else default
    except Exception:
        return default

def auth0_config_status() -> Dict[str, bool]:
    domain = _get_secret("AUTH0_DOMAIN")
    m2m_client_id = _get_secret("AUTH0_M2M_CLIENT_ID")
    m2m_client_secret = _get_secret("AUTH0_M2M_CLIENT_SECRET")
    connection = _get_secret("AUTH0_CONNECTION", "Username-Password-Authentication")
    app_client_id = _get_secret("AUTH0_APP_CLIENT_ID") or _get_nested_secret("auth.auth0", "client_id") or _get_nested_secret("auth0", "client_id")
    return {
        "AUTH0_DOMAIN": bool(domain),
        "AUTH0_M2M_CLIENT_ID": bool(m2m_client_id),
        "AUTH0_M2M_CLIENT_SECRET": bool(m2m_client_secret),
        "AUTH0_CONNECTION": bool(connection),
        "AUTH0_APP_CLIENT_ID": bool(app_client_id),
    }

def _auth0_domain() -> str:
    domain = _get_secret("AUTH0_DOMAIN").strip()
    if domain.startswith("https://"):
        domain = domain.replace("https://", "", 1)
    if domain.endswith("/"):
        domain = domain[:-1]
    return domain

def is_auth0_provisioning_configured() -> bool:
    status = auth0_config_status()
    return bool(status["AUTH0_DOMAIN"] and status["AUTH0_M2M_CLIENT_ID"] and status["AUTH0_M2M_CLIENT_SECRET"] and status["AUTH0_CONNECTION"])

def _management_token() -> Tuple[bool, str]:
    domain = _auth0_domain()
    client_id = _get_secret("AUTH0_M2M_CLIENT_ID")
    client_secret = _get_secret("AUTH0_M2M_CLIENT_SECRET")
    audience = _get_secret("AUTH0_AUDIENCE") or f"https://{domain}/api/v2/"

    if not domain or not client_id or not client_secret:
        return False, "Auth0 Management API secrets are not configured."

    try:
        resp = requests.post(
            f"https://{domain}/oauth/token",
            json={
                "client_id": client_id,
                "client_secret": client_secret,
                "audience": audience,
                "grant_type": "client_credentials",
            },
            timeout=20,
        )
        if resp.status_code >= 300:
            return False, f"Could not get Auth0 Management token: {resp.status_code} {resp.text[:500]}"
        return True, resp.json().get("access_token", "")
    except Exception as exc:
        return False, f"Could not connect to Auth0 Management API: {exc}"

def _headers(token: str) -> Dict[str, str]:
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

def _random_temp_password() -> str:
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return "".join(secrets.choice(alphabet) for _ in range(18))

def find_auth0_user_by_email(email: str) -> Tuple[bool, Optional[dict], str]:
    ok, token_or_msg = _management_token()
    if not ok:
        return False, None, token_or_msg

    domain = _auth0_domain()
    try:
        resp = requests.get(
            f"https://{domain}/api/v2/users-by-email",
            params={"email": email},
            headers=_headers(token_or_msg),
            timeout=20,
        )
        if resp.status_code >= 300:
            return False, None, f"Could not check Auth0 user: {resp.status_code} {resp.text[:500]}"
        users = resp.json() or []
        return True, users[0] if users else None, ""
    except Exception as exc:
        return False, None, f"Could not check Auth0 user: {exc}"

def create_auth0_user(email: str, name: str = "") -> Tuple[bool, Optional[dict], str]:
    ok, token_or_msg = _management_token()
    if not ok:
        return False, None, token_or_msg

    domain = _auth0_domain()
    connection = _get_secret("AUTH0_CONNECTION", "Username-Password-Authentication")

    payload = {
        "email": email,
        "connection": connection,
        "password": _random_temp_password(),
        "email_verified": False,
        "verify_email": True,
        "name": name or email,
        "user_metadata": {"created_by": "HealthyMe"},
        "app_metadata": {"healthyme_invited": True},
    }

    try:
        resp = requests.post(
            f"https://{domain}/api/v2/users",
            json=payload,
            headers=_headers(token_or_msg),
            timeout=20,
        )
        if resp.status_code in [409]:
            # Race-safe fallback: user exists
            return find_auth0_user_by_email(email)
        if resp.status_code >= 300:
            return False, None, f"Could not create Auth0 user: {resp.status_code} {resp.text[:700]}"
        return True, resp.json(), ""
    except Exception as exc:
        return False, None, f"Could not create Auth0 user: {exc}"

def send_password_setup_email(email: str) -> Tuple[bool, str]:
    """Trigger Auth0's database password change email.

    Requires the OIDC application client_id and database connection.
    """
    domain = _auth0_domain()
    connection = _get_secret("AUTH0_CONNECTION", "Username-Password-Authentication")
    client_id = _get_secret("AUTH0_APP_CLIENT_ID") or _get_nested_secret("auth.auth0", "client_id") or _get_nested_secret("auth0", "client_id")

    if not domain or not client_id or not connection:
        return False, "Password setup email not sent: AUTH0_DOMAIN, AUTH0_APP_CLIENT_ID/client_id, or AUTH0_CONNECTION is missing."

    try:
        resp = requests.post(
            f"https://{domain}/dbconnections/change_password",
            json={
                "client_id": client_id,
                "email": email,
                "connection": connection,
            },
            timeout=20,
        )
        if resp.status_code >= 300:
            return False, f"Auth0 user was created/found, but password setup email failed: {resp.status_code} {resp.text[:500]}"
        return True, str(resp.text or "Password setup email requested.")
    except Exception as exc:
        return False, f"Auth0 user was created/found, but password setup email failed: {exc}"

def provision_auth0_user(email: str, name: str = "", send_setup_email: bool = True) -> Dict[str, object]:
    """Create/find Auth0 user and optionally trigger password setup email."""
    result = {
        "configured": is_auth0_provisioning_configured(),
        "auth0_user_exists": False,
        "auth0_user_created": False,
        "password_email_sent": False,
        "ok": False,
        "message": "",
    }

    if not result["configured"]:
        result["message"] = "Auth0 provisioning is not configured. HealthyMe user can be created, but Auth0 user/invite will not be created."
        return result

    ok, existing, msg = find_auth0_user_by_email(email)
    if not ok:
        result["message"] = msg
        return result

    if existing:
        result["auth0_user_exists"] = True
        result["ok"] = True
        result["message"] = "Auth0 user already exists."
    else:
        ok, created, msg = create_auth0_user(email, name)
        if not ok:
            result["message"] = msg
            return result
        result["auth0_user_created"] = True
        result["ok"] = True
        result["message"] = "Auth0 user created."

    if send_setup_email:
        mail_ok, mail_msg = send_password_setup_email(email)
        result["password_email_sent"] = bool(mail_ok)
        result["message"] = result["message"] + " " + mail_msg

    return result

def update_auth0_user_profile(email: str, name: str = "", email_new: str = "") -> Dict[str, object]:
    """Update Auth0 user profile. Email update is supported but should be used carefully."""
    result = {"ok": False, "message": "", "auth0_user_found": False}
    ok, user, msg = find_auth0_user_by_email(email)
    if not ok:
        result["message"] = msg
        return result
    if not user:
        result["message"] = "Auth0 user not found for this email."
        return result

    ok, token_or_msg = _management_token()
    if not ok:
        result["message"] = token_or_msg
        return result

    domain = _auth0_domain()
    user_id = user.get("user_id")
    payload = {}
    if name:
        payload["name"] = name
    if email_new and email_new.strip().lower() != email.strip().lower():
        payload["email"] = email_new.strip().lower()
        payload["email_verified"] = False
        payload["verify_email"] = True

    if not payload:
        result.update({"ok": True, "auth0_user_found": True, "message": "No Auth0 profile changes needed."})
        return result

    try:
        resp = requests.patch(
            f"https://{domain}/api/v2/users/{user_id}",
            json=payload,
            headers=_headers(token_or_msg),
            timeout=20,
        )
        if resp.status_code >= 300:
            result["message"] = f"Could not update Auth0 user: {resp.status_code} {resp.text[:700]}"
            return result
        result.update({"ok": True, "auth0_user_found": True, "message": "Auth0 user updated."})
        return result
    except Exception as exc:
        result["message"] = f"Could not update Auth0 user: {exc}"
        return result

def set_auth0_user_blocked(email: str, blocked: bool) -> Dict[str, object]:
    """Block/unblock Auth0 user. Used for deactivate/reactivate."""
    result = {"ok": False, "message": "", "auth0_user_found": False}
    ok, user, msg = find_auth0_user_by_email(email)
    if not ok:
        result["message"] = msg
        return result
    if not user:
        result["message"] = "Auth0 user not found for this email."
        return result

    ok, token_or_msg = _management_token()
    if not ok:
        result["message"] = token_or_msg
        return result

    domain = _auth0_domain()
    user_id = user.get("user_id")
    try:
        resp = requests.patch(
            f"https://{domain}/api/v2/users/{user_id}",
            json={"blocked": bool(blocked)},
            headers=_headers(token_or_msg),
            timeout=20,
        )
        if resp.status_code >= 300:
            result["message"] = f"Could not {'block' if blocked else 'unblock'} Auth0 user: {resp.status_code} {resp.text[:700]}"
            return result
        result.update({"ok": True, "auth0_user_found": True, "message": f"Auth0 user {'blocked' if blocked else 'unblocked'}."})
        return result
    except Exception as exc:
        result["message"] = f"Could not {'block' if blocked else 'unblock'} Auth0 user: {exc}"
        return result

def delete_auth0_user_by_email(email: str) -> Dict[str, object]:
    """Hard delete Auth0 user. Function present for later use; UI keeps this hidden/disabled for now."""
    result = {"ok": False, "message": "", "auth0_user_found": False}
    ok, user, msg = find_auth0_user_by_email(email)
    if not ok:
        result["message"] = msg
        return result
    if not user:
        result["message"] = "Auth0 user not found for this email."
        return result

    ok, token_or_msg = _management_token()
    if not ok:
        result["message"] = token_or_msg
        return result

    domain = _auth0_domain()
    user_id = user.get("user_id")
    try:
        resp = requests.delete(
            f"https://{domain}/api/v2/users/{user_id}",
            headers=_headers(token_or_msg),
            timeout=20,
        )
        if resp.status_code >= 300:
            result["message"] = f"Could not delete Auth0 user: {resp.status_code} {resp.text[:700]}"
            return result
        result.update({"ok": True, "auth0_user_found": True, "message": "Auth0 user hard-deleted."})
        return result
    except Exception as exc:
        result["message"] = f"Could not delete Auth0 user: {exc}"
        return result

def check_auth0_user_status(email: str) -> Dict[str, object]:
    ok, user, msg = find_auth0_user_by_email(email)
    if not ok:
        return {"ok": False, "exists": False, "blocked": None, "message": msg}
    if not user:
        return {"ok": True, "exists": False, "blocked": None, "message": "Auth0 user does not exist."}
    return {
        "ok": True,
        "exists": True,
        "blocked": bool(user.get("blocked", False)),
        "user_id": user.get("user_id", ""),
        "email_verified": bool(user.get("email_verified", False)),
        "message": "Auth0 user found.",
    }
