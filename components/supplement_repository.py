from __future__ import annotations

import datetime as dt
import html
import re
import uuid
from typing import Any

from components.db import load_db, save_db


_MIGRATION_KEY = "supplement_repository_v1_migration"
_REPOSITORY_KEY = "supplement_repository"
_AUDIT_KEY = "supplement_repository_audit"


def _now_iso() -> str:
    return dt.datetime.now().isoformat(timespec="seconds")


def _clean(value: Any) -> str:
    text = html.unescape(str(value or "")).strip()
    text = re.sub(r"<\s*br\s*/?\s*>", ", ", text, flags=re.I)
    text = re.sub(r"<\s*[^>]*>", " ", text)
    text = re.sub(r"\s+", " ", text).strip(" ,;:-")
    return text


def _status(value: Any) -> str:
    return "Inactive" if _clean(value).lower() in {"inactive", "stopped", "archived"} else "Active"


def _normalise(row: dict[str, Any] | None) -> dict[str, Any]:
    source = dict(row or {})
    item_id = _clean(source.get("id") or source.get("source_id")) or f"suprepo_{uuid.uuid4().hex[:8]}"
    return {
        "id": item_id,
        "source_id": item_id,
        "supplement_name": _clean(source.get("supplement_name") or source.get("name") or source.get("title")),
        "title": _clean(source.get("supplement_name") or source.get("name") or source.get("title")),
        "dosage": _clean(source.get("dosage") or source.get("default_dosage")),
        "frequency": _clean(source.get("frequency") or source.get("default_frequency")),
        "timing": _clean(source.get("timing") or source.get("default_timing")),
        "instructions": _clean(source.get("instructions")),
        "admin_notes": _clean(source.get("admin_notes") or source.get("notes")),
        "status": _status(source.get("status")),
        "created_at": _clean(source.get("created_at")),
        "created_by": _clean(source.get("created_by")),
        "updated_at": _clean(source.get("updated_at")),
        "updated_by": _clean(source.get("updated_by")),
        "source": _clean(source.get("source")) or "supplement_repository",
        "legacy_source_id": _clean(source.get("legacy_source_id")),
    }


def _ensure_store(db: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(db.get(_REPOSITORY_KEY), list):
        db[_REPOSITORY_KEY] = []
    if not isinstance(db.get(_AUDIT_KEY), list):
        db[_AUDIT_KEY] = []
    return db


def _write_audit(
    db: dict[str, Any],
    action: str,
    row: dict[str, Any],
    actor_id: str,
    changes: dict[str, Any] | None = None,
) -> None:
    db[_AUDIT_KEY].append(
        {
            "ts": _now_iso(),
            "action": action,
            "supplement_repository_id": row.get("id", ""),
            "supplement_name": row.get("supplement_name", ""),
            "actor_id": actor_id or "admin",
            "changes": changes or {},
        }
    )
    db[_AUDIT_KEY] = db[_AUDIT_KEY][-500:]


def _migrate_legacy_member_definitions(db: dict[str, Any]) -> bool:
    """Seed the master repository once from unique legacy member regimen definitions.

    Existing member_supplements rows are read-only inputs to this migration. They are
    never edited, removed or reclassified.
    """
    if db.get(_MIGRATION_KEY):
        return False

    repository = db[_REPOSITORY_KEY]
    imported = 0
    if not repository:
        legacy_rows = [
            dict(row or {})
            for row in (db.get("member_supplements", []) or [])
            if _clean((row or {}).get("supplement_name") or (row or {}).get("name"))
        ]
        legacy_rows.sort(
            key=lambda row: _clean(row.get("updated_at") or row.get("created_at")),
            reverse=True,
        )
        seen: set[str] = set()
        now = _now_iso()
        for legacy in legacy_rows:
            name = _clean(legacy.get("supplement_name") or legacy.get("name"))
            key = name.casefold()
            if not name or key in seen:
                continue
            seen.add(key)
            row = _normalise(
                {
                    "id": f"suprepo_{uuid.uuid4().hex[:8]}",
                    "supplement_name": name,
                    "dosage": legacy.get("dosage", ""),
                    "frequency": legacy.get("frequency", ""),
                    "timing": legacy.get("timing", ""),
                    "instructions": legacy.get("instructions", ""),
                    "admin_notes": legacy.get("admin_notes", ""),
                    "status": "Active",
                    "created_at": now,
                    "created_by": "system",
                    "updated_at": now,
                    "updated_by": "system",
                    "source": "legacy_member_regimen_backfill",
                    "legacy_source_id": legacy.get("id", ""),
                }
            )
            repository.append(row)
            _write_audit(db, "legacy_definition_imported", row, "system")
            imported += 1

    db[_MIGRATION_KEY] = {
        "completed_at": _now_iso(),
        "imported_count": imported,
        "member_regimens_unchanged": True,
    }
    return True


def list_supplement_repository(active_only: bool = True) -> list[dict[str, Any]]:
    db = _ensure_store(load_db())
    changed = _migrate_legacy_member_definitions(db)

    rows: list[dict[str, Any]] = []
    for index, raw in enumerate(list(db[_REPOSITORY_KEY])):
        row = _normalise(raw)
        if row != raw:
            db[_REPOSITORY_KEY][index] = row
            changed = True
        if active_only and row.get("status") != "Active":
            continue
        rows.append(dict(row))

    if changed:
        save_db(db)

    rows.sort(
        key=lambda row: (
            0 if row.get("status") == "Active" else 1,
            _clean(row.get("supplement_name")).casefold(),
        )
    )
    return rows


def supplement_repository_counts() -> dict[str, int]:
    rows = list_supplement_repository(active_only=False)
    active = sum(1 for row in rows if row.get("status") == "Active")
    return {"active": active, "inactive": len(rows) - active, "total": len(rows)}


def _validate_unique_name(
    rows: list[dict[str, Any]],
    name: str,
    *,
    ignore_id: str = "",
) -> None:
    key = _clean(name).casefold()
    if not key:
        raise ValueError("Supplement name is required.")
    for row in rows:
        if ignore_id and str(row.get("id")) == str(ignore_id):
            continue
        if _clean(row.get("supplement_name")).casefold() == key:
            raise ValueError("This supplement already exists in the repository. Edit the existing item instead.")


def add_supplement_repository_item(data: dict[str, Any], actor_id: str = "admin") -> dict[str, Any]:
    db = _ensure_store(load_db())
    _migrate_legacy_member_definitions(db)
    name = _clean((data or {}).get("supplement_name") or (data or {}).get("name"))
    _validate_unique_name(db[_REPOSITORY_KEY], name)

    now = _now_iso()
    row = _normalise(
        {
            **dict(data or {}),
            "id": f"suprepo_{uuid.uuid4().hex[:8]}",
            "supplement_name": name,
            "status": "Active",
            "created_at": now,
            "created_by": actor_id or "admin",
            "updated_at": now,
            "updated_by": actor_id or "admin",
            "source": "supplement_repository",
        }
    )
    db[_REPOSITORY_KEY].append(row)
    _write_audit(db, "created", row, actor_id)
    save_db(db)
    return dict(row)


def update_supplement_repository_item(
    item_id: str,
    updates: dict[str, Any],
    actor_id: str = "admin",
) -> dict[str, Any]:
    db = _ensure_store(load_db())
    _migrate_legacy_member_definitions(db)
    item_id = _clean(item_id)
    allowed = {"supplement_name", "dosage", "frequency", "timing", "instructions", "admin_notes"}

    for index, raw in enumerate(db[_REPOSITORY_KEY]):
        row = _normalise(raw)
        if str(row.get("id")) != item_id:
            continue

        before = dict(row)
        next_name = _clean((updates or {}).get("supplement_name", row.get("supplement_name")))
        _validate_unique_name(db[_REPOSITORY_KEY], next_name, ignore_id=item_id)

        for key in allowed:
            if key in (updates or {}):
                row[key] = _clean((updates or {}).get(key))
        row["supplement_name"] = next_name
        row["title"] = next_name
        row["updated_at"] = _now_iso()
        row["updated_by"] = actor_id or "admin"
        db[_REPOSITORY_KEY][index] = _normalise(row)

        changes = {
            key: {"from": before.get(key, ""), "to": row.get(key, "")}
            for key in allowed
            if before.get(key, "") != row.get(key, "")
        }
        _write_audit(db, "updated", row, actor_id, changes=changes)
        save_db(db)
        return dict(db[_REPOSITORY_KEY][index])

    raise ValueError("Supplement repository item was not found.")


def set_supplement_repository_status(
    item_id: str,
    active: bool,
    actor_id: str = "admin",
) -> dict[str, Any]:
    db = _ensure_store(load_db())
    _migrate_legacy_member_definitions(db)
    item_id = _clean(item_id)
    next_status = "Active" if active else "Inactive"

    for index, raw in enumerate(db[_REPOSITORY_KEY]):
        row = _normalise(raw)
        if str(row.get("id")) != item_id:
            continue
        previous = row.get("status", "Active")
        row["status"] = next_status
        row["updated_at"] = _now_iso()
        row["updated_by"] = actor_id or "admin"
        db[_REPOSITORY_KEY][index] = _normalise(row)
        _write_audit(
            db,
            "reactivated" if active else "deactivated",
            row,
            actor_id,
            changes={"status": {"from": previous, "to": next_status}},
        )
        save_db(db)
        return dict(db[_REPOSITORY_KEY][index])

    raise ValueError("Supplement repository item was not found.")
