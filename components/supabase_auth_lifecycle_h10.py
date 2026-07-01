"""H10 Supabase Auth lifecycle audit helpers.

Server-side Streamlit admin only. This module must not be imported by Flutter or
member-side code.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from components.supabase_provisioning_h6 import (
    VALID_MEMBER_ROLE,
    auth_user_email,
    auth_user_id,
    clean_text,
    existing_auth_id,
    hm_users_by_email,
    list_auth_users,
    load_hm_users,
    member_name,
    normalize_email,
    send_password_reset_email,
    valid_email,
    write_audit,
)


def _auth_maps(client: Any) -> Tuple[bool, Dict[str, List[Any]], Dict[str, Any], str]:
    ok, users, message = list_auth_users(client)
    if not ok:
        return False, {}, {}, message
    by_email: Dict[str, List[Any]] = {}
    by_id: Dict[str, Any] = {}
    for user in users:
        email = auth_user_email(user)
        uid = auth_user_id(user)
        if email:
            by_email.setdefault(email, []).append(user)
        if uid:
            by_id[uid] = user
    return True, by_email, by_id, message


def lifecycle_audit_rows(client: Any) -> List[Dict[str, Any]]:
    hm_ok, hm_rows, hm_message = load_hm_users(client, include_inactive=True, role_filter="member")
    if not hm_ok:
        return [{"status": "failed", "message": hm_message}]

    auth_ok, auth_by_email, auth_by_id, auth_message = _auth_maps(client)
    if not auth_ok:
        return [{"status": "failed", "message": auth_message}]

    _hm_by_email, hm_duplicate_emails = hm_users_by_email(hm_rows)
    duplicate_hm = set(hm_duplicate_emails or [])
    duplicate_auth = {email for email, users in auth_by_email.items() if len(users) > 1}

    rows: List[Dict[str, Any]] = []
    for row in hm_rows:
        member_id = clean_text(row.get("id"))
        email = normalize_email(row.get("email"))
        role = clean_text(row.get("role", "member")).lower()
        active = bool(row.get("is_active", True))
        linked_id = existing_auth_id(row)
        matching_auth_users = auth_by_email.get(email, []) if email else []
        matching_auth_ids = [auth_user_id(user) for user in matching_auth_users if auth_user_id(user)]
        linked_auth_exists = bool(linked_id and linked_id in auth_by_id)
        first_matching_auth_id = matching_auth_ids[0] if matching_auth_ids else ""

        status = "safe_for_mobile_login"
        eligibility = "Safe"
        action = "No action required."
        message = "Active member has a matching Supabase Auth user and link is clean."

        if role != VALID_MEMBER_ROLE:
            status = "non_member_skipped"
            eligibility = "Blocked"
            action = "No member-auth action."
            message = "Only member-role users are in scope for Flutter member login."
        elif not email:
            status = "review_missing_email"
            eligibility = "Needs admin action"
            action = "Add a valid member email before provisioning."
            message = "Member email is missing."
        elif not valid_email(email):
            status = "review_invalid_email"
            eligibility = "Needs admin action"
            action = "Correct the member email before provisioning."
            message = "Member email format is invalid."
        elif email in duplicate_hm:
            status = "review_duplicate_member_email"
            eligibility = "Needs admin action"
            action = "Resolve duplicate hm_users email records."
            message = "More than one HealthyMe member record uses this email."
        elif email in duplicate_auth:
            status = "review_duplicate_auth_email"
            eligibility = "Needs admin action"
            action = "Review duplicate Supabase Auth users in Supabase dashboard."
            message = "More than one Supabase Auth user uses this email."
        elif not active:
            status = "blocked_inactive_member"
            eligibility = "Blocked"
            action = "Keep blocked unless admin reactivates the member."
            message = "Inactive HealthyMe member should not access Flutter member data."
        elif linked_id and linked_auth_exists and matching_auth_ids and linked_id not in matching_auth_ids:
            status = "review_link_email_mismatch"
            eligibility = "Needs admin action"
            action = "Review auth_user_id because linked Auth user does not match member email."
            message = "auth_user_id exists, but the linked Auth user email differs from hm_users.email."
        elif linked_id and not linked_auth_exists:
            status = "review_stale_auth_link"
            eligibility = "Needs admin action"
            action = "Clear or repair stale auth_user_id after checking Supabase Auth."
            message = "hm_users.auth_user_id is populated, but that Auth user was not found."
        elif matching_auth_ids and not linked_id:
            status = "needs_link_verify"
            eligibility = "Needs admin action"
            action = "Run Link/Verify for this existing Supabase Auth user."
            message = "Auth user exists by email, but hm_users.auth_user_id is not populated."
        elif not matching_auth_ids:
            status = "needs_provisioning"
            eligibility = "Needs admin action"
            action = "Provision or invite this active member."
            message = "No Supabase Auth user found for this active member email."

        rows.append(
            {
                "member_id": member_id,
                "member_name": member_name(row),
                "email": email,
                "role": role,
                "active": active,
                "hm_auth_user_id": linked_id,
                "auth_user_id_by_email": first_matching_auth_id,
                "auth_user_count_for_email": len(matching_auth_users),
                "linked_auth_exists": linked_auth_exists,
                "status": status,
                "login_eligibility": eligibility,
                "recommended_action": action,
                "message": message,
            }
        )
    return rows


def lifecycle_summary(client: Any) -> Dict[str, int]:
    rows = lifecycle_audit_rows(client)
    if rows and rows[0].get("status") == "failed":
        return {"Lifecycle audit failed": 1}
    safe = [r for r in rows if r.get("status") == "safe_for_mobile_login"]
    blocked = [r for r in rows if str(r.get("login_eligibility")) == "Blocked"]
    needs_action = [r for r in rows if str(r.get("login_eligibility")) == "Needs admin action"]
    return {
        "Members audited": len(rows),
        "Safe for mobile login": len(safe),
        "Blocked": len(blocked),
        "Needs admin action": len(needs_action),
    }


def orphan_auth_user_rows(client: Any) -> List[Dict[str, Any]]:
    hm_ok, hm_rows, hm_message = load_hm_users(client, include_inactive=True, role_filter="member")
    if not hm_ok:
        return [{"status": "failed", "message": hm_message}]
    auth_ok, auth_by_email, auth_by_id, auth_message = _auth_maps(client)
    if not auth_ok:
        return [{"status": "failed", "message": auth_message}]

    hm_by_email = {normalize_email(row.get("email")): row for row in hm_rows if normalize_email(row.get("email"))}
    linked_ids = {existing_auth_id(row) for row in hm_rows if existing_auth_id(row)}

    rows: List[Dict[str, Any]] = []
    for uid, user in sorted(auth_by_id.items(), key=lambda item: auth_user_email(item[1])):
        email = auth_user_email(user)
        member = hm_by_email.get(email)
        if member and uid in linked_ids:
            continue
        if member:
            status = "auth_user_matches_email_but_not_linked"
            action = "Run Link/Verify from the provisioning workbench."
            member_id = clean_text(member.get("id"))
            name = member_name(member)
        else:
            status = "orphan_auth_user_no_member_email_match"
            action = "Review in Supabase Auth. Do not delete blindly; confirm it is not an admin or legacy account."
            member_id = ""
            name = ""
        rows.append(
            {
                "auth_user_id": uid,
                "email": email,
                "matched_member_id": member_id,
                "matched_member_name": name,
                "status": status,
                "recommended_action": action,
            }
        )
    return rows


def send_password_reset_for_member(client: Any, *, email: str, actor_email: str = "", dry_run: bool = True) -> Dict[str, Any]:
    email = normalize_email(email)
    result: Dict[str, Any] = {
        "email": email,
        "member_id": "",
        "member_name": "",
        "active": "",
        "auth_user_id": "",
        "status": "blocked",
        "message": "",
        "audit": "not_written",
    }
    if not email or not valid_email(email):
        result["message"] = "Enter a valid member email."
        return result

    hm_ok, hm_rows, hm_message = load_hm_users(client, include_inactive=True, role_filter="member")
    if not hm_ok:
        result["status"] = "failed"
        result["message"] = hm_message
        return result
    matches = [row for row in hm_rows if normalize_email(row.get("email")) == email]
    if not matches:
        result["message"] = "No HealthyMe member record exists for this email."
        return result
    if len(matches) > 1:
        result["status"] = "review"
        result["message"] = "Review required: more than one member record uses this email."
        return result

    member = matches[0]
    active = bool(member.get("is_active", True))
    result.update({"member_id": clean_text(member.get("id")), "member_name": member_name(member), "active": active})
    if not active:
        result["message"] = "Blocked: inactive members should not receive mobile onboarding reset emails."
        return result

    auth_ok, auth_by_email, _auth_by_id, auth_message = _auth_maps(client)
    if not auth_ok:
        result["status"] = "failed"
        result["message"] = auth_message
        return result
    matches_auth = auth_by_email.get(email, [])
    if not matches_auth:
        result["message"] = "No Supabase Auth user exists for this email. Provision or link first."
        return result
    if len(matches_auth) > 1:
        result["status"] = "review"
        result["message"] = "Review required: duplicate Supabase Auth users exist for this email."
        return result

    result["auth_user_id"] = auth_user_id(matches_auth[0])
    if dry_run:
        result["status"] = "dry_run"
        result["message"] = "Dry run: password reset email can be sent for this active provisioned member."
        return result

    reset_ok, reset_message = send_password_reset_email(client, email)
    result["status"] = "sent" if reset_ok else "failed"
    result["message"] = reset_message
    audit_ok, audit_msg = write_audit(
        client,
        action="h10_password_reset",
        status=result["status"],
        member_id=result.get("member_id", ""),
        member_email=email,
        auth_user_id_value=result.get("auth_user_id", ""),
        actor_email=actor_email,
        message=result.get("message", ""),
        metadata={"h10": True, "dry_run": False},
    )
    result["audit"] = "written" if audit_ok else audit_msg
    return result
