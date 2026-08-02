from __future__ import annotations

import csv
import datetime as dt
import html
import pathlib
import re
from typing import Any

from components.storage_backend import (
    get_storage_status,
    load_state,
    save_state,
    supabase_configured,
)


BASE_DIR = pathlib.Path(__file__).resolve().parents[1]
LEGACY_CSV_PATH = BASE_DIR / "data" / "exercises.csv"

_MIGRATION_KEY = "exercise_repository_v1_migration"
_REPOSITORY_KEY = "exercises"
_AUDIT_KEY = "exercise_repository_audit"

EXERCISE_COLUMNS = [
    "title",
    "description",
    "category",
    "difficulty",
    "goal_tags",
    "condition_tags",
    "duration_or_reps",
    "hidden_calories_v96",
    "equipment",
    "image_url",
    "image_bucket",
    "image_path",
    "image_access_type",
    "instructions",
    "benefits",
    "status",
]


def _now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def _clean(value: Any) -> str:
    text = html.unescape(str(value or "")).strip()
    if text.lower() in {"nan", "none", "null"}:
        return ""
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _status(value: Any) -> str:
    return "inactive" if _clean(value).lower() in {"inactive", "stopped", "archived"} else "active"


def _normalise(row: dict[str, Any] | None, *, fallback_id: str = "") -> dict[str, Any]:
    source = dict(row or {})
    item_id = _clean(source.get("id") or source.get("source_id") or fallback_id)
    if not item_id:
        item_id = "0"
    return {
        "id": item_id,
        "source_id": item_id,
        "resource_type": "exercises",
        "title": _clean(source.get("title")),
        "description": _clean(source.get("description")),
        "category": _clean(source.get("category")),
        "difficulty": _clean(source.get("difficulty")),
        "goal_tags": _clean(source.get("goal_tags")),
        "condition_tags": _clean(source.get("condition_tags")),
        "duration_or_reps": _clean(source.get("duration_or_reps")),
        "hidden_calories_v96": _clean(
            source.get("hidden_calories_v96") or source.get("calories")
        ),
        "equipment": _clean(source.get("equipment")),
        "image_url": _clean(source.get("image_url")),
        "image_bucket": _clean(source.get("image_bucket")),
        "image_path": _clean(source.get("image_path")),
        "image_access_type": _clean(source.get("image_access_type")) or "public",
        "instructions": _clean(source.get("instructions")),
        "benefits": _clean(source.get("benefits")),
        "status": _status(source.get("status")),
        "created_at": _clean(source.get("created_at")),
        "created_by": _clean(source.get("created_by")),
        "updated_at": _clean(source.get("updated_at")),
        "updated_by": _clean(source.get("updated_by")),
        "source": _clean(source.get("source")) or "exercise_repository",
    }


def _ensure_store(db: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(db.get(_REPOSITORY_KEY), list):
        db[_REPOSITORY_KEY] = []
    if not isinstance(db.get(_AUDIT_KEY), list):
        db[_AUDIT_KEY] = []
    return db


def _read_legacy_rows() -> list[dict[str, Any]]:
    if not LEGACY_CSV_PATH.exists():
        return []
    try:
        with LEGACY_CSV_PATH.open("r", encoding="utf-8-sig", newline="") as handle:
            return [dict(row) for row in csv.DictReader(handle)]
    except Exception:
        return []


def _write_audit(
    db: dict[str, Any],
    action: str,
    row: dict[str, Any] | None,
    actor_id: str,
    changes: dict[str, Any] | None = None,
) -> None:
    row = dict(row or {})
    db[_AUDIT_KEY].append(
        {
            "ts": _now_iso(),
            "action": action,
            "exercise_repository_id": _clean(row.get("id")),
            "exercise_title": _clean(row.get("title")),
            "actor_id": actor_id or "admin",
            "changes": changes or {},
        }
    )
    db[_AUDIT_KEY] = db[_AUDIT_KEY][-500:]


def _migrate_legacy_repository(db: dict[str, Any]) -> bool:
    changed = False
    normalised_rows: list[dict[str, Any]] = []
    for index, raw in enumerate(list(db.get(_REPOSITORY_KEY) or [])):
        row = _normalise(raw, fallback_id=str(index))
        normalised_rows.append(row)
        if row != raw:
            changed = True
    db[_REPOSITORY_KEY] = normalised_rows

    if db.get(_MIGRATION_KEY):
        return changed

    imported = 0
    source = "existing_supabase_state"
    if not db[_REPOSITORY_KEY]:
        source = "legacy_csv"
        now = _now_iso()
        for index, raw in enumerate(_read_legacy_rows()):
            row = _normalise(
                {
                    **raw,
                    "id": str(index),
                    "source_id": str(index),
                    "created_at": now,
                    "created_by": "system",
                    "updated_at": now,
                    "updated_by": "system",
                    "source": "legacy_csv_migration",
                },
                fallback_id=str(index),
            )
            if not row.get("title"):
                continue
            db[_REPOSITORY_KEY].append(row)
            imported += 1

    db[_MIGRATION_KEY] = {
        "completed_at": _now_iso(),
        "source": source,
        "imported_count": imported,
        "existing_count": len(db[_REPOSITORY_KEY]),
        "legacy_ids_preserved": True,
    }
    _write_audit(db, "repository_migrated", None, "system", changes=db[_MIGRATION_KEY])
    return True


def _next_numeric_id(rows: list[dict[str, Any]]) -> str:
    numeric_ids = []
    for row in rows:
        try:
            numeric_ids.append(int(str(row.get("id", "")).strip()))
        except Exception:
            continue
    return str(max(numeric_ids, default=-1) + 1)


def _clear_streamlit_data_cache() -> None:
    try:
        import streamlit as st

        st.cache_data.clear()
    except Exception:
        pass


def _verify_persistence(expected_ids: set[str], *, absent_ids: set[str] | None = None) -> None:
    status = get_storage_status()
    if supabase_configured() and status.get("mode") != "SUPABASE":
        raise RuntimeError(
            "Exercise Repository could not be confirmed in Supabase. No success was recorded; retry after the storage connection is healthy."
        )

    verified = _ensure_store(load_state(force_refresh=True))
    actual_ids = {str((row or {}).get("id", "")) for row in verified.get(_REPOSITORY_KEY, [])}
    missing = expected_ids - actual_ids
    unexpected = set(absent_ids or set()) & actual_ids
    if missing or unexpected:
        raise RuntimeError(
            "Exercise Repository persistence verification failed. The submitted change was not confirmed after a fresh Supabase read."
        )


def _persist(
    db: dict[str, Any],
    *,
    expected_ids: set[str],
    absent_ids: set[str] | None = None,
) -> None:
    save_state(db)
    _verify_persistence(expected_ids, absent_ids=absent_ids)
    _clear_streamlit_data_cache()


def _validate_unique_title(
    rows: list[dict[str, Any]],
    title: str,
    *,
    ignore_id: str = "",
) -> str:
    clean_title = _clean(title)
    if not clean_title:
        raise ValueError("Exercise title is required.")
    title_key = clean_title.casefold()
    for row in rows:
        if ignore_id and str(row.get("id")) == str(ignore_id):
            continue
        if _clean(row.get("title")).casefold() == title_key:
            raise ValueError(
                "This exercise already exists in the repository. Edit the existing item instead."
            )
    return clean_title


def list_exercise_repository(active_only: bool = True) -> list[dict[str, Any]]:
    db = _ensure_store(load_state(force_refresh=True))
    changed = _migrate_legacy_repository(db)
    if changed:
        save_state(db)

    rows = [dict(_normalise(row)) for row in db[_REPOSITORY_KEY]]
    if active_only:
        rows = [row for row in rows if row.get("status") == "active"]
    rows.sort(
        key=lambda row: (
            0 if row.get("status") == "active" else 1,
            _clean(row.get("title")).casefold(),
        )
    )
    return rows


def exercise_repository_counts() -> dict[str, int]:
    rows = list_exercise_repository(active_only=False)
    active = sum(1 for row in rows if row.get("status") == "active")
    return {"active": active, "inactive": len(rows) - active, "total": len(rows)}


def add_exercise_repository_item(
    data: dict[str, Any],
    actor_id: str = "admin",
) -> dict[str, Any]:
    db = _ensure_store(load_state(force_refresh=True))
    _migrate_legacy_repository(db)
    title = _validate_unique_title(db[_REPOSITORY_KEY], (data or {}).get("title", ""))
    now = _now_iso()
    item_id = _next_numeric_id(db[_REPOSITORY_KEY])
    row = _normalise(
        {
            **dict(data or {}),
            "id": item_id,
            "source_id": item_id,
            "title": title,
            "status": (data or {}).get("status") or "active",
            "created_at": now,
            "created_by": actor_id or "admin",
            "updated_at": now,
            "updated_by": actor_id or "admin",
            "source": "exercise_repository",
        },
        fallback_id=item_id,
    )
    db[_REPOSITORY_KEY].append(row)
    _write_audit(db, "created", row, actor_id)
    _persist(db, expected_ids={item_id})
    return dict(row)


def update_exercise_repository_item(
    item_id: str,
    updates: dict[str, Any],
    actor_id: str = "admin",
) -> dict[str, Any]:
    db = _ensure_store(load_state(force_refresh=True))
    _migrate_legacy_repository(db)
    item_id = _clean(item_id)
    allowed = set(EXERCISE_COLUMNS) - {"status"}

    for index, raw in enumerate(db[_REPOSITORY_KEY]):
        row = _normalise(raw, fallback_id=str(index))
        if str(row.get("id")) != item_id:
            continue

        before = dict(row)
        next_title = _validate_unique_title(
            db[_REPOSITORY_KEY],
            (updates or {}).get("title", row.get("title", "")),
            ignore_id=item_id,
        )
        for key in allowed:
            if key in (updates or {}):
                row[key] = _clean((updates or {}).get(key))
        row["title"] = next_title
        if "status" in (updates or {}):
            row["status"] = _status((updates or {}).get("status"))
        row["updated_at"] = _now_iso()
        row["updated_by"] = actor_id or "admin"
        row = _normalise(row, fallback_id=item_id)
        db[_REPOSITORY_KEY][index] = row

        changes = {
            key: {"from": before.get(key, ""), "to": row.get(key, "")}
            for key in EXERCISE_COLUMNS
            if before.get(key, "") != row.get(key, "")
        }
        _write_audit(db, "updated", row, actor_id, changes=changes)
        _persist(db, expected_ids={item_id})
        return dict(row)

    raise ValueError("Exercise repository item was not found.")


def set_exercise_repository_status(
    item_id: str,
    active: bool,
    actor_id: str = "admin",
) -> dict[str, Any]:
    return update_exercise_repository_item(
        item_id,
        {"status": "active" if active else "inactive"},
        actor_id=actor_id,
    )


def delete_exercise_repository_item(
    item_id: str,
    actor_id: str = "admin",
) -> dict[str, Any]:
    db = _ensure_store(load_state(force_refresh=True))
    _migrate_legacy_repository(db)
    item_id = _clean(item_id)
    for index, raw in enumerate(db[_REPOSITORY_KEY]):
        row = _normalise(raw, fallback_id=str(index))
        if str(row.get("id")) != item_id:
            continue
        removed = db[_REPOSITORY_KEY].pop(index)
        _write_audit(db, "deleted", row, actor_id)
        remaining_ids = {str((item or {}).get("id", "")) for item in db[_REPOSITORY_KEY]}
        _persist(db, expected_ids=remaining_ids, absent_ids={item_id})
        return dict(_normalise(removed, fallback_id=item_id))
    raise ValueError("Exercise repository item was not found.")


def import_exercise_repository_items(
    rows: list[dict[str, Any]],
    actor_id: str = "admin",
) -> dict[str, int]:
    db = _ensure_store(load_state(force_refresh=True))
    _migrate_legacy_repository(db)
    existing_titles = {
        _clean(row.get("title")).casefold()
        for row in db[_REPOSITORY_KEY]
        if _clean(row.get("title"))
    }
    imported = 0
    skipped = 0
    new_ids: set[str] = set()
    now = _now_iso()

    for raw in rows or []:
        title = _clean((raw or {}).get("title"))
        if not title or title.casefold() in existing_titles:
            skipped += 1
            continue
        item_id = _next_numeric_id(db[_REPOSITORY_KEY])
        row = _normalise(
            {
                **dict(raw or {}),
                "id": item_id,
                "source_id": item_id,
                "title": title,
                "created_at": now,
                "created_by": actor_id or "admin",
                "updated_at": now,
                "updated_by": actor_id or "admin",
                "source": "exercise_csv_import",
            },
            fallback_id=item_id,
        )
        db[_REPOSITORY_KEY].append(row)
        _write_audit(db, "imported", row, actor_id)
        existing_titles.add(title.casefold())
        new_ids.add(item_id)
        imported += 1

    if imported:
        _persist(db, expected_ids=new_ids)
    return {"imported": imported, "skipped": skipped}
