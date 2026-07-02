"""H11 Supabase Auth cutover readiness helpers.

Admin/server-side only. No Flutter import path and no member-side secrets.
"""

from __future__ import annotations

from typing import Any, Dict, List

from components.supabase_auth_lifecycle_h10 import lifecycle_audit_rows, orphan_auth_user_rows
from components.supabase_provisioning_h6 import config_status, password_reset_redirect_to, readiness_snapshot


PASS = "PASS"
WARN = "WARN"
BLOCKED = "BLOCKED"
INFO = "INFO"


def _row(area: str, check: str, status: str, evidence: str, action: str) -> Dict[str, str]:
    return {
        "Area": area,
        "Check": check,
        "Status": status,
        "Evidence": evidence,
        "Admin action": action,
    }


def _count(rows: List[Dict[str, Any]], key: str, value: str) -> int:
    return len([r for r in rows if str(r.get(key, "")) == value])


def cutover_readiness_rows(client: Any) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    config = config_status()
    snapshot = readiness_snapshot(client)
    lifecycle = lifecycle_audit_rows(client)
    orphans = orphan_auth_user_rows(client)

    failed_lifecycle = bool(lifecycle and lifecycle[0].get("status") == "failed")
    failed_orphan = bool(orphans and orphans[0].get("status") == "failed")

    rows.append(
        _row(
            "Secrets",
            "Supabase URL configured",
            PASS if config.get("SUPABASE_URL") else BLOCKED,
            "Configured" if config.get("SUPABASE_URL") else "Missing SUPABASE_URL",
            "Set Streamlit secret before cutover." if not config.get("SUPABASE_URL") else "No action.",
        )
    )
    rows.append(
        _row(
            "Secrets",
            "Supabase anon key configured",
            PASS if config.get("SUPABASE_ANON_KEY") else BLOCKED,
            "Configured" if config.get("SUPABASE_ANON_KEY") else "Missing SUPABASE_ANON_KEY",
            "Set Streamlit secret and Flutter env before cutover." if not config.get("SUPABASE_ANON_KEY") else "No action.",
        )
    )
    rows.append(
        _row(
            "Secrets",
            "Supabase service-role key stays server-side",
            PASS if config.get("SUPABASE_SERVICE_ROLE_KEY") else BLOCKED,
            "Configured for admin workbench only" if config.get("SUPABASE_SERVICE_ROLE_KEY") else "Missing service-role key for admin audit/provisioning",
            "Never copy service-role key into Flutter. Configure only in Streamlit secrets." if not config.get("SUPABASE_SERVICE_ROLE_KEY") else "Keep server-side only.",
        )
    )

    summary = snapshot.get("summary", {}) if isinstance(snapshot, dict) else {}
    active_members = int(summary.get("Active members", summary.get("active_members", 0)) or 0)
    auth_users = int(summary.get("Supabase Auth users", summary.get("auth_users", 0)) or 0)
    rows.append(
        _row(
            "Provisioning",
            "Existing H6/H7 provisioning base is visible",
            PASS if client is not None else BLOCKED,
            f"Active members: {active_members}; Supabase Auth users visible: {auth_users}",
            "Open provisioning workbench and run dry-run before final member-auth cutover." if client is not None else "Fix service-role admin client first.",
        )
    )

    if failed_lifecycle:
        rows.append(_row("Lifecycle", "Lifecycle audit can run", BLOCKED, lifecycle[0].get("message", "Lifecycle audit failed"), "Fix lifecycle audit before cutover."))
    else:
        safe = _count(lifecycle, "status", "safe_for_mobile_login")
        needs_action = len([r for r in lifecycle if str(r.get("login_eligibility")) == "Needs admin action"])
        blocked = len([r for r in lifecycle if str(r.get("login_eligibility")) == "Blocked"])
        rows.append(
            _row(
                "Lifecycle",
                "Active member mobile-login readiness",
                PASS if needs_action == 0 else BLOCKED,
                f"Safe: {safe}; needs admin action: {needs_action}; blocked/inactive: {blocked}",
                "Resolve all Needs admin action rows before declaring cutover." if needs_action else "No action for active eligible members.",
            )
        )
        rows.append(
            _row(
                "Lifecycle",
                "Inactive members remain blocked",
                PASS,
                f"Blocked/inactive rows: {blocked}",
                "Do not provision inactive members unless admin intentionally reactivates them.",
            )
        )

    if failed_orphan:
        rows.append(_row("Orphan Auth", "Orphan/unlinked Auth review can run", WARN, orphans[0].get("message", "Orphan review failed"), "Review Supabase Auth users manually."))
    else:
        unlinked = len(orphans)
        rows.append(
            _row(
                "Orphan Auth",
                "Orphan/unlinked Auth users reviewed",
                PASS if unlinked == 0 else WARN,
                f"Rows needing review: {unlinked}",
                "Review listed Auth users. Do not delete blindly; confirm admin/legacy accounts first." if unlinked else "No action.",
            )
        )

    redirect = password_reset_redirect_to()
    rows.append(
        _row(
            "Password Reset",
            "Password reset/onboarding redirect available",
            PASS if redirect else WARN,
            redirect or "No redirect configured",
            "Confirm redirect target before sending onboarding/reset emails at scale." if redirect else "Configure reset redirect before rollout.",
        )
    )

    rows.append(_row("Auth0", "Streamlit admin Auth0 remains active", PASS, "H11 does not retire Auth0", "Keep Auth0 admin login until a separate admin-auth migration is approved."))
    rows.append(_row("Rollback", "Member-auth rollback path documented", PASS, "Pause Supabase member rollout; keep Streamlit admin/Auth0 unchanged", "If Flutter member login fails, stop onboarding/reset emails and use Streamlit admin as control plane."))
    rows.append(_row("Flutter", "Flutter stream remains independent", INFO, "H11 does not touch Flutter files", "Continue H9A/H9A.3 APK smoke test separately."))
    return rows


def cutover_summary(rows: List[Dict[str, str]]) -> Dict[str, int]:
    return {
        "PASS": len([r for r in rows if r.get("Status") == PASS]),
        "WARN": len([r for r in rows if r.get("Status") == WARN]),
        "BLOCKED": len([r for r in rows if r.get("Status") == BLOCKED]),
        "INFO": len([r for r in rows if r.get("Status") == INFO]),
    }


def session_guardrail_rows() -> List[Dict[str, str]]:
    return [
        _row("Login", "Active provisioned member login", INFO, "Validate in Flutter APK", "Login as active member and confirm dashboard loads."),
        _row("Logout", "Session cleanup after logout", INFO, "Validate in Flutter APK", "Logout Member A, then login Member B. Confirm no A data is visible."),
        _row("Member switch", "Cross-member data isolation", INFO, "Validate in Flutter APK", "Test two members with different saved days/profile data."),
        _row("Inactive after login", "Inactive member access blocked", INFO, "Validate after admin deactivates test member", "Deactivate member, relaunch app, confirm blocked on reload/login."),
        _row("Password reset", "Reset email is controlled", INFO, "Validate in H10/H11 admin workbench", "Dry run first; execution only with exact confirmation."),
        _row("Rollback", "Rollout can be paused", INFO, "Operational playbook", "Stop onboarding/reset emails; do not change Auth0 admin path."),
    ]


def cutover_decision(summary: Dict[str, int]) -> str:
    if summary.get("BLOCKED", 0) > 0:
        return "NOT READY — blocked checks remain. Do not declare Supabase Auth cutover yet."
    if summary.get("WARN", 0) > 0:
        return "CONDITIONALLY READY — warnings must be reviewed before broad rollout."
    return "READY FOR CONTROLLED MEMBER-AUTH CUTOVER — proceed with pilot-size rollout and monitoring."
