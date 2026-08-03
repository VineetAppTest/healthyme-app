from __future__ import annotations

import datetime
import os
import uuid
from typing import Any, Dict, List, Tuple


APP_STATE_ID = "healthyme_app_state_v1"
USER_CANONICAL_FIELDS = (
    "name",
    "email",
    "password_hash",
    "role",
    "must_reset_password",
    "is_active",
    "auth_provider",
    "auth_user_id",
    "auth_migrated_at",
)


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


def _configured() -> bool:
    return bool(
        _get_secret("SUPABASE_URL")
        and (_get_secret("SUPABASE_SERVICE_ROLE_KEY") or _get_secret("SUPABASE_ANON_KEY"))
    )


def _service_role_configured() -> bool:
    return bool(_get_secret("SUPABASE_URL") and _get_secret("SUPABASE_SERVICE_ROLE_KEY"))


def _client():
    from supabase import create_client

    url = _get_secret("SUPABASE_URL")
    key = _get_secret("SUPABASE_SERVICE_ROLE_KEY") or _get_secret("SUPABASE_ANON_KEY")
    return create_client(url, key)


def _service_client():
    from supabase import create_client

    url = _get_secret("SUPABASE_URL")
    key = _get_secret("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        raise RuntimeError("SUPABASE_SERVICE_ROLE_KEY is required for canonical User writes.")
    return create_client(url, key)


def normalized_configured() -> bool:
    return _configured()


def _workflow_base(wf=None):
    base = {
        "laf_completed": False,
        "nsp1_completed": False,
        "nsp2_completed": False,
        "submitted_for_review": False,
        "admin_completed": False,
        "final_report_ready": False,
        "workflow_status": "not_started",
    }
    base.update(wf or {})
    base["workflow_status"] = (
        "finalized"
        if base.get("final_report_ready")
        else "admin_completed"
        if base.get("admin_completed")
        else "submitted"
        if base.get("submitted_for_review")
        else "in_progress"
        if base.get("laf_completed") or base.get("nsp1_completed") or base.get("nsp2_completed")
        else "not_started"
    )
    return base


def _actor_context() -> Tuple[str, str]:
    actor_id = ""
    actor_email = ""
    try:
        import streamlit as st

        actor_id = str(
            st.session_state.get("user_id")
            or st.session_state.get("member_id")
            or st.session_state.get("admin_id")
            or ""
        ).strip()
        actor_email = str(
            st.session_state.get("oidc_email")
            or st.session_state.get("supabase_auth_email")
            or st.session_state.get("user_email")
            or ""
        ).strip().lower()
        try:
            if not actor_email and getattr(st, "user", None):
                actor_email = str(getattr(st.user, "email", "") or "").strip().lower()
        except Exception:
            pass
    except Exception:
        pass
    return actor_id, actor_email


def _canonical_user_patch(user: Dict[str, Any]) -> Dict[str, Any]:
    patch: Dict[str, Any] = {
        "name": str(user.get("name", "") or ""),
        "email": str(user.get("email", "") or "").strip().lower(),
        "password_hash": str(user.get("password_hash", "") or ""),
        "role": str(user.get("role", "member") or "member").strip().lower(),
        "must_reset_password": bool(user.get("must_reset_password", False)),
        "is_active": bool(user.get("is_active", True)),
        "auth_provider": str(user.get("auth_provider", "oidc") or "oidc").strip().lower(),
    }
    # These are canonical-only fields and must never be cleared merely because an
    # older shared projection does not contain them.
    if "auth_user_id" in user:
        patch["auth_user_id"] = str(user.get("auth_user_id") or "")
    if "auth_migrated_at" in user:
        patch["auth_migrated_at"] = str(user.get("auth_migrated_at") or "")
    return patch


def _values_equal(field: str, desired: Any, existing: Any) -> bool:
    if field in {"must_reset_password", "is_active"}:
        return bool(desired) == bool(existing)
    if field in {"email", "role", "auth_provider"}:
        return str(desired or "").strip().lower() == str(existing or "").strip().lower()
    return str(desired or "") == str(existing or "")


def _changed_user_entries(client: Any, db: Dict[str, Any]) -> List[Dict[str, Any]]:
    response = client.table("hm_users").select("*").execute()
    canonical = {str(row.get("id")): row for row in (getattr(response, "data", None) or []) if row.get("id")}
    entries: List[Dict[str, Any]] = []
    for user in db.get("users", []) or []:
        user_id = str(user.get("id", "") or "").strip()
        if not user_id:
            continue
        patch = _canonical_user_patch(user)
        existing = canonical.get(user_id)
        if existing is None or any(
            not _values_equal(field, value, existing.get(field)) for field, value in patch.items()
        ):
            entries.append({"user_id": user_id, "patch": patch})
    return entries


def commit_users_and_state(
    db: Dict[str, Any],
    *,
    state_id: str = APP_STATE_ID,
    source: str = "streamlit_user_cutover",
    force_state_commit: bool = False,
) -> Tuple[bool, bool, str, Dict[str, Any]]:
    """Atomically commit changed canonical Users and the complete compatibility state.

    Returns (ok, committed, message, response). `committed=False` means no
    canonical User or shared User projection change required this contract.
    """
    if not _service_role_configured():
        return False, False, "SUPABASE_SERVICE_ROLE_KEY is required for canonical User writes.", {}
    try:
        client = _service_client()
        changed_users = _changed_user_entries(client, db)
        if not changed_users and not force_state_commit:
            return True, False, "No canonical User changes detected.", {}
        actor_id, actor_email = _actor_context()
        request_id = f"user-state-{uuid.uuid4()}"
        params = {
            "p_request_id": request_id,
            "p_state_id": state_id,
            "p_state_data": db,
            "p_users": changed_users,
            "p_actor_id": actor_id or None,
            "p_actor_email": actor_email or None,
            "p_source": source,
            "p_metadata": {
                "cutover_gate": 3,
                "changed_user_candidates": len(changed_users),
            },
        }
        result = client.rpc("hm_admin_commit_users_and_state", params).execute()
        data = getattr(result, "data", None)
        if isinstance(data, list) and data:
            data = data[0]
        if not isinstance(data, dict) or not data.get("ok"):
            return False, False, "Canonical User/state contract returned an invalid response.", {}
        return (
            True,
            True,
            f"Canonical User/state commit accepted; {int(data.get('changed_user_count', 0) or 0)} User row(s) changed.",
            data,
        )
    except Exception as exc:
        return False, False, f"Canonical User/state commit failed: {exc}", {}


def check_normalized_tables() -> Dict[str, Any]:
    if not _configured():
        return {
            "ok": False,
            "hm_users": False,
            "hm_workflow": False,
            "message": "Supabase secrets are not configured.",
        }
    try:
        c = _client()
        users_ok = False
        workflow_ok = False
        user_count = 0
        workflow_count = 0
        try:
            r = c.table("hm_users").select("id", count="exact").limit(1).execute()
            users_ok = True
            user_count = getattr(r, "count", None) if getattr(r, "count", None) is not None else 0
        except Exception:
            users_ok = False
        try:
            r = c.table("hm_workflow").select("user_id", count="exact").limit(1).execute()
            workflow_ok = True
            workflow_count = getattr(r, "count", None) if getattr(r, "count", None) is not None else 0
        except Exception:
            workflow_ok = False
        return {
            "ok": bool(users_ok and workflow_ok),
            "hm_users": users_ok,
            "hm_workflow": workflow_ok,
            "hm_users_count": user_count,
            "hm_workflow_count": workflow_count,
            "message": "Normalized tables are ready."
            if users_ok and workflow_ok
            else "Normalized tables are missing or blocked by permissions/RLS.",
        }
    except Exception as exc:
        return {
            "ok": False,
            "hm_users": False,
            "hm_workflow": False,
            "message": str(exc),
        }


def load_users_workflow_from_normalized() -> Tuple[bool, List[dict], Dict[str, dict], str]:
    status = check_normalized_tables()
    if not status.get("ok"):
        return False, [], {}, status.get("message", "Normalized tables not ready.")
    try:
        c = _client()
        users_res = c.table("hm_users").select("*").execute()
        wf_res = c.table("hm_workflow").select("*").execute()

        users = []
        for row in users_res.data or []:
            users.append(
                {
                    "id": row.get("id"),
                    "name": row.get("name", ""),
                    "email": row.get("email", ""),
                    "password_hash": row.get("password_hash", ""),
                    "role": row.get("role", "member"),
                    "must_reset_password": bool(row.get("must_reset_password", False)),
                    "is_active": bool(row.get("is_active", True)),
                    "auth_provider": row.get("auth_provider", "oidc"),
                }
            )

        workflow = {}
        for row in wf_res.data or []:
            uid = row.get("user_id")
            if uid:
                workflow[uid] = _workflow_base(
                    {
                        "laf_completed": bool(row.get("laf_completed", False)),
                        "nsp1_completed": bool(row.get("nsp1_completed", False)),
                        "nsp2_completed": bool(row.get("nsp2_completed", False)),
                        "submitted_for_review": bool(row.get("submitted_for_review", False)),
                        "admin_completed": bool(row.get("admin_completed", False)),
                        "final_report_ready": bool(row.get("final_report_ready", False)),
                        "workflow_status": row.get("workflow_status", "not_started"),
                    }
                )
        return True, users, workflow, "Loaded users/workflow from normalized tables."
    except Exception as exc:
        return False, [], {}, f"Could not load normalized users/workflow: {exc}"


def sync_workflow_to_normalized(db: Dict[str, Any]) -> Tuple[bool, str]:
    status = check_normalized_tables()
    if not status.get("hm_workflow"):
        return False, status.get("message", "Normalized Workflow table not ready.")
    try:
        c = _client()
        rows = []
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        user_ids = {str(u.get("id")) for u in db.get("users", []) or [] if u.get("id")}
        for user_id in user_ids:
            wf = _workflow_base(db.get("workflow", {}).get(user_id, {}))
            rows.append(
                {
                    "user_id": user_id,
                    "laf_completed": bool(wf.get("laf_completed")),
                    "nsp1_completed": bool(wf.get("nsp1_completed")),
                    "nsp2_completed": bool(wf.get("nsp2_completed")),
                    "submitted_for_review": bool(wf.get("submitted_for_review")),
                    "admin_completed": bool(wf.get("admin_completed")),
                    "final_report_ready": bool(wf.get("final_report_ready")),
                    "workflow_status": wf.get("workflow_status", "not_started"),
                    "updated_at": now,
                }
            )
        if rows:
            c.table("hm_workflow").upsert(rows).execute()
        return True, f"Synced {len(rows)} Workflow record(s) to hm_workflow."
    except Exception as exc:
        return False, f"Could not sync Workflow to hm_workflow: {exc}"


def sync_users_workflow_to_normalized(db: Dict[str, Any]) -> Tuple[bool, str]:
    """Compatibility/manual action after Gate 3.

    User rows use the transactional audited contract; Workflow remains on the
    legacy synchronization path until its independent cutover gate.
    """
    user_ok, _, user_msg, _ = commit_users_and_state(
        db,
        state_id=APP_STATE_ID,
        source="manual_users_workflow_sync",
        force_state_commit=True,
    )
    if not user_ok:
        return False, user_msg
    workflow_ok, workflow_msg = sync_workflow_to_normalized(db)
    return bool(workflow_ok), f"{user_msg} {workflow_msg}"


def upsert_user_to_normalized(user: dict, workflow: dict = None) -> Tuple[bool, str]:
    if not _service_role_configured():
        return False, "SUPABASE_SERVICE_ROLE_KEY is required for canonical User writes."
    user_id = str(user.get("id", "") or "").strip()
    if not user_id:
        return False, "User ID is required."
    try:
        client = _service_client()
        actor_id, actor_email = _actor_context()
        request_id = f"user-upsert-{uuid.uuid4()}"
        result = client.rpc(
            "hm_admin_upsert_user",
            {
                "p_request_id": request_id,
                "p_user_id": user_id,
                "p_patch": _canonical_user_patch(user),
                "p_actor_id": actor_id or None,
                "p_actor_email": actor_email or None,
                "p_source": "normalized_store_compatibility",
                "p_metadata": {"cutover_gate": 3},
            },
        ).execute()
        data = getattr(result, "data", None)
        if isinstance(data, list) and data:
            data = data[0]
        if not isinstance(data, dict) or not data.get("ok"):
            return False, "Canonical User contract returned an invalid response."
        return True, "Canonical User write accepted through hm_admin_upsert_user."
    except Exception as exc:
        return False, f"Canonical User write failed: {exc}"


def find_user_by_email_fast(email: str):
    """Fast login-time lookup from hm_users.

    This avoids loading the full JSONB app state during Auth0 callback.
    Returns (ok, user_or_none, message). ok=False means caller should fallback.
    """
    email = (email or "").strip().lower()
    if not email or not _configured():
        return False, None, "Supabase not configured or email missing."
    try:
        c = _client()
        res = (
            c.table("hm_users")
            .select("id,name,email,role,is_active,auth_provider,must_reset_password")
            .eq("email", email)
            .limit(1)
            .execute()
        )
        rows = res.data or []
        if not rows:
            return True, None, "No normalized user found."
        row = rows[0]
        if not bool(row.get("is_active", True)):
            return True, None, "User is inactive."
        return (
            True,
            {
                "id": row.get("id"),
                "name": row.get("name", ""),
                "email": row.get("email", ""),
                "role": row.get("role", "member"),
                "is_active": bool(row.get("is_active", True)),
                "auth_provider": row.get("auth_provider", "oidc"),
                "must_reset_password": bool(row.get("must_reset_password", False)),
            },
            "Loaded user from normalized hm_users.",
        )
    except Exception as exc:
        return False, None, f"Fast normalized lookup failed: {exc}"
