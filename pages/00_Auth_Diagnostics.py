import json
from urllib.parse import urlparse

import streamlit as st
import streamlit

from components.admin_role_model import is_admin_role


st.set_page_config(
    page_title="HealthyMe Auth Diagnostics",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def _safe_bool(value) -> bool:
    try:
        return bool(value)
    except Exception:
        return False


def _context_url() -> str:
    try:
        return str(st.context.url or "")
    except Exception:
        return ""


def _is_embedded() -> bool:
    try:
        return bool(st.context.is_embedded)
    except Exception:
        return False


def _cookie_snapshot():
    try:
        cookies = dict(st.context.cookies)
    except Exception:
        cookies = {}

    streamlit_cookies = {
        str(name): len(str(value or ""))
        for name, value in cookies.items()
        if "streamlit" in str(name).lower()
    }
    auth_cookie_value = cookies.get("_streamlit_user")
    return {
        "streamlit_cookie_names": sorted(streamlit_cookies.keys()),
        "streamlit_cookie_lengths": streamlit_cookies,
        "auth_cookie_present": auth_cookie_value is not None,
        "auth_cookie_length": len(str(auth_cookie_value or "")),
        "all_cookie_count": len(cookies),
    }


def _user_snapshot():
    native_logged_in = False
    claim_keys = []
    claim_payload_size = 0
    try:
        native_logged_in = bool(st.user.is_logged_in)
    except Exception:
        native_logged_in = False

    try:
        user_dict = dict(st.user)
        claim_keys = sorted(str(key) for key in user_dict.keys())
        claim_payload_size = len(json.dumps(user_dict, default=str, sort_keys=True))
    except Exception:
        pass

    return {
        "native_oidc_logged_in": native_logged_in,
        "claim_keys": claim_keys,
        "claim_payload_size": claim_payload_size,
    }


cookie_info = _cookie_snapshot()
user_info = _user_snapshot()
context_url = _context_url()
parsed_url = urlparse(context_url) if context_url else None
role = "none"
if st.session_state.get("_hm_auth_role_resolved"):
    role = (
        "admin"
        if is_admin_role(st.session_state.get("user_role"))
        else "member"
    )

snapshot = {
    "router_build": str(st.session_state.get("_hm_router_build") or "unknown"),
    "streamlit_version": streamlit.__version__,
    "url_path": parsed_url.path if parsed_url else "unknown",
    "embedded": _is_embedded(),
    "auth_cookie_present": cookie_info["auth_cookie_present"],
    "auth_cookie_length": cookie_info["auth_cookie_length"],
    "streamlit_cookie_names": cookie_info["streamlit_cookie_names"],
    "streamlit_cookie_lengths": cookie_info["streamlit_cookie_lengths"],
    "all_cookie_count": cookie_info["all_cookie_count"],
    "native_oidc_logged_in": user_info["native_oidc_logged_in"],
    "oidc_claim_key_count": len(user_info["claim_keys"]),
    "oidc_claim_keys": user_info["claim_keys"],
    "oidc_claim_payload_size": user_info["claim_payload_size"],
    "healthyme_logged_in": _safe_bool(st.session_state.get("logged_in")),
    "healthyme_role_resolved": _safe_bool(
        st.session_state.get("_hm_auth_role_resolved")
    ),
    "healthyme_role": role,
    "router_restore_ms": st.session_state.get("_hm_router_restore_ms"),
    "role_restore_attempts": st.session_state.get("_hm_role_restore_attempts"),
    "role_restore_status": str(
        st.session_state.get("_hm_role_restore_status") or "unknown"
    ),
    "role_restore_failed": _safe_bool(
        st.session_state.get("_hm_role_restore_failed")
    ),
    "router_final_retry_done": _safe_bool(
        st.session_state.get("_hm_router_final_retry_done")
    ),
}

st.title("HealthyMe authentication diagnostics")
st.caption(
    "This page shows only safe status indicators, cookie names and byte lengths. "
    "It never displays cookie values, passwords, tokens, email addresses or user IDs."
)

left, middle, right = st.columns(3)
with left:
    st.metric(
        "Native OIDC identity",
        "Present" if snapshot["native_oidc_logged_in"] else "Absent",
    )
with middle:
    st.metric(
        "Streamlit auth cookie",
        "Present" if snapshot["auth_cookie_present"] else "Absent",
    )
with right:
    st.metric("HealthyMe role", snapshot["healthyme_role"].title())

if snapshot["native_oidc_logged_in"] and not snapshot["auth_cookie_present"]:
    st.error(
        "The current WebSocket session knows the identity, but the browser did not "
        "send the persistent Streamlit auth cookie. This points to cookie creation, "
        "storage, size or browser-policy failure rather than HealthyMe role routing."
    )
elif snapshot["auth_cookie_present"] and not snapshot["native_oidc_logged_in"]:
    st.error(
        "The auth cookie reached Streamlit, but Streamlit did not accept it as a valid "
        "identity. This points to cookie validation, secret mismatch or cookie expiry."
    )
elif snapshot["native_oidc_logged_in"] and not snapshot["healthyme_role_resolved"]:
    st.warning(
        "OIDC identity restoration succeeded, but HealthyMe role resolution failed."
    )
elif snapshot["native_oidc_logged_in"] and snapshot["healthyme_role_resolved"]:
    st.success("Both the native identity and HealthyMe role are available in this run.")
else:
    st.info("No active native OIDC identity is available in this run.")

if snapshot["auth_cookie_length"] > 3500:
    st.warning(
        "The Streamlit authentication cookie is close to common browser cookie-size "
        "limits. Oversized identity claims can cause a login to work only until refresh."
    )

st.subheader("Safe diagnostic snapshot")
st.code(json.dumps(snapshot, indent=2, sort_keys=True), language="json")
st.caption(
    "The role restoration fields show whether HealthyMe loaded the access profile on "
    "the first attempt, after an automatic retry, or not at all."
)
