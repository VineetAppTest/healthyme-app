"""H6 Supabase Auth provisioning hardening helpers.

Server-side Streamlit admin only. Do not import from Flutter/mobile code.
"""

from __future__ import annotations

import datetime as _dt
import os
import re
import secrets
import string
from typing import Any, Dict, Iterable, List, Optional, Tuple

import streamlit as st

AUDIT_TABLE = "hm_supabase_auth_provisioning_audit"
DEFAULT_REDIRECT_TO = "healthyme://reset-password/"
VALID_MEMBER_ROLE = "member"
SECRET_SECTIONS = ("auth", "auth0", "authentication", "healthyme", "supabase")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def clean_text(value: object, default: str = "") -> str:
    if value is None:
        return default
    return str(value).strip()


def normalize_email(email: object) -> str:
    return clean_text(email).lower()


def valid_email(email: object) -> bool:
    return bool(EMAIL_RE.match(normalize_email(email)))


def utc_now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat()


def get_secret(name: str, default: str = "") -> str:
    value = os.environ.get(name)
    if value:
        return clean_text(value, default)
    try:
        value = st.secrets.get(name)
        if value is not None:
            return clean_text(value, default)
        lower_name = name.lower()
        value = st.secrets.get(lower_name)
        if value is not None:
            return clean_text(value, default)
        for section in SECRET_SECTIONS:
            section_values = st.secrets.get(section)
            if not section_values:
                continue
            try:
                value = section_values.get(name)
                if value is None:
                    value = section_values.get(lower_name)
                if value is not None:
                    return clean_text(value, default)
            except Exception:
                continue
    except Exception:
        pass
    return default


def config_status() -> Dict[str, bool]:
    return {
        "SUPABASE_URL": bool(get_secret("SUPABASE_URL")),
        "SUPABASE_ANON_KEY": bool(get_secret("SUPABASE_ANON_KEY")),
        "SUPABASE_SERVICE_ROLE_KEY": bool(get_secret("SUPABASE_SERVICE_ROLE_KEY")),
    }


def password_reset_redirect_to() -> str:
    return get_secret("SUPABASE_PASSWORD_RESET_REDIRECT_TO", DEFAULT_REDIRECT_TO) or DEFAULT_REDIRECT_TO


def service_role_client() -> Any:
    url = get_secret("SUPABASE_URL")
    key = get_secret("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        return None
    try:
        from supabase import create_client
        return create_client(url, key)
    except Exception:
        return None


def random_temp_password(length: int = 18) -> str:
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    while True:
        pwd = "".join(secrets.choice(alphabet) for _ in range(length))
        if (
            any(ch.islower() for ch in pwd)
            and any(ch.isupper() for ch in pwd)
            and any(ch.isdigit() for ch in pwd)
            and any(ch in "!@#$%^&*" for ch in pwd)
        ):
            return pwd


def _extract_auth_users(response: Any) -> List[Any]:
    if response is None:
        return []
    if isinstance(response, list):
        return response
    if isinstance(response, dict):
        for key in ("users", "data", "items"):
            value = response.get(key)
            if isinstance(value, list):
                return value
            if isinstance(value, dict) and isinstance(value.get("users"), list):
                return value.get("users") or []
    for attr in ("users", "data", "items"):
        value = getattr(response, attr, None)
        if isinstance(value, list):
            return value
        if isinstance(value, dict) and isinstance(value.get("users"), list):
            return value.get("users") or []
    try:
        return _extract_auth_users(response.model_dump())
    except Exception:
        return []


def _auth_user_dict(user: Any) -> Dict[str, Any]:
    if isinstance(user, dict):
        return user
    try:
        return dict(user.model_dump())
    except Exception:
        return {"id": getattr(user, "id", ""), "email": getattr(user, "email", "")}


def auth_user_id(user: Any) -> str:
    data = _auth_user_dict(user)
    return clean_text(data.get("id") or data.get("user_id") or getattr(user, "id", ""))


def auth_user_email(user: Any) -> str:
    data = _auth_user_dict(user)
    return normalize_email(data.get("email") or getattr(user, "email", ""))


def list_auth_users(client: Any, max_pages: int = 30, per_page: int = 1000) -> Tuple[bool, List[Any], str]:
    if client is None:
        return False, [], "Supabase service role key is not configured or the admin client could not be created."
    admin = getattr(getattr(client, "auth", None), "admin", None)
    if admin is None or not hasattr(admin, "list_users"):
        return False, [], "Supabase Auth user listing is not available in the installed client."
    try:
        users: List[Any] = []
        try:
            for page in range(1, max_pages + 1):
                response = admin.list_users(page=page, per_page=per_page)
                page_users = _extract_auth_users(response)
                if not page_users:
                    break
                users.extend(page_users)
                if len(page_users) < per_page:
                    break
        except TypeError:
            response = admin.list_users()
            users = _extract_auth_users(response)
        return True, users, f"Loaded {len(users)} Supabase Auth users."
    except Exception as exc:
        return False, [], f"Supabase Auth user listing failed. Technical detail: {exc}"


def auth_users_by_email(client: Any) -> Tuple[bool, Dict[str, Any], str, List[str]]:
    ok, users, message = list_auth_users(client)
    if not ok:
        return False, {}, message, []
    by_email: Dict[str, Any] = {}
    duplicates: List[str] = []
    for user in users:
        email = auth_user_email(user)
        if not email:
            continue
        if email in by_email:
            duplicates.append(email)
            continue
        by_email[email] = user
    return True, by_email, message, sorted(set(duplicates))


def load_hm_users(client: Any, *, include_inactive: bool = True, role_filter: str = "member") -> Tuple[bool, List[Dict[str, Any]], str]:
    if client is None:
        return False, [], "Supabase service role key is not configured or the admin client could not be created."
    try:
        query = client.table("hm_users").select("*")
        if role_filter and role_filter != "all":
            query = query.eq("role", role_filter)
        if not include_inactive:
            query = query.eq("is_active", True)
        response = query.execute()
        rows = list(getattr(response, "data", None) or [])
        for row in rows:
            row["email"] = normalize_email(row.get("email", ""))
            row["role"] = clean_text(row.get("role", "member")).lower()
            row["is_active"] = bool(row.get("is_active", True))
        return True, rows, f"Loaded {len(rows)} hm_users records."
    except Exception as exc:
        return False, [], f"Could not load hm_users. Technical detail: {exc}"


def hm_users_by_email(rows: Iterable[Dict[str, Any]]) -> Tuple[Dict[str, Dict[str, Any]], List[str]]:
    by_email: Dict[str, Dict[str, Any]] = {}
    duplicates: List[str] = []
    for row in rows:
        email = normalize_email(row.get("email", ""))
        if not email:
            continue
        if email in by_email:
            duplicates.append(email)
            continue
        by_email[email] = row
    return by_email, sorted(set(duplicates))


def member_name(row: Dict[str, Any]) -> str:
    return clean_text(row.get("name") or row.get("full_name") or row.get("member_name") or row.get("first_name") or "")


def existing_auth_id(row: Dict[str, Any]) -> str:
    return clean_text(row.get("auth_user_id") or row.get("supabase_auth_id"))


def readiness_snapshot(client: Any) -> Dict[str, Any]:
    config = config_status()
    checks: List[Dict[str, str]] = []

    def add_check(name: str, status: bool, note: str) -> None:
        checks.append({"Check": name, "Status": "pass" if status else "fail", "Note": note})

    add_check("Supabase URL configured", config["SUPABASE_URL"], "Required for Supabase client creation.")
    add_check("Supabase anon key configured", config["SUPABASE_ANON_KEY"], "Required for member-side Supabase client use.")
    add_check("Supabase service role key configured", config["SUPABASE_SERVICE_ROLE_KEY"], "Required for admin-only provisioning. Never expose to Flutter.")
    add_check("Service-role admin client initialized", client is not None, "Used only inside Streamlit admin pages.")

    hm_ok, hm_rows, hm_msg = load_hm_users(client, include_inactive=True, role_filter="member")
    auth_ok, auth_map, auth_msg, auth_dupes = auth_users_by_email(client)
    add_check("hm_users readable through service role", hm_ok, hm_msg)
    add_check("Supabase Auth API reachable", auth_ok, auth_msg)

    by_email, hm_dupes = hm_users_by_email(hm_rows)
    active_rows = [r for r in hm_rows if bool(r.get("is_active", True))]
    inactive_rows = [r for r in hm_rows if not bool(r.get("is_active", True))]
    missing_email = [r for r in hm_rows if not normalize_email(r.get("email"))]
    invalid_email = [r for r in hm_rows if normalize_email(r.get("email")) and not valid_email(r.get("email"))]
    already = [r for r in active_rows if normalize_email(r.get("email")) in auth_map]
    pending = [r for r in active_rows if valid_email(r.get("email")) and normalize_email(r.get("email")) not in auth_map and normalize_email(r.get("email")) not in hm_dupes]

    required_fields_ok = bool(hm_rows) and all(k in hm_rows[0] for k in ("id", "email", "role", "is_active")) if hm_rows else hm_ok
    add_check("Required hm_users fields available", required_fields_ok, "Expected fields: id, email, role, is_active.")
    add_check("Duplicate member emails absent", not hm_dupes, "Duplicate member emails must be resolved before batch provisioning.")
    add_check("Duplicate Supabase Auth emails absent", not auth_dupes, "Duplicate Auth emails require Supabase dashboard review.")

    summary = {
        "Total member records": len(hm_rows) if hm_ok else "unknown",
        "Active members": len(active_rows) if hm_ok else "unknown",
        "Inactive members": len(inactive_rows) if hm_ok else "unknown",
        "Missing email records": len(missing_email) if hm_ok else "unknown",
        "Invalid email records": len(invalid_email) if hm_ok else "unknown",
        "Duplicate member emails": len(hm_dupes) if hm_ok else "unknown",
        "Supabase Auth users loaded": len(auth_map) if auth_ok else "unknown",
        "Already provisioned active members": len(already) if hm_ok and auth_ok else "unknown",
        "Pending active members": len(pending) if hm_ok and auth_ok else "unknown",
    }
    return {"checks": checks, "summary": summary, "hm_rows": hm_rows, "auth_map": auth_map, "hm_dupes": hm_dupes, "auth_dupes": auth_dupes, "hm_ok": hm_ok, "auth_ok": auth_ok}


def member_review_rows(client: Any) -> List[Dict[str, Any]]:
    snap = readiness_snapshot(client)
    rows: List[Dict[str, Any]] = []
    auth_map = snap.get("auth_map", {}) or {}
    hm_dupes = set(snap.get("hm_dupes", []) or [])
    for row in snap.get("hm_rows", []) or []:
        email = normalize_email(row.get("email"))
        role = clean_text(row.get("role", "")).lower()
        active = bool(row.get("is_active", True))
        auth_user = auth_map.get(email)
        reason = "Ready to provision"
        action = "Provision"
        status = "pending"
        if not email:
            status, reason, action = "skipped", "Skipped: member email is missing.", "Skip"
        elif not valid_email(email):
            status, reason, action = "skipped", "Skipped: member email is invalid.", "Skip"
        elif role != VALID_MEMBER_ROLE:
            status, reason, action = "skipped", "Skipped: only member-role users are provisioned in this branch.", "Skip"
        elif not active:
            status, reason, action = "skipped", "Skipped: member is inactive.", "Skip"
        elif email in hm_dupes:
            status, reason, action = "review", "Review required: more than one member record uses this email.", "Review"
        elif auth_user:
            status, reason, action = "already_provisioned", "Already provisioned in Supabase Auth.", "Link/Verify"
        rows.append({
            "Member ID": clean_text(row.get("id")),
            "Name": member_name(row),
            "Email": email,
            "Role": role,
            "Active": "yes" if active else "no",
            "Supabase Auth status": status,
            "Auth User ID": auth_user_id(auth_user) if auth_user else existing_auth_id(row),
            "Reason": reason,
            "Action": action,
        })
    return rows


def create_auth_user(client: Any, email: str, password: str, name: str = "") -> Tuple[bool, Optional[Any], str]:
    admin = getattr(getattr(client, "auth", None), "admin", None) if client is not None else None
    if admin is None or not hasattr(admin, "create_user"):
        return False, None, "Supabase admin create_user is not available in the installed client."
    payloads = [
        {"email": email, "password": password, "email_confirm": True, "user_metadata": {"name": name or email, "created_by": "HealthyMe Streamlit Admin"}, "app_metadata": {"healthyme_role": "member", "healthyme_provisioned": True}},
        {"email": email, "password": password, "email_confirm": True, "data": {"name": name or email, "created_by": "HealthyMe Streamlit Admin"}},
        {"email": email, "password": password},
    ]
    last_error = ""
    for payload in payloads:
        try:
            response = admin.create_user(payload)
            user = getattr(response, "user", None) or getattr(response, "data", None) or response
            if isinstance(user, dict) and user.get("user"):
                user = user.get("user")
            return True, user, "Provisioned successfully."
        except Exception as exc:
            last_error = str(exc)
            if any(token in last_error.lower() for token in ("already", "registered", "exists")):
                return False, None, "Already provisioned in Supabase Auth."
    return False, None, f"Provisioning failed. Technical detail: {last_error}"


def send_password_reset_email(client: Any, email: str, redirect_to: Optional[str] = None) -> Tuple[bool, str]:
    auth = getattr(client, "auth", None) if client is not None else None
    method = getattr(auth, "reset_password_for_email", None) if auth is not None else None
    if not callable(method):
        return False, "Password reset email could not be sent because the Supabase client does not expose reset_password_for_email."
    redirect_to = clean_text(redirect_to or password_reset_redirect_to())
    attempts = []
    if redirect_to:
        attempts.extend([lambda: method(email, {"redirect_to": redirect_to}), lambda: method(email, options={"redirect_to": redirect_to})])
    attempts.append(lambda: method(email))
    last_error = ""
    for attempt in attempts:
        try:
            attempt()
            return True, "Password reset email requested."
        except TypeError as exc:
            last_error = str(exc)
            continue
        except Exception as exc:
            last_error = str(exc)
            break
    return False, f"Password reset email failed. Technical detail: {last_error}"


def link_hm_user_to_auth(client: Any, hm_user: Dict[str, Any], auth_id: str) -> Tuple[bool, str]:
    hm_id = clean_text(hm_user.get("id"))
    if not hm_id:
        return False, "Could not link: hm_users.id is missing."
    current_id = existing_auth_id(hm_user)
    if current_id and current_id != auth_id:
        return False, "Review required: this member is already linked to a different Supabase Auth user."
    now = utc_now_iso()
    payloads = [
        {"auth_user_id": auth_id, "auth_provider": "supabase", "auth_migrated_at": now, "updated_at": now},
        {"auth_user_id": auth_id, "auth_provider": "supabase", "updated_at": now},
        {"auth_user_id": auth_id, "auth_provider": "supabase"},
        {"auth_user_id": auth_id},
    ]
    last_error = ""
    for payload in payloads:
        try:
            client.table("hm_users").update(payload).eq("id", hm_id).execute()
            return True, "HealthyMe member linked to Supabase Auth."
        except Exception as exc:
            last_error = str(exc)
            continue
    return False, f"Could not update hm_users.auth_user_id. Technical detail: {last_error}"


def write_audit(client: Any, *, action: str, status: str, member_id: str = "", member_email: str = "", auth_user_id_value: str = "", actor_email: str = "", message: str = "", metadata: Optional[Dict[str, Any]] = None) -> Tuple[bool, str]:
    if client is None:
        return False, "Audit not written because service-role client is missing."
    payload = {"action": action, "status": status, "member_id": member_id or None, "member_email": normalize_email(member_email) or None, "auth_user_id": auth_user_id_value or None, "actor_email": normalize_email(actor_email) or None, "message": clean_text(message)[:1000], "metadata": metadata or {}}
    try:
        client.table(AUDIT_TABLE).insert(payload).execute()
        return True, "Audit row written."
    except Exception as exc:
        return False, f"Audit not written. Technical detail: {exc}"


def load_audit_rows(client: Any, limit: int = 200) -> Tuple[bool, List[Dict[str, Any]], str]:
    if client is None:
        return False, [], "Service-role client missing."
    try:
        response = client.table(AUDIT_TABLE).select("created_at,action,status,member_email,member_id,auth_user_id,actor_email,message").order("created_at", desc=True).limit(int(limit)).execute()
        return True, list(getattr(response, "data", None) or []), "Audit rows loaded."
    except Exception as exc:
        return False, [], f"Could not load audit table. Technical detail: {exc}"


def load_hm_user_by_email(client: Any, email: str) -> Tuple[bool, List[Dict[str, Any]], str]:
    email = normalize_email(email)
    if not email:
        return False, [], "Email is required."
    if client is None:
        return False, [], "Supabase service role key is not configured."
    try:
        result = client.table("hm_users").select("*").eq("email", email).execute()
        rows = list(getattr(result, "data", None) or [])
        for row in rows:
            row["email"] = normalize_email(row.get("email", ""))
            row["role"] = clean_text(row.get("role", "member")).lower()
            row["is_active"] = bool(row.get("is_active", True))
        return True, rows, f"Found {len(rows)} hm_users row(s)."
    except Exception as exc:
        return False, [], f"Could not read hm_users. Technical detail: {exc}"


def provision_single_member(client: Any, *, email: str, temp_password: str = "", send_reset: bool = False, actor_email: str = "", dry_run: bool = True) -> Dict[str, Any]:
    email = normalize_email(email)
    result: Dict[str, Any] = {"email": email, "member_id": "", "member_name": "", "role": "", "active": "", "auth_status": "unknown", "auth_user_id": "", "hm_link_status": "not_run", "password_reset_status": "not_requested", "temp_password": "", "status": "blocked", "message": "", "audit": "not_written"}
    if not email:
        result["message"] = "Skipped: member email is missing."
        return result
    if not valid_email(email):
        result["message"] = "Skipped: member email is invalid."
        return result
    if client is None:
        result["message"] = "Supabase service role key is not configured."
        return result
    ok, hm_rows, msg = load_hm_user_by_email(client, email)
    if not ok:
        result["message"] = msg
        return result
    if not hm_rows:
        result["message"] = "No HealthyMe member record exists for this email."
        return result
    if len(hm_rows) > 1:
        result["message"] = "Review required: more than one member record uses this email."
        return result
    hm_user = hm_rows[0]
    result.update({"member_id": clean_text(hm_user.get("id")), "member_name": member_name(hm_user), "role": clean_text(hm_user.get("role")), "active": bool(hm_user.get("is_active", True)), "auth_user_id": existing_auth_id(hm_user)})
    if result["role"] != VALID_MEMBER_ROLE:
        result["message"] = "Skipped: only member-role users are provisioned in this branch."
        return result
    if not result["active"]:
        result["message"] = "Skipped: member is inactive."
        return result
    ok, auth_map, auth_msg, _ = auth_users_by_email(client)
    if not ok:
        result["status"] = "failed"
        result["message"] = auth_msg
        return result
    auth_user = auth_map.get(email)
    if auth_user:
        auth_id = auth_user_id(auth_user)
        result["auth_status"] = "already_provisioned"
        result["auth_user_id"] = result["auth_user_id"] or auth_id
        if dry_run:
            result["status"] = "dry_run"
            result["message"] = "Dry run: already provisioned Auth user would be linked/verified."
            return result
        link_ok, link_msg = link_hm_user_to_auth(client, hm_user, auth_id)
        result["hm_link_status"] = "linked" if link_ok else "link_failed"
        result["auth_user_id"] = auth_id
        result["status"] = "ok" if link_ok else "failed"
        result["message"] = "Already provisioned in Supabase Auth. " + link_msg
    else:
        result["auth_status"] = "pending"
        if dry_run:
            result["status"] = "dry_run"
            result["message"] = "Dry run: Auth user would be created and linked."
            return result
        password = temp_password or random_temp_password()
        result["temp_password"] = "admin_entered_password" if temp_password else "generated_not_displayed"
        create_ok, created_user, create_msg = create_auth_user(client, email, password, result["member_name"])
        if not create_ok:
            result["status"] = "failed"
            result["message"] = create_msg
            write_audit(client, action="single_provision", status="failed", member_id=result["member_id"], member_email=email, actor_email=actor_email, message=create_msg)
            return result
        auth_id = auth_user_id(created_user)
        result["auth_status"] = "created"
        result["auth_user_id"] = auth_id
        link_ok, link_msg = link_hm_user_to_auth(client, hm_user, auth_id)
        result["hm_link_status"] = "linked" if link_ok else "link_failed"
        result["status"] = "ok" if link_ok else "partial"
        result["message"] = f"{create_msg} {link_msg}".strip()
    if send_reset and result.get("auth_user_id"):
        reset_ok, reset_msg = send_password_reset_email(client, email)
        result["password_reset_status"] = "sent" if reset_ok else "failed"
        result["message"] = f"{result['message']} {reset_msg}".strip()
    audit_ok, audit_msg = write_audit(client, action="single_provision", status=result["status"], member_id=result["member_id"], member_email=email, auth_user_id_value=result.get("auth_user_id", ""), actor_email=actor_email, message=result["message"], metadata={"auth_status": result.get("auth_status"), "hm_link_status": result.get("hm_link_status"), "password_reset_status": result.get("password_reset_status")})
    result["audit"] = "written" if audit_ok else audit_msg
    return result


def provision_batch_members(client: Any, *, temp_password: str = "", send_reset: bool = False, actor_email: str = "", dry_run: bool = True, include_inactive: bool = False, limit: int = 500) -> List[Dict[str, Any]]:
    ok, rows, hm_msg = load_hm_users(client, include_inactive=True, role_filter="member")
    if not ok:
        return [{"email": "", "status": "failed", "message": hm_msg}]
    by_email, duplicates = hm_users_by_email(rows)
    ok, auth_map, auth_msg, _ = auth_users_by_email(client)
    if not ok:
        return [{"email": "", "status": "failed", "message": auth_msg}]
    out: List[Dict[str, Any]] = []
    processed = 0
    for email in sorted(by_email.keys()):
        if processed >= max(1, int(limit)):
            out.append({"email": "", "status": "stopped", "message": f"Stopped at batch limit {limit}."})
            break
        row = by_email[email]
        active = bool(row.get("is_active", True))
        result = {"email": email, "member_id": clean_text(row.get("id")), "member_name": member_name(row), "active": active, "auth_status": "unknown", "auth_user_id": existing_auth_id(row), "hm_link_status": "not_run", "password_reset_status": "not_requested", "status": "blocked", "message": "", "audit": "not_written"}
        processed += 1
        if not email:
            result["message"] = "Skipped: member email is missing."
            out.append(result); continue
        if not valid_email(email):
            result["message"] = "Skipped: member email is invalid."
            out.append(result); continue
        if email in duplicates:
            result["status"] = "review"
            result["message"] = "Review required: more than one member record uses this email."
            out.append(result); continue
        if not active:
            result["message"] = "Skipped: member is inactive."
            out.append(result); continue
        auth_user = auth_map.get(email)
        if auth_user:
            auth_id = auth_user_id(auth_user)
            result["auth_status"] = "already_provisioned"
            result["auth_user_id"] = result["auth_user_id"] or auth_id
            if dry_run:
                result["status"] = "dry_run"
                result["message"] = "Dry run: already provisioned Auth user would be linked/verified."
            else:
                link_ok, link_msg = link_hm_user_to_auth(client, row, auth_id)
                result["hm_link_status"] = "linked" if link_ok else "link_failed"
                result["auth_user_id"] = auth_id
                result["status"] = "ok" if link_ok else "failed"
                result["message"] = "Already provisioned in Supabase Auth. " + link_msg
        else:
            result["auth_status"] = "pending"
            if dry_run:
                result["status"] = "dry_run"
                result["message"] = "Dry run: Auth user would be created and linked."
            else:
                pwd = temp_password or random_temp_password()
                create_ok, created_user, create_msg = create_auth_user(client, email, pwd, result["member_name"])
                if not create_ok:
                    result["status"] = "failed"
                    result["message"] = create_msg
                else:
                    auth_id = auth_user_id(created_user)
                    result["auth_status"] = "created"
                    result["auth_user_id"] = auth_id
                    link_ok, link_msg = link_hm_user_to_auth(client, row, auth_id)
                    result["hm_link_status"] = "linked" if link_ok else "link_failed"
                    result["status"] = "ok" if link_ok else "partial"
                    result["message"] = f"{create_msg} {link_msg}".strip()
        if send_reset and not dry_run and result.get("auth_user_id") and result.get("status") in {"ok", "partial"}:
            reset_ok, reset_msg = send_password_reset_email(client, email)
            result["password_reset_status"] = "sent" if reset_ok else "failed"
            result["message"] = f"{result['message']} {reset_msg}".strip()
        if not dry_run:
            audit_ok, audit_msg = write_audit(client, action="batch_provision", status=result["status"], member_id=result.get("member_id", ""), member_email=email, auth_user_id_value=result.get("auth_user_id", ""), actor_email=actor_email, message=result.get("message", ""), metadata={"auth_status": result.get("auth_status"), "hm_link_status": result.get("hm_link_status"), "password_reset_status": result.get("password_reset_status")})
            result["audit"] = "written" if audit_ok else audit_msg
        else:
            result["audit"] = "dry_run_not_written"
        out.append(result)
    return out
