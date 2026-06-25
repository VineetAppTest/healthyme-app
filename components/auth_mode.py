import os

AUTH_MODE_AUTH0 = "auth0"
AUTH_MODE_DUAL = "dual"
AUTH_MODE_SUPABASE = "supabase"
_ALLOWED_AUTH_MODES = {AUTH_MODE_AUTH0, AUTH_MODE_DUAL, AUTH_MODE_SUPABASE}


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


def get_auth_mode() -> str:
    """Return the configured HealthyMe auth mode.

    Default remains Auth0 so this scaffold does not alter current production login
    unless AUTH_MODE is explicitly changed in Streamlit secrets/environment.
    """
    mode = (_get_secret("AUTH_MODE", AUTH_MODE_AUTH0) or AUTH_MODE_AUTH0).strip().lower()
    return mode if mode in _ALLOWED_AUTH_MODES else AUTH_MODE_AUTH0


def auth0_enabled() -> bool:
    return get_auth_mode() in {AUTH_MODE_AUTH0, AUTH_MODE_DUAL}


def supabase_auth_enabled() -> bool:
    return get_auth_mode() in {AUTH_MODE_DUAL, AUTH_MODE_SUPABASE}


def auth_mode_label() -> str:
    mode = get_auth_mode()
    if mode == AUTH_MODE_DUAL:
        return "Auth0 / Supabase secure access"
    if mode == AUTH_MODE_SUPABASE:
        return "Supabase secure access"
    return "Auth0 / OIDC secure access"
