import datetime
from typing import Dict, Tuple, List, Any

def _get_secret(name: str, default: str = "") -> str:
    import os
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
    return bool(_get_secret("SUPABASE_URL") and (_get_secret("SUPABASE_SERVICE_ROLE_KEY") or _get_secret("SUPABASE_ANON_KEY")))

def _client():
    from supabase import create_client
    url = _get_secret("SUPABASE_URL")
    key = _get_secret("SUPABASE_SERVICE_ROLE_KEY") or _get_secret("SUPABASE_ANON_KEY")
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
        "finalized" if base.get("final_report_ready") else
        "admin_completed" if base.get("admin_completed") else
        "submitted" if base.get("submitted_for_review") else
        "in_progress" if base.get("laf_completed") or base.get("nsp1_completed") or base.get("nsp2_completed") else
        "not_started"
    )
    return base

def check_normalized_tables() -> Dict[str, Any]:
    if not _configured():
        return {"ok": False, "hm_users": False, "hm_workflow": False, "message": "Supabase secrets are not configured."}
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
            "message": "Normalized tables are ready." if users_ok and workflow_ok else "Normalized tables are missing or blocked by permissions/RLS.",
        }
    except Exception as exc:
        return {"ok": False, "hm_users": False, "hm_workflow": False, "message": str(exc)}

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
            users.append({
                "id": row.get("id"),
                "name": row.get("name", ""),
                "email": row.get("email", ""),
                "password_hash": row.get("password_hash", ""),
                "role": row.get("role", "member"),
                "must_reset_password": bool(row.get("must_reset_password", False)),
                "is_active": bool(row.get("is_active", True)),
                "auth_provider": row.get("auth_provider", "oidc"),
            })

        workflow = {}
        for row in wf_res.data or []:
            uid = row.get("user_id")
            if uid:
                workflow[uid] = _workflow_base({
                    "laf_completed": bool(row.get("laf_completed", False)),
                    "nsp1_completed": bool(row.get("nsp1_completed", False)),
                    "nsp2_completed": bool(row.get("nsp2_completed", False)),
                    "submitted_for_review": bool(row.get("submitted_for_review", False)),
                    "admin_completed": bool(row.get("admin_completed", False)),
                    "final_report_ready": bool(row.get("final_report_ready", False)),
                    "workflow_status": row.get("workflow_status", "not_started"),
                })
        return True, users, workflow, "Loaded users/workflow from normalized tables."
    except Exception as exc:
        return False, [], {}, f"Could not load normalized users/workflow: {exc}"

def sync_users_workflow_to_normalized(db: Dict[str, Any]) -> Tuple[bool, str]:
    status = check_normalized_tables()
    if not status.get("ok"):
        return False, status.get("message", "Normalized tables not ready.")

    try:
        c = _client()
        users = []
        workflow_rows = []
        now = datetime.datetime.utcnow().isoformat()
        for u in db.get("users", []):
            if not u.get("id"):
                continue
            users.append({
                "id": u.get("id"),
                "name": u.get("name", ""),
                "email": (u.get("email", "") or "").strip().lower(),
                "password_hash": u.get("password_hash", ""),
                "role": u.get("role", "member"),
                "must_reset_password": bool(u.get("must_reset_password", False)),
                "is_active": bool(u.get("is_active", True)),
                "auth_provider": u.get("auth_provider", "oidc"),
                "updated_at": now,
            })
            wf = _workflow_base(db.get("workflow", {}).get(u.get("id"), {}))
            workflow_rows.append({
                "user_id": u.get("id"),
                "laf_completed": bool(wf.get("laf_completed")),
                "nsp1_completed": bool(wf.get("nsp1_completed")),
                "nsp2_completed": bool(wf.get("nsp2_completed")),
                "submitted_for_review": bool(wf.get("submitted_for_review")),
                "admin_completed": bool(wf.get("admin_completed")),
                "final_report_ready": bool(wf.get("final_report_ready")),
                "workflow_status": wf.get("workflow_status", "not_started"),
                "updated_at": now,
            })

        if users:
            c.table("hm_users").upsert(users).execute()
        if workflow_rows:
            c.table("hm_workflow").upsert(workflow_rows).execute()
        return True, f"Migrated/synced {len(users)} users and {len(workflow_rows)} workflow records to normalized tables."
    except Exception as exc:
        return False, f"Could not sync users/workflow to normalized tables: {exc}"

def upsert_user_to_normalized(user: dict, workflow: dict = None) -> Tuple[bool, str]:
    return sync_users_workflow_to_normalized({"users": [user], "workflow": {user.get("id"): workflow or {}}})


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
        return True, {
            "id": row.get("id"),
            "name": row.get("name", ""),
            "email": row.get("email", ""),
            "role": row.get("role", "member"),
            "is_active": bool(row.get("is_active", True)),
            "auth_provider": row.get("auth_provider", "oidc"),
            "must_reset_password": bool(row.get("must_reset_password", False)),
        }, "Loaded user from normalized hm_users."
    except Exception as exc:
        return False, None, f"Fast normalized lookup failed: {exc}"
