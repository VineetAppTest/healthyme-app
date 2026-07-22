import json
import os

import streamlit as st


BUILD = "H13Q1-native-oidc-provider-parity-v1"
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

if not logged_in:
    st.metric("Native Streamlit identity", "Absent")
    st.info(f"Configured provider: {provider_label}")
    if st.button(
        f"Continue with {provider_label}",
        type="primary",
        use_container_width=True,
    ):
        st.login(provider)
    st.caption(
        "After login, refresh this page ten times. No email address, token or cookie value is displayed."
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
    "healthyme_role_lookup_used": False,
    "application_session_state_required": False,
    "custom_browser_marker_used": False,
    "local_storage_used": False,
}

st.success(f"Streamlit restored a native identity from {provider_label}.")
col1, col2, col3 = st.columns(3)
col1.metric("Native identity", "Present")
col2.metric("Email claim", "Present" if safe_snapshot["email_claim_present"] else "Absent")
col3.metric("Subject claim", "Present" if safe_snapshot["subject_claim_present"] else "Absent")

st.code(json.dumps(safe_snapshot, indent=2, sort_keys=True), language="json")
st.caption(
    "Refresh this page ten consecutive times, then close and reopen the tab. "
    "The page passes only if Native identity remains Present."
)

if st.button("Logout", use_container_width=True):
    st.logout()
