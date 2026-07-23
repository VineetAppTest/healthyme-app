import json
import os
import sys
from pathlib import Path
from typing import Any

import streamlit as st

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from components.admin_role_model import (  # noqa: E402
    is_admin_role,
    is_member_role,
    resolve_app_user,
)


BUILD = "H13Q2-native-identity-role-bridge-gate1-v1"
SUPPORTED_PROVIDER = "supabaseoidc"


def _secret(name: str, default: str = "") -> str:
    value = os.environ.get(name)
    if value is not None:
        return str(value).strip()
    try:
        value = st.secrets.get(name)
    except Exception:
        value = None
    return str(value if value is not None else default).strip()


def _native_identity_present() -> bool:
    try:
        return bool(st.user and st.user.is_logged_in)
    except Exception:
        return False


def _claim(name: str) -> str:
    try:
        value = st.user.get(name)
    except Exception:
        try:
            value = getattr(st.user, name, "")
        except Exception:
            value = ""
    return str(value or "").strip()


def _safe_cookie_snapshot() -> dict[str, Any]:
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
            suffix = name[len(prefix):]
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


def _role_category(role: str) -> str:
    if is_admin_role(role):
        return "Admin"
    if is_member_role(role):
        return "Member"
    return "Unsupported"


st.set_page_config(
    page_title="HealthyMe Native Role Bridge",
    page_icon="🌿",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.title("HealthyMe native identity → role bridge")
st.caption(
    "Gate 1 tests one additional layer beyond the proven parity app: "
    "Streamlit restores the Supabase OIDC identity first, then HealthyMe performs "
    "one role lookup. No custom browser marker, durable auth session, legacy guard, "
    "application login Session State or protected-page routing is used."
)
st.code(BUILD)

provider = _secret("AUTH_BRIDGE_PROVIDER", SUPPORTED_PROVIDER).lower()
if provider != SUPPORTED_PROVIDER:
    st.error("AUTH_BRIDGE_PROVIDER must be 'supabaseoidc' for this Gate 1 deployment.")
    st.stop()

cookie_snapshot = _safe_cookie_snapshot()
native_identity_present = _native_identity_present()

if not native_identity_present:
    st.metric("Native Streamlit identity", "Absent")
    logged_out_snapshot = {
        "build": BUILD,
        "configured_provider": provider,
        "native_identity_present": False,
        "healthyme_role_lookup_used": False,
        "healthyme_role_resolved": False,
        "application_session_state_required": False,
        "custom_browser_marker_used": False,
        "durable_auth_session_used": False,
        "legacy_page_guard_used": False,
        "protected_page_routing_used": False,
        "local_storage_used": False,
        **cookie_snapshot,
    }
    st.code(json.dumps(logged_out_snapshot, indent=2, sort_keys=True), language="json")
    if st.button(
        "Continue with Supabase OIDC",
        type="primary",
        use_container_width=True,
    ):
        st.login(provider)
    st.stop()

email = _claim("email").lower()
subject = _claim("sub")
claim_snapshot = {
    "email_claim_present": bool(email),
    "subject_claim_present": bool(subject),
}

if not email and not subject:
    st.error(
        "Streamlit restored a native identity, but neither the email nor subject claim "
        "is available for HealthyMe role resolution."
    )
    st.code(
        json.dumps(
            {
                "build": BUILD,
                "native_identity_present": True,
                "healthyme_role_lookup_used": False,
                "healthyme_role_resolved": False,
                **claim_snapshot,
                **cookie_snapshot,
            },
            indent=2,
            sort_keys=True,
        ),
        language="json",
    )
    if st.button("Logout", use_container_width=True):
        st.logout()
    st.stop()

role_lookup_ok = False
app_user = None
lookup_message = ""
try:
    role_lookup_ok, app_user, lookup_message = resolve_app_user(
        email=email,
        auth_user_id=subject,
    )
except Exception as exc:
    lookup_message = f"{type(exc).__name__}: role lookup could not complete."

if not role_lookup_ok or not app_user:
    st.warning(
        "Your Supabase OIDC identity is active, but HealthyMe did not resolve an "
        "authorized Admin or Member role. This is a role-bridge result, not a logout."
    )
    unresolved_snapshot = {
        "build": BUILD,
        "native_identity_present": True,
        "healthyme_role_lookup_used": True,
        "healthyme_role_resolved": False,
        "role_lookup_completed": bool(role_lookup_ok),
        "application_session_state_required": False,
        "custom_browser_marker_used": False,
        "durable_auth_session_used": False,
        "legacy_page_guard_used": False,
        "protected_page_routing_used": False,
        "local_storage_used": False,
        **claim_snapshot,
        **cookie_snapshot,
    }
    st.code(json.dumps(unresolved_snapshot, indent=2, sort_keys=True), language="json")
    st.caption(lookup_message or "No active HealthyMe user mapping was returned.")
    if st.button("Logout", use_container_width=True):
        st.logout()
    st.stop()

role = str(app_user.get("role") or "").strip().lower()
role_category = _role_category(role)

if role_category == "Unsupported":
    st.warning(
        "The native identity and HealthyMe user mapping were restored, but this role "
        "is outside the Gate 1 Admin/Member acceptance boundary."
    )
elif role_category == "Admin":
    st.success("Native identity restored first; HealthyMe then resolved the Admin role.")
    st.subheader("Admin access — Gate 1 test page")
    st.write(
        "This is intentionally not the real Admin Dashboard. It proves only the "
        "identity-to-role bridge before routing and legacy page code are introduced."
    )
else:
    st.success("Native identity restored first; HealthyMe then resolved the Member role.")
    st.subheader("Member access — Gate 1 test page")
    st.write(
        "This is intentionally not the real Member Home. It proves only the "
        "identity-to-role bridge before routing and legacy page code are introduced."
    )

resolved_snapshot = {
    "build": BUILD,
    "native_identity_present": True,
    "healthyme_role_lookup_used": True,
    "healthyme_role_resolved": True,
    "resolved_role_category": role_category,
    "supported_gate1_role": role_category in {"Admin", "Member"},
    "application_session_state_required": False,
    "custom_browser_marker_used": False,
    "durable_auth_session_used": False,
    "legacy_page_guard_used": False,
    "protected_page_routing_used": False,
    "local_storage_used": False,
    **claim_snapshot,
    **cookie_snapshot,
}
st.code(json.dumps(resolved_snapshot, indent=2, sort_keys=True), language="json")
st.caption(lookup_message or "HealthyMe role lookup completed.")

if st.button("Logout", use_container_width=True):
    st.logout()
