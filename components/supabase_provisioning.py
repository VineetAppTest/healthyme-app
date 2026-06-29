"""HealthyMe Supabase Auth provisioning helpers.

Sprint 2A + 2B + 2C scope:
- single member provisioning
- batch existing member provisioning
- provisioning audit log

This module is intentionally server-side only. It must only be used from the
Streamlit admin app with SUPABASE_SERVICE_ROLE_KEY configured. Do not import it
from Flutter/mobile code.
"""

from __future__ import annotations

import datetime as _dt
import os
import secrets
import string
from typing import Any, Dict, Iterable, List, Optional, Tuple

import streamlit as st

SECRET_SECTIONS = ("auth", "auth0", "authentication", "healthyme", "supabase")
VALID_PROVISIONING_ROLES = {"member"}
AUDIT_TABLE = "hm_supabase_auth_provisioning_audit"
DEFAULT_REDIRECT_TO = "healthyme://reset-password/"


def clean_text(value: object, default: str = "") -> str:
    if value is None:
        return default
    return str(value).strip()


def normalize_email(email: str) -> str:
    return clean_text(email).lower()


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


def password_reset_redirect_to() -> str:
    return get_secret("SUPABASE_PASSWORD_RESET_REDIRECT_TO", DEFAULT_REDIRECT_TO) or DEFAULT_REDIRECT_TO


def random_temp_password(length: int = 16) -> str:
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
        pass
    return {
        "id": getattr(user, "id", ""),
        "email": getattr(user, "email", ""),
        "created_at": getattr(user, "created_at", ""),
        "last_sign_in_at": getattr(user, "last_sign_in_at", ""),
    }


def auth_user_id(user: Any) -> str:
    data = _auth_user_dict(user)
    return clean_text(data.get("id") or data.get("user_id") or getattr(user, "id", ""))


def auth_user_email(user: Any) -> str:
    data = _auth_user_dict(user)
    return normalize_email(data.get("email") or getattr(user, "email", ""))


def extract_created_user(response: Any) -> Optional[Any]:
    if response is None:
        return None
    if isinstance(response, dict):
        if response.get("user"):
            return response.get("user")
        if isinstance(response.get("data"), dict) and response["data"].get("user"):
            return response["data"].get("user")
        if response.get("id") or response.get("email"):
            return response
    user = getattr(response, "user", None)
    if user is not None:
        return user
    data = getattr(response, "data", None)
    if isinstance(data, dict) and data.get("user"):
        return data.get("user")
    try:
        dumped = response.model_dump()
        return extract_created_user(dumped)
    except Exception:
        return None


def list_auth_users(client: Any, max_pages: int = 30, per_page: int = 1000) -> Tuple[bool, List[Any], str]:
    if client is None:
        return False, [], "SUPABASE_SERVICE_ROLE_KEY is missing or the service-role client could not be created."
    admin = getattr(getattr(client, "auth", None), "admin", None)
    if admin is None or not hasattr(admin, "list_users"):
        return False, [], "Supabase Auth user listing is not available in the installed supabase client."
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
        return False, [], f"Supabase Auth user listing failed: {exc}"


def auth_users_by_email(client: Any) -> Tuple[bool, Dict[str, Any], str]:
    ok, users, message = list_auth_users(client)
    if not ok:
        return False, {}, message
    by_email: Dict[str, Any] = {}
    duplicate_emails = []
    for user in users:
        email = auth_user_email(user)
        if not email:
            continue
        if email in by_email:
            duplicate_emails.append(email)
            continue
        by_email[email] = user
    if duplicate_emails:
        message += f" Duplicate Auth emails ignored for safety: {', '.join(sorted(set(duplicate_emails))[:5])}."
    return True, by_email, message


def load_hm_users(client: Any, *, include_inactive: bool = False, role_filter: str = "member") -> Tuple[bool, List[Dict[str, Any]], str]:
    if client is None:
        return False, [], "SUPABASE_SERVICE_ROLE_KEY is missing or the service-role client could not be created."
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
        return False, [], f"Could not load hm_users. Run the Sprint 2A+2B+2C SQL first if auth_user_id/audit columns are missing. Detail: {exc}"


def hm_users_by_email(rows: Iterable[Dict[str, Any]]) -> Tuple[Dict[str, Dict[str, Any]], set]:
    by_email: Dict[str, Dict[str, Any]] = {}
    duplicates = set()
    for row in rows:
        email = normalize_email(row.get("email", ""))
        if not email:
            continue
        if email in by_email:
            duplicates.add(email)
            continue
        by_email[email] = row
    return by_email, duplicates


def load_hm_user_by_email(client: Any, email: str) -> Tuple[bool, List[Dict[str, Any]], str]:
    email = normalize_email(email)
    if not email:
        return False, [], "Email is required."
    if client is None:
        return False, [], "SUPABASE_SERVICE_ROLE_KEY is missing or the service-role client could not be created."
    try:
        result = client.table("hm_users").select("*").eq("email", email).execute()
        rows = list(getattr(result, "data", None) or [])
        for row in rows:
            row["email"] = normalize_email(row.get("email", ""))
            row["role"] = clean_text(row.get("role", "member")).lower()
            row["is_active"] = bool(row.get("is_active", True))
        return True, rows, f"Found {len(rows)} hm_users row(s) for {email}."
    except Exception as exc:
        return False, [], f"Could not read hm_users for {email}: {exc}"


def create_auth_user(client: Any, email: str, password: str, name: str = "") -> Tuple[bool, Optional[Any], str]:
    email = normalize_email(email)
    admin = getattr(getattr(client, "auth", None), "admin", None) if client is not None else None
    if admin is None or not hasattr(admin, "create_user"):
        return False, None, "Supabase admin create_user is not available in the installed client."

    payload_variants = [
        {
            "email": email,
            "password": password,
            "email_confirm": True,
            "user_metadata": {"name": name or email, "created_by": "HealthyMe Streamlit Admin"},
            "app_metadata": {"healthyme_role": "member", "healthyme_provisioned": True},
        },
        {
            "email": email,
            "password": password,
            "email_confirm": True,
            "data": {"name": name or email, "created_by": "HealthyMe Streamlit Admin"},
        },
        {"email": email, "password": password},
    ]

    last_error = ""
    for payload in payload_variants:
        try:
            response = admin.create_user(payload)
            user = extract_created_user(response)
            return True, user, "Supabase Auth user created."
        except Exception as exc:
            last_error = str(exc)
            if "already" in last_error.lower() or "registered" in last_error.lower() or "exists" in last_error.lower():
                return False, None, "Supabase Auth user already exists."
    return False, None, f"Supabase Auth user creation failed: {last_error}"


def send_password_reset_email(client: Any, email: str, redirect_to: Optional[str] = None) -> Tuple[bool, str]:
    email = normalize_email(email)
    redirect_to = clean_text(redirect_to or password_reset_redirect_to())
    auth = getattr(client, "auth", None) if client is not None else None
    method = getattr(auth, "reset_password_for_email", None) if auth is not None else None
    if not callable(method):
        return False, "Supabase reset_password_for_email is not available in the installed client."

    attempts = []
    if redirect_to:
        attempts.extend([
            lambda: method(email, {"redirect_to": redirect_to}),
            lambda: method(email, options={"redirect_to": redirect_to}),
        ])
    attempts.append(lambda: method(email))

    last_error = ""
    for attempt in attempts:
        try:
            attempt()
            return True, "Supabase password reset email requested."
        except TypeError as exc:
            last_error = str(exc)
            continue
        except Exception as exc:
            last_error = str(exc)
            break
    return False, f"Supabase password reset email failed: {last_error}"


def link_hm_user_to_auth(client: Any, hm_user: Dict[str, Any], auth_id: str) -> Tuple[bool, str]:
    if client is None:
        return False, "Service-role client missing."
    hm_id = clean_text(hm_user.get("id"))
    if not hm_id:
        return False, "hm_users.id is missing."
    existing_auth_id = clean_text(hm_user.get("auth_user_id") or hm_user.get("supabase_auth_id"))
    if existing_auth_id and existing_auth_id != auth_id:
        return False, "hm_users row is already linked to a different Supabase Auth user."

    now = utc_now_iso()
    payloads = [
        {
            "auth_user_id": auth_id,
            "auth_provider": "supabase",
            "auth_migrated_at": now,
            "updated_at": now,
        },
        {
            "auth_user_id": auth_id,
            "auth_provider": "supabase",
            "updated_at": now,
        },
        {
            "auth_user_id": auth_id,
            "auth_provider": "supabase",
        },
        {"auth_user_id": auth_id},
    ]
    last_error = ""
    for payload in payloads:
        try:
            client.table("hm_users").update(payload).eq("id", hm_id).execute()
            return True, "hm_users.auth_user_id linked."
        except Exception as exc:
            last_error = str(exc)
            continue
    return False, f"Could not update hm_users.auth_user_id. Run the Sprint 2A+2B+2C SQL first. Detail: {last_error}"


def write_audit(
    client: Any,
    *,
    action: str,
    status: str,
    member_id: str = "",
    member_email: str = "",
    auth_user_id_value: str = "",
    actor_email: str = "",
    message: str = "",
    metadata: Optional[Dict[str, Any]] = None,
) -> Tuple[bool, str]:
    if client is None:
        return False, "Audit not written because service-role client is missing."
    payload = {
        "action": action,
        "status": status,
        "member_id": member_id or None,
        "member_email": normalize_email(member_email) or None,
        "auth_user_id": auth_user_id_value or None,
        "actor_email": normalize_email(actor_email) or None,
        "message": clean_text(message)[:1000],
        "metadata": metadata or {},
    }
    try:
        client.table(AUDIT_TABLE).insert(payload).execute()
        return True, "Audit row written."
    except Exception as exc:
        return False, f"Audit not written. Run the Sprint 2A+2B+2C SQL first. Detail: {exc}"


def load_audit_rows(client: Any, limit: int = 200) -> Tuple[bool, List[Dict[str, Any]], str]:
    if client is None:
        return False, [], "Service-role client missing."
    try:
        response = (
            client.table(AUDIT_TABLE)
            .select("created_at,action,status,member_email,member_id,auth_user_id,actor_email,message")
            .order("created_at", desc=True)
            .limit(int(limit))
            .execute()
        )
        return True, list(getattr(response, "data", None) or []), "Audit rows loaded."
    except Exception as exc:
        return False, [], f"Could not load audit table. Run the Sprint 2A+2B+2C SQL first. Detail: {exc}"


def provision_single_member(
    client: Any,
    *,
    email: str,
    temp_password: str = "",
    send_reset: bool = False,
    actor_email: str = "",
    dry_run: bool = True,
) -> Dict[str, Any]:
    email = normalize_email(email)
    result: Dict[str, Any] = {
        "email": email,
        "member_id": "",
        "member_name": "",
        "role": "",
        "is_active": "",
        "auth_status": "unknown",
        "auth_user_id": "",
        "hm_link_status": "not_run",
        "password_reset_status": "not_requested",
        "temp_password": "",
        "status": "blocked",
        "message": "",
        "audit": "not_written",
    }

    if not email:
        result["message"] = "Email is required."
        return result
    if client is None:
        result["message"] = "SUPABASE_SERVICE_ROLE_KEY is missing or invalid."
        return result

    ok, hm_rows, msg = load_hm_user_by_email(client, email)
    if not ok:
        result["message"] = msg
        write_audit(client, action="single_provision", status="failed", member_email=email, actor_email=actor_email, message=msg)
        return result
    if not hm_rows:
        result["message"] = "No hm_users row exists for this email. Create the HealthyMe member first."
        write_audit(client, action="single_provision", status="blocked", member_email=email, actor_email=actor_email, message=result["message"])
        return result
    if len(hm_rows) > 1:
        result["message"] = "Duplicate hm_users rows found for this email. Resolve duplicates before provisioning."
        write_audit(client, action="single_provision", status="blocked", member_email=email, actor_email=actor_email, message=result["message"])
        return result

    hm_user = hm_rows[0]
    result.update(
        {
            "member_id": clean_text(hm_user.get("id")),
            "member_name": clean_text(hm_user.get("name")),
            "role": clean_text(hm_user.get("role")),
            "is_active": bool(hm_user.get("is_active", True)),
            "auth_user_id": clean_text(hm_user.get("auth_user_id") or hm_user.get("supabase_auth_id")),
        }
    )

    if result["role"] not in VALID_PROVISIONING_ROLES:
        result["message"] = "Only member-role users are provisioned in Sprint 2. Admin auth migration comes later."
        write_audit(client, action="single_provision", status="blocked", member_id=result["member_id"], member_email=email, actor_email=actor_email, message=result["message"])
        return result
    if not result["is_active"]:
        result["message"] = "Inactive member blocked. Mark active before provisioning."
        write_audit(client, action="single_provision", status="blocked", member_id=result["member_id"], member_email=email, actor_email=actor_email, message=result["message"])
        return result

    ok, auth_map, auth_msg = auth_users_by_email(client)
    if not ok:
        result["message"] = auth_msg
        write_audit(client, action="single_provision", status="failed", member_id=result["member_id"], member_email=email, actor_email=actor_email, message=auth_msg)
        return result

    existing_auth = auth_map.get(email)
    if existing_auth:
        existing_id = auth_user_id(existing_auth)
        result["auth_status"] = "exists"
        result["auth_user_id"] = result["auth_user_id"] or existing_id
        if dry_run:
            result["status"] = "dry_run"
            result["message"] = "Dry run: existing Supabase Auth user would be linked if hm_users.auth_user_id is blank."
            return result
        link_ok, link_msg = link_hm_user_to_auth(client, hm_user, existing_id)
        result["hm_link_status"] = "linked" if link_ok else "link_failed"
        result["auth_user_id"] = existing_id
        result["status"] = "ok" if link_ok else "failed"
        result["message"] = link_msg
    else:
        password = temp_password or random_temp_password()
        result["temp_password"] = password if not temp_password else "admin_entered_password"
        result["auth_status"] = "missing"
        if dry_run:
            result["status"] = "dry_run"
            result["message"] = "Dry run: missing Supabase Auth user would be created and linked."
            return result
        create_ok, created_user, create_msg = create_auth_user(client, email, password, result["member_name"])
        if not create_ok:
            result["status"] = "failed"
            result["message"] = create_msg
            write_audit(client, action="single_provision", status="failed", member_id=result["member_id"], member_email=email, actor_email=actor_email, message=create_msg)
            return result
        created_id = auth_user_id(created_user)
        result["auth_status"] = "created"
        result["auth_user_id"] = created_id
        link_ok, link_msg = link_hm_user_to_auth(client, hm_user, created_id)
        result["hm_link_status"] = "linked" if link_ok else "link_failed"
        result["status"] = "ok" if link_ok else "partial"
        result["message"] = f"{create_msg} {link_msg}".strip()

    if send_reset and result.get("auth_user_id"):
        reset_ok, reset_msg = send_password_reset_email(client, email)
        result["password_reset_status"] = "sent" if reset_ok else "failed"
        result["message"] = f"{result['message']} {reset_msg}".strip()

    audit_ok, audit_msg = write_audit(
        client,
        action="single_provision",
        status=result["status"],
        member_id=result["member_id"],
        member_email=email,
        auth_user_id_value=result.get("auth_user_id", ""),
        actor_email=actor_email,
        message=result["message"],
        metadata={
            "auth_status": result.get("auth_status"),
            "hm_link_status": result.get("hm_link_status"),
            "password_reset_status": result.get("password_reset_status"),
        },
    )
    result["audit"] = "written" if audit_ok else audit_msg
    return result


def provision_batch_members(
    client: Any,
    *,
    temp_password: str = "",
    send_reset: bool = False,
    actor_email: str = "",
    dry_run: bool = True,
    include_inactive: bool = False,
    limit: int = 500,
) -> List[Dict[str, Any]]:
    rows_out: List[Dict[str, Any]] = []
    ok, hm_rows, hm_msg = load_hm_users(client, include_inactive=include_inactive, role_filter="member")
    if not ok:
        return [{"email": "", "status": "failed", "message": hm_msg}]

    by_email, duplicates = hm_users_by_email(hm_rows)
    ok, auth_map, auth_msg = auth_users_by_email(client)
    if not ok:
        return [{"email": "", "status": "failed", "message": auth_msg}]

    processed = 0
    for email in sorted(by_email.keys()):
        if processed >= max(1, int(limit)):
            rows_out.append({"email": "", "status": "stopped", "message": f"Stopped at batch limit {limit}."})
            break
        hm_user = by_email[email]
        processed += 1
        row = {
            "email": email,
            "member_id": clean_text(hm_user.get("id")),
            "member_name": clean_text(hm_user.get("name")),
            "active": bool(hm_user.get("is_active", True)),
            "auth_status": "unknown",
            "auth_user_id": clean_text(hm_user.get("auth_user_id") or hm_user.get("supabase_auth_id")),
            "hm_link_status": "not_run",
            "password_reset_status": "not_requested",
            "status": "blocked",
            "message": "",
        }
        if email in duplicates:
            row["message"] = "Duplicate hm_users email skipped."
            rows_out.append(row)
            continue
        if not row["active"]:
            row["message"] = "Inactive member skipped."
            rows_out.append(row)
            continue

        existing_auth = auth_map.get(email)
        if existing_auth:
            existing_id = auth_user_id(existing_auth)
            row["auth_status"] = "exists"
            row["auth_user_id"] = row["auth_user_id"] or existing_id
            if dry_run:
                row["status"] = "dry_run"
                row["message"] = "Dry run: existing Auth user would be linked if required."
            else:
                link_ok, link_msg = link_hm_user_to_auth(client, hm_user, existing_id)
                row["hm_link_status"] = "linked" if link_ok else "link_failed"
                row["auth_user_id"] = existing_id
                row["status"] = "ok" if link_ok else "failed"
                row["message"] = link_msg
        else:
            row["auth_status"] = "missing"
            if dry_run:
                row["status"] = "dry_run"
                row["message"] = "Dry run: missing Auth user would be created and linked."
            else:
                pwd = temp_password or random_temp_password()
                create_ok, created_user, create_msg = create_auth_user(client, email, pwd, row["member_name"])
                if not create_ok:
                    row["status"] = "failed"
                    row["message"] = create_msg
                else:
                    created_id = auth_user_id(created_user)
                    row["auth_status"] = "created"
                    row["auth_user_id"] = created_id
                    link_ok, link_msg = link_hm_user_to_auth(client, hm_user, created_id)
                    row["hm_link_status"] = "linked" if link_ok else "link_failed"
                    row["status"] = "ok" if link_ok else "partial"
                    row["message"] = f"{create_msg} {link_msg}".strip()

        if send_reset and not dry_run and row.get("auth_user_id") and row.get("status") in {"ok", "partial"}:
            reset_ok, reset_msg = send_password_reset_email(client, email)
            row["password_reset_status"] = "sent" if reset_ok else "failed"
            row["message"] = f"{row['message']} {reset_msg}".strip()

        if not dry_run:
            audit_ok, audit_msg = write_audit(
                client,
                action="batch_provision",
                status=row["status"],
                member_id=row.get("member_id", ""),
                member_email=email,
                auth_user_id_value=row.get("auth_user_id", ""),
                actor_email=actor_email,
                message=row.get("message", ""),
                metadata={
                    "auth_status": row.get("auth_status"),
                    "hm_link_status": row.get("hm_link_status"),
                    "password_reset_status": row.get("password_reset_status"),
                },
            )
            row["audit"] = "written" if audit_ok else audit_msg
        else:
            row["audit"] = "dry_run_not_written"
        rows_out.append(row)

    return rows_out
