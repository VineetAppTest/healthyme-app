from __future__ import annotations

import datetime as dt
import html
import os
import re
import uuid
from typing import Any

import requests


RESEND_ENDPOINT = "https://api.resend.com/emails"
DELIVERY_VERSION = "member-event-email-v1"
_SECRET_SECTIONS = ("email", "resend", "healthyme", "notifications")


def _text(value: object) -> str:
    return str(value or "").strip()


def _now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def _secret(name: str, default: str = "") -> str:
    value = os.environ.get(name)
    if value:
        return _text(value)
    try:
        import streamlit as st

        direct = st.secrets.get(name)
        if direct is not None:
            return _text(direct)
        lower_name = name.lower()
        direct = st.secrets.get(lower_name)
        if direct is not None:
            return _text(direct)
        for section in _SECRET_SECTIONS:
            values = st.secrets.get(section)
            if not values:
                continue
            try:
                nested = values.get(name)
                if nested is None:
                    nested = values.get(lower_name)
                if nested is not None:
                    return _text(nested)
            except Exception:
                continue
    except Exception:
        pass
    return default


def _first_secret(*names: str) -> str:
    for name in names:
        value = _secret(name)
        if value:
            return value
    return ""


def email_delivery_configuration_status() -> dict[str, Any]:
    api_key = _first_secret("RESEND_API_KEY")
    sender = _first_secret(
        "RESEND_FROM_EMAIL",
        "RESEND_FROM",
        "EMAIL_FROM",
        "FROM_EMAIL",
    )
    reply_to = _first_secret("RESEND_REPLY_TO", "EMAIL_REPLY_TO")
    return {
        "configured": bool(api_key and sender),
        "api_key_configured": bool(api_key),
        "sender_configured": bool(sender),
        "reply_to_configured": bool(reply_to),
        "provider": "Resend",
        "version": DELIVERY_VERSION,
    }


def _valid_email(value: object) -> bool:
    text = _text(value)
    return bool(re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", text))


def _member_row(db: dict[str, Any], member_id: object) -> dict[str, Any]:
    wanted = _text(member_id)
    wanted_lower = wanted.lower()
    for row in db.get("users", []) or []:
        row_id = _text(row.get("id"))
        row_email = _text(row.get("email")).lower()
        if wanted and (row_id == wanted or row_email == wanted_lower):
            return row
    return {}


def _format_sender(raw_sender: str) -> str:
    sender = _text(raw_sender)
    if not sender:
        return ""
    if "<" in sender and ">" in sender:
        return sender
    return f"HealthyMe <{sender}>"


def _details_html(details: dict[str, object]) -> str:
    rows = []
    for label, value in details.items():
        clean = _text(value)
        if not clean:
            continue
        rows.append(
            "<tr>"
            f"<td style='padding:7px 10px;color:#5D4A1E;font-weight:700;vertical-align:top'>{html.escape(str(label))}</td>"
            f"<td style='padding:7px 10px;color:#334155;vertical-align:top'>{html.escape(clean)}</td>"
            "</tr>"
        )
    if not rows:
        return ""
    return (
        "<table role='presentation' style='width:100%;border-collapse:collapse;margin:18px 0;"
        "background:#FFFDF8;border:1px solid #E3C98E;border-radius:12px;overflow:hidden'>"
        + "".join(rows)
        + "</table>"
    )


def _email_html(
    member_name: str,
    subject: str,
    message: str,
    details: dict[str, object],
) -> str:
    app_url = _first_secret("HEALTHYME_APP_URL", "APP_URL") or "https://healthymeappbyankita.streamlit.app"
    greeting_name = member_name or "there"
    return f"""
<!doctype html>
<html>
  <body style="margin:0;background:#F7F4EC;font-family:Arial,Helvetica,sans-serif;color:#334155">
    <div style="max-width:640px;margin:0 auto;padding:24px 14px">
      <div style="background:linear-gradient(135deg,#064E3B,#0F766E);border-radius:18px 18px 0 0;padding:22px 24px;color:#FFFFFF">
        <div style="font-size:22px;font-weight:800;letter-spacing:.2px">HealthyMe</div>
        <div style="font-size:13px;opacity:.9;margin-top:4px">A personal update from your wellness team</div>
      </div>
      <div style="background:#FFFFFF;border:1px solid #E3C98E;border-top:0;border-radius:0 0 18px 18px;padding:24px">
        <p style="margin:0 0 14px">Dear {html.escape(greeting_name)},</p>
        <h1 style="font-size:20px;line-height:1.35;color:#064E3B;margin:0 0 14px">{html.escape(subject)}</h1>
        <p style="font-size:15px;line-height:1.65;margin:0 0 8px">{html.escape(message)}</p>
        {_details_html(details)}
        <div style="margin:22px 0 8px">
          <a href="{html.escape(app_url)}" style="display:inline-block;background:#064E3B;color:#FFFFFF;text-decoration:none;padding:11px 18px;border-radius:10px;font-weight:700">Open HealthyMe</a>
        </div>
        <p style="font-size:13px;line-height:1.55;color:#64748B;margin:20px 0 0">Please sign in to HealthyMe for the latest details. Contact your HealthyMe team if anything needs clarification.</p>
        <p style="font-size:13px;color:#64748B;margin:16px 0 0">Warm regards,<br><strong style="color:#064E3B">Team HealthyMe</strong></p>
      </div>
    </div>
  </body>
</html>
"""


def _email_text(
    member_name: str,
    subject: str,
    message: str,
    details: dict[str, object],
) -> str:
    app_url = _first_secret("HEALTHYME_APP_URL", "APP_URL") or "https://healthymeappbyankita.streamlit.app"
    lines = [
        f"Dear {member_name or 'there'},",
        "",
        subject,
        "",
        message,
    ]
    for label, value in details.items():
        clean = _text(value)
        if clean:
            lines.append(f"{label}: {clean}")
    lines.extend(
        [
            "",
            f"Open HealthyMe: {app_url}",
            "",
            "Please sign in to HealthyMe for the latest details. Contact your HealthyMe team if anything needs clarification.",
            "",
            "Warm regards,",
            "Team HealthyMe",
        ]
    )
    return "\n".join(lines)


def _send_resend_email(
    *,
    recipient: str,
    member_name: str,
    subject: str,
    message: str,
    details: dict[str, object],
    idempotency_key: str,
) -> dict[str, Any]:
    api_key = _first_secret("RESEND_API_KEY")
    sender = _first_secret(
        "RESEND_FROM_EMAIL",
        "RESEND_FROM",
        "EMAIL_FROM",
        "FROM_EMAIL",
    )
    reply_to = _first_secret("RESEND_REPLY_TO", "EMAIL_REPLY_TO")
    attempted_at = _now_iso()

    if not _valid_email(recipient):
        return {
            "status": "recipient_missing",
            "provider": "Resend",
            "provider_id": "",
            "error": "A valid member email address is not available.",
            "attempted_at": attempted_at,
        }
    if not api_key or not sender:
        return {
            "status": "configuration_missing",
            "provider": "Resend",
            "provider_id": "",
            "error": "RESEND_API_KEY and RESEND_FROM_EMAIL/RESEND_FROM are required.",
            "attempted_at": attempted_at,
        }

    payload: dict[str, Any] = {
        "from": _format_sender(sender),
        "to": [recipient],
        "subject": subject,
        "html": _email_html(member_name, subject, message, details),
        "text": _email_text(member_name, subject, message, details),
    }
    if _valid_email(reply_to):
        payload["reply_to"] = reply_to

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Idempotency-Key": idempotency_key[:256],
    }
    try:
        response = requests.post(
            RESEND_ENDPOINT,
            headers=headers,
            json=payload,
            timeout=12,
        )
        response_data: dict[str, Any] = {}
        try:
            response_data = response.json() if response.content else {}
        except Exception:
            response_data = {}
        if response.status_code in {200, 201, 202}:
            return {
                "status": "sent",
                "provider": "Resend",
                "provider_id": _text(response_data.get("id")),
                "error": "",
                "attempted_at": attempted_at,
            }
        error_message = _text(
            response_data.get("message")
            or (response_data.get("error") or {}).get("message")
            or response.text
        )
        return {
            "status": "failed",
            "provider": "Resend",
            "provider_id": "",
            "error": error_message[:500] or f"Email provider returned HTTP {response.status_code}.",
            "attempted_at": attempted_at,
        }
    except Exception as exc:
        return {
            "status": "failed",
            "provider": "Resend",
            "provider_id": "",
            "error": str(exc)[:500],
            "attempted_at": attempted_at,
        }


def queue_member_event_email(
    db: dict[str, Any],
    *,
    member_id: object,
    kind: str,
    subject: str,
    message: str,
    actor_id: object = "system",
    source: str = "member_event",
    source_id: object = "",
    email_to: object = "",
    details: dict[str, object] | None = None,
    dedupe_key: str = "",
    append_message: bool = True,
    append_notification: bool = True,
) -> dict[str, Any]:
    """Create an in-app event, attempt immediate email delivery and retain an audit log.

    Existing legacy queued notifications are never sent automatically. Only events
    explicitly passed through this function receive DELIVERY_VERSION and are eligible
    for provider delivery, preventing a deployment from mailing historical records.
    """
    member_key = _text(member_id)
    member = _member_row(db, member_key)
    recipient = _text(email_to) or _text(member.get("email"))
    member_name = _text(member.get("name")) or _text(member.get("full_name"))
    event_id = str(uuid.uuid4())
    source_key = _text(source_id)
    stable_key = dedupe_key or "|".join(
        [kind, member_key, source, source_key, subject]
    )

    db.setdefault("email_delivery_logs", [])
    existing = next(
        (
            row
            for row in db["email_delivery_logs"]
            if row.get("dedupe_key") == stable_key
        ),
        None,
    )
    if existing:
        return dict(existing)

    delivery = _send_resend_email(
        recipient=recipient,
        member_name=member_name,
        subject=_text(subject),
        message=_text(message),
        details=dict(details or {}),
        idempotency_key=stable_key,
    )
    common = {
        "email_event_id": event_id,
        "email_delivery_version": DELIVERY_VERSION,
        "email_delivery_status": delivery.get("status"),
        "email_provider": delivery.get("provider"),
        "email_provider_id": delivery.get("provider_id"),
        "email_delivery_error": delivery.get("error"),
        "email_attempted_at": delivery.get("attempted_at"),
        "email_to": recipient,
        "email_subject": _text(subject),
        "dedupe_key": stable_key,
    }
    timestamp = _now_iso()

    message_id = ""
    if append_message:
        message_id = str(uuid.uuid4())[:8]
        db.setdefault("messages", []).append(
            {
                "id": message_id,
                "ts": timestamp,
                "member_id": member_key,
                "member_email": recipient,
                "sender_role": "admin",
                "actor_id": _text(actor_id) or "system",
                "subject": _text(subject),
                "message": _text(message),
                "status": "queued",
                "email_required": True,
                "source": source,
                "source_id": source_key,
                "read": False,
                "archived": False,
                **common,
            }
        )

    notification_id = ""
    if append_notification:
        notification_id = str(uuid.uuid4())[:8]
        db.setdefault("notifications", []).append(
            {
                "id": notification_id,
                "ts": timestamp,
                "kind": kind,
                "user_id": member_key,
                "member_id": member_key,
                "message": _text(message)[:500],
                "status": "queued",
                "email_required": True,
                "created_by": _text(actor_id) or "system",
                "source": source,
                "source_id": source_key,
                "source_message_id": message_id,
                **common,
            }
        )

    log = {
        "id": event_id,
        "ts": timestamp,
        "member_id": member_key,
        "member_name": member_name,
        "email_to": recipient,
        "kind": kind,
        "subject": _text(subject),
        "message": _text(message),
        "details": dict(details or {}),
        "actor_id": _text(actor_id) or "system",
        "source": source,
        "source_id": source_key,
        "message_id": message_id,
        "notification_id": notification_id,
        "dedupe_key": stable_key,
        "email_delivery_version": DELIVERY_VERSION,
        **delivery,
    }
    db["email_delivery_logs"].append(log)
    db["email_delivery_logs"] = db["email_delivery_logs"][-1000:]
    return dict(log)
