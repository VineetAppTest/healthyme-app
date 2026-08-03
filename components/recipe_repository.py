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


RECIPE_COLUMNS = [
    "title",
    "description",
    "meal_type",
    "diet_type",
    "goal_tags",
    "condition_tags",
    "prep_time",
    "calories",
    "protein",
    "fat",
    "carbohydrates",
    "additional_nutrition",
    "servings",
    "portion_size",
    "image_url",
    "image_bucket",
    "image_path",
    "image_access_type",
    "ingredients",
    "steps",
    "nutrition",
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
        "resource_type": "recipes",
        "title": _clean(source.get("title")),
        "description": _clean(source.get("description")),
        "meal_type": _clean(source.get("meal_type")),
        "diet_type": _clean(source.get("diet_type")),
        "goal_tags": _clean(source.get("goal_tags")),
        "condition_tags": _clean(source.get("condition_tags")),
        "prep_time": _clean(source.get("prep_time")),
        "calories": _clean(source.get("calories")),
        "protein": _clean(source.get("protein")),
        "fat": _clean(source.get("fat")),
        "carbohydrates": _clean(source.get("carbohydrates")),
        "additional_nutrition": _clean(source.get("additional_nutrition")),
        "servings": _clean(source.get("servings")),
        "portion_size": _clean(source.get("portion_size")),
        "image_url": _clean(source.get("image_url")),
        "image_bucket": _clean(source.get("image_bucket")),
        "image_path": _clean(source.get("image_path")),
        "image_access_type": _clean(source.get("image_access_type")) or "public",
        "ingredients": _clean(source.get("ingredients")),
        "steps": _clean(source.get("steps")),
        "nutrition": _clean(source.get("nutrition")),
        "status": _status(source.get("status")),
        "created_at": _clean(source.get("created_at")),
        "created_by": _clean(source.get("created_by")),
        "updated_at": _clean(source.get("updated_at")),
        "updated_by": _clean(source.get("updated_by")),
        "source": _clean(source.get("source") or source.get("source_system"))
        or "recipe_repository",
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


def _recipe_payload(row: dict[str, Any]) -> dict[str, Any]:
    normalised = _normalise(row)
    return {
        column: normalised.get(column, "")
        for column in RECIPE_COLUMNS
        if column != "status"
    }


def _clear_streamlit_data_cache() -> None:
    try:
        import streamlit as st

        st.cache_data.clear()
    except Exception:
        pass


def _required_title(value: Any) -> str:
    title = _clean(value)
    if not title:
        raise ValueError("Recipe title is required.")
    return title


def list_recipe_repository(active_only: bool = True) -> list[dict[str, Any]]:
    rows = [
        _from_canonical(row)
        for row in list_repository_items("recipe", active_only=active_only)
    ]
    rows.sort(
        key=lambda row: (
            0 if row.get("status") == "active" else 1,
            _clean(row.get("title")).casefold(),
            _clean(row.get("source_id")),
        )
    )
    return rows


def recipe_repository_counts() -> dict[str, int]:
    rows = list_recipe_repository(active_only=False)
    active = sum(1 for row in rows if row.get("status") == "active")
    return {"active": active, "inactive": len(rows) - active, "total": len(rows)}


def add_recipe_repository_item(
    data: dict[str, Any],
    actor_id: str = "admin",
) -> dict[str, Any]:
    title = _required_title((data or {}).get("title"))
    row = _normalise(
        {
            **dict(data or {}),
            "title": title,
            "status": (data or {}).get("status") or "active",
            "source": "recipe_repository",
        }
    )
    stored = create_numeric_repository_item(
        "recipe",
        title,
        _recipe_payload(row),
        status=row["status"],
        actor_id=actor_id or "admin",
        source_system="recipe_repository",
    )
    _clear_streamlit_data_cache()
    return _from_canonical(stored)


def update_recipe_repository_item(
    item_id: str,
    updates: dict[str, Any],
    actor_id: str = "admin",
) -> dict[str, Any]:
    clean_id = _clean(item_id)
    canonical = get_repository_item("recipe", clean_id)
    if not canonical:
        raise ValueError("Recipe repository item was not found.")

    current = _from_canonical(canonical)
    next_title = _required_title(
        (updates or {}).get("title", current.get("title", ""))
    )
    merged = dict(current)
    for key in RECIPE_COLUMNS:
        if key in (updates or {}):
            merged[key] = (updates or {}).get(key)
    merged["title"] = next_title
    merged["status"] = _status(merged.get("status"))
    merged = _normalise(merged, fallback_id=clean_id)

    stored = save_repository_item(
        "recipe",
        clean_id,
        next_title,
        _recipe_payload(merged),
        status=merged["status"],
        actor_id=actor_id or "admin",
        source_system=canonical.get("source_system") or "recipe_repository",
        legacy_reference=canonical.get("legacy_reference") or "",
    )
    _clear_streamlit_data_cache()
    return _from_canonical(stored)


def set_recipe_repository_status(
    item_id: str,
    active: bool,
    actor_id: str = "admin",
) -> dict[str, Any]:
    clean_id = _clean(item_id)
    stored = set_repository_item_status(
        "recipe",
        clean_id,
        active=bool(active),
        actor_id=actor_id or "admin",
    )
    _clear_streamlit_data_cache()
    return _from_canonical(stored)


def delete_recipe_repository_item(
    item_id: str,
    actor_id: str = "admin",
) -> dict[str, Any]:
    """Compatibility alias: deletion is a safe inactive-status transition."""
    return set_recipe_repository_status(item_id, False, actor_id=actor_id)
