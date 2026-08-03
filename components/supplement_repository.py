from __future__ import annotations

import html
import re
import uuid
from typing import Any

from components.content_repository_store import (
    get_repository_item,
    list_repository_items,
    save_repository_item,
    set_repository_item_status,
)


SUPPLEMENT_FIELDS = (
    "supplement_name",
    "title",
    "dosage",
    "frequency",
    "timing",
    "instructions",
    "admin_notes",
    "legacy_source_id",
)


def _clean(value: Any) -> str:
    text = html.unescape(str(value or "")).strip()
    text = re.sub(r"<\s*br\s*/?\s*>", ", ", text, flags=re.I)
    text = re.sub(r"<\s*[^>]*>", " ", text)
    text = re.sub(r"\s+", " ", text).strip(" ,;:-")
    if text.lower() in {"nan", "none", "null"}:
        return ""
    return text


def _canonical_status(value: Any) -> str:
    return (
        "inactive"
        if _clean(value).lower() in {"inactive", "stopped", "archived"}
        else "active"
    )


def _legacy_status(value: Any) -> str:
    return "Inactive" if _canonical_status(value) == "inactive" else "Active"


def _normalise(
    row: dict[str, Any] | None,
    *,
    fallback_id: str = "",
) -> dict[str, Any]:
    source = dict(row or {})
    item_id = _clean(source.get("id") or source.get("source_id") or fallback_id)
    name = _clean(
        source.get("supplement_name")
        or source.get("name")
        or source.get("title")
    )
    return {
        "id": item_id,
        "source_id": item_id,
        "supplement_name": name,
        "title": name,
        "dosage": _clean(source.get("dosage") or source.get("default_dosage")),
        "frequency": _clean(
            source.get("frequency") or source.get("default_frequency")
        ),
        "timing": _clean(source.get("timing") or source.get("default_timing")),
        "instructions": _clean(source.get("instructions")),
        "admin_notes": _clean(source.get("admin_notes") or source.get("notes")),
        "status": _legacy_status(source.get("status")),
        "created_at": _clean(source.get("created_at")),
        "created_by": _clean(source.get("created_by")),
        "updated_at": _clean(source.get("updated_at")),
        "updated_by": _clean(source.get("updated_by")),
        "source": _clean(source.get("source") or source.get("source_system"))
        or "supplement_repository",
        "legacy_source_id": _clean(source.get("legacy_source_id")),
        "legacy_reference": _clean(source.get("legacy_reference")),
        "content_version": source.get("content_version") or "",
    }


def _from_canonical(row: dict[str, Any] | None) -> dict[str, Any]:
    source = dict(row or {})
    payload = dict(source.get("payload") or {})
    return _normalise(
        {
            **payload,
            "id": source.get("source_id"),
            "source_id": source.get("source_id"),
            "supplement_name": source.get("display_name")
            or payload.get("supplement_name")
            or payload.get("title"),
            "status": source.get("status"),
            "created_at": source.get("created_at"),
            "created_by": source.get("created_by"),
            "updated_at": source.get("updated_at"),
            "updated_by": source.get("updated_by"),
            "source": source.get("source_system"),
            "legacy_reference": source.get("legacy_reference"),
            "content_version": source.get("content_version"),
        }
    )


def _supplement_payload(row: dict[str, Any]) -> dict[str, Any]:
    normalised = _normalise(row)
    return {
        field: normalised.get(field, "")
        for field in SUPPLEMENT_FIELDS
    }


def _clear_streamlit_data_cache() -> None:
    try:
        import streamlit as st

        st.cache_data.clear()
    except Exception:
        pass


def _validate_unique_name(
    rows: list[dict[str, Any]],
    name: str,
    *,
    ignore_id: str = "",
) -> str:
    clean_name = _clean(name)
    if not clean_name:
        raise ValueError("Supplement name is required.")
    key = clean_name.casefold()
    for row in rows:
        if ignore_id and str(row.get("id")) == str(ignore_id):
            continue
        if _clean(row.get("supplement_name")).casefold() == key:
            raise ValueError(
                "This supplement already exists in the repository. Edit the existing item instead."
            )
    return clean_name


def _new_source_id() -> str:
    """Generate a durable suprepo_* ID and defend against an unlikely collision."""
    for _attempt in range(10):
        source_id = f"suprepo_{uuid.uuid4().hex[:8]}"
        if get_repository_item("supplement", source_id) is None:
            return source_id
    raise RuntimeError("Could not allocate a unique Supplement Repository ID.")


def list_supplement_repository(active_only: bool = True) -> list[dict[str, Any]]:
    rows = [
        _from_canonical(row)
        for row in list_repository_items("supplement", active_only=active_only)
    ]
    rows.sort(
        key=lambda row: (
            0 if row.get("status") == "Active" else 1,
            _clean(row.get("supplement_name")).casefold(),
            _clean(row.get("id")),
        )
    )
    return rows


def supplement_repository_counts() -> dict[str, int]:
    rows = list_supplement_repository(active_only=False)
    active = sum(1 for row in rows if row.get("status") == "Active")
    return {"active": active, "inactive": len(rows) - active, "total": len(rows)}


def add_supplement_repository_item(
    data: dict[str, Any],
    actor_id: str = "admin",
) -> dict[str, Any]:
    existing = list_supplement_repository(active_only=False)
    name = _validate_unique_name(
        existing,
        (data or {}).get("supplement_name") or (data or {}).get("name"),
    )
    source_id = _new_source_id()
    row = _normalise(
        {
            **dict(data or {}),
            "id": source_id,
            "source_id": source_id,
            "supplement_name": name,
            "status": "Active",
            "source": "supplement_repository",
        },
        fallback_id=source_id,
    )
    stored = save_repository_item(
        "supplement",
        source_id,
        name,
        _supplement_payload(row),
        status="active",
        actor_id=actor_id or "admin",
        source_system="supplement_repository",
    )
    _clear_streamlit_data_cache()
    return _from_canonical(stored)


def update_supplement_repository_item(
    item_id: str,
    updates: dict[str, Any],
    actor_id: str = "admin",
) -> dict[str, Any]:
    clean_id = _clean(item_id)
    canonical = get_repository_item("supplement", clean_id)
    if not canonical:
        raise ValueError("Supplement repository item was not found.")

    current = _from_canonical(canonical)
    existing_rows = list_supplement_repository(active_only=False)
    next_name = _validate_unique_name(
        existing_rows,
        (updates or {}).get("supplement_name", current.get("supplement_name")),
        ignore_id=clean_id,
    )

    merged = dict(current)
    allowed = {
        "supplement_name",
        "dosage",
        "frequency",
        "timing",
        "instructions",
        "admin_notes",
    }
    for key in allowed:
        if key in (updates or {}):
            merged[key] = (updates or {}).get(key)
    merged["supplement_name"] = next_name
    merged["title"] = next_name
    merged = _normalise(merged, fallback_id=clean_id)

    stored = save_repository_item(
        "supplement",
        clean_id,
        next_name,
        _supplement_payload(merged),
        status=_canonical_status(merged.get("status")),
        actor_id=actor_id or "admin",
        source_system=canonical.get("source_system") or "supplement_repository",
        legacy_reference=canonical.get("legacy_reference") or "",
    )
    _clear_streamlit_data_cache()
    return _from_canonical(stored)


def set_supplement_repository_status(
    item_id: str,
    active: bool,
    actor_id: str = "admin",
) -> dict[str, Any]:
    clean_id = _clean(item_id)
    stored = set_repository_item_status(
        "supplement",
        clean_id,
        active=bool(active),
        actor_id=actor_id or "admin",
    )
    _clear_streamlit_data_cache()
    return _from_canonical(stored)
