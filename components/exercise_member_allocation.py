from __future__ import annotations

import copy
import datetime as dt
import uuid
from typing import Any

from components.exercise_repository import list_exercise_repository
from components.member_planning_separation_contract import (
    validate_canonical_source_reference,
)
from components.storage_backend import load_state, save_state


STORE_KEY = "member_exercise_allocations"
AUDIT_KEY = "exercise_member_allocation_audit"
SOURCE_TYPE = "exercise_repository"
ACTIVE_STATUS = "active"
INACTIVE_STATUSES = {"inactive", "stopped", "archived"}


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _now_iso() -> str:
    return dt.datetime.now().isoformat(timespec="seconds")


def _normalise_status(value: Any) -> str:
    return "stopped" if _clean(value).lower() in INACTIVE_STATUSES else ACTIVE_STATUS


def _parse_date(value: Any) -> dt.date | None:
    if isinstance(value, dt.datetime):
        return value.date()
    if isinstance(value, dt.date):
        return value
    text = _clean(value)[:10]
    if not text:
        return None
    try:
        return dt.date.fromisoformat(text)
    except ValueError:
        return None


def exercise_allocation_effective_state(
    row: dict[str, Any],
    on_date: dt.date | str,
) -> str:
    """Return the read-only lifecycle state for one allocation on one date."""

    target = _parse_date(on_date)
    if target is None:
        raise ValueError("A valid Exercise allocation date is required.")
    if _normalise_status(row.get("status")) != ACTIVE_STATUS:
        return "stopped"
    start = _parse_date(row.get("start_date"))
    end = _parse_date(row.get("end_date"))
    if start and start > target:
        return "upcoming"
    if end and end < target:
        return "expired"
    return "current"


def _repository_lookup(*, active_only: bool = False) -> dict[str, dict[str, Any]]:
    rows = list_exercise_repository(active_only=active_only)
    return {
        _clean(row.get("source_id") or row.get("id")): dict(row)
        for row in rows
        if _clean(row.get("source_id") or row.get("id"))
    }


def list_active_exercise_sources() -> list[dict[str, Any]]:
    """Return only active canonical Exercise repository sources for new allocations."""
    rows = [dict(row) for row in list_exercise_repository(active_only=True)]
    rows.sort(key=lambda row: _clean(row.get("title")).casefold())
    return rows


def _snapshot(source: dict[str, Any]) -> dict[str, Any]:
    """Freeze the member-facing source fields used by an allocation."""
    return {
        "source_type": SOURCE_TYPE,
        "source_id": _clean(source.get("source_id") or source.get("id")),
        "title": _clean(source.get("title")),
        "description": _clean(source.get("description")),
        "category": _clean(source.get("category")),
        "difficulty": _clean(source.get("difficulty")),
        "duration_or_reps": _clean(source.get("duration_or_reps")),
        "equipment": _clean(source.get("equipment")),
        "instructions": _clean(source.get("instructions")),
        "benefits": _clean(source.get("benefits")),
        "image_url": _clean(source.get("image_url")),
        "content_version": source.get("content_version") or "",
    }


def _normalise_existing_row(
    row: dict[str, Any] | None,
    *,
    member_id: str,
    repository: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    source = copy.deepcopy(dict(row or {}))
    source_id = _clean(
        source.get("source_id")
        or source.get("exercise_id")
        or (source.get("source_snapshot") or {}).get("source_id")
    )
    source_type = _clean(source.get("source_type")) or SOURCE_TYPE
    if source_id:
        validate_canonical_source_reference("exercise", source_type, source_id)

    repository = repository or {}
    repo_row = repository.get(source_id, {})
    stored_snapshot = dict(source.get("source_snapshot") or {})
    snapshot = stored_snapshot or (_snapshot(repo_row) if repo_row else {})
    title = (
        _clean(source.get("exercise_name"))
        or _clean(source.get("title"))
        or _clean(snapshot.get("title"))
        or _clean(repo_row.get("title"))
        or "Exercise"
    )
    allocation_id = _clean(source.get("id")) or f"exercise_alloc_{uuid.uuid4().hex}"

    return {
        **source,
        "id": allocation_id,
        "member_id": _clean(source.get("member_id")) or _clean(member_id),
        "source_type": source_type,
        "source_id": source_id,
        "exercise_id": source_id,
        "exercise_name": title,
        "title": title,
        "duration_or_reps": (
            _clean(source.get("duration_or_reps"))
            or _clean(stored_snapshot.get("duration_or_reps"))
            or _clean(repo_row.get("duration_or_reps"))
        ),
        "start_date": _clean(source.get("start_date")),
        "end_date": _clean(source.get("end_date")),
        "instructions": _clean(source.get("instructions")),
        "notes": _clean(source.get("notes")),
        "status": _normalise_status(source.get("status")),
        "source_snapshot": snapshot,
    }


def list_member_exercise_allocations(
    member_id: str,
    *,
    include_stopped: bool = True,
) -> list[dict[str, Any]]:
    clean_member_id = _clean(member_id)
    if not clean_member_id:
        return []
    state = load_state()
    repository = _repository_lookup(active_only=False)
    raw_rows = list((state.get(STORE_KEY, {}) or {}).get(clean_member_id, []) or [])
    rows = [
        _normalise_existing_row(row, member_id=clean_member_id, repository=repository)
        for row in raw_rows
        if isinstance(row, dict)
    ]
    if not include_stopped:
        rows = [row for row in rows if row.get("status") == ACTIVE_STATUS]
    rows.sort(
        key=lambda row: (
            0 if row.get("status") == ACTIVE_STATUS else 1,
            _clean(row.get("start_date")),
            _clean(row.get("exercise_name")).casefold(),
        )
    )
    return rows


def list_member_exercise_allocations_for_date(
    member_id: str,
    on_date: dt.date | str,
) -> list[dict[str, Any]]:
    """Return only Exercise allocations effective on a selected member date.

    This is a pure read. It does not auto-stop expired allocations or mutate
    repository/allocation state.
    """

    target = _parse_date(on_date)
    if target is None:
        raise ValueError("A valid Exercise allocation date is required.")
    rows = list_member_exercise_allocations(member_id, include_stopped=True)
    current: list[dict[str, Any]] = []
    for raw in rows:
        row = copy.deepcopy(dict(raw or {}))
        state = exercise_allocation_effective_state(row, target)
        if state != "current":
            continue
        row["effective_state"] = state
        current.append(row)
    current.sort(
        key=lambda row: (
            _clean(row.get("start_date")),
            _clean(row.get("exercise_name") or row.get("title")).casefold(),
            _clean(row.get("id")),
        )
    )
    return current


def _validate_dates(start_date: Any, end_date: Any) -> tuple[str, str]:
    start = _clean(start_date)
    end = _clean(end_date)
    if start and end and end < start:
        raise ValueError("End date cannot be before start date.")
    return start, end


def save_exercise_member_allocation(
    *,
    member_id: str,
    source_id: str,
    start_date: Any = "",
    end_date: Any = "",
    duration_or_reps: Any = None,
    instructions: Any = "",
    notes: Any = "",
    status: Any = ACTIVE_STATUS,
    actor_id: str = "admin",
    allocation_id: str = "",
) -> dict[str, Any]:
    """Create or update one Exercise allocation without replacing sibling rows."""
    clean_member_id = _clean(member_id)
    if not clean_member_id:
        raise ValueError("Member is required.")

    source_ref = validate_canonical_source_reference(
        "exercise", SOURCE_TYPE, _clean(source_id)
    )
    start, end = _validate_dates(start_date, end_date)
    state = load_state()
    all_repository = _repository_lookup(active_only=False)
    active_repository = _repository_lookup(active_only=True)
    existing_rows = list((state.get(STORE_KEY, {}) or {}).get(clean_member_id, []) or [])

    clean_allocation_id = _clean(allocation_id)
    existing_index = next(
        (
            index
            for index, row in enumerate(existing_rows)
            if _clean((row or {}).get("id")) == clean_allocation_id
        ),
        None,
    )
    existing = (
        _normalise_existing_row(
            existing_rows[existing_index],
            member_id=clean_member_id,
            repository=all_repository,
        )
        if existing_index is not None
        else {}
    )
    if clean_allocation_id and existing_index is None:
        raise ValueError("Exercise allocation was not found.")

    if existing:
        existing_source_id = _clean(existing.get("source_id"))
        if existing_source_id and existing_source_id != source_ref["source_id"]:
            raise ValueError("Existing allocation source identity cannot be changed.")
        source = all_repository.get(existing_source_id or source_ref["source_id"], {})
    else:
        source = active_repository.get(source_ref["source_id"], {})
        if not source:
            raise ValueError(
                "Only active canonical Exercise repository items can be allocated."
            )

    if not source:
        raise ValueError("Exercise repository source was not found.")

    display_title = (
        _clean((existing.get("source_snapshot") or {}).get("title"))
        or _clean(existing.get("exercise_name"))
        or _clean(source.get("title"))
        or "Exercise"
    )
    snapshot = existing.get("source_snapshot") or _snapshot(source)
    display_duration = (
        _clean(duration_or_reps)
        if duration_or_reps is not None
        else (
            _clean(existing.get("duration_or_reps"))
            or _clean(snapshot.get("duration_or_reps"))
            or _clean(source.get("duration_or_reps"))
        )
    )
    now = _now_iso()
    saved = {
        **existing,
        "id": clean_allocation_id or f"exercise_alloc_{uuid.uuid4().hex}",
        "member_id": clean_member_id,
        "source_type": SOURCE_TYPE,
        "source_id": source_ref["source_id"],
        "exercise_id": source_ref["source_id"],
        "exercise_name": display_title,
        "title": display_title,
        "duration_or_reps": display_duration,
        "start_date": start,
        "end_date": end,
        "instructions": _clean(instructions),
        "notes": _clean(notes),
        "status": _normalise_status(status),
        "source_snapshot": snapshot,
        "source": "exercise_member_allocation",
        "updated_at": now,
        "updated_by": _clean(actor_id) or "admin",
    }
    if not existing:
        saved["created_at"] = now
        saved["created_by"] = _clean(actor_id) or "admin"

    member_rows = list(existing_rows)
    if existing_index is None:
        member_rows.append(saved)
        action = "create"
    else:
        member_rows[existing_index] = saved
        action = "update"

    state.setdefault(STORE_KEY, {})[clean_member_id] = member_rows
    state.setdefault(AUDIT_KEY, []).append(
        {
            "ts": now,
            "action": action,
            "member_id": clean_member_id,
            "allocation_id": saved["id"],
            "source_type": SOURCE_TYPE,
            "source_id": saved["source_id"],
            "status": saved["status"],
            "actor_id": _clean(actor_id) or "admin",
        }
    )
    save_state(state)
    return copy.deepcopy(saved)


def stop_exercise_member_allocation(
    *,
    member_id: str,
    allocation_id: str,
    actor_id: str = "admin",
    stop_date: Any = "",
    stop_reason: Any = "",
) -> dict[str, Any]:
    rows = list_member_exercise_allocations(member_id, include_stopped=True)
    allocation = next(
        (row for row in rows if _clean(row.get("id")) == _clean(allocation_id)),
        None,
    )
    if not allocation:
        raise ValueError("Exercise allocation was not found.")
    end_date = _clean(stop_date) or _clean(allocation.get("end_date"))
    return save_exercise_member_allocation(
        member_id=member_id,
        source_id=_clean(allocation.get("source_id")),
        start_date=allocation.get("start_date", ""),
        end_date=end_date,
        duration_or_reps=allocation.get("duration_or_reps"),
        instructions=allocation.get("instructions", ""),
        notes=_clean(stop_reason) or allocation.get("notes", ""),
        status="stopped",
        actor_id=actor_id,
        allocation_id=allocation_id,
    )