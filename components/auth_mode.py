import os

import streamlit as st

_ALLOWED_AUTH_MODES = {"auth0", "dual", "supabase"}
_DEFAULT_AUTH_MODE = "auth0"


def _setting(name: str, default: str = "") -> str:
    value = os.environ.get(name)
    if value:
        return value
    try:
        value = st.secrets.get(name, default)
        return str(value) if value is not None else default
    except Exception:
        return default


def get_auth_mode() -> str:
    raw_value = _setting("AUTH_MODE", _DEFAULT_AUTH_MODE)
    value = (raw_value or _DEFAULT_AUTH_MODE).strip().lower()
    if value not in _ALLOWED_AUTH_MODES:
        return _DEFAULT_AUTH_MODE
    return value


def auth0_enabled() -> bool:
    return get_auth_mode() in {"auth0", "dual"}


def supabase_auth_enabled() -> bool:
    return get_auth_mode() in {"dual", "supabase"}


def auth_mode_label() -> str:
    mode = get_auth_mode()
    if mode == "dual":
        return "Auth0 / Supabase secure access"
    if mode == "supabase":
        return "Supabase secure access"
    return "Auth0 / OIDC secure access"
