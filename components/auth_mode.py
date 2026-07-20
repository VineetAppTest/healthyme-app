import os

AUTH_MODE_AUTH0 = "auth0"
AUTH_MODE_DUAL = "dual"
AUTH_MODE_SUPABASE = "supabase"
AUTH_MODE_SUPABASE_OIDC_POC = "supabase_oidc_poc"
_ALLOWED_AUTH_MODES = {
    AUTH_MODE_AUTH0,
    AUTH_MODE_DUAL,
    AUTH_MODE_SUPABASE,
    AUTH_MODE_SUPABASE_OIDC_POC,
}
_SECRET_SECTIONS = ("auth", "auth0", "authentication", "healthyme", "supabase")


def _clean_value(value: object, default: str = "") -> str:
    if value is None:
        return default
    return str(value).strip()


def _get_secret(name: str, default: str = "") -> str:
    value = os.environ.get(name)
    if value:
        return _clean_value(value, default)

    try:
        import streamlit as st

        value = st.secrets.get(name)
        if value is not None:
            return _clean_value(value, default)

        lower_name = name.lower()
        value = st.secrets.get(lower_name)
        if value is not None:
            return _clean_value(value, default)

        for section in _SECRET_SECTIONS:
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


def get_auth_mode() -> str:
    """Return the configured HealthyMe auth mode.

    Default remains Auth0 so this scaffold does not alter current production login
    unless AUTH_MODE is explicitly changed in Streamlit secrets/environment.
    """
    mode = (_get_secret("AUTH_MODE", AUTH_MODE_AUTH0) or AUTH_MODE_AUTH0).strip().lower()
    return mode if mode in _ALLOWED_AUTH_MODES else AUTH_MODE_AUTH0


def supabase_oidc_poc_enabled() -> bool:
    return get_auth_mode() == AUTH_MODE_SUPABASE_OIDC_POC


def auth0_enabled() -> bool:
    """Return whether a Streamlit-native OIDC identity should be inspected.

    The historical helper name is retained because existing page guards import it.
    H13O1 reuses the same native Streamlit OIDC restoration path with Supabase as
    the provider when the isolated PoC mode is selected.
    """
    return get_auth_mode() in {
        AUTH_MODE_AUTH0,
        AUTH_MODE_DUAL,
        AUTH_MODE_SUPABASE_OIDC_POC,
    }


def supabase_auth_enabled() -> bool:
    return get_auth_mode() in {AUTH_MODE_DUAL, AUTH_MODE_SUPABASE}


def oidc_provider_name() -> str:
    return "supabase_oidc" if supabase_oidc_poc_enabled() else "auth0"


def oidc_button_label() -> str:
    if supabase_oidc_poc_enabled():
        return "Continue with Supabase OIDC (PoC)"
    return "Continue with Auth0"


def auth_mode_label() -> str:
    mode = get_auth_mode()
    if mode == AUTH_MODE_DUAL:
        return "Auth0 / Supabase secure access"
    if mode == AUTH_MODE_SUPABASE:
        return "Supabase secure access"
    if mode == AUTH_MODE_SUPABASE_OIDC_POC:
        return "Supabase OIDC proof-of-concept access"
    return "Auth0 / OIDC secure access"
