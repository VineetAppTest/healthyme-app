"""H9A.4 structured Nutritionist Notes helpers.

Admin-side source of truth for Food Journal-linked guidance.
This module intentionally uses the existing HealthyMe app-state store so Streamlit
admin and Flutter member can read the same note records.
"""

from __future__ import annotations

import datetime as _dt
import uuid
from typing import Any, Dict, Iterable, List, Optional

from components.db import load_db, save_db

NOTE_STORE_KEY = "nutritionist_structured_notes"
VALID_NOTE_TYPES = {"single_day", "date_range", "general"}


def _today_iso() -> str:
    return _dt.date.today().isoformat()


def _normalise_date(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, _dt.datetime):
        return value.date().isoformat()
    if isinstance(value, _dt.date):
        return value.isoformat()
    text = str(value).strip()
    if not text:
        return ""
    try:
        return _dt.date.fromisoformat(text[:10]).isoformat()
    except Exception:
        return ""


def _date_range(start: str, end: str, max_days: int = 120) -> List[str]:
    start_date = _dt.date.fromisoformat(start)
    end_date = _dt.date.fromisoformat(end)
    if end_date < start_date:
        raise ValueError("To Date cannot be before From Date.")
    days = (end_date - start_date).days + 1
    if days > max_days:
        raise ValueError(f"Date range cannot exceed {max_days} days.")
    return [(start_date + _dt.timedelta(days=i)).isoformat() for i in range(days)]


def related_dates_for_note(note_type: str, from_date: str, to_date: str, sent_date: str) -> List[str]:
    if note_type == "general":
        return [sent_date]
    if note_type == "single_day":
        if not from_date:
            raise ValueError("From Date is required for a single-day note.")
        return [from_date]
    if note_type == "date_range":
        if not from_date or not to_date:
            raise ValueError("Both From Date and To Date are required for a multi-day note.")
        return _date_range(from_date, to_date)
    raise ValueError("Invalid note type.")


def create_structured_nutritionist_note(
    *,
    member_id: str,
    member_name: str = "",
    note_type: str,
    subject: str,
    note_text: str,
    from_date: Any = None,
    to_date: Any = None,
    created_by: str = "admin",
) -> Dict[str, Any]:
    member_id = str(member_id or "").strip()
    if not member_id:
        raise ValueError("Member is required.")
    note_type = str(note_type or "").strip()
    if note_type not in VALID_NOTE_TYPES:
        raise ValueError("Select a valid note type.")
    subject = str(subject or "").strip()
    note_text = str(note_text or "").strip()
    if not note_text:
        raise ValueError("Nutritionist Note is required.")
    if not subject:
        subject = "Nutritionist Note"

    sent_date = _today_iso()
    from_iso = _normalise_date(from_date)
    to_iso = _normalise_date(to_date)
    if note_type == "single_day":
        to_iso = from_iso
    if note_type == "general":
        from_iso = sent_date
        to_iso = sent_date

    related_dates = related_dates_for_note(note_type, from_iso, to_iso, sent_date)
    now = _dt.datetime.now().isoformat(timespec="seconds")
    note = {
        "id": str(uuid.uuid4())[:12],
        "member_id": member_id,
        "member_name": str(member_name or "").strip(),
        "note_type": note_type,
        "subject": subject,
        "note_text": note_text,
        "from_date": from_iso,
        "to_date": to_iso,
        "sent_date": sent_date,
        "related_dates": related_dates,
        "created_by": str(created_by or "admin"),
        "created_at": now,
        "read_at": "",
        "archived_at": "",
        "member_archived": False,
        "status": "published",
    }

    db = load_db()
    db.setdefault(NOTE_STORE_KEY, []).append(note)
    db.setdefault("messages", []).append(
        {
            "id": note["id"],
            "ts": now,
            "member_id": member_id,
            "sender_role": "nutritionist",
            "actor_id": note["created_by"],
            "subject": subject,
            "message": note_text,
            "status": "queued",
            "email_required": True,
            "note_type": note_type,
            "note_id": note["id"],
            "from_date": from_iso,
            "to_date": to_iso,
            "related_dates": related_dates,
            "log_date": from_iso,
            "read": False,
            "archived": False,
        }
    )
    save_db(db)
    return note


def list_structured_nutritionist_notes(member_id: Optional[str] = None) -> List[Dict[str, Any]]:
    db = load_db()
    rows = list(db.get(NOTE_STORE_KEY, []) or [])
    if member_id:
        rows = [r for r in rows if str(r.get("member_id", "")) == str(member_id)]
    rows.sort(key=lambda r: str(r.get("created_at", "")), reverse=True)
    return rows


def notes_for_journal_date(member_id: str, journal_date: Any, include_archived: bool = True) -> List[Dict[str, Any]]:
    date_iso = _normalise_date(journal_date)
    if not date_iso:
        return []
    rows = []
    for note in list_structured_nutritionist_notes(member_id):
        related = [str(x) for x in note.get("related_dates", [])]
        if date_iso not in related:
            continue
        if not include_archived and note.get("member_archived"):
            continue
        rows.append(note)
    return rows


def note_rows_for_admin(member_id: Optional[str] = None) -> List[Dict[str, Any]]:
    rows = []
    for note in list_structured_nutritionist_notes(member_id):
        rows.append(
            {
                "id": note.get("id", ""),
                "member_id": note.get("member_id", ""),
                "member_name": note.get("member_name", ""),
                "note_type": note.get("note_type", ""),
                "subject": note.get("subject", ""),
                "from_date": note.get("from_date", ""),
                "to_date": note.get("to_date", ""),
                "sent_date": note.get("sent_date", ""),
                "related_dates": ", ".join([str(x) for x in note.get("related_dates", [])]),
                "read_at": note.get("read_at", ""),
                "archived_at": note.get("archived_at", ""),
                "member_archived": bool(note.get("member_archived", False)),
                "created_by": note.get("created_by", ""),
                "created_at": note.get("created_at", ""),
            }
        )
    return rows


def active_notes_for_member(member_id: str) -> List[Dict[str, Any]]:
    return [
        r
        for r in list_structured_nutritionist_notes(member_id)
        if not bool(r.get("member_archived", False))
    ]
