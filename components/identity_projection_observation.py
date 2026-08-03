from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Tuple


PROJECTION_RPC = "hm_identity_projection_snapshot"
OBSERVATION_RPC = "hm_admin_observe_identity_projection"
WINDOW_STATUS_RPC = "hm_identity_observation_window_status"


def _get_secret(name: str, default: str = "") -> str:
    value = os.environ.get(name)
    if value:
        return str(value)
    try:
        import streamlit as st

        value = st.secrets.get(name, default)
        return str(value) if value is not None else default
    except Exception:
        return default


def _service_client():
    from supabase import create_client

    url = _get_secret("SUPABASE_URL")
    key = _get_secret("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        raise RuntimeError(
            "SUPABASE_SERVICE_ROLE_KEY is required for identity projection observation."
        )
    return create_client(url, key)


def _actor_context() -> Tuple[str, str]:
    try:
        import streamlit as st

        actor_id = str(
            st.session_state.get("user_id")
            or st.session_state.get("admin_id")
            or ""
        ).strip()
        actor_email = str(
            st.session_state.get("user_email")
            or st.session_state.get("supabase_auth_email")
            or st.session_state.get("oidc_email")
            or ""
        ).strip().lower()
        return actor_id, actor_email
    except Exception:
        return "", ""


def _rpc_dict(rpc_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
    result = _service_client().rpc(rpc_name, params).execute()
    data = getattr(result, "data", None)
    if isinstance(data, list) and data:
        data = data[0]
    if not isinstance(data, dict):
        raise RuntimeError(f"{rpc_name} returned an invalid response.")
    return data


def get_identity_projection_snapshot() -> Tuple[bool, Dict[str, Any], str]:
    """Return a read-only canonical-versus-shared projection snapshot."""
    try:
        data = _rpc_dict(PROJECTION_RPC, {})
        healthy = bool(data.get("healthy", False))
        message = (
            "Canonical identity projection is aligned."
            if healthy
            else "Canonical identity projection drift was detected."
        )
        return True, data, message
    except Exception as exc:
        return False, {}, f"Identity projection snapshot failed: {exc}"


def get_identity_observation_window_status(
    *,
    window_hours: int = 24,
    minimum_observations: int = 3,
    minimum_span_minutes: int = 60,
) -> Tuple[bool, Dict[str, Any], str]:
    """Return Gate 6 database observation and automated retirement preconditions.

    This is evidence only. A positive automated result never substitutes for
    signed-in Streamlit and Flutter device smoke evidence.
    """
    try:
        safe_window_hours = max(int(window_hours), 1)
        safe_minimum_observations = max(int(minimum_observations), 1)
        safe_minimum_span_minutes = max(int(minimum_span_minutes), 0)
        window_start = datetime.now(timezone.utc) - timedelta(hours=safe_window_hours)
        data = _rpc_dict(
            WINDOW_STATUS_RPC,
            {
                "p_window_start": window_start.isoformat(),
                "p_min_observations": safe_minimum_observations,
                "p_min_span_minutes": safe_minimum_span_minutes,
            },
        )
        ready = bool(data.get("automated_retirement_preconditions_ready", False))
        blockers = list(data.get("blockers") or [])
        if ready:
            message = (
                "Automated projection-retirement preconditions are satisfied; "
                "signed-in route and device evidence is still required."
            )
        elif blockers:
            message = "Gate 6 blockers: " + ", ".join(str(item) for item in blockers)
        else:
            message = "Gate 6 automated evidence is incomplete."
        return True, data, message
    except Exception as exc:
        return False, {}, f"Identity observation-window status failed: {exc}"


def observe_identity_projection(
    *,
    apply_repair: bool = False,
    source: str = "streamlit_database_status",
) -> Tuple[bool, Dict[str, Any], str]:
    """Persist one observation and optionally repair shared projection from canonical rows.

    Repair is explicit. It never changes canonical Users or Workflow, and it
    preserves shared-only fields for identities that still exist canonically.
    """
    try:
        actor_id, actor_email = _actor_context()
        request_id = f"identity-projection-{uuid.uuid4()}"
        data = _rpc_dict(
            OBSERVATION_RPC,
            {
                "p_request_id": request_id,
                "p_apply_repair": bool(apply_repair),
                "p_actor_id": actor_id or None,
                "p_actor_email": actor_email or None,
                "p_source": source,
                "p_metadata": {
                    "gate": "5A_6A",
                    "explicit_repair": bool(apply_repair),
                },
            },
        )
        if not data.get("ok"):
            return False, {}, "Identity projection observation returned an invalid response."
        repaired = bool(data.get("repair_applied", False))
        healthy_after = bool(data.get("healthy_after", False))
        if repaired and healthy_after:
            message = "Compatibility projection repaired from canonical Users and Workflow."
        elif apply_repair and not repaired and healthy_after:
            message = "Compatibility projection was already aligned; no repair was required."
        elif healthy_after:
            message = "Identity projection observation recorded; no drift detected."
        else:
            message = "Identity projection observation recorded; drift remains and repair was not applied."
        return True, data, message
    except Exception as exc:
        return False, {}, f"Identity projection observation failed: {exc}"
