from __future__ import annotations

import copy
import datetime as dt
import uuid
from typing import Any

from components.member_planning_separation_contract import (
    validate_canonical_source_reference,
)
from components.storage_backend import load_state, save_state
from components.supplement_repository import list_supplement_repository


STORE_KEY = "member_supplements"
AUDIT_KEY = "supplement_audit_logs"
SOURCE_TYPE = "supplement_repository"
ACTIVE_STATUS = "Active"
STOPPED_STATUS = "Stopped"


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _now_iso() -> str:
    return dt.datetime.now().isoformat(timespec="seconds")


def _clean_date(value: Any) -> str:
    if value in (None, ""):
        return ""
    try:
        return value.isoformat()
    except Exception:
        return _clean(value)[:10]


def _parse_date(value: Any) -> dt.date | None:
    text = _clean(value)[:10]
    if not text:
        return None
    try:
        return dt.date.fromisoformat(text)
    except Exception:
        return None


def _normalise_status(value: Any) -> str:
    return (
        STOPPED_STATUS
        if _clean(value).lower() in {"stopped", "inactive", "archived"}
        else ACTIVE_STATUS
    )


def _repository_lookup(*, active_only: bool = False) -> dict[str, dict[str, Any]]:
    rows = list_supplement_repository(active_only=active_only)
    return {
        _clean(row.get("source_id") or row.get("id")): dict(row)
        for row in rows
        if _clean(row.get("source_id") or row.get("id"))
    }


def list_active_supplement_sources() -> list[dict[str, Any]]:
    rows = [dict(row) for row in list_supplement_repository(active_only=True)]
    rows.sort(key=lambda row: _clean(row.get("supplement_name")).casefold())
    return rows


def _source_snapshot(source: dict[str, Any]) -> dict[str, Any]:
    """Freeze member-facing repository fields; repository admin notes are excluded."""
    return {
        "source_type": SOURCE_TYPE,
        "source_id": _clean(source.get("source_id") or source.get("id")),
        "supplement_name": _clean(
            source.get("supplement_name") or source.get("title")
        ),
        "title": _clean(source.get("supplement_name") or source.get("title")),
        "dosage": _clean(source.get("dosage")),
        "frequency": _clean(source.get("frequency")),
        "timing": _clean(source.get("timing")),
        "instructions": _clean(source.get("instructions")),
        "content_version": source.get("content_version") or "",
    }


def _mapping_for_row(
    row: dict[str, Any],
    repository: dict[str, dict[str, Any]],
) -> dict[str, str]:
    stored_snapshot = dict(row.get("source_snapshot") or {})
    direct_source_id = _clean(
        row.get("source_id")
        or row.get("supplement_source_id")
        or stored_snapshot.get("source_id")
    )
    if direct_source_id:
        source_type = _clean(row.get("source_type")) or SOURCE_TYPE
        validate_canonical_source_reference(
            "supplement", source_type, direct_source_id
        )
        return {
            "source_id": direct_source_id,
            "source_type": source_type,
            "status": (
                "canonical"
                if direct_source_id in repository
                else "missing_canonical_source"
            ),
            "persisted": "true",
        }

    allocation_id = _clean(row.get("id"))
    legacy_matches = [
        source_id
        for source_id, source in repository.items()
        if allocation_id
        and _clean(source.get("legacy_source_id")) == allocation_id
    ]
    if len(legacy_matches) == 1:
        return {
            "source_id": legacy_matches[0],
            "source_type": SOURCE_TYPE,
            "status": "mapped_by_legacy_id",
            "persisted": "false",
        }
    if len(legacy_matches) > 1:
        return {
            "source_id": "",
            "source_type": SOURCE_TYPE,
            "status": "ambiguous_legacy_id",
            "persisted": "false",
        }

    name_key = _clean(
        row.get("supplement_name") or row.get("name")
    ).casefold()
    name_matches = [
        source_id
        for source_id, source in repository.items()
        if name_key
        and _clean(
            source.get("supplement_name") or source.get("title")
        ).casefold()
        == name_key
    ]
    if len(name_matches) == 1:
        return {
            "source_id": name_matches[0],
            "source_type": SOURCE_TYPE,
            "status": "mapped_by_exact_name",
            "persisted": "false",
        }
    if len(name_matches) > 1:
        return {
            "source_id": "",
            "source_type": SOURCE_TYPE,
            "status": "ambiguous_exact_name",
            "persisted": "false",
        }
    return {
        "source_id": "",
        "source_type": SOURCE_TYPE,
        "status": "unmapped_legacy",
        "persisted": "false",
    }


def _normalise_existing_row(
    row: dict[str, Any] | None,
    *,
    repository: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    source = copy.deepcopy(dict(row or {}))
    mapping = _mapping_for_row(source, repository)
    source_id = mapping["source_id"]
    repository_source = repository.get(source_id, {})
    stored_snapshot = dict(source.get("source_snapshot") or {})
    snapshot = stored_snapshot or (
        _source_snapshot(repository_source) if repository_source else {}
    )
    name = (
        _clean(source.get("supplement_name") or source.get("name"))
        or _clean(snapshot.get("supplement_name") or snapshot.get("title"))
        or _clean(
            repository_source.get("supplement_name")
            or repository_source.get("title")
        )
        or "Supplement"
    )
    return {
        **source,
        "id": _clean(source.get("id")) or str(uuid.uuid4())[:8],
        "member_id": _clean(source.get("member_id")),
        "member_name": _clean(source.get("member_name")),
        "member_email": _clean(source.get("member_email")),
        "supplement_name": name,
        "title": name,
        "dosage": _clean(source.get("dosage")),
        "frequency": _clean(source.get("frequency")),
        "timing": _clean(source.get("timing")),
        "instructions": _clean(source.get("instructions")),
        "start_date": _clean_date(source.get("start_date")),
        "end_date": _clean_date(source.get("end_date")),
        "stop_date": _clean_date(source.get("stop_date")),
        "stop_reason": _clean(source.get("stop_reason")),
        "status": _normalise_status(source.get("status")),
        "source_type": mapping["source_type"],
        "source_id": source_id,
        "supplement_source_id": source_id,
        "source_mapping_status": mapping["status"],
        "source_reference_persisted": mapping["persisted"] == "true",
        "source_snapshot": snapshot,
    }


def _validate_dates(start_date: Any, end_date: Any) -> tuple[str, str]:
    start = _clean_date(start_date)
    end = _clean_date(end_date)
    start_dt = _parse_date(start)
    end_dt = _parse_date(end)
    if start_dt and end_dt and end_dt < start_dt:
        raise ValueError("End Date cannot be earlier than Start Date.")
    return start, end


def _member_lookup(state: dict[str, Any], member_id: str) -> dict[str, Any]:
    clean_member_id = _clean(member_id)
    return next(
        (
            dict(user)
            for user in state.get("users", [])
            if _clean(user.get("id")) == clean_member_id
            and user.get("role") == "member"
            and user.get("is_active", True)
        ),
        {},
    )


def _append_audit(
    state: dict[str, Any],
    *,
    action: str,
    row: dict[str, Any],
    actor_id: str,
    changes: dict[str, Any] | None = None,
) -> None:
    state.setdefault(AUDIT_KEY, []).append(
        {
            "ts": _now_iso(),
            "action": action,
            "supplement_id": row.get("id", ""),
            "allocation_id": row.get("id", ""),
            "member_id": row.get("member_id", ""),
            "member_email": row.get("member_email", ""),
            "supplement_name": row.get("supplement_name", ""),
            "source_type": row.get("source_type", ""),
            "source_id": row.get("source_id", ""),
            "source_mapping_status": row.get("source_mapping_status", ""),
            "actor_id": _clean(actor_id) or "admin",
            "changes": changes or {},
        }
    )
    state[AUDIT_KEY] = state[AUDIT_KEY][-500:]


def _append_notification(
    state: dict[str, Any],
    *,
    member_id: str,
    actor_id: str,
    timestamp: str,
) -> None:
    state.setdefault("notifications", []).append(
        {
            "ts": timestamp,
            "kind": "supplement_regimen_updated",
            "user_id": member_id,
            "message": "Your nutritionist has updated your supplement regimen.",
            "status": "queued",
            "email_required": False,
            "created_by": _clean(actor_id) or "admin",
        }
    )


def _auto_stop_expired(
    state: dict[str, Any],
    repository: dict[str, dict[str, Any]],
) -> bool:
    today = dt.date.today()
    changed = False
    rows = list(state.get(STORE_KEY, []) or [])
    for index, raw in enumerate(rows):
        if not isinstance(raw, dict):
            continue
        row = _normalise_existing_row(raw, repository=repository)
        end_dt = _parse_date(row.get("end_date"))
        if row.get("status") != ACTIVE_STATUS or not end_dt or end_dt > today:
            continue
        now = _now_iso()
        stopped = {
            **raw,
            "status": STOPPED_STATUS,
            "stop_date": end_dt.isoformat(),
            "stop_reason": "Predefined Timelines",
            "stopped_at": now,
            "stopped_by": "system",
            "updated_at": now,
            "updated_by": "system",
        }
        if row.get("source_id"):
            stopped.update(
                {
                    "source_type": SOURCE_TYPE,
                    "source_id": row["source_id"],
                    "supplement_source_id": row["source_id"],
                    "source_snapshot": row.get("source_snapshot") or {},
                    "source_mapping_status": row.get("source_mapping_status"),
                }
            )
        state.setdefault(STORE_KEY, [])[index] = stopped
        stopped_row = _normalise_existing_row(stopped, repository=repository)
        _append_audit(
            state,
            action="auto_stopped",
            row=stopped_row,
            actor_id="system",
            changes={
                "status": {"from": ACTIVE_STATUS, "to": STOPPED_STATUS},
                "stop_date": end_dt.isoformat(),
                "stop_reason": "Predefined Timelines",
            },
        )
        _append_notification(
            state,
            member_id=stopped_row.get("member_id", ""),
            actor_id="system",
            timestamp=now,
        )
        changed = True
    return changed


def list_member_supplement_allocations(
    member_id: str,
    *,
    include_stopped: bool = True,
) -> list[dict[str, Any]]:
    clean_member_id = _clean(member_id)
    if not clean_member_id:
        return []
    state = load_state()
    repository = _repository_lookup(active_only=False)
    if _auto_stop_expired(state, repository):
        save_state(state)
    rows = [
        _normalise_existing_row(row, repository=repository)
        for row in list(state.get(STORE_KEY, []) or [])
        if isinstance(row, dict)
        and _clean(row.get("member_id")) == clean_member_id
    ]
    if not include_stopped:
        rows = [row for row in rows if row.get("status") == ACTIVE_STATUS]
    rows.sort(
        key=lambda row: (
            0 if row.get("status") == ACTIVE_STATUS else 1,
            _clean(row.get("updated_at") or row.get("created_at")),
            _clean(row.get("supplement_name")).casefold(),
        ),
        reverse=False,
    )
    return rows


def save_supplement_member_allocation(
    *,
    member_id: str,
    source_id: str,
    dosage: Any = "",
    frequency: Any = "",
    timing: Any = "",
    instructions: Any = "",
    start_date: Any = "",
    end_date: Any = "",
    actor_id: str = "admin",
    allocation_id: str = "",
) -> dict[str, Any]:
    clean_member_id = _clean(member_id)
    if not clean_member_id:
        raise ValueError("Member is required.")
    source_ref = validate_canonical_source_reference(
        "supplement", SOURCE_TYPE, _clean(source_id)
    )
    start, end = _validate_dates(start_date, end_date)
    state = load_state()
    member = _member_lookup(state, clean_member_id)
    if not member:
        raise ValueError("Selected member was not found.")

    all_repository = _repository_lookup(active_only=False)
    active_repository = _repository_lookup(active_only=True)
    rows = list(state.get(STORE_KEY, []) or [])
    clean_allocation_id = _clean(allocation_id)
    existing_index = next(
        (
            index
            for index, row in enumerate(rows)
            if isinstance(row, dict)
            and _clean(row.get("id")) == clean_allocation_id
        ),
        None,
    )
    if clean_allocation_id and existing_index is None:
        raise ValueError("Supplement allocation was not found.")

    existing_raw = (
        copy.deepcopy(rows[existing_index])
        if existing_index is not None
        else {}
    )
    existing = (
        _normalise_existing_row(existing_raw, repository=all_repository)
        if existing_raw
        else {}
    )
    if existing and existing.get("member_id") != clean_member_id:
        raise ValueError("Supplement allocation belongs to another member.")
    if existing and existing.get("status") != ACTIVE_STATUS:
        raise ValueError(
            "Stopped supplements cannot be edited. Add a new active supplement instead."
        )

    persisted_source_id = _clean(
        existing_raw.get("source_id")
        or existing_raw.get("supplement_source_id")
        or (existing_raw.get("source_snapshot") or {}).get("source_id")
    )
    if persisted_source_id and persisted_source_id != source_ref["source_id"]:
        raise ValueError("Existing allocation source identity cannot be changed.")

    if persisted_source_id:
        source = all_repository.get(persisted_source_id, {})
    else:
        source = active_repository.get(source_ref["source_id"], {})
    if not source:
        raise ValueError(
            "Only active canonical Supplement repository items can be newly allocated or mapped."
        )

    if not existing:
        mapping_status = "canonical_new"
    elif persisted_source_id:
        mapping_status = "canonical_existing"
    elif (
        existing.get("source_id") == source_ref["source_id"]
        and existing.get("source_mapping_status")
        in {"mapped_by_legacy_id", "mapped_by_exact_name"}
    ):
        mapping_status = f"backfilled_{existing.get('source_mapping_status')}"
    else:
        mapping_status = "explicit_admin_mapping"

    now = _now_iso()
    source_name = _clean(
        source.get("supplement_name") or source.get("title")
    ) or "Supplement"
    visible_name = _clean(existing.get("supplement_name")) or source_name
    snapshot = existing.get("source_snapshot") or _source_snapshot(source)
    saved = {
        **existing_raw,
        "id": clean_allocation_id or str(uuid.uuid4())[:8],
        "member_id": clean_member_id,
        "member_name": _clean(member.get("name")),
        "member_email": _clean(member.get("email")),
        "supplement_name": visible_name,
        "dosage": _clean(dosage),
        "frequency": _clean(frequency),
        "timing": _clean(timing),
        "instructions": _clean(instructions),
        "start_date": start,
        "end_date": end,
        "stop_date": "",
        "stop_reason": "",
        "status": ACTIVE_STATUS,
        "source_type": SOURCE_TYPE,
        "source_id": source_ref["source_id"],
        "supplement_source_id": source_ref["source_id"],
        "source_snapshot": snapshot,
        "source_mapping_status": mapping_status,
        "updated_at": now,
        "updated_by": _clean(actor_id) or "admin",
    }
    if not existing:
        saved["created_at"] = now
        saved["created_by"] = _clean(actor_id) or "admin"

    if existing_index is None:
        rows.append(saved)
        action = "created"
    else:
        rows[existing_index] = saved
        action = "updated"
    state[STORE_KEY] = rows
    normalised_saved = _normalise_existing_row(saved, repository=all_repository)
    _append_audit(
        state,
        action=action,
        row=normalised_saved,
        actor_id=actor_id,
        changes={
            "source_mapping_status": mapping_status,
            "source_id": source_ref["source_id"],
        },
    )
    _append_notification(
        state,
        member_id=clean_member_id,
        actor_id=actor_id,
        timestamp=now,
    )
    save_state(state)
    return copy.deepcopy(normalised_saved)


def stop_supplement_member_allocation(
    *,
    member_id: str,
    allocation_id: str,
    stop_date: Any = "",
    stop_reason: Any = "",
    actor_id: str = "admin",
) -> dict[str, Any]:
    clean_member_id = _clean(member_id)
    clean_allocation_id = _clean(allocation_id)
    state = load_state()
    repository = _repository_lookup(active_only=False)
    rows = list(state.get(STORE_KEY, []) or [])
    existing_index = next(
        (
            index
            for index, row in enumerate(rows)
            if isinstance(row, dict)
            and _clean(row.get("id")) == clean_allocation_id
            and _clean(row.get("member_id")) == clean_member_id
        ),
        None,
    )
    if existing_index is None:
        raise ValueError("Supplement allocation was not found.")
    existing_raw = copy.deepcopy(rows[existing_index])
    existing = _normalise_existing_row(existing_raw, repository=repository)
    if existing.get("status") == STOPPED_STATUS:
        return existing

    now = _now_iso()
    stopped = {
        **existing_raw,
        "status": STOPPED_STATUS,
        "stop_date": _clean_date(stop_date) or dt.date.today().isoformat(),
        "stop_reason": _clean(stop_reason),
        "stopped_at": now,
        "stopped_by": _clean(actor_id) or "admin",
        "updated_at": now,
        "updated_by": _clean(actor_id) or "admin",
    }
    if existing.get("source_id"):
        stopped.update(
            {
                "source_type": SOURCE_TYPE,
                "source_id": existing["source_id"],
                "supplement_source_id": existing["source_id"],
                "source_snapshot": existing.get("source_snapshot") or {},
                "source_mapping_status": (
                    existing.get("source_mapping_status")
                    if existing.get("source_reference_persisted")
                    else f"backfilled_{existing.get('source_mapping_status')}"
                ),
            }
        )
    rows[existing_index] = stopped
    state[STORE_KEY] = rows
    normalised_stopped = _normalise_existing_row(stopped, repository=repository)
    _append_audit(
        state,
        action="stopped",
        row=normalised_stopped,
        actor_id=actor_id,
        changes={
            "status": {"from": ACTIVE_STATUS, "to": STOPPED_STATUS},
            "stop_date": stopped["stop_date"],
        },
    )
    _append_notification(
        state,
        member_id=clean_member_id,
        actor_id=actor_id,
        timestamp=now,
    )
    save_state(state)
    return copy.deepcopy(normalised_stopped)
