import json
import os

import streamlit as st


BUILD = "H13Q1-native-oidc-provider-parity-v3-post-logout-observation"
SUPPORTED_PROVIDERS = {"auth0", "supabaseoidc"}


def _secret(name: str, default: str = "") -> str:
    value = os.environ.get(name)
    if value is not None:
        return str(value).strip()
    try:
        value = st.secrets.get(name)
    except Exception:
        value = None
    return str(value if value is not None else default).strip()


def _is_logged_in() -> bool:
    try:
        return bool(st.user and st.user.is_logged_in)
    except Exception:
        return False


def _claim_present(name: str) -> bool:
    try:
        value = st.user.get(name)
    except Exception:
        try:
            value = getattr(st.user, name, None)
        except Exception:
            value = None
    return bool(str(value or "").strip())


def _safe_native_cookie_snapshot() -> dict[str, object]:
    """Return only native auth-cookie presence/count indicators, never values."""
    try:
        names = {str(name) for name in st.context.cookies.keys()}
    except Exception:
        names = set()

    def piece_count(base_name: str) -> int:
        count = 1 if base_name in names else 0
        prefix = f"{base_name}_"
        for name in names:
            if not name.startswith(prefix):
                continue
            suffix = name[len(prefix) :]
            if suffix.isdigit():
                count += 1
        return count

    identity_piece_count = piece_count("_streamlit_user")
    token_piece_count = piece_count("_streamlit_user_tokens")
    return {
        "native_identity_cookie_present": identity_piece_count > 0,
        "native_identity_cookie_piece_count": identity_piece_count,
        "native_tokens_cookie_present": token_piece_count > 0,
        "native_tokens_cookie_piece_count": token_piece_count,
        "cookie_values_displayed": False,
    }


provider = _secret("AUTH_TEST_PROVIDER", "auth0").lower()
provider_label = "Auth0" if provider == "auth0" else "Supabase OIDC"

st.set_page_config(
    page_title="HealthyMe Native Identity Test",
    page_icon="🔐",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.title("HealthyMe native identity test")
st.caption(
    "This isolated page tests only Streamlit native OIDC identity persistence. "
    "It does not load HealthyMe roles, legacy pages, durable sessions or custom browser markers."
)
st.code(BUILD)

if provider not in SUPPORTED_PROVIDERS:
    st.error(
        "AUTH_TEST_PROVIDER must be either 'auth0' or 'supabaseoidc' in this temporary app."
    )
    st.stop()

logged_in = _is_logged_in()
cookie_snapshot = _safe_native_cookie_snapshot()

if not logged_in:
    st.metric("Native Streamlit identity", "Absent")
    st.info(f"Configured provider: {provider_label}")
    safe_logged_out_snapshot = {
        "build": BUILD,
        "configured_provider": provider,
        "native_identity_present": False,
        **cookie_snapshot,
        "healthyme_role_lookup_used": False,
        "application_session_state_required": False,
        "custom_browser_marker_used": False,
        "local_storage_used": False,
        "diagnostic_focus": "post_logout_relogin_cookie_lifecycle",
    }
    st.code(
        json.dumps(safe_logged_out_snapshot, indent=2, sort_keys=True),
        language="json",
    )
    if st.button(
        f"Continue with {provider_label}",
        type="primary",
        use_container_width=True,
    ):
        st.login(provider)
    st.caption(
        "This diagnostic displays only cookie presence and piece counts. "
        "It never displays cookie values, email addresses or tokens."
    )
    st.stop()

safe_snapshot = {
    "build": BUILD,
    "configured_provider": provider,
    "native_identity_present": True,
    "email_claim_present": _claim_present("email"),
    "subject_claim_present": _claim_present("sub"),
    "name_claim_present": any(
        _claim_present(key) for key in ("name", "given_name", "nickname")
    ),
    "picture_claim_present": _claim_present("picture"),
    **cookie_snapshot,
    "healthyme_role_lookup_used": False,
    "application_session_state_required": False,
    "custom_browser_marker_used": False,
    "local_storage_used": False,
    "diagnostic_focus": "post_logout_relogin_cookie_lifecycle",
}

st.success(f"Streamlit restored a native identity from {provider_label}.")
col1, col2, col3 = st.columns(3)
col1.metric("Native identity", "Present")
col2.metric("Email claim", "Present" if safe_snapshot["email_claim_present"] else "Absent")
col3.metric("Subject claim", "Present" if safe_snapshot["subject_claim_present"] else "Absent")

st.code(json.dumps(safe_snapshot, indent=2, sort_keys=True), language="json")
st.caption(
    "Current focus: log out once, log back in once, then refresh the root page once. "
    "Capture the logged-in screen before refresh and the root screen after refresh."
)

if st.button("Logout", use_container_width=True):
    st.logout()
