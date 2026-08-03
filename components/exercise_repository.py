from __future__ import annotations

import html
import re
from typing import Any

from components.content_repository_store import (
    create_numeric_repository_item,
    get_repository_item,
    list_repository_items,
    save_repository_item,
    set_repository_item_status,
)


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


def _clean(value: Any) -> str:
    text = html.unescape(str(value or "")).strip()
    if text.lower() in {"nan", "none", "null"}:
        return ""
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _status(value: Any) -> str:
    return (
        "inactive"
        if _clean(value).lower() in {"inactive", "stopped", "archived"}
        else "active"
    )


def _normalise(
    row: dict[str, Any] | None,
    *,
    fallback_id: str = "",
) -> dict[str, Any]:
    source = dict(row or {})
    item_id = _clean(source.get("id") or source.get("source_id") or fallback_id)
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
        "source": _clean(source.get("source") or source.get("source_system"))
        or "exercise_repository",
        "content_version": source.get("content_version") or "",
        "legacy_reference": _clean(source.get("legacy_reference")),
    }


def _from_canonical(row: dict[str, Any] | None) -> dict[str, Any]:
    source = dict(row or {})
    payload = dict(source.get("payload") or {})
    return _normalise(
        {
            **payload,
            "id": source.get("source_id"),
            "source_id": source.get("source_id"),
            "title": source.get("display_name") or payload.get("title"),
            "status": source.get("status"),
            "created_at": source.get("created_at"),
            "created_by": source.get("created_by"),
            "updated_at": source.get("updated_at"),
            "updated_by": source.get("updated_by"),
            "source": source.get("source_system"),
            "content_version": source.get("content_version"),
            "legacy_reference": source.get("legacy_reference"),
        }
    )


def _exercise_payload(row: dict[str, Any]) -> dict[str, Any]:
    normalised = _normalise(row)
    return {
        column: normalised.get(column, "")
        for column in EXERCISE_COLUMNS
        if column != "status"
    }


def _clear_streamlit_data_cache() -> None:
    try:
        import streamlit as st

        st.cache_data.clear()
    except Exception:
        pass


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


def _next_numeric_id(rows: list[dict[str, Any]]) -> str:
    """Compatibility helper retained for callers/tests; creation is DB-atomic."""
    numeric_ids: list[int] = []
    for row in rows:
        try:
            numeric_ids.append(int(str(row.get("id", "")).strip()))
        except Exception:
            continue
    return str(max(numeric_ids, default=-1) + 1)


def list_exercise_repository(active_only: bool = True) -> list[dict[str, Any]]:
    rows = [
        _from_canonical(row)
        for row in list_repository_items("exercise", active_only=active_only)
    ]
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
    existing = list_exercise_repository(active_only=False)
    title = _validate_unique_title(existing, (data or {}).get("title", ""))
    row = _normalise(
        {
            **dict(data or {}),
            "title": title,
            "status": (data or {}).get("status") or "active",
            "source": "exercise_repository",
        }
    )
    stored = create_numeric_repository_item(
        "exercise",
        title,
        _exercise_payload(row),
        status=row["status"],
        actor_id=actor_id or "admin",
        source_system="exercise_repository",
    )
    _clear_streamlit_data_cache()
    return _from_canonical(stored)


def update_exercise_repository_item(
    item_id: str,
    updates: dict[str, Any],
    actor_id: str = "admin",
) -> dict[str, Any]:
    clean_id = _clean(item_id)
    canonical = get_repository_item("exercise", clean_id)
    if not canonical:
        raise ValueError("Exercise repository item was not found.")

    existing_rows = list_exercise_repository(active_only=False)
    current = _from_canonical(canonical)
    next_title = _validate_unique_title(
        existing_rows,
        (updates or {}).get("title", current.get("title", "")),
        ignore_id=clean_id,
    )

    merged = dict(current)
    allowed = set(EXERCISE_COLUMNS)
    for key in allowed:
        if key in (updates or {}):
            merged[key] = (updates or {}).get(key)
    merged["title"] = next_title
    merged["status"] = _status(merged.get("status"))
    merged = _normalise(merged, fallback_id=clean_id)

    stored = save_repository_item(
        "exercise",
        clean_id,
        next_title,
        _exercise_payload(merged),
        status=merged["status"],
        actor_id=actor_id or "admin",
        source_system=canonical.get("source_system") or "exercise_repository",
        legacy_reference=canonical.get("legacy_reference") or "",
    )
    _clear_streamlit_data_cache()
    return _from_canonical(stored)


def set_exercise_repository_status(
    item_id: str,
    active: bool,
    actor_id: str = "admin",
) -> dict[str, Any]:
    clean_id = _clean(item_id)
    stored = set_repository_item_status(
        "exercise",
        clean_id,
        active=bool(active),
        actor_id=actor_id or "admin",
    )
    _clear_streamlit_data_cache()
    return _from_canonical(stored)


def delete_exercise_repository_item(
    item_id: str,
    actor_id: str = "admin",
) -> dict[str, Any]:
    """Compatibility alias: deletion is a safe inactive-status transition."""
    return set_exercise_repository_status(item_id, False, actor_id=actor_id)


def import_exercise_repository_items(
    rows: list[dict[str, Any]],
    actor_id: str = "admin",
) -> dict[str, int]:
    existing = list_exercise_repository(active_only=False)
    existing_titles = {
        _clean(row.get("title")).casefold()
        for row in existing
        if _clean(row.get("title"))
    }
    imported = 0
    skipped = 0

    for raw in rows or []:
        title = _clean((raw or {}).get("title"))
        if not title or title.casefold() in existing_titles:
            skipped += 1
            continue
        row = _normalise(
            {
                **dict(raw or {}),
                "title": title,
                "status": (raw or {}).get("status") or "active",
                "source": "exercise_csv_import",
            }
        )
        create_numeric_repository_item(
            "exercise",
            title,
            _exercise_payload(row),
            status=row["status"],
            actor_id=actor_id or "admin",
            source_system="exercise_csv_import",
        )
        existing_titles.add(title.casefold())
        imported += 1

    if imported:
        _clear_streamlit_data_cache()
    return {"imported": imported, "skipped": skipped}
