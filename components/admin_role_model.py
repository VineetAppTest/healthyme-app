"""HealthyMe Streamlit Supabase admin role model.

Sprint 3A + 3B scope:
- make Supabase pilot login role-aware for Streamlit admin access
- keep Auth0 production login working during parallel run
- centralize admin/member role checks before route-guard cutover

This module is server-side Streamlit code only. It may use the Supabase
service-role key when configured. Do not copy it into Flutter/mobile code.
"""

from __future__ import annotations

import os
from typing import Any, Dict, Optional, Tuple

import streamlit as st

from components.db import find_user_by_email
from components.normalized_store import find_user_by_email_fast

SECRET_SECTIONS = ("auth", "auth0", "authentication", "healthyme", "supabase")
FULL_ADMIN_ROLES = {"admin", "super_admin"}
FUTURE_STAFF_ROLES = {"nutritionist", "practitioner"}
MEMBER_ROLES = {"member"}


def clean_text(value: object, default: str = "") -> str:
    if value is None:
        return default
    return str(value).strip()


def normalize_email(email: object) -> str:
    return clean_text(email).lower()


def normalize_role(role: object) -> str:
    return clean_text(role, "member").lower().replace(" ", "_")


def is_admin_role(role: object) -> bool:
    return normalize_role(role) in FULL_ADMIN_ROLES


def is_member_role(role: object) -> bool:
    return normalize_role(role) in MEMBER_ROLES


def is_future_staff_role(role: object) -> bool:
    return normalize_role(role) in FUTURE_STAFF_ROLES


def current_user_is_admin() -> bool:
    return is_admin_role(st.session_state.get("user_role") or st.session_state.get("role"))


def current_user_is_member() -> bool:
    return is_member_role(st.session_state.get("user_role") or st.session_state.get("role"))


def _get_secret(name: str, default: str = "") -> str:
    value = os.environ.get(name)
    if value:
        return clean_text(value, default)

    try:
        value = st.secrets.get(name)
        if value is not None:
            return clean_text(value, default)

        lower_name = name.lower()
        value = st.secrets.get(lower_name)
        if value is not None:
            return clean_text(value, default)

        for section in SECRET_SECTIONS:
            section_values = st.secrets.get(section)
            if not section_values:
                continue
            try:
                value = section_values.get(name)
                if value is None:
                    value = section_values.get(lower_name)
                if value is not None:
                    return clean_text(value, default)
            except Exception:
                continue
    except Exception:
        pass

    return default


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


def _row_to_app_user(row: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if not row:
        return None
    if not bool(row.get("is_active", True)):
        return None
    role = normalize_role(row.get("role"))
    return {
        "id": row.get("id"),
        "name": row.get("name") or row.get("full_name") or row.get("email") or "User",
        "email": normalize_email(row.get("email")),
        "role": role,
        "is_active": bool(row.get("is_active", True)),
        "auth_provider": row.get("auth_provider") or "supabase",
        "must_reset_password": bool(row.get("must_reset_password", False)),
        "auth_user_id": clean_text(row.get("auth_user_id")),
    }


def _lookup_hm_user_service_role(email: str = "", auth_user_id: str = "") -> Optional[Dict[str, Any]]:
    client = _service_role_client()
    if client is None:
        return None

    select_cols = "id,name,email,role,is_active,auth_provider,must_reset_password,auth_user_id"
    clean_auth_user_id = clean_text(auth_user_id)
    clean_email = normalize_email(email)

    try:
        if clean_auth_user_id:
            result = (
                client.table("hm_users")
                .select(select_cols)
                .eq("auth_user_id", clean_auth_user_id)
                .limit(1)
                .execute()
            )
            rows = list(getattr(result, "data", None) or [])
            if rows:
                return _row_to_app_user(rows[0])
    except Exception:
        # Older databases may not have auth_user_id yet. Email fallback below is intentional.
        pass

    if not clean_email:
        return None

    try:
        result = (
            client.table("hm_users")
            .select(select_cols)
            .ilike("email", clean_email)
            .limit(2)
            .execute()
        )
        rows = list(getattr(result, "data", None) or [])
        if len(rows) == 1:
            return _row_to_app_user(rows[0])
    except Exception:
        pass

    return None


def resolve_app_user(email: str = "", auth_user_id: str = "") -> Tuple[bool, Optional[Dict[str, Any]], str]:
    """Resolve a Supabase/Auth0 identity to a HealthyMe app user.

    Lookup order:
    1. hm_users.auth_user_id through service-role client when available
    2. hm_users.email through service-role client when available
    3. existing fast normalized lookup by email
    4. legacy local app-store lookup by email
    """
    clean_email = normalize_email(email)
    clean_auth_user_id = clean_text(auth_user_id)

    app_user = _lookup_hm_user_service_role(clean_email, clean_auth_user_id)
    if app_user:
        return True, app_user, "Loaded user from Supabase role model."

    if clean_email:
        ok, fast_user, message = find_user_by_email_fast(clean_email)
        if ok and fast_user:
            fast_user = dict(fast_user)
            fast_user["role"] = normalize_role(fast_user.get("role"))
            return True, fast_user, "Loaded user from normalized hm_users."
        if ok and not fast_user:
            return True, None, message or "No active HealthyMe user found."

        local_user = find_user_by_email(clean_email)
        if local_user:
            local_user = dict(local_user)
            local_user["role"] = normalize_role(local_user.get("role"))
            return True, local_user, "Loaded user from legacy local store."

    return False, None, "No authorized HealthyMe user mapping found."


def apply_app_user_to_session(app_user: Dict[str, Any], *, email: str = "", auth_provider: str = "supabase", auth_user_id: str = "") -> bool:
    clean_email = normalize_email(email or app_user.get("email"))
    role = normalize_role(app_user.get("role"))
    st.session_state["logged_in"] = True
    st.session_state["user_id"] = app_user["id"]
    st.session_state["user_role"] = role
    st.session_state["role"] = role
    st.session_state["user_name"] = app_user.get("name") or clean_email or "User"
    st.session_state["user_email"] = clean_email
    st.session_state["must_reset_password"] = bool(app_user.get("must_reset_password", False))
    st.session_state["oidc_email"] = clean_email
    st.session_state["auth_login_method"] = auth_provider
    st.session_state["auth_provider"] = "oidc" if auth_provider == "auth0" else auth_provider
    st.session_state["_hm_auth_role_resolved"] = True
    st.session_state["_hm_role_model"] = "sprint3a_3b"

    if auth_provider == "supabase":
        st.session_state["supabase_auth_email"] = clean_email
        if auth_user_id:
            st.session_state["supabase_auth_user_id"] = clean_text(auth_user_id)

    st.session_state["is_admin"] = is_admin_role(role)
    st.session_state["admin_logged_in"] = is_admin_role(role)
    st.session_state["is_member"] = is_member_role(role)
    return True


def role_access_summary() -> Dict[str, str]:
    role = normalize_role(st.session_state.get("user_role"))
    if is_admin_role(role):
        access = "Full admin access"
    elif is_member_role(role):
        access = "Member access only"
    elif is_future_staff_role(role):
        access = "Future staff/practitioner role detected; admin page access not enabled yet"
    else:
        access = "No admin access"
    return {
        "role": role,
        "access": access,
        "provider": clean_text(st.session_state.get("auth_provider") or st.session_state.get("auth_login_method")),
        "email": normalize_email(st.session_state.get("user_email") or st.session_state.get("supabase_auth_email") or st.session_state.get("oidc_email")),
    }
